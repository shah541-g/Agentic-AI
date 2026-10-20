"""The three tools an agent can call, plus the text that tells the LLM how to call them."""
from pathlib import Path
from typing import Any

from llm import web_search
from logger import clip, get_logger
from memory import MemoryStore

log = get_logger("tools")

MAX_FILE_CHARS = 6000

TOOL_DOCS = """
You can use tools. To call ONE tool, reply with ONLY the tool call (plus a file block if needed):

<tool_call>{"tool": "<name>", "args": {...}}</tool_call>

You will then receive the tool result and may call another tool. When you have
everything you need, reply with your final answer and NO <tool_call> block.

TOOLS:
1. get_project_details  args: {"query": "<what you need to know>"}
   Returns full stored details of the user's projects that match the query.
   Use it when the task relates to one of the user's projects in the project index.
2. web_search  args: {"query": "<search query>"}
   Searches the web for current information.
3. file_op  args: {"op": "create|read|update|delete|list", "path": "<relative path>"}
   Manages files inside the workspace folder only.
   For create/update the file text goes in a <file_content> block (see below), NOT inside the JSON.

FILE TEXT: right after the tool call, write the raw file text (no JSON escaping needed):

<tool_call>{"tool": "file_op", "args": {"op": "create", "path": "notes.md"}}</tool_call>
<file_content>
# Title
Any text or code, written exactly as it should appear in the file.
</file_content>

OTHER EXAMPLES (ALWAYS nest parameters inside "args"):
<tool_call>{"tool": "web_search", "args": {"query": "LLM agent long-term memory"}}</tool_call>
<tool_call>{"tool": "get_project_details", "args": {"query": "orchestrator"}}</tool_call>
<tool_call>{"tool": "file_op", "args": {"op": "list", "path": "."}}</tool_call>

RULES:
- Use tools to DO things (list/read/write files, search the web, look up the user's projects). Do NOT write code that would do these things.
- Call at most ONE tool per reply.
- After using tools, your final answer must report the real results you observed (for example which file you created and what the file listing showed).
"""


class ToolBox:
    def __init__(self, memory: MemoryStore, workspace: Path):
        self.memory = memory
        self.workspace = workspace.resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def call(self, name: str, args: dict[str, Any]) -> str:
        log.info("TOOL CALL %s %s", name, clip(args, 150))
        if not args:
            msg = (f"Tool '{name}' got no arguments. Put parameters inside \"args\", e.g. "
                   f'<tool_call>{{"tool": "{name}", "args": {{...}}}}</tool_call>')
            log.warning(msg)
            return msg
        try:
            if name == "get_project_details":
                result = self.get_project_details(str(args.get("query", "")))
            elif name == "web_search":
                result = web_search(str(args.get("query", "")))
            elif name == "file_op":
                result = self.file_op(
                    str(args.get("op", "")), str(args.get("path", "")), str(args.get("content", ""))
                )
            else:
                log.warning("Unknown tool requested: %s", name)
                return f"Unknown tool '{name}'. Valid tools: get_project_details, web_search, file_op."
        except Exception as exc:  # noqa: BLE001
            log.error("TOOL %s failed: %s", name, clip(exc, 200))
            log.debug("TOOL %s traceback", name, exc_info=True)
            return f"Tool error ({name}): {clip(exc, 200)}"
        log.info("TOOL RESULT %s -> %s", name, clip(result, 150))
        log.debug("TOOL RESULT %s full:\n%s", name, result)
        return result

    # ---- tool 1: project details ----------------------------------------
    def get_project_details(self, query: str) -> str:
        hits = self.memory.search_projects(query)
        log.info("Project search '%s' -> %d match(es): %s",
                 clip(query, 80), len(hits), [p["name"] for p in hits])
        if not hits:
            return "No matching project found."
        return "\n\n".join(f"PROJECT: {p['name']}\n{p['details']}" for p in hits)

    # ---- tool 3: file CRUD (sandboxed to the workspace) ------------------
    def _safe_path(self, rel: str) -> Path:
        path = (self.workspace / rel).resolve()
        if path != self.workspace and self.workspace not in path.parents:
            raise ValueError("Path escapes the workspace folder.")
        return path

    def file_op(self, op: str, rel_path: str, content: str = "") -> str:
        try:
            if op == "list":
                files = sorted(
                    str(p.relative_to(self.workspace))
                    for p in self.workspace.rglob("*")
                    if p.is_file() and p.relative_to(self.workspace).parts[0] != "outputs"
                )
                return "\n".join(files) or "(workspace is empty)"

            path = self._safe_path(rel_path)
            if op == "create":
                if path.exists():
                    return f"{rel_path} already exists. Use op 'update' to overwrite."
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return f"Created {rel_path}."
            if op == "read":
                if not path.is_file():
                    return f"{rel_path} does not exist."
                text = path.read_text(encoding="utf-8", errors="replace")
                return text[:MAX_FILE_CHARS] + ("\n...[truncated]" if len(text) > MAX_FILE_CHARS else "")
            if op == "update":
                if not path.is_file():
                    return f"{rel_path} does not exist. Use op 'create'."
                path.write_text(content, encoding="utf-8")
                return f"Updated {rel_path}."
            if op == "delete":
                if not path.is_file():
                    return f"{rel_path} does not exist."
                path.unlink()
                return f"Deleted {rel_path}."
            return f"Unknown file op '{op}'. Valid ops: create, read, update, delete, list."
        except (ValueError, OSError) as exc:
            return f"File error: {exc}"