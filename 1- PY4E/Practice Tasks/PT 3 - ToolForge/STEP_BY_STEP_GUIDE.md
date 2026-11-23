# Step-by-Step Guide: Building ToolForge & Dynamic Tool Calling 🛠️

> **Target Directory:** [`Practice Tasks/PT 3 - ToolForge/`](README.md)  
> **Key Objective:** Build a clean, framework-independent ReAct tool-calling agent using XML delimiters, dynamic dispatch, and SQLite memory.

---

## 🏗️ Step 1: Defining the Tool Calling Protocol (`tools.py`)

LLMs generate text. To instruct an LLM to call external code without breaking JSON formatting when handling long multiline files, we establish an XML-wrapped JSON protocol:

```python
TOOL_DOCS = """
You can use tools. To call ONE tool, reply with ONLY the tool call (plus a file block if needed):

<tool_call>{"tool": "<name>", "args": {...}}</tool_call>

TOOLS:
1. get_project_details  args: {"query": "<search keywords>"}
2. web_search           args: {"query": "<search query>"}
3. file_op              args: {"op": "create|read|update|delete|list", "path": "<relative path>"}

FILE TEXT: right after the tool call, write the raw file text:
<tool_call>{"tool": "file_op", "args": {"op": "create", "path": "notes.md"}}</tool_call>
<file_content>
# Raw File Content Here (No JSON escaping required)
</file_content>
"""
```

---

## 🏗️ Step 2: Implementing the Dynamic `ToolBox`

Create a unified dispatcher that routes calls to specific Python methods:

```python
from pathlib import Path
from typing import Any

class ToolBox:
    def __init__(self, workspace_dir: Path, memory_store):
        self.workspace = workspace_dir
        self.memory = memory_store

    def execute(self, tool_name: str, args: dict, file_content: str = None) -> str:
        if tool_name == "web_search":
            query = args.get("query", "")
            return self._web_search(query)
        elif tool_name == "file_op":
            return self._file_op(args.get("op"), args.get("path"), file_content)
        elif tool_name == "get_project_details":
            return self.memory.query_projects(args.get("query", ""))
        else:
            return f"Error: Unknown tool '{tool_name}'."

    def _file_op(self, op: str, rel_path: str, content: str = None) -> str:
        target = (self.workspace / rel_path).resolve()
        # Security sandbox check: prevent directory traversal attacks (../)
        if not str(target).startswith(str(self.workspace.resolve())):
            return "Error: Access outside workspace directory is forbidden."

        if op == "create" or op == "update":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content or "", encoding="utf-8")
            return f"File successfully written to {rel_path} ({len(content or '')} chars)."
        elif op == "read":
            if not target.exists():
                return f"Error: File {rel_path} does not exist."
            return target.read_text(encoding="utf-8")[:6000]
        elif op == "list":
            files = [str(p.relative_to(self.workspace)) for p in self.workspace.glob("**/*") if p.is_file()]
            return f"Workspace files:\n" + "\n".join(files)
        return f"Error: Unsupported file operation '{op}'."
```

---

## 🏗️ Step 3: Parsing XML Tool Blocks (`app.py`)

Compile regexes to parse the LLM's response:

```python
import re, json

TOOL_CALL_RE = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)
FILE_CONTENT_RE = re.compile(r"<file_content>\s*(.*?)\s*</file_content>", re.DOTALL)

def parse_agent_response(llm_output: str):
    tool_match = TOOL_CALL_RE.search(llm_output)
    if not tool_match:
        return None, None, None  # No tool call; final response reached!

    raw_json = tool_match.group(1).strip()
    tool_data = json.loads(raw_json)
    tool_name = tool_data.get("tool")
    args = tool_data.get("args", {})

    file_match = FILE_CONTENT_RE.search(llm_output)
    file_content = file_match.group(1) if file_match else None

    return tool_name, args, file_content
```

---

## 🏗️ Step 4: The ReAct Reasoning Loop

Implement the execution loop that allows the agent to reason, act, observe, and iterate:

```python
def run_agent(task_prompt: str, toolbox: ToolBox, max_steps: int = 8):
    messages = [
        {"role": "system", "content": f"You are an autonomous problem-solving agent.\n{TOOL_DOCS}"},
        {"role": "user", "content": task_prompt}
    ]

    for step in range(1, max_steps + 1):
        print(f"\n[Step {step}] Invoking LLM...")
        llm_reply = call_llm(messages)

        tool_name, args, file_content = parse_agent_response(llm_reply)

        if not tool_name:
            print("\n[Final Answer Reached]:")
            print(llm_reply)
            return llm_reply

        print(f"--> Tool Requested: {tool_name} with args: {args}")
        tool_result = toolbox.execute(tool_name, args, file_content)
        print(f"<-- Tool Result: {tool_result[:150]}...")

        # Append observation to history
        messages.append({"role": "assistant", "content": llm_reply})
        messages.append({"role": "user", "content": f"Tool Result for {tool_name}:\n{tool_result}"})

    print("Max steps exceeded before reaching final answer.")
```

---

## 💡 Key Architectural Insights

1. **Path Traversal Protection:** Agents generating paths must never write outside their intended sandbox. Checking `str(target).startswith(str(workspace))` eliminates accidental file deletions on the host operating system.
2. **Separating JSON from Raw Content:** Escaping JSON inside JSON for code files (handling newlines, quotation marks, and backslashes) is error-prone for LLMs. Separating raw code into a dedicated `<file_content>` tag eliminates 100% of JSON escaping syntax errors.
3. **Loop Termination:** Enforcing `MAX_TOOL_STEPS` protects against infinite loops and token budget depletion when an agent encounters unexpected tool errors.
