import json
import re
import uuid
from datetime import datetime
from collections import defaultdict
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional

from llm import call_llm, extract_json
from logger import clip, get_logger
from memory import MemoryStore
from tools import TOOL_DOCS, ToolBox

log = get_logger("agent")

MAX_TOOL_STEPS = 8
TOOL_CALL_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
FILE_CONTENT_RE = re.compile(r"<file_content>\n?(.*?)\n?</file_content>", re.DOTALL)
FILE_TAG_RE = re.compile(r"</?file_content>\n?")


class TaskStatus(Enum):
    PENDING = auto()
    COMPLETED = auto()
    FAILED = auto()


ROLE_INSTRUCTIONS = {
    "writer": "You are a professional Writer. Produce polished, well-structured content. Output only the final content.",
    "researcher": "You are a careful Researcher. Give accurate, organized findings and say when unsure. Output only the findings.",
    "coder": ("You are an expert Coder. Write complete, runnable, commented code, then a short usage note. "
              "Only write code when the task asks for code; for tasks about files, projects or research use your tools."),
    "chat": ("You are a friendly, concise assistant talking directly to the user. Use the USER SUMMARY and "
             "USER PROJECT INDEX to answer questions about the user (name, background, projects), and your "
             "tools if you need project details or the web. If the user is just sharing information about "
             "themselves, acknowledge it in one or two sentences."),
}


class Task:
    def __init__(self, task: str, role: Optional[str], task_id: str,
                 input_from_tasks: list[str], acceptance_criteria: list[str]):
        self.task = task
        self.role = role
        self.task_id = task_id
        self.input_from_tasks = input_from_tasks
        self.acceptance_criteria = acceptance_criteria
        self.status = TaskStatus.PENDING
        self.result: Optional[str] = None
        self.feedback = ""
        self.retries = 0
        self.agent_name: Optional[str] = None
        self.actions: list[str] = []
        self.saved_path: Optional[Path] = None


def memory_context(memory: MemoryStore) -> str:
    """Always-on memory: the summary and the project index (no details)."""
    summary = memory.get_summary() or "(nothing known yet)"
    index = memory.project_index()
    index_text = "\n".join(f"- {p['name']}: {p['description']}" for p in index) or "(none)"
    return f"<<USER SUMMARY>>\n{summary}\n\n<<USER PROJECT INDEX>>\n{index_text}\n"


class TaskAgent:
    """Worker agent. Runs a tool loop: LLM -> optional tool call -> result -> LLM ..."""

    def __init__(self, name: str, role: str, tools: ToolBox, memory: MemoryStore):
        self.name, self.role, self.tools, self.memory = name, role, tools, memory
        self.actions: list[str] = []

    def _record(self, tool: str, args: dict, result: str) -> None:
        """Keep a compact log of what this agent did, so the verifier can check it."""
        shown = {k: v for k, v in args.items() if k != "content"}
        entry = f"{tool} {json.dumps(shown, ensure_ascii=False)} -> {clip(result, 200)}"
        if args.get("content"):
            entry += f"\n   file text ({len(args['content'])} chars), first 1500 chars:\n{args['content'][:1500]}"
        self.actions.append(entry)

    def run(self, prompt: str) -> str:
        self.actions = []
        system = ROLE_INSTRUCTIONS[self.role] + "\n" + TOOL_DOCS
        base = memory_context(self.memory) + "\n<<TASK>>\n" + prompt
        transcript = ""

        for step in range(1, MAX_TOOL_STEPS + 1):
            log.info("%s: thinking (step %d/%d)", self.name, step, MAX_TOOL_STEPS)
            reply = call_llm(system, base + transcript)
            match = TOOL_CALL_RE.search(reply)
            if not match:
                reply = FILE_TAG_RE.sub("", reply).strip()
                log.info("%s: final answer ready (%d chars) after %d step(s)",
                         self.name, len(reply), step)
                return reply
            try:
                call = json.loads(match.group(1), strict=False)  # tolerate raw newlines in strings
                args = call.get("args")
                if not isinstance(args, dict) or not args:
                    # Models often put the parameters next to "tool" instead of inside "args".
                    args = {k: v for k, v in call.items() if k not in ("tool", "args")}
                if call.get("tool") == "file_op" and "content" not in args:
                    block = FILE_CONTENT_RE.search(reply)
                    if block:
                        args["content"] = block.group(1)
                result = self.tools.call(call["tool"], args)
                self._record(call["tool"], args, result)
                if (call["tool"] == "file_op" and args.get("op") in ("create", "update")
                        and result.startswith(("Created", "Updated"))):
                    result += ("\nThe file is saved. Do NOT write it again. Give your final answer now: a short "
                               "report of what you saved (file name + 2-3 line summary), unless you still "
                               "need another tool.")
            except Exception as exc:
                log.error("%s: tool call failed: %s", self.name, clip(exc, 200))
                result = f"Tool error: {exc}"
            transcript += f"\n\n[Your tool call]: {match.group(0)}\n[Tool result]:\n{result}"

        log.warning("%s: tool budget (%d) exhausted, forcing final answer", self.name, MAX_TOOL_STEPS)
        final = call_llm(
            system,
            base + transcript + "\n\nTool budget used up. Give your FINAL answer now, with no tool call. "
            "If you saved the deliverable to a file, give a short report of what you saved instead of "
            "pasting its text again.",
        )
        return FILE_TAG_RE.sub("", final).strip()


class Verifier:
    SYSTEM = (
        "You are a strict but fair Verifier. You get a task, acceptance criteria, a result and the "
        "TOOL ACTIVITY (what the agent actually did with its tools). Judge the result together with the "
        "tool activity: a file the agent really created or a search it really ran counts as delivered. "
        'Return valid JSON only: {"passed": true or false, "feedback": "short, specific explanation"}'
    )

    def verify(self, task: Task, output: str) -> tuple[bool, str]:
        if not output.strip():
            log.warning("[%s] verifier: empty result", task.task_id)
            return False, "The result is empty."
        criteria = task.acceptance_criteria or ["The result fully and correctly completes the task."]
        prompt = (
            f"TASK:\n{task.task}\n\nACCEPTANCE CRITERIA:\n"
            + "\n".join(f"- {c}" for c in criteria)
            + f"\n\nRESULT:\n{output}\n"
            + "\nTOOL ACTIVITY:\n" + ("\n".join(f"- {a}" for a in task.actions) or "(no tools used)") + "\n"
        )
        try:
            verdict = extract_json(call_llm(self.SYSTEM, prompt))
            passed = bool(verdict.get("passed", False))
            feedback = str(verdict.get("feedback", "")) or "-"
            log.info("[%s] verifier: %s - %s", task.task_id,
                     "PASSED" if passed else "REJECTED", clip(feedback, 200))
            return passed, feedback
        except Exception as exc:
            log.error("[%s] verifier produced no valid verdict: %s", task.task_id, exc)
            return False, f"Verifier could not produce a valid verdict: {exc}"


class MemoryUpdater:
    """Runs ONCE per session, after the work. Keeps the summary and projects current.

    It only WRITES memory. Reading is never LLM-decided.
    """

    SYSTEM = """
You maintain long-term memory about a user. You receive the CURRENT SUMMARY, the CURRENT
PROJECTS, and the user's NEW MESSAGE. Return valid JSON only:
{
  "summary": "<updated summary of who the user is: background, skills, goals, habits, preferences. Under 200 words. Keep still-valid facts.>",
  "projects": [
    {"name": "<project name>", "description": "<one line>", "details": "<full details: goal, stack, architecture, status, decisions>"}
  ]
}
Record only facts the user STATES about themselves or their projects. A request to do something
(research, write a file, implement) is NOT a fact about the project.
Rules: only include projects that are new or changed by the NEW MESSAGE (use the same
name for an existing project and give its COMPLETE updated details). Never invent facts.
If nothing durable was said, return the current summary unchanged and "projects": [].
"""

    def __init__(self, memory: MemoryStore):
        self.memory = memory

    def update(self, user_message: str) -> None:
        current_projects = self.memory.all_projects()
        prompt = (
            f"CURRENT SUMMARY:\n{self.memory.get_summary() or '(empty)'}\n\n"
            f"CURRENT PROJECTS:\n{json.dumps(current_projects, indent=2)}\n\n"
            f"NEW MESSAGE:\n{user_message}"
        )
        log.info("Memory update: analysing the user's message")
        try:
            data = extract_json(call_llm(self.SYSTEM, prompt))
        except Exception as exc:
            log.error("Memory update skipped (could not parse LLM output): %s", exc)
            return
        if isinstance(data.get("summary"), str) and data["summary"].strip():
            self.memory.set_summary(data["summary"].strip())
        projects = [p for p in data.get("projects", []) if p.get("name") and p.get("details")]
        for p in projects:
            self.memory.upsert_project(p["name"], p.get("description", ""), p["details"])
        log.info("Memory update done: summary refreshed, %d project(s) written", len(projects))


class Orchestrator:
    PLANNER = """
You are an Orchestrator. Convert a user request into a dependency-aware task plan.
Return valid JSON only: a list of objects, each with exactly these keys:
- "subtask": string, a clear self-contained instruction for one agent
- "taskAssignedTo": one of "writer", "researcher", "coder", or null if no role fits
- "taskId": string like "T1", "T2", ... (unique)
- "inputFromTasks": list of taskIds whose output this task needs ([] if none)
- "acceptanceCriteria": list of 1-3 short, checkable criteria
Use the user summary and project index to make subtasks specific to the user.
Split independent outcomes into separate tasks. Do not add markdown or commentary.
Every agent has tools to list/read/write files, search the web and look up the user's projects.
So do NOT create a separate task just to list, read or write a file: include that step inside the
task of the agent that produces the content (usually the writer). Prefer 2-4 tasks. Use "coder"
only when the user actually wants code written.
If the message only shares information about the user (background, projects, goals), or is a simple
question or chat message answerable from the user summary and project index, return an empty list: []
(a separate assistant will reply to it).
"""

    def __init__(self, memory: MemoryStore, workspace: Path, max_retries: int = 2):
        self.memory = memory
        self.tools = ToolBox(memory, workspace)
        self.verifier = Verifier()
        self.updater = MemoryUpdater(memory)
        self.max_retries = max_retries
        self._rr: dict[str, int] = defaultdict(int)
        names = {"writer": ["Ahmad", "Akram"], "researcher": ["Ali", "Asad"], "coder": ["Saqib", "Bilal"]}
        self.agents = {
            role: [TaskAgent(n, role, self.tools, memory) for n in ns] for role, ns in names.items()
        }
        self.results: dict[str, str] = {}
        self.chat_agent = TaskAgent("Assistant", "chat", self.tools, memory)
        self.last_reply = ""

    def _pick_agent(self, role: str) -> TaskAgent:
        pool = self.agents[role]
        agent = pool[self._rr[role] % len(pool)]
        self._rr[role] += 1
        return agent

    def plan(self, prompt: str) -> list[Task]:
        log.info("Planning: %s", clip(prompt, 150))
        raw = call_llm(self.PLANNER, memory_context(self.memory) + f"\nUSER REQUEST:\n{prompt}")
        try:
            plan = extract_json(raw)
        except ValueError:
            log.error("Planner output was not valid JSON. Raw output:\n%s", raw)
            raise
        if not isinstance(plan, list):
            log.error("Planner returned %s instead of a list. Raw output:\n%s", type(plan).__name__, raw)
            raise ValueError("Planner did not return a JSON list of tasks.")
        if isinstance(plan, dict):
            plan = plan.get("tasks", [plan])
        tasks = []
        for i, item in enumerate(plan, start=1):
            role = str(item.get("taskAssignedTo") or "").lower()
            tasks.append(Task(
                task=str(item.get("subtask", "")).strip(),
                role=role if role in self.agents else None,
                task_id=str(item.get("taskId") or f"T{i}"),
                input_from_tasks=[str(d) for d in item.get("inputFromTasks", [])],
                acceptance_criteria=[str(c) for c in item.get("acceptanceCriteria", [])],
            ))
        tasks = [t for t in tasks if t.task]
        log.info("Plan ready: %d task(s)", len(tasks))
        for t in tasks:
            log.info("  %s [%s] depends on %s: %s", t.task_id, t.role or "no-role",
                     t.input_from_tasks or "-", clip(t.task, 100))
        return tasks

    def _run_task(self, task: Task, deps: list[Task]) -> None:
        agent = self._pick_agent(task.role)
        task.agent_name = agent.name
        prompt = task.task
        if deps:
            prompt += "\n\nPrerequisite outputs:\n" + json.dumps({d.task_id: self.results[d.task_id] for d in deps})

        attempt_prompt = prompt
        for attempt in range(self.max_retries + 1):
            log.info("[%s] START %s (%s) attempt %d/%d", task.task_id, agent.name,
                     task.role, attempt + 1, self.max_retries + 1)
            try:
                output = agent.run(attempt_prompt)
                task.actions = list(agent.actions)
            except Exception as exc:
                log.error("[%s] execution error: %s", task.task_id, clip(exc, 200))
                log.debug("[%s] traceback", task.task_id, exc_info=True)
                task.feedback = f"Execution error: {exc}"
                attempt_prompt = prompt + f"\n\nPrevious attempt errored: {exc}. Try again."
                continue
            passed, feedback = self.verifier.verify(task, output)
            task.result, task.feedback = output, feedback
            if passed:
                task.status = TaskStatus.COMPLETED
                self.results[task.task_id] = output
                log.info("[%s] COMPLETED", task.task_id)
                return
            task.retries += 1
            log.warning("[%s] rejected, retrying with feedback", task.task_id)
            attempt_prompt = prompt + f"\n\nYour previous attempt was rejected. Feedback:\n{feedback}\nFix these issues."
        task.status = TaskStatus.FAILED
        log.error("[%s] FAILED after %d attempt(s): %s", task.task_id,
                  self.max_retries + 1, clip(task.feedback, 200))

    def _save_outputs(self, tasks: list[Task]) -> None:
        """Write every completed task's full output to <workspace>/outputs/<timestamp>/."""
        out_dir = self.tools.workspace / "outputs" / datetime.now().strftime("%Y%m%d_%H%M%S")
        for t in tasks:
            if t.status != TaskStatus.COMPLETED or not t.result:
                continue
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / f"{t.task_id}_{t.role}_{t.agent_name}.md"
            path.write_text(f"<!-- Task {t.task_id}: {t.task} -->\n\n{t.result}\n", encoding="utf-8")
            t.saved_path = path
            log.info("[%s] output saved: %s", t.task_id, path)

    def execute(self, prompt: str) -> list[Task]:
        tasks = self.plan(prompt)
        self.last_reply = ""
        if not tasks:
            log.info("No tasks planned; answering directly")
            try:
                self.last_reply = self.chat_agent.run(prompt)
            except Exception as exc:  # noqa: BLE001
                log.error("Direct reply failed: %s", clip(exc, 200))
                self.last_reply = "Sorry, I could not reply (see logs/agent.log)."
        by_id = {t.task_id: t for t in tasks}
        pending = list(tasks)

        while pending:
            progressed = False
            for task in list(pending):
                deps = [by_id.get(d) for d in task.input_from_tasks]
                if any(d is None for d in deps) or any(d.status == TaskStatus.FAILED for d in deps):
                    task.status, task.feedback = TaskStatus.FAILED, "Unknown or failed prerequisite."
                    log.error("[%s] skipped: %s", task.task_id, task.feedback)
                elif any(d.status != TaskStatus.COMPLETED for d in deps):
                    continue
                elif task.role is None:
                    task.status, task.feedback = TaskStatus.FAILED, "No eligible agent for this task."
                    log.error("[%s] skipped: %s", task.task_id, task.feedback)
                else:
                    self._run_task(task, deps)
                pending.remove(task)
                progressed = True
            if not progressed:  # circular dependency
                for task in pending:
                    task.status, task.feedback = TaskStatus.FAILED, "Circular or unresolved dependency."
                pending.clear()

        done = sum(t.status == TaskStatus.COMPLETED for t in tasks)
        log.info("Session finished: %d/%d task(s) completed", done, len(tasks))
        self._save_outputs(tasks)
        self.updater.update(prompt)
        return tasks


def print_report(tasks: list[Task]) -> None:
    print("\n=== REPORT ===")
    for t in tasks:
        print(f"{t.task_id} [{t.role or '-'}] {t.status.name}: {t.task[:70]}")
        print(f"    verifier: {t.feedback or '-'}")
        if t.status == TaskStatus.COMPLETED and t.result:
            print(f"    output  : {' '.join(t.result.split())[:100]}...")
            print(f"    saved   : {t.saved_path}")


if __name__ == "__main__":
    workspace = Path(input("Workspace folder (absolute path): ").strip().strip('"')).expanduser()
    memory = MemoryStore("memory.db")
    orchestrator = Orchestrator(memory, workspace)
    print("Ready. Type a task, or 'exit'.")
    while True:
        user_prompt = input("\nTask: ").strip()
        if user_prompt.lower() in ("exit", "quit"):
            break
        if user_prompt:
            try:
                tasks = orchestrator.execute(user_prompt)
                if tasks:
                    print_report(tasks)
                else:
                    print(f"\n{orchestrator.last_reply}")
            except KeyboardInterrupt:
                log.warning("Interrupted by user")
                break
            except Exception:
                log.exception("Task crashed with an unhandled error")
                print("\nTask failed. Full details are in logs/agent.log")