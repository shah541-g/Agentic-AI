import json
import logging
import os
import re
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum, auto
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Optional, override

from dotenv import load_dotenv
from google import genai

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)

load_dotenv()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY is missing. Add it to your .env file.")

MODEL_NAME = "gemini-3.5-flash-lite"
client = genai.Client(api_key=API_KEY)


def call_llm(system_instructions: str, prompt: str) -> str:
    """Single place for all LLM calls."""
    interaction = client.interactions.create(
        model=MODEL_NAME,
        input="<<SYSTEM INSTRUCTIONS>> \n" + system_instructions + "\n\n" + prompt,
    )
    return interaction.output_text


def extract_json(text: str) -> Any:
    """Parse JSON from an LLM reply, tolerating ```json fences and extra prose."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fall back to the first {...} or [...] block in the text.
    for open_ch, close_ch in (("[", "]"), ("{", "}")):
        start, end = text.find(open_ch), text.rfind(close_ch)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Could not parse JSON from LLM output:\n{text}")


# ---------------------------------------------------------------------------
# Output-folder helpers
# ---------------------------------------------------------------------------

# Maps a markdown code-fence language to a file extension.
CODE_EXTENSIONS = {
    "python": ".py", "py": ".py",
    "javascript": ".js", "js": ".js",
    "typescript": ".ts", "ts": ".ts",
    "java": ".java",
    "c": ".c",
    "cpp": ".cpp", "c++": ".cpp",
    "csharp": ".cs", "cs": ".cs",
    "go": ".go",
    "rust": ".rs",
    "php": ".php",
    "ruby": ".rb",
    "html": ".html",
    "css": ".css",
    "sql": ".sql",
    "bash": ".sh", "sh": ".sh", "shell": ".sh",
    "json": ".json",
    "yaml": ".yaml", "yml": ".yaml",
}


def prepare_output_dir(raw_path: str) -> Path:
    """Validate the user-supplied absolute folder path and create it if needed."""
    raw_path = raw_path.strip().strip('"').strip("'")
    if not raw_path:
        raise ValueError("No output folder was provided.")

    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        raise ValueError(f"Output folder must be an absolute path, got: {raw_path}")
    if path.exists() and not path.is_dir():
        raise ValueError(f"Output path exists but is not a folder: {path}")

    path.mkdir(parents=True, exist_ok=True)
    return path


def _slug(text: str) -> str:
    """Make a string safe to use inside a file name."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_") or "task"


def _output_text(result: Any) -> str:
    """Pull the raw text out of an agent result dict."""
    if isinstance(result, dict) and "output" in result:
        return str(result["output"])
    return str(result)


def extract_code_block(text: str) -> Optional[tuple[str, str]]:
    """Return (language, code) for the first fenced code block, or None."""
    match = re.search(r"```([\w+#-]*)[ \t]*\n(.*?)```", text, re.DOTALL)
    if not match:
        return None
    return match.group(1).strip().lower(), match.group(2).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Verifier tool: run generated code to catch runtime errors
# ---------------------------------------------------------------------------

CODE_RUN_TIMEOUT_SECONDS = 10
MAX_TOOL_OUTPUT_CHARS = 2000


def _clip(text: str) -> str:
    text = text or ""
    if len(text) <= MAX_TOOL_OUTPUT_CHARS:
        return text
    return text[:MAX_TOOL_OUTPUT_CHARS] + "\n...[truncated]"


def run_code_tool(language: str, code: str) -> dict[str, Any]:
    """Syntax-check, then execute generated code in a throwaway folder.

    Only Python is supported. Returns a dict with:
      ran (bool), ok (bool), stage ("skipped"|"syntax"|"runtime"|"timeout"|"ok"),
      exit_code, stdout, stderr.

    NOTE: this executes LLM-written code on your machine. It runs in a temp
    directory with a timeout, no stdin, Python isolated mode and the API key
    removed from its environment, but it is NOT a real sandbox.
    """
    if language not in ("python", "py"):
        return {"ran": False, "ok": True, "stage": "skipped", "exit_code": None,
                "stdout": "", "stderr": f"Execution not supported for '{language or 'unknown'}' code."}

    # Stage 1: compile only (never executes the code).
    try:
        compile(code, "generated_code.py", "exec")
    except SyntaxError as exc:
        return {"ran": False, "ok": False, "stage": "syntax", "exit_code": None,
                "stdout": "", "stderr": f"SyntaxError: {exc.msg} (line {exc.lineno})"}

    # Stage 2: actually run it.
    env = {k: v for k, v in os.environ.items() if k != "API_KEY"}
    with tempfile.TemporaryDirectory(prefix="verifier_run_") as workdir:
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
                timeout=CODE_RUN_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            return {"ran": True, "ok": True, "stage": "timeout", "exit_code": None,
                    "stdout": _clip(exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")),
                    "stderr": f"Timed out after {CODE_RUN_TIMEOUT_SECONDS}s (may be a long-running program)."}

    ok = proc.returncode == 0
    return {"ran": True, "ok": ok, "stage": "ok" if ok else "runtime",
            "exit_code": proc.returncode,
            "stdout": _clip(proc.stdout), "stderr": _clip(proc.stderr)}


def output_preview(result: Any, limit: int = 80) -> str:
    """One-line preview of an agent result, shared by the console and the DB."""
    text = _output_text(result).strip() if result is not None else ""
    preview = " ".join(text.split())
    return (preview[:limit] + "...") if len(preview) > limit else (preview or "-")


# ---------------------------------------------------------------------------
# Database layer (SQLite)
#
# Foreign-key rules:
#   session  -> conversation, report : ON DELETE CASCADE
#   conversation -> message          : ON DELETE CASCADE
#   conversation -> report           : ON DELETE SET NULL (report row is kept)
#   agent -> conversation/message/report : ON DELETE RESTRICT (an agent that
#       has history cannot be deleted)
# message.sender_agent_id is NULL when the sender is the human user.
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS agent (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL,
    role  TEXT NOT NULL,
    UNIQUE (name, role)
);

CREATE TABLE IF NOT EXISTS session (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    ended_at     TEXT,
    user_prompt  TEXT,
    output_dir   TEXT
);

CREATE TABLE IF NOT EXISTS conversation (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES session(id) ON DELETE CASCADE,
    agent_id    INTEGER NOT NULL REFERENCES agent(id)   ON DELETE RESTRICT,
    task_id     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS message (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id  INTEGER NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
    sender_agent_id  INTEGER REFERENCES agent(id) ON DELETE RESTRICT,
    kind             TEXT NOT NULL,
    content          TEXT NOT NULL,
    created_at       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS report (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id             INTEGER NOT NULL REFERENCES session(id) ON DELETE CASCADE,
    conversation_id        INTEGER REFERENCES conversation(id) ON DELETE SET NULL,
    agent_id               INTEGER REFERENCES agent(id) ON DELETE RESTRICT,
    task_id                TEXT,
    role                   TEXT,
    agent_name             TEXT,
    depends_on             TEXT,
    subtask                TEXT,
    acceptance_criteria    TEXT,
    status                 TEXT,
    output_preview         TEXT,
    verifier_feedback      TEXT,
    tasks_assigned         INTEGER,
    tasks_completed        INTEGER,
    tasks_failed           INTEGER,
    agent_assigned_tasks   INTEGER,
    agent_completed_tasks  INTEGER,
    agent_failed_tasks     INTEGER,
    saved_files            TEXT,
    created_at             TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation(session_id);
CREATE INDEX IF NOT EXISTS idx_message_conversation ON message(conversation_id);
CREATE INDEX IF NOT EXISTS idx_report_session ON report(session_id);
"""

REPORT_COLUMNS = (
    "session_id", "conversation_id", "agent_id", "task_id", "role", "agent_name",
    "depends_on", "subtask", "acceptance_criteria", "status", "output_preview",
    "verifier_feedback", "tasks_assigned", "tasks_completed", "tasks_failed",
    "agent_assigned_tasks", "agent_completed_tasks", "agent_failed_tasks",
    "saved_files",
)


class Database:
    """Thin wrapper over sqlite3 for agents, sessions, conversations, messages, reports."""

    def __init__(self, path: str = "agent_system.db"):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        # SQLite ignores foreign keys unless this is switched on per connection.
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)

    def _write(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self.conn:  # commit on success, rollback on error
            return self.conn.execute(sql, params)

    def _read(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchall()

    # ---- insert ----------------------------------------------------------

    def get_or_create_agent(self, name: str, role: str) -> int:
        """Stable DB id for an agent; the same name+role always maps to the same row."""
        self._write("INSERT OR IGNORE INTO agent (name, role) VALUES (?, ?)", (name, role))
        row = self._read("SELECT id FROM agent WHERE name = ? AND role = ?", (name, role))[0]
        return int(row["id"])

    def create_session(self, user_prompt: str, output_dir: Optional[str]) -> int:
        cur = self._write(
            "INSERT INTO session (user_prompt, output_dir) VALUES (?, ?)",
            (user_prompt, output_dir),
        )
        return int(cur.lastrowid)

    def end_session(self, session_id: int) -> None:
        self._write(
            "UPDATE session SET ended_at = datetime('now', 'localtime') WHERE id = ?",
            (session_id,),
        )

    def create_conversation(self, session_id: int, agent_id: int, task_id: Optional[str]) -> int:
        cur = self._write(
            "INSERT INTO conversation (session_id, agent_id, task_id) VALUES (?, ?, ?)",
            (session_id, agent_id, task_id),
        )
        return int(cur.lastrowid)

    def add_message(
        self, conversation_id: int, sender_agent_id: Optional[int], kind: str, content: str
    ) -> int:
        cur = self._write(
            "INSERT INTO message (conversation_id, sender_agent_id, kind, content) "
            "VALUES (?, ?, ?, ?)",
            (conversation_id, sender_agent_id, kind, content),
        )
        return int(cur.lastrowid)

    def add_report(self, **fields: Any) -> int:
        values = tuple(fields.get(col) for col in REPORT_COLUMNS)
        cur = self._write(
            f"INSERT INTO report ({', '.join(REPORT_COLUMNS)}) "
            f"VALUES ({', '.join('?' for _ in REPORT_COLUMNS)})",
            values,
        )
        return int(cur.lastrowid)

    # ---- query -----------------------------------------------------------

    def list_sessions(self) -> list[sqlite3.Row]:
        return self._read(
            "SELECT s.id, s.started_at, s.ended_at, s.user_prompt, "
            "(SELECT COUNT(*) FROM conversation c WHERE c.session_id = s.id) AS conversations, "
            "(SELECT COUNT(*) FROM report r WHERE r.session_id = s.id) AS tasks "
            "FROM session s ORDER BY s.id DESC"
        )

    def list_conversations(self, session_id: int) -> list[sqlite3.Row]:
        return self._read(
            "SELECT c.id, c.task_id, c.created_at, a.name AS agent_name, a.role AS agent_role, "
            "(SELECT COUNT(*) FROM message m WHERE m.conversation_id = c.id) AS messages "
            "FROM conversation c JOIN agent a ON a.id = c.agent_id "
            "WHERE c.session_id = ? ORDER BY c.id",
            (session_id,),
        )

    def list_messages(self, conversation_id: int) -> list[sqlite3.Row]:
        return self._read(
            "SELECT m.id, m.created_at, m.kind, a.name AS sender, m.content "
            "FROM message m LEFT JOIN agent a ON a.id = m.sender_agent_id "
            "WHERE m.conversation_id = ? ORDER BY m.id",
            (conversation_id,),
        )

    def list_reports(self, session_id: int) -> list[sqlite3.Row]:
        return self._read("SELECT * FROM report WHERE session_id = ? ORDER BY id", (session_id,))

    # ---- delete ----------------------------------------------------------

    def delete_session(self, session_id: int) -> bool:
        """Cascades to the session's conversations, their messages, and reports."""
        return self._write("DELETE FROM session WHERE id = ?", (session_id,)).rowcount > 0

    def delete_conversation(self, conversation_id: int) -> bool:
        """Cascades to its messages; report rows keep existing with conversation_id NULL."""
        return self._write("DELETE FROM conversation WHERE id = ?", (conversation_id,)).rowcount > 0

    def delete_agent(self, agent_id: int) -> bool:
        """Raises sqlite3.IntegrityError if the agent still has history (RESTRICT)."""
        return self._write("DELETE FROM agent WHERE id = ?", (agent_id,)).rowcount > 0


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
    ORCHESTRATOR = "orchestrator"


ROLE_INSTRUCTIONS = {
    AgentRole.WRITER: (
        "You are a professional Writer. Produce polished, well-structured written "
        "content that fully completes the task. Output only the final content."
    ),
    AgentRole.RESEARCHER: (
        "You are a careful Researcher. Investigate the topic, give accurate, "
        "organized findings, and clearly say when you are unsure. "
        "Output only the findings."
    ),
    AgentRole.CODER: (
        "You are an expert Coder. Write complete, runnable, well-commented code "
        "that fulfils the task. Output the code followed by a short usage note."
    ),
}


class Task:
    def __init__(
        self,
        task: str,
        status: TaskStatus = TaskStatus.PENDING,
        agent_id: Optional[int] = None,
        task_id: Optional[str] = None,
        input_from_tasks: Optional[list[str]] = None,
        acceptance_criteria: Optional[list[str]] = None,
        max_retries: int = 2,
    ):
        self.__task = task
        self.__status = status
        self.__assigned_to = agent_id
        self.task_id = task_id or str(uuid.uuid4())
        self.input_from_tasks = input_from_tasks or []
        self.acceptance_criteria = acceptance_criteria or []
        self.result: Any = None
        self.verification_feedback = ""
        self.retry_count = 0
        self.max_retries = max_retries

    @property
    def status(self) -> TaskStatus:
        return self.__status

    @status.setter
    def status(self, value: TaskStatus) -> None:
        self.__status = value

    @property
    def task(self) -> str:
        return self.__task

    @task.setter
    def task(self, value: str) -> None:
        self.__task = value

    @property
    def assignTo(self) -> Optional[int]:
        return self.__assigned_to

    @assignTo.setter
    def assignTo(self, value: Optional[int]) -> None:
        self.__assigned_to = value

    def to_dict(self) -> dict[str, Any]:
        return {
            "subtask": self.task,
            "taskAssignedTo": self.assignTo,
            "taskId": self.task_id,
            "inputFromTasks": self.input_from_tasks,
            "acceptanceCriteria": self.acceptance_criteria,
        }


class Agent(ABC):
    def __init__(self, name: str, role: AgentRole, db: Database):
        self.name = name
        self.role = role
        # Primary key from the database (stable across runs), not a random UUID.
        self.agent_id: int = db.get_or_create_agent(name, role.value)
        self.status = AgentStatus.IDLE
        self.task: Optional[Task] = None
        self.systemInstructions = ROLE_INSTRUCTIONS.get(role, "")

    @abstractmethod
    def execute(self, prompt: str) -> Any:
        """Execute a prompt and return a result."""
        raise NotImplementedError


class TaskAgent(Agent):
    def __init__(self, name: str, role: AgentRole, db: Database):
        super().__init__(name, role, db)
        self.taskHistory: list[Task] = []
        self.tasksCompleted = 0
        self.tasksFailed = 0

    @override
    def execute(self, prompt: str) -> Any:
        if self.status == AgentStatus.BUSY:
            raise RuntimeError(f"{self.name} is already busy.")

        task = self.task
        if task is None:
            task = Task(prompt, TaskStatus.PENDING, self.agent_id)

        self.status = AgentStatus.BUSY
        task.status = TaskStatus.IN_PROGRESS
        if task not in self.taskHistory:
            self.taskHistory.append(task)

        try:
            result = self.perform_task(prompt)
            task.result = result
            # Execution returned normally; this does not mean verification passed.
            return result
        except Exception:
            task.status = TaskStatus.FAILED
            self.tasksFailed += 1
            raise
        finally:
            self.status = AgentStatus.IDLE
            self.task = None

    def perform_task(self, prompt: str) -> Any:
        """Real LLM call using this agent's role instructions."""
        output = call_llm(self.systemInstructions, prompt)
        print(f"[{self.name} | {self.role.value}] done")
        return {
            "agent": self.name,
            "role": self.role.value,
            "output": output,
        }


class Coder(TaskAgent):
    def __init__(self, name: str, db: Database):
        super().__init__(name, AgentRole.CODER, db)


class Researcher(TaskAgent):
    def __init__(self, name: str, db: Database):
        super().__init__(name, AgentRole.RESEARCHER, db)


class Writer(TaskAgent):
    def __init__(self, name: str, db: Database):
        super().__init__(name, AgentRole.WRITER, db)


class VerifierAgent(Agent):
    """LLM-based verifier: judges a task result against its acceptance criteria."""

    def __init__(self, db: Database, name: str = "Verifier"):
        super().__init__(name, AgentRole.VERIFIER, db)
        self.verificationHistory: list[dict[str, Any]] = []
        self.systemInstructions = """
You are a strict but fair Verifier. You receive a task, optional acceptance
criteria, and a result. Decide whether the result genuinely completes the task
and meets every criterion. Return valid JSON only, in this exact shape:
{"passed": true or false, "feedback": "short, specific explanation"}
"""

    @override
    def execute(self, prompt: str) -> bool:
        """Agent interface; use verify_task() for real task records."""
        return bool(prompt.strip())

    def verify_task(self, task: Task, result: Any) -> bool:
        self.status = AgentStatus.BUSY
        try:
            passed, feedback = self.verify_result(task, result)
            task.verification_feedback = feedback
            self.verificationHistory.append({
                "task_id": task.task_id,
                "passed": passed,
                "feedback": feedback,
            })
            return passed
        finally:
            self.status = AgentStatus.IDLE

    def verify_result(self, task: Task, result: Any) -> tuple[bool, str]:
        if result is None:
            return False, "No result was returned."

        output = result["output"] if isinstance(result, dict) and "output" in result else result
        if not str(output).strip():
            return False, "The result is empty."

        # Tool use: for coder results, actually run the code.
        execution_report = ""
        if isinstance(result, dict) and result.get("role") == AgentRole.CODER.value:
            block = extract_code_block(str(output))
            if block is None:
                return False, "Coder result contains no fenced code block to run."
            language, code = block
            run = run_code_tool(language, code)
            if run["stage"] in ("syntax", "runtime"):
                # Hard failure: real error output goes back to the coder as feedback.
                return False, (
                    f"Code failed at {run['stage']} stage "
                    f"(exit code {run['exit_code']}).\n{run['stderr']}"
                )
            execution_report = (
                "\n\nEXECUTION REPORT (code was actually run):\n"
                f"stage: {run['stage']}\nexit_code: {run['exit_code']}\n"
                f"stdout:\n{run['stdout']}\nstderr:\n{run['stderr']}\n"
            )

        criteria = task.acceptance_criteria or [
            "The result fully and correctly completes the task."
        ]
        prompt = (
            f"TASK:\n{task.task}\n\n"
            f"ACCEPTANCE CRITERIA:\n" + "\n".join(f"- {c}" for c in criteria) + "\n\n"
            f"RESULT:\n{output}\n"
            + execution_report
        )

        try:
            verdict = extract_json(call_llm(self.systemInstructions, prompt))
            passed = bool(verdict.get("passed", False))
            feedback = str(verdict.get("feedback", "")) or "No feedback provided."
            return passed, feedback
        except Exception as exc:
            # Fail closed: if we can't read the verdict, don't mark the task as passed.
            return False, f"Verifier could not produce a valid verdict: {exc}"


class Orchestrator(Agent):
    def __init__(self, db: Database, name: str = "Orchestrator"):
        super().__init__(name, AgentRole.ORCHESTRATOR, db)
        self.db = db
        # task_id -> conversation id for the run currently being executed.
        self._conversations: dict[str, int] = {}

        self.taskHistory: list[Task] = []
        self.tasksAssigned = 0
        self.tasksCompleted = 0
        self.tasksFailed = 0
        self.agentsToTasksMapping: dict[TaskAgent, list[Task]] = {}

        self.verifier = VerifierAgent(db)
        self.scaffoldAgents()

        # Separate round-robin cursor for each role.
        self._round_robin_index: dict[AgentRole, int] = defaultdict(int)

        # In-memory result lookup for dependency injection.
        self._results: dict[str, Any] = {}

        self.max_retries = 2
        self.systemInstructions = """
You are an Orchestrator. Convert a user request into a dependency-aware task plan.
Return valid JSON only: a list of objects, each with exactly these keys:
- "subtask": string, a clear self-contained instruction for one agent
- "taskAssignedTo": one of "writer", "researcher", "coder", or null if no role fits
- "taskId": string like "T1", "T2", ... (unique)
- "inputFromTasks": list of taskIds whose output this task needs (use [] if none)
- "acceptanceCriteria": list of 1-3 short, checkable criteria for this subtask
Split independent outcomes into separate tasks. Use dependencies only when a task
genuinely needs another task's output. Do not add markdown or commentary.
"""

    def scaffoldAgents(self) -> None:
        self.agentsToTasksMapping = {
            Writer("Ahmad", self.db): [],
            Writer("Akram", self.db): [],
            Writer("Afzal", self.db): [],
            Researcher("Ali", self.db): [],
            Researcher("Muhammad", self.db): [],
            Researcher("Asad", self.db): [],
            Coder("Saqib", self.db): [],
            Coder("Bilal", self.db): [],
            Coder("Yasoob", self.db): [],
        }

    def _agents_for_role(self, role: AgentRole) -> list[TaskAgent]:
        return [
            agent
            for agent in self.agentsToTasksMapping
            if agent.role == role and agent.status == AgentStatus.IDLE
        ]

    def _assign_agent(self, role: AgentRole) -> Optional[TaskAgent]:
        eligible = self._agents_for_role(role)
        if not eligible:
            return None

        index = self._round_robin_index[role] % len(eligible)
        selected = eligible[index]
        self._round_robin_index[role] += 1
        return selected

    def create_task_plan(self, prompt: str) -> list[Task]:
        """LLM planner: turns the user request into a validated list of Tasks."""
        prompt = prompt.strip()
        if not prompt:
            return []

        raw = call_llm(self.systemInstructions, f"USER REQUEST:\n{prompt}")
        plan = extract_json(raw)
        if isinstance(plan, dict):  # tolerate {"tasks": [...]}
            plan = plan.get("tasks", [plan])
        if not isinstance(plan, list):
            raise ValueError("Planner did not return a JSON list of tasks.")

        valid_roles = {
            "writer": AgentRole.WRITER,
            "researcher": AgentRole.RESEARCHER,
            "coder": AgentRole.CODER,
        }

        tasks: list[Task] = []
        for index, item in enumerate(plan, start=1):
            role_name = str(item.get("taskAssignedTo") or "").strip().lower()
            role = valid_roles.get(role_name)
            agent = self._assign_agent(role) if role else None

            tasks.append(Task(
                task=str(item.get("subtask", "")).strip(),
                status=TaskStatus.PENDING,
                agent_id=agent.agent_id if agent else None,
                task_id=str(item.get("taskId") or f"T{index}"),
                input_from_tasks=[str(d) for d in item.get("inputFromTasks", [])],
                acceptance_criteria=[str(c) for c in item.get("acceptanceCriteria", [])],
                max_retries=self.max_retries,
            ))

        return [t for t in tasks if t.task]

    def plan_to_json(self, tasks: list[Task]) -> str:
        return json.dumps([task.to_dict() for task in tasks], indent=2)

    def execute(self, prompt: str, output_dir: Optional[Path] = None) -> dict[str, Any]:
        """Plan and run the request. If output_dir is given, results are saved there."""
        if self.status == AgentStatus.BUSY:
            raise RuntimeError("Orchestrator is already processing a request.")

        self.status = AgentStatus.BUSY
        session_id: Optional[int] = None
        try:
            session_id = self.db.create_session(
                prompt, str(output_dir) if output_dir is not None else None
            )
            self._conversations = {}

            # The orchestrator's own conversation: the user's request and the plan.
            orchestrator_conv = self.db.create_conversation(session_id, self.agent_id, None)
            self.db.add_message(orchestrator_conv, None, "user_prompt", prompt)

            tasks = self.create_task_plan(prompt)
            self.db.add_message(orchestrator_conv, self.agent_id, "plan", self.plan_to_json(tasks))

            # One conversation per task, authored by the agent assigned to it.
            for task in tasks:
                if task.assignTo is not None:
                    self._conversations[task.task_id] = self.db.create_conversation(
                        session_id, task.assignTo, task.task_id
                    )

            self.taskHistory.extend(tasks)
            self.tasksAssigned += sum(task.assignTo is not None for task in tasks)

            agent_by_id = {
                agent.agent_id: agent for agent in self.agentsToTasksMapping
            }
            for task in tasks:
                agent = agent_by_id.get(task.assignTo) if task.assignTo else None
                if agent is not None:
                    self.agentsToTasksMapping[agent].append(task)

            # Execute in dependency order. Repeated passes allow prerequisites first.
            pending = {task.task_id: task for task in tasks}
            while pending:
                made_progress = False

                for task_id, task in list(pending.items()):
                    prerequisite_tasks = [
                        next((c for c in tasks if c.task_id == dep), None)
                        for dep in task.input_from_tasks
                    ]

                    if any(dep is None for dep in prerequisite_tasks):
                        task.status = TaskStatus.FAILED
                        task.verification_feedback = "Unknown dependency task ID."
                        self.tasksFailed += 1
                        del pending[task_id]
                        made_progress = True
                        continue

                    if any(dep.status == TaskStatus.FAILED for dep in prerequisite_tasks):
                        task.status = TaskStatus.FAILED
                        task.verification_feedback = "A prerequisite task failed."
                        self.tasksFailed += 1
                        del pending[task_id]
                        made_progress = True
                        continue

                    if any(dep.status != TaskStatus.COMPLETED for dep in prerequisite_tasks):
                        continue

                    if task.assignTo is None:
                        task.status = TaskStatus.FAILED
                        task.verification_feedback = "No eligible agent for this task."
                        self.tasksFailed += 1
                        del pending[task_id]
                        made_progress = True
                        continue

                    agent = agent_by_id.get(task.assignTo)
                    if agent is None:
                        task.status = TaskStatus.FAILED
                        task.verification_feedback = "Assigned agent ID was not found."
                        self.tasksFailed += 1
                        del pending[task_id]
                        made_progress = True
                        continue

                    # Pass prerequisite outputs into the prompt.
                    dependency_context = {
                        dep.task_id: self._results[dep.task_id]
                        for dep in prerequisite_tasks
                        if dep.task_id in self._results
                    }
                    execution_prompt = task.task
                    if dependency_context:
                        execution_prompt += "\n\nPrerequisite outputs:\n" + json.dumps(
                            dependency_context, default=str
                        )

                    task.assignTo = agent.agent_id
                    agent.task = task
                    self._log(task, self.agent_id, "task_prompt", execution_prompt)

                    try:
                        result = agent.execute(execution_prompt)
                        task.result = result
                        self._log(task, agent.agent_id, "agent_output", _output_text(result))
                        passed = self.verifier.verify_task(task, result)
                        self._log_verdict(task, passed)

                        if passed:
                            task.status = TaskStatus.COMPLETED
                            self.tasksCompleted += 1
                            agent.tasksCompleted += 1
                            self._results[task.task_id] = result
                        else:
                            self._retry_or_fail(task, agent, execution_prompt)
                    except Exception as exc:
                        task.result = None
                        task.verification_feedback = f"Execution error: {exc}"
                        self._log(task, agent.agent_id, "error", task.verification_feedback)
                        self._retry_or_fail(task, agent, execution_prompt)

                    del pending[task_id]
                    made_progress = True

                if not made_progress:
                    for task in pending.values():
                        task.status = TaskStatus.FAILED
                        task.verification_feedback = (
                            "Could not schedule task; check for circular or unresolved dependencies."
                        )
                        self.tasksFailed += 1
                    pending.clear()

            outcome: dict[str, Any] = {
                "plan": [task.to_dict() for task in tasks],
                "report": self.get_report(),
                "results": {
                    task.task_id: {
                        "status": task.status.name,
                        "assigned_to": task.assignTo,
                        "result": task.result,
                        "verification_feedback": task.verification_feedback,
                    }
                    for task in tasks
                },
            }

            task_files: dict[str, list[str]] = {}
            if output_dir is not None:
                saved, task_files = self.save_outputs(tasks, output_dir, agent_by_id, outcome)
                outcome["saved_files"] = saved

            # Final status line in every task conversation (covers all failure paths).
            for task in tasks:
                self._log(
                    task, self.agent_id, "final_status",
                    f"{task.status.name}: {task.verification_feedback or '-'}",
                )
            self._persist_report(session_id, tasks, outcome, task_files)
            outcome["session_id"] = session_id
            return outcome
        finally:
            if session_id is not None:
                self.db.end_session(session_id)
            self.status = AgentStatus.IDLE
            self.task = None

    def _log(self, task: Task, sender_id: Optional[int], kind: str, content: str) -> None:
        """Append a message to the task's conversation (no-op if it has none)."""
        conversation_id = self._conversations.get(task.task_id)
        if conversation_id is not None:
            self.db.add_message(conversation_id, sender_id, kind, content)

    def _log_verdict(self, task: Task, passed: bool) -> None:
        verdict = "PASSED" if passed else "REJECTED"
        self._log(
            task, self.verifier.agent_id, "verdict",
            f"{verdict}: {task.verification_feedback}",
        )

    def _persist_report(
        self,
        session_id: int,
        tasks: list[Task],
        outcome: dict[str, Any],
        task_files: dict[str, list[str]],
    ) -> None:
        """Store every field shown in the console tables, one row per task."""
        report = outcome["report"]
        agent_stats = {a["agent_id"]: a for a in report["agents"]}
        agents = {a.agent_id: a for a in self.agentsToTasksMapping}

        for task in tasks:
            agent = agents.get(task.assignTo) if task.assignTo is not None else None
            stats = agent_stats.get(task.assignTo, {})
            self.db.add_report(
                session_id=session_id,
                conversation_id=self._conversations.get(task.task_id),
                agent_id=task.assignTo,
                task_id=task.task_id,
                role=agent.role.value if agent else None,
                agent_name=agent.name if agent else None,
                depends_on=", ".join(task.input_from_tasks),
                subtask=task.task,
                acceptance_criteria="\n".join(task.acceptance_criteria),
                status=task.status.name,
                output_preview=output_preview(task.result),
                verifier_feedback=task.verification_feedback,
                tasks_assigned=report["tasks_assigned"],
                tasks_completed=report["tasks_completed"],
                tasks_failed=report["tasks_failed"],
                agent_assigned_tasks=stats.get("assigned_tasks"),
                agent_completed_tasks=stats.get("completed_tasks"),
                agent_failed_tasks=stats.get("failed_tasks"),
                saved_files=", ".join(task_files.get(task.task_id, [])),
            )

    def save_outputs(
        self,
        tasks: list[Task],
        output_dir: Path,
        agent_by_id: dict[int, TaskAgent],
        outcome: dict[str, Any],
    ) -> tuple[list[str], dict[str, list[str]]]:
        """Write each completed task's output to its own file, plus plan/report.

        Files are named like  T1_writer_Ahmad.md . For coder tasks the first
        fenced code block is also saved as a runnable file (e.g. T2_coder_Saqib.py).
        Failed tasks produce no output file; they are listed in summary.json.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        saved: list[str] = []
        task_files: dict[str, list[str]] = {}

        def write(name: str, content: str) -> None:
            path = output_dir / name
            path.write_text(content, encoding="utf-8")
            saved.append(str(path))

        for task in tasks:
            if task.status != TaskStatus.COMPLETED or task.result is None:
                continue

            agent = agent_by_id.get(task.assignTo) if task.assignTo else None
            role = agent.role.value if agent else "task"
            agent_name = agent.name if agent else "unassigned"
            base = f"{_slug(task.task_id)}_{role}_{_slug(agent_name)}"
            text = _output_text(task.result)

            files_before = len(saved)
            header = f"<!-- Task {task.task_id}: {task.task} -->\n\n"
            write(f"{base}.md", header + text + "\n")

            if agent and agent.role == AgentRole.CODER:
                block = extract_code_block(text)
                if block:
                    lang, code = block
                    ext = CODE_EXTENSIONS.get(lang, ".txt")
                    write(f"{base}{ext}", code)

            task_files[task.task_id] = [Path(p).name for p in saved[files_before:]]

        write("plan.json", self.plan_to_json(tasks))
        write("summary.json", json.dumps(
            {
                "report": outcome["report"],
                "tasks": {
                    task.task_id: {
                        "status": task.status.name,
                        "verification_feedback": task.verification_feedback,
                    }
                    for task in tasks
                },
            },
            indent=2,
            default=str,
        ))

        return saved, task_files

    def _retry_or_fail(self, task: Task, agent: TaskAgent, base_prompt: str) -> None:
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.PENDING

            # Give the agent the verifier's feedback so the retry can actually improve.
            retry_prompt = base_prompt
            if task.verification_feedback:
                retry_prompt += (
                    "\n\nYour previous attempt was rejected. Feedback:\n"
                    f"{task.verification_feedback}\nFix these issues."
                )

            self._log(task, self.agent_id, "retry_prompt", retry_prompt)
            try:
                agent.task = task
                result = agent.execute(retry_prompt)
                task.result = result
                self._log(task, agent.agent_id, "agent_output", _output_text(result))
                passed = self.verifier.verify_task(task, result)
                self._log_verdict(task, passed)
                if passed:
                    task.status = TaskStatus.COMPLETED
                    self.tasksCompleted += 1
                    agent.tasksCompleted += 1
                    self._results[task.task_id] = result
                    return
                self._retry_or_fail(task, agent, base_prompt)
                return
            except Exception as exc:
                task.verification_feedback = f"Retry execution error: {exc}"
                self._log(task, agent.agent_id, "error", task.verification_feedback)
                self._retry_or_fail(task, agent, base_prompt)
                return

        task.status = TaskStatus.FAILED
        self.tasksFailed += 1
        agent.tasksFailed += 1

    def get_report(self) -> dict[str, Any]:
        agent_reports = []
        for agent, tasks in self.agentsToTasksMapping.items():
            agent_reports.append({
                "name": agent.name,
                "agent_id": agent.agent_id,
                "role": agent.role.value,
                "status": agent.status.name,
                "assigned_tasks": len(tasks),
                "completed_tasks": agent.tasksCompleted,
                "failed_tasks": agent.tasksFailed,
            })

        return {
            "tasks_assigned": self.tasksAssigned,
            "tasks_completed": self.tasksCompleted,
            "tasks_failed": self.tasksFailed,
            "agents": agent_reports,
        }

def printSystemName():
  art_left = r"""⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                                                  ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
                                                  ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠠⡹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
                                                  ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠋⣿⠧⠇⣿⡹⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
                                                  ⣿⣿⣿⣿⣿⣿⣿⣿⠏⢹⠏⣴⡔⡋⡀⢠⡟⣟⡽⣿⢻⣿⣿⡿⣿⣿⣿⣿
                                                  ⣿⣿⣿⣿⣿⡟⢿⡟⡀⡏⢰⡗⠀⣰⣿⢸⢸⣿⠠⠁⠈⣿⠏⠀⣿⣿⣿⣿
                                                  ⣿⣿⡿⣿⣿⢡⡜⠁⠇⡇⠸⠑⡠⣹⢸⠌⢸⣿⡄⢸⣶⡐⢃⠇⣿⣿⣿⣿
                                                  ⣿⣿⡁⠙⠇⣼⣹⡀⢰⣹⡀⢰⢃⣿⢸⡀⣿⠟⢠⢾⣿⣷⠞⢲⢿⣿⣿⣿
                                                  ⣿⣿⣧⢷⢀⢻⣧⢇⠘⣿⡇⠘⢸⣿⣿⡇⠀⣴⢇⣼⣿⣿⣆⡿⢸⣿⣿⠿
                                                  ⣟⠻⣿⡞⢸⢸⢻⣾⣆⢝⠇⠀⠸⣿⣿⠇⠀⣠⣿⢳⣿⣿⠙⠅⠛⡉⣠⣰
                                                  ⣿⡰⠺⣝⡀⢨⢢⢿⣿⣮⠃⠀⣀⡝⠋⣠⣤⢻⠿⣾⢯⠃⣜⡴⣫⢎⣱⣿
                                                  ⣿⣧⠨⡺⣕⠈⣎⠋⣉⠉⣠⢞⢅⣤⠞⣽⠍⠀⢹⡈⢊⢀⡾⢚⡵⣳⣿⣿
                                                  ⣿⣿⣆⠙⢦⡑⠀⣰⡏⣼⣽⠋⡰⣣⢞⣵⣦⠀⢸⡗⠐⡍⠔⣩⡾⢿⣿⣿
                                                  ⣿⣿⣿⡷⠄⠈⠀⡟⠀⡇⣱⠂⡵⣣⣿⣿⠿⡃⠛⠁⠈⠡⠆⠀⣠⣾⣿⣿
                                                  ⣿⣿⣿⣿⣄⢉⠀⠀⠀⢀⡪⠀⣬⠻⢿⡵⠛⠁⠀⠀⡄⠀⢀⣼⣿⣿⣿⣿
                                                  ⣿⣿⣿⣿⣿⣷⣥⠂⠀⣤⣋⣀⣀⢤⣤⣤⣪⣵⡏⢄⣡⣼⣿⣿⣿⣿⣿⣿
                                                  ⣿⣿⣿⣿⣿⣿⣿⣿⡆⠙⣿⣿⣷⠸⢿⣿⣿⡿⡄⣿⣿⣿⣿⣿⣿⣿⣿⣿
                                                  ⣿⣿⣿⣿⣿⣿⢿⣫⢸⡇⡀⡻⣿⣤⣴⡿⠋⢸⡇⣯⡻⣿⣿⣿⣿⣿⣿⣿
                                                  ⣿⣿⣿⣯⣠⡶⣫⢕⣾⣿⡘⣅⢄⢭⣭⢎⢠⣿⣧⡹⡿⣆⢠⣽⣿⣿⣿⣿
                                                  ⣿⣿⣿⣿⣇⠬⣻⣯⣭⣭⣭⣽⣎⡚⠳⣃⣿⣯⣿⣟⡊⣡⣿⣿⣿⣿⣿⣿
                                                  ⣿⣿⣿⣿⣿⣷⣄⠶⣶⣿⣿⣿⣿⡏⣺⣶⣶⡦⢍⣫⣾⣿⣿⣿⣿⣿⣿⣿
                                                  ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣶⣶⣶⣷⣶⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿


"""

  art_right = """
  ██████ ██████ ██████ ██████ ██████  ██ ██     ██████ ██████
  ██     ██  ██   ██   ██  ██ ██  ██  ██ ██     ██  ██   ██
  ██     ██  ██   ██   ██  ██ ██████  ██ ██     ██  ██   ██
  ██████ ██████   ██   ██████ ██      ██ ██████ ██████   ██
  """

  GAP = "   "  # spacing between the two arts

  left = art_left.strip("\n").splitlines()
  right = [line.rstrip() for line in art_right.strip("\n").splitlines()]

  left_w = max(len(l) for l in left)
  right_w = max(len(r) for r in right)

  # Vertically center the shorter art against the taller one
  height = max(len(left), len(right))


  def center(lines, width, height):
      top = (height - len(lines)) // 2
      padded = [" " * width] * top + [l.ljust(width) for l in lines]
      padded += [" " * width] * (height - len(padded))
      return padded


  left = center(left, left_w, height)
  right = center(right, right_w, height)

  print("\n".join(l + GAP + r for l, r in zip(left, right)))


def ask_output_dir() -> Path:
    """Keep asking until the user gives a usable absolute folder path."""
    while True:
        raw = input("Output folder (absolute path): ")
        try:
            return prepare_output_dir(raw)
        except (ValueError, OSError) as exc:
            print(f"Invalid folder: {exc}")


def render_table(
    title: str,
    headers: list[str],
    rows: list[list[Any]],
    max_col_width: int = 40,
) -> str:
    """Render rows as a boxed text table; long cells wrap onto extra lines."""
    if not rows:
        return f"{title}\n(no rows)\n"

    cells = [[str(c) if c is not None else "-" for c in row] for row in rows]
    widths = [
        min(max_col_width, max(len(h), *(len(max(r[i].split("\n"), key=len)) for r in cells)))
        for i, h in enumerate(headers)
    ]

    def wrap_row(row: list[str]) -> list[list[str]]:
        wrapped = []
        for text, width in zip(row, widths):
            lines: list[str] = []
            for part in text.split("\n"):
                lines.extend(textwrap.wrap(part, width) or [""])
            wrapped.append(lines)
        height = max(len(c) for c in wrapped)
        return [c + [""] * (height - len(c)) for c in wrapped]

    def line(left: str, mid: str, right: str) -> str:
        return left + mid.join("─" * (w + 2) for w in widths) + right

    def format_row(row: list[str]) -> list[str]:
        columns = wrap_row(row)
        return [
            "│ " + " │ ".join(col[i].ljust(w) for col, w in zip(columns, widths)) + " │"
            for i in range(len(columns[0]))
        ]

    out = [title, line("┌", "┬", "┐")]
    out += format_row(headers)
    out.append(line("├", "┼", "┤"))
    for index, row in enumerate(cells):
        out += format_row(row)
        if index < len(cells) - 1:
            out.append(line("├", "┼", "┤"))
    out.append(line("└", "┴", "┘"))
    return "\n".join(out) + "\n"


def print_outcome(orchestrator: Orchestrator, outcome: dict[str, Any], output_folder: Path) -> None:
    """Print the run as tables instead of raw JSON."""
    name_by_id = {a.agent_id: a.name for a in orchestrator.agentsToTasksMapping}
    role_by_id = {a.agent_id: a.role.value for a in orchestrator.agentsToTasksMapping}

    print()
    print(render_table(
        "TASK PLAN",
        ["ID", "Role", "Agent", "Depends on", "Subtask", "Acceptance criteria"],
        [
            [
                t["taskId"],
                role_by_id.get(t["taskAssignedTo"], "-"),
                name_by_id.get(t["taskAssignedTo"], "-"),
                ", ".join(t["inputFromTasks"]) or "-",
                t["subtask"],
                "\n".join(f"• {c}" for c in t["acceptanceCriteria"]) or "-",
            ]
            for t in outcome["plan"]
        ],
        max_col_width=45,
    ))

    results_rows = []
    for task_id, r in outcome["results"].items():
        preview = output_preview(r["result"])
        results_rows.append([
            task_id,
            r["status"],
            name_by_id.get(r["assigned_to"], "-"),
            preview,
            r["verification_feedback"] or "-",
        ])
    print(render_table(
        "EXECUTION RESULTS",
        ["ID", "Status", "Agent", "Output preview", "Verifier feedback"],
        results_rows,
        max_col_width=45,
    ))

    report = outcome["report"]
    print(render_table(
        "SUMMARY",
        ["Assigned", "Completed", "Failed"],
        [[report["tasks_assigned"], report["tasks_completed"], report["tasks_failed"]]],
    ))

    # Only agents that actually did something, to keep the table short.
    print(render_table(
        "AGENT ACTIVITY",
        ["Agent", "Role", "Assigned", "Completed", "Failed"],
        [
            [a["name"], a["role"], a["assigned_tasks"], a["completed_tasks"], a["failed_tasks"]]
            for a in report["agents"]
            if a["assigned_tasks"] > 0
        ],
    ))

    print(render_table(
        f"SAVED FILES  ({output_folder})",
        ["File"],
        [[Path(p).name] for p in outcome.get("saved_files", [])],
        max_col_width=80,
    ))


HISTORY_USAGE = """Usage:
  python orchestrator.py                    run a new task
  python orchestrator.py sessions           list past sessions
  python orchestrator.py show <session_id>  conversations and report of a session
  python orchestrator.py messages <conversation_id>
  python orchestrator.py delete <session_id>   delete a session (cascades)
"""


def history_cli(db: Database, args: list[str]) -> None:
    """Query / delete commands for the stored history."""
    command, rest = args[0], args[1:]
    try:
        if command == "sessions":
            print(render_table(
                "SESSIONS",
                ["ID", "Started", "Ended", "Conversations", "Tasks", "Prompt"],
                [[r["id"], r["started_at"], r["ended_at"], r["conversations"], r["tasks"],
                  r["user_prompt"]] for r in db.list_sessions()],
                max_col_width=50,
            ))
        elif command == "show" and rest:
            session_id = int(rest[0])
            print(render_table(
                f"CONVERSATIONS (session {session_id})",
                ["ID", "Task", "Author", "Role", "Messages", "Created"],
                [[r["id"], r["task_id"], r["agent_name"], r["agent_role"], r["messages"],
                  r["created_at"]] for r in db.list_conversations(session_id)],
            ))
            print(render_table(
                f"REPORT (session {session_id})",
                ["ID", "Conv", "Agent", "Task", "Role", "Depends on", "Status",
                 "Output preview", "Verifier feedback", "Files"],
                [[r["id"], r["conversation_id"], r["agent_name"], r["task_id"], r["role"],
                  r["depends_on"], r["status"], r["output_preview"], r["verifier_feedback"],
                  r["saved_files"]] for r in db.list_reports(session_id)],
                max_col_width=35,
            ))
        elif command == "messages" and rest:
            conversation_id = int(rest[0])
            print(render_table(
                f"MESSAGES (conversation {conversation_id})",
                ["ID", "Time", "Kind", "Sender", "Content"],
                [[r["id"], r["created_at"], r["kind"], r["sender"] or "user", r["content"]]
                 for r in db.list_messages(conversation_id)],
                max_col_width=70,
            ))
        elif command == "delete" and rest:
            deleted = db.delete_session(int(rest[0]))
            print("Session deleted." if deleted else "No such session.")
        else:
            print(HISTORY_USAGE)
    except ValueError:
        print(HISTORY_USAGE)


if __name__ == "__main__":
    db = Database(os.getenv("DB_PATH", "agent_system.db"))
    if len(sys.argv) > 1:
        history_cli(db, sys.argv[1:])
        sys.exit(0)

    printSystemName()
    orchestrator = Orchestrator(db)
    user_prompt = input("Task: ")
    output_folder = ask_output_dir()

    outcome = orchestrator.execute(user_prompt, output_folder)
    print_outcome(orchestrator, outcome, output_folder)
    print(f"Saved to database {db.path} as session {outcome['session_id']}.")