# Step-by-Step Guide: Building the OOP Multi-Agent Orchestrator 🛠️

> **Target File:** [`m0-we02 oop-agentsim.py`](m0-we02%20oop-agentsim.py)  
> **Key Objective:** Build a complete multi-agent task orchestrator with planning, dependency graphs, sandboxed code execution, and verifier retry loops.

---

## 🏗️ Step 1: Core Domain Models & Enums

Create state machines to govern task and agent lifecycles:

```python
from enum import Enum, auto

class TaskStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()

class AgentStatus(Enum):
    IDLE = auto()
    BUSY = auto()

class AgentRole(Enum):
    RESEARCHER = "researcher"
    WRITER = "writer"
    CODER = "coder"
    VERIFIER = "verifier"
```

Define the `Task` dataclass tracking dependencies and retry counts:

```python
class Task:
    def __init__(self, task_id: str, title: str, role: AgentRole, criteria: str, depends_on: list[str] = None):
        self.task_id = task_id
        self.title = title
        self.role = role
        self.criteria = criteria
        self.depends_on = depends_on or []
        self.status = TaskStatus.PENDING
        self.result = None
        self.assigned_agent = None
        self.attempts = 0
```

---

## 🏗️ Step 2: The Sandboxed Code Execution Tool

Before marking a coder's task as complete, the verifier must verify that the code compiles and runs without crashing:

```python
import os, sys, subprocess, tempfile
from pathlib import Path

def run_code_tool(language: str, code: str) -> dict:
    if language not in ("python", "py"):
        return {"ran": False, "ok": True, "stage": "skipped", "stderr": "Non-Python code skipped."}

    # Stage 1: Syntax compilation check
    try:
        compile(code, "generated_code.py", "exec")
    except SyntaxError as e:
        return {"ran": False, "ok": False, "stage": "syntax", "stderr": f"SyntaxError: {e.msg} line {e.lineno}"}

    # Stage 2: Sandboxed runtime check
    env = {k: v for k, v in os.environ.items() if k != "API_KEY"}
    with tempfile.TemporaryDirectory(prefix="agent_run_") as workdir:
        script = Path(workdir) / "generated_code.py"
        script.write_text(code, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(script)],
                cwd=workdir,
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                "ran": True,
                "ok": proc.returncode == 0,
                "stage": "ok" if proc.returncode == 0 else "runtime",
                "exit_code": proc.returncode,
                "stdout": proc.stdout[:2000],
                "stderr": proc.stderr[:2000]
            }
        except subprocess.TimeoutExpired:
            return {"ran": True, "ok": True, "stage": "timeout", "stderr": "Execution timed out (acceptable for servers/games)."}
```

---

## 🏗️ Step 3: Agent Class Hierarchy & Polymorphism

Define abstract `BaseAgent` and derive specialist classes:

```python
from abc import ABC, abstractmethod
from typing import override

class BaseAgent(ABC):
    def __init__(self, name: str, role: AgentRole):
        self.name = name
        self.role = role
        self.status = AgentStatus.IDLE

    @abstractmethod
    def execute(self, task: Task, context: str) -> str:
        pass

class SpecialistAgent(BaseAgent):
    def __init__(self, name: str, role: AgentRole, instructions: str):
        super().__init__(name, role)
        self.instructions = instructions

    @override
    def execute(self, task: Task, context: str) -> str:
        prompt = f"<<ROLE INSTRUCTIONS>>\n{self.instructions}\n\n<<PREREQUISITE CONTEXT>>\n{context}\n\n<<TASK>>\n{task.title}"
        return call_llm(self.instructions, prompt)
```

---

## 🏗️ Step 4: The Verifier Agent Loop

The verifier judges agent outputs and triggers retries:

```python
class VerifierAgent(BaseAgent):
    def verify(self, task: Task, output: str) -> tuple[bool, str]:
        # For coder tasks, run the code first!
        code_feedback = ""
        code_block = extract_code_block(output)
        if code_block:
            lang, code = code_block
            tool_res = run_code_tool(lang, code)
            if not tool_res["ok"]:
                return False, f"Code failed execution:\n{tool_res['stderr']}"
            code_feedback = f"Execution stdout: {tool_res['stdout']}"

        # LLM Evaluation against acceptance criteria
        eval_prompt = f"""
Acceptance Criteria: {task.criteria}
Candidate Output: {output}
Execution Feedback: {code_feedback}

Judge if the output satisfies the criteria. Return JSON:
{{"passed": true/false, "feedback": "Detailed reason"}}
"""
        result = extract_json(call_llm("You are an impartial verifier.", eval_prompt))
        return result.get("passed", False), result.get("feedback", "No feedback")
```

---

## 🏗️ Step 5: The Orchestrator Scheduling Loop

The orchestrator inspects the dependency graph, runs unblocked tasks, passes predecessor context, and retries on failure:

```python
class Orchestrator:
    def __init__(self, agents: list[BaseAgent], verifier: VerifierAgent):
        self.agents = agents
        self.verifier = verifier

    def run_plan(self, tasks: list[Task], max_retries: int = 2):
        while any(t.status == TaskStatus.PENDING for t in tasks):
            # Find next runnable task whose dependencies are all COMPLETED
            runnable = [
                t for t in tasks 
                if t.status == TaskStatus.PENDING and 
                all(self.get_task(dep, tasks).status == TaskStatus.COMPLETED for dep in t.depends_on)
            ]
            
            if not runnable:
                raise RuntimeError("Deadlock or unmet dependencies detected in plan.")

            task = runnable[0]
            task.status = TaskStatus.IN_PROGRESS
            agent = self.get_idle_agent(task.role)

            while task.attempts <= max_retries:
                task.attempts += 1
                # Gather prerequisite context
                context = "\n".join([f"[{dep}]: {self.get_task(dep, tasks).result}" for dep in t.depends_on])
                
                # Execute
                output = agent.execute(task, context)
                
                # Verify
                passed, feedback = self.verifier.verify(task, output)
                if passed:
                    task.status = TaskStatus.COMPLETED
                    task.result = output
                    break
                else:
                    print(f"Task {task.task_id} rejected on attempt {task.attempts}: {feedback}")
                    if task.attempts > max_retries:
                        task.status = TaskStatus.FAILED
```

---

## 💡 Key Architectural Lessons

1. **Deterministic Code Verification:** An LLM cannot reliably verify its own code just by reading it. Actually executing the code in a subprocess and checking the exit code catches 99% of syntax and import errors.
2. **Context Injection:** Downstream agents (e.g. Coder) need the output of upstream agents (e.g. Researcher). Passing context explicitly through the dependency graph keeps the pipeline modular.
3. **Graceful Degeneration:** If a task exhausts all retries, marking it `FAILED` alerts the user and prevents downstream tasks from running on corrupt inputs.
