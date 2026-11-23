# Step-by-Step Guide: Building SQLite Memory for Multi-Agent Systems 🛠️

> **Target File:** [`m0-we03 sqlitememory.py`](m0-we03%20sqlitememory.py)  
> **Key Objective:** Build a production-grade relational SQLite memory store with foreign-key cascades, multi-turn history tracking, and a CLI history browser.

---

## 🏗️ Step 1: SQLite Schema with Foreign Key Constraints

SQLite ignores foreign keys by default unless explicitly enabled. Always execute `PRAGMA foreign_keys = ON;` upon opening every database connection:

```python
import sqlite3
from pathlib import Path

class Database:
    def __init__(self, db_path: str = "agent_system.db"):
        self.db_path = db_path
        self._init_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enables column access by name (row["role"])
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_schema(self):
        with self.get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS agent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS session (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                output_folder TEXT NOT NULL,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ended_at DATETIME
            );

            CREATE TABLE IF NOT EXISTS conversation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                agent_id INTEGER NOT NULL,
                task_id TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE,
                FOREIGN KEY (agent_id) REFERENCES agent(id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS message (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                event_type TEXT NOT NULL, -- 'prompt', 'response', 'verification', 'error'
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversation(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS report (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                task_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                status TEXT NOT NULL,
                attempts INTEGER DEFAULT 1,
                FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE
            );
            """)
```

---

## 🏗️ Step 2: Logging Sessions & Messages

When the orchestrator starts, log the session:

```python
    def create_session(self, prompt: str, output_folder: str) -> int:
        with self.get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO session (prompt, output_folder) VALUES (?, ?)",
                (prompt, output_folder)
            )
            return cur.lastrowid

    def log_message(self, conversation_id: int, event_type: str, content: str):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO message (conversation_id, event_type, content) VALUES (?, ?, ?)",
                (conversation_id, event_type, content)
            )
```

---

## 🏗️ Step 3: Cascading Deletions & Constraint Guarantees

Notice the foreign key actions in the schema:
1. **`session` -> `conversation` (`ON DELETE CASCADE`):** If you delete a session (e.g. `python orchestrator.py delete 3`), SQLite automatically deletes all conversations, messages, and reports associated with session 3.
2. **`agent` -> `conversation` (`ON DELETE RESTRICT`):** An agent cannot be accidentally deleted if historical conversations link to it. This guarantees data integrity.

---

## 🏗️ Step 4: CLI History Browser

Implement command-line arguments to let users query past agent executions:

```python
def cli_history():
    import sys
    db = Database()
    args = sys.argv[1:]

    if not args:
        return

    cmd = args[0]
    if cmd == "sessions":
        with db.get_connection() as conn:
            rows = conn.execute("SELECT id, prompt, started_at FROM session ORDER BY id DESC LIMIT 10").fetchall()
            print("\nRecent Sessions:")
            for r in rows:
                print(f"[{r['id']}] {r['started_at']} | Prompt: {r['prompt'][:60]}...")

    elif cmd == "show" and len(args) > 1:
        session_id = int(args[1])
        with db.get_connection() as conn:
            reports = conn.execute("SELECT * FROM report WHERE session_id = ?", (session_id,)).fetchall()
            print(f"\nTasks for Session #{session_id}:")
            for rep in reports:
                print(f"- Task {rep['task_id']} ({rep['agent_name']}): {rep['status']} ({rep['attempts']} attempts)")

    elif cmd == "delete" and len(args) > 1:
        session_id = int(args[1])
        with db.get_connection() as conn:
            conn.execute("DELETE FROM session WHERE id = ?", (session_id,))
            print(f"Session #{session_id} and all related messages deleted.")
        exit(0)
```

---

## 🧪 Testing History Commands

Run these in your terminal to inspect the persistent SQLite memory:

```bash
# List past multi-agent runs
python "m0-we03 sqlitememory.py" sessions

# Inspect specific session tasks and verdicts
python "m0-we03 sqlitememory.py" show 1

# Delete a session with full cascading cleanup
python "m0-we03 sqlitememory.py" delete 1
```

---

## 💡 Key Agentic Engineering Insights

1. **Standard Library Only:** SQLite is embedded in Python's standard library (`sqlite3`). No external database servers or Docker containers are required for local agent execution.
2. **Crash Resilience:** If an agent script is killed mid-run, all progress up to the last completed step remains committed in `agent_system.db`.
3. **Observability Foundation:** Storing every prompt, raw LLM completion, code tool output, and verifier decision enables post-run evaluation and regression testing.
