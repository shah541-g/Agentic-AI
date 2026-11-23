# Step-by-Step Guide: Building Persistent Database Memory for Agents 🛠️

> **Target Files:**
> - [`Deliverable/chat.py`](Deliverable/chat.py)
> - [`Deliverable/m0-d08-mysqlcrud.py`](Deliverable/m0-d08-mysqlcrud.py)
>
> **Key Objective:** Build a relational database layer that provides persistent memory, multi-turn history, and agent switching for autonomous AI systems.

---

## 🏗️ Step 1: Designing the Database Schema

To build a persistent agent system, we create tables for agents, conversations, and executed tasks.

```sql
-- Agents Table: Holds agent personas
CREATE TABLE IF NOT EXISTS agents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(100) NOT NULL,
    instructions TEXT NOT NULL
);

-- Conversations Table: Groups messages into multi-turn sessions
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- Messages / Tasks Table: Records prompt and response history
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    task TEXT NOT NULL,
    response MEDIUMTEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);
```

*(Note: In SQLite environments, replace `INT AUTO_INCREMENT PRIMARY KEY` with `INTEGER PRIMARY KEY AUTOINCREMENT` and `TIMESTAMP` with `DATETIME DEFAULT CURRENT_TIMESTAMP`.)*

---

## 🏗️ Step 2: Building the Reusable Database Connector

In [`Deliverable/m0-d08-mysqlcrud.py`](Deliverable/m0-d08-mysqlcrud.py), encapsulate database connection logic:

```python
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

class DBConnector:
    def __init__(self, host, user, password, database):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )

    def getConnection(self):
        return self.conn

class DB:
    def __init__(self):
        self.host = os.getenv("host", "localhost")
        self.user = os.getenv("user", "root")
        self.password = os.getenv("password", "")
        self.database = os.getenv("database", "agent_memory")
        self.con = DBConnector(self.host, self.user, self.password, self.database).getConnection()
        self.cur = self.con.cursor(dictionary=True)

    def insert(self, table: str, attributes: list, values: list):
        cols = ", ".join(attributes)
        placeholders = ", ".join(["%s"] * len(values))
        query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
        self.cur.execute(query, tuple(values))
        self.con.commit()
        return self.cur.lastrowid

    def select(self, table: str, condition: str = None, params: tuple = None):
        query = f"SELECT * FROM {table}"
        if condition:
            query += f" WHERE {condition}"
        self.cur.execute(query, params or ())
        return self.cur.fetchall()
```

---

## 🏗️ Step 3: Implementing the Multi-Agent Switcher & Runner (`chat.py`)

In [`Deliverable/chat.py`](Deliverable/chat.py), create an `AgentManager` that switches between active agent personas and records memory:

```python
from google import genai
import os

class AgentManager:
    def __init__(self, db: DB):
        self.db = db
        self.client = genai.Client(api_key=os.getenv("API_KEY"))
        self.agents = {
            "researcher": {
                "name": "Ahmad",
                "role": "Researcher",
                "instructions": "You are a research agent. Return structured IEEE-style findings in markdown."
            },
            "coder": {
                "name": "Ayesha",
                "role": "Developer",
                "instructions": "You are a software engineer. Return runnable code blocks with clean documentation."
            },
            "writer": {
                "name": "Akram",
                "role": "Writer",
                "instructions": "You are a creative writer. Deliver deep narrative prose under 350 words."
            }
        }
        self.active_agent_key = "researcher"

    def showAgents(self):
        print("\nAvailable Specialist Agents:")
        for key, agent in self.agents.items():
            print(f"- {key}: {agent['name']} ({agent['role']})")

    def switchAgent(self, agent_key: str):
        if agent_key in self.agents:
            self.active_agent_key = agent_key
            print(f"\nSwitched active agent to: {self.agents[agent_key]['name']} [{self.agents[agent_key]['role']}]")
        else:
            print(f"Unknown agent: {agent_key}")

    def executeTask(self, task: str):
        agent = self.agents[self.active_agent_key]
        print(f"\n[Thinking...] Running task with {agent['name']}...")

        prompt = f"<<SYSTEM INSTRUCTIONS>>\n{agent['instructions']}\n\n<<TASK>>\n{task}"
        
        response = self.client.interactions.create(
            model="gemini-3.5-flash-lite",
            input=prompt
        )
        output = response.output_text
        print(f"\n[{agent['role']} Output]:\n{output}")

        # Persist memory record to database
        try:
            self.db.insert(
                "messages",
                ["conversation_id", "task", "response"],
                [1, task, output]
            )
            print("\n[Memory Synced to Database]")
        except Exception as e:
            print(f"\n[Warning: Memory sync failed: {e}]")
```

---

## 🏗️ Step 4: Building the Interactive CLI Loop

Provide an intuitive terminal shell that enables non-technical users to query the agents:

```python
def main():
    db = DB()
    manager = AgentManager(db)

    print("========================================")
    print("   AI AGENT CLI & PERSISTENT MEMORY     ")
    print("========================================")
    print("Commands: 'agents' to list, 'switch' to change agent, 'exit' to quit.\n")

    while True:
        manager.showAgents()
        choice = input("\nSelect an agent by key (or 'exit'): ").strip().lower()
        if choice == "exit":
            break
        if choice not in manager.agents:
            print("Invalid choice, please select from the listed keys.")
            continue

        manager.switchAgent(choice)

        while True:
            task = input("\nEnter task ('switch' to change agent, 'exit' to quit):\n> ").strip()
            if task == "exit":
                print("Goodbye!")
                return
            if task == "switch":
                break
            if not task:
                continue

            manager.executeTask(task)

if __name__ == "__main__":
    main()
```

---

## 💡 Key Agentic Engineering Insights

1. **Context Window Protection:** Rather than stuffing thousands of lines of past chat history into the LLM prompt (which drains tokens and causes context drift), databases allow agents to query recent memories or semantic summaries.
2. **Session Isolation:** Grouping messages by `conversation_id` allows multiple concurrent users or multi-agent threads to operate simultaneously without state collisions.
3. **Database Independence:** By encapsulating queries inside `DB.insert()` and `DB.select()`, you can seamlessly swap MySQL for SQLite (for local embedded agents) or PostgreSQL (for production cloud deployments) without modifying agent application code.
