import os
import json
import mysql.connector

from enum import Enum
from google import genai
from dotenv import load_dotenv


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

API_KEY = os.getenv("API_KEY")
MODEL = "gemini-3.5-flash-lite"


# ============================================================
# DATABASE
# ============================================================

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

        self.host = os.getenv("host")
        self.user = os.getenv("user")
        self.password = os.getenv("password")
        self.database = os.getenv("database")

        self.con = DBConnector(
            self.host,
            self.user,
            self.password,
            self.database
        ).getConnection()

        self.cur = self.con.cursor(dictionary=True)

    def insert(self, table, attributes, values):

        placeholders = ", ".join(["%s"] * len(values))

        query = f"""
            INSERT INTO {table} {attributes}
            VALUES ({placeholders})
        """

        self.cur.execute(query, values)
        self.con.commit()

    def get(self, attributes, table, conditionalAttribute,
            conditionalOperator, conditionalValue):

        query = f"""
            SELECT {attributes}
            FROM {table}
            WHERE {conditionalAttribute} {conditionalOperator} %s
            LIMIT 1
        """

        self.cur.execute(query, (conditionalValue,))

        return self.cur.fetchone()

    def getAll(self, attributes, table):

        query = f"""
            SELECT {attributes}
            FROM {table}
        """

        self.cur.execute(query)

        return self.cur.fetchall()

    def getAllOnCondition(self, attributes, table,
                          conditionalAttribute,
                          conditionalOperator,
                          conditionalValue):

        query = f"""
            SELECT {attributes}
            FROM {table}
            WHERE {conditionalAttribute} {conditionalOperator} %s
        """

        self.cur.execute(query, (conditionalValue,))

        return self.cur.fetchall()

    def update(self, table, attribute, value,
               conditionalAttribute,
               conditionalOperator,
               conditionalValue):

        query = f"""
            UPDATE {table}
            SET {attribute} = %s
            WHERE {conditionalAttribute} {conditionalOperator} %s
        """

        self.cur.execute(
            query,
            (value, conditionalValue)
        )

        self.con.commit()

    def delete(self, table,
               conditionalAttribute,
               conditionalOperator,
               conditionalValue):

        query = f"""
            DELETE FROM {table}
            WHERE {conditionalAttribute} {conditionalOperator} %s
        """

        self.cur.execute(
            query,
            (conditionalValue,)
        )

        self.con.commit()


# ============================================================
# TABLES
# ============================================================

class Tables(Enum):
    MEMORY = "memory"


# ============================================================
# MEMORY STORE
# ============================================================

class MemoryStore:

    def __init__(self):

        self.db = DB()
        self.memoryTable = Tables.MEMORY.value

    def createMemory(self, memory_type, content):

        self.db.insert(
            self.memoryTable,
            "(memory_type, content)",
            (memory_type, content)
        )

    def readMemoryByType(self, memory_type):

        return self.db.getAllOnCondition(
            "*",
            self.memoryTable,
            "memory_type",
            "=",
            memory_type
        )

    def readMemoryById(self, id):

        return self.db.get(
            "content",
            self.memoryTable,
            "id",
            "=",
            id
        )

    def readCompleteMemory(self):

        return self.db.getAll(
            "*",
            self.memoryTable
        )

    def updateMemoryContent(self, id, content):

        self.db.update(
            self.memoryTable,
            "content",
            content,
            "id",
            "=",
            id
        )

    def deleteMemory(self, id):

        self.db.delete(
            self.memoryTable,
            "id",
            "=",
            id
        )


# ============================================================
# BASE AGENT
# ============================================================

class Agent:

    def __init__(self):

        self.buildAgent()
        self.client = genai.Client(api_key=API_KEY)

    def buildAgent(self):

        self.name = ""
        self.role = ""
        self.instructions = ""

    def ask(self, prompt):

        interaction = self.client.interactions.create(
            model=MODEL,
            input=prompt
        )

        return interaction.output_text

    def assignTask(self, task):

        self.task = task

    def execute(self):

        prompt = f"""
{self.instructions}

TASK:
{self.task}
"""

        return self.ask(prompt)


# ============================================================
# MEMORY TYPE RETRIEVER
# ============================================================

class MemoryTypeRetriever(Agent):

    def buildAgent(self):

        self.name = "Murtaza"
        self.role = "Memory Type Retriever"

        self.instructions = f"""
You are {self.name}, a Memory Type Retriever.

Your job is ONLY to analyze the current user's task and determine
which memory types may contain relevant existing memories.

You do NOT create memories.
You do NOT update memories.
You do NOT delete memories.
You do NOT answer the user's task.
You do NOT access the database.

AVAILABLE MEMORY TYPES:

- identity
- preference
- skill
- education
- career
- project
- goal
- habit
- interest
- experience
- relationship
- other

Return the smallest useful set of memory types.

Do not return every possible type.

If no memory type is relevant, return an empty list.

Return valid JSON only.

OUTPUT FORMAT:

{{
    "memory_types": ["type1", "type2"]
}}

If no relevant memories are needed:

{{
    "memory_types": []
}}
"""


# ============================================================
# MEMORY MANAGER
# ============================================================

class MemoryAgent(Agent):

    def buildAgent(self):

        self.name = "Mustafa"
        self.role = "Memory Manager"

        self.instructions = f"""
You are {self.name}, a Memory Manager.

Your role is to manage the long-term historical memory of a person.

You receive:

1. The user's current task/message.
2. Existing candidate memories retrieved from MemoryStore.

Your job is NOT to answer the user's task.

Your job is to determine whether the user's message requires:

- creating a new memory
- updating an existing memory
- deleting an existing memory
- or doing nothing

AVAILABLE MEMORY TYPES:

- identity
- preference
- skill
- education
- career
- project
- goal
- habit
- interest
- experience
- relationship
- other

AVAILABLE OPERATIONS:

CREATE:

{{
    "operation": "create",
    "memory_type": "interest",
    "content": "The person likes C++."
}}

UPDATE:

{{
    "operation": "update",
    "memory_id": 12,
    "content": "The person prefers Java over C++."
}}

DELETE:

{{
    "operation": "delete",
    "memory_id": 12
}}

IMPORTANT RULES:

1. Only store useful long-term information.
2. Do not store temporary or irrelevant information.
3. Never invent information.
4. Never invent memory IDs.
5. For update/delete, only use IDs from the provided existing memories.
6. Do not create duplicate memories.
7. If new information changes an existing memory, update it.
8. If the user explicitly asks to forget/remove information, delete it.
9. If there is no memory operation required, return an empty list.
10. Do not generate SQL.
11. Do not generate Python.
12. Return valid JSON only.
13. Do not include explanations outside JSON.

OUTPUT FORMAT:

{{
    "operations": [
        {{
            "operation": "create",
            "memory_type": "skill",
            "content": "The person is learning Python."
        }}
    ]
}}

OR:

{{
    "operations": []
}}
"""


# ============================================================
# RESEARCH AGENT
# ============================================================

class ResearchAgent(Agent):

    def buildAgent(self):

        self.name = "Ahmad"
        self.role = "Researcher"

        self.instructions = f"""
You are a researcher.

Your name is {self.name}.

You have extensive experience in researching topics.

You first understand the task properly and then produce a structured
research response.

Use the provided memories as context when they are relevant.

Return the research document in Markdown format and nothing else.
"""


# ============================================================
# CODING AGENT
# ============================================================

class CodingAgent(Agent):

    def buildAgent(self):

        self.name = "Ayesha"
        self.role = "Developer"

        self.instructions = f"""
You are a professional software developer.

Your name is {self.name}.

You first understand the complete problem, then design the solution,
and then implement it.

Use the provided memories as context when relevant.

When the task requires code, return the code as the primary response.
"""


# ============================================================
# WRITING AGENT
# ============================================================

class WritingAgent(Agent):

    def buildAgent(self):

        self.name = "Akram"
        self.role = "Writer"

        self.instructions = f"""
You are a professional writer.

Your name is {self.name}.

You can write in different genres, topics, and languages.

Follow the user's requested language, style, and length.

If no language is specified, use English.

If no length is specified, write a reasonably concise response.

Use the provided memories as context when relevant.

Return the requested piece of writing and nothing else.
"""


# ============================================================
# MEMORY SYSTEM
# ============================================================

class MemorySystem:

    def __init__(self):

        self.memoryStore = MemoryStore()

        self.memoryTypeRetriever = MemoryTypeRetriever()
        self.memoryAgent = MemoryAgent()

    # --------------------------------------------------------
    # STEP 1: FIND MEMORY TYPES
    # --------------------------------------------------------

    def retrieveMemoryTypes(self, task):

        self.memoryTypeRetriever.assignTask(task)

        response = self.memoryTypeRetriever.execute()

        try:

            data = json.loads(response)

            memory_types = data.get(
                "memory_types",
                []
            )

            return memory_types

        except json.JSONDecodeError:

            print("\nMemoryTypeRetriever returned invalid JSON:")
            print(response)

            return []

    # --------------------------------------------------------
    # STEP 2: RETRIEVE MEMORIES
    # --------------------------------------------------------

    def retrieveMemories(self, memory_types):

        memories = []

        for memory_type in memory_types:

            type_memories = (
                self.memoryStore.readMemoryByType(
                    memory_type
                )
            )

            memories.extend(type_memories)

        return memories

    # --------------------------------------------------------
    # STEP 3: MEMORY MANAGER
    # --------------------------------------------------------

    def manageMemory(self, task, memories):

        memory_context = json.dumps(
            memories,
            indent=2,
            ensure_ascii=False
        )

        prompt = f"""
{self.memoryAgent.instructions}

CURRENT USER TASK:

{task}

EXISTING CANDIDATE MEMORIES:

{memory_context}

Now determine the required memory operations.

Return JSON only.
"""

        response = self.memoryAgent.ask(prompt)

        try:

            return json.loads(response)

        except json.JSONDecodeError:

            print("\nMemoryAgent returned invalid JSON:")
            print(response)

            return {
                "operations": []
            }

    # --------------------------------------------------------
    # STEP 4: EXECUTE MEMORY OPERATIONS
    # --------------------------------------------------------

    def executeMemoryOperations(self, result, memories):

        operations = result.get(
            "operations",
            []
        )

        valid_memory_ids = {
            memory["id"]
            for memory in memories
        }

        for operation in operations:

            operation_type = operation.get(
                "operation"
            )

            # ----------------------------------------------
            # CREATE
            # ----------------------------------------------

            if operation_type == "create":

                memory_type = operation.get(
                    "memory_type"
                )

                content = operation.get(
                    "content"
                )

                if memory_type and content:

                    self.memoryStore.createMemory(
                        memory_type,
                        content
                    )

                    print(
                        f"[Memory Created] "
                        f"{memory_type}: {content}"
                    )

            # ----------------------------------------------
            # UPDATE
            # ----------------------------------------------

            elif operation_type == "update":

                memory_id = operation.get(
                    "memory_id"
                )

                content = operation.get(
                    "content"
                )

                if memory_id not in valid_memory_ids:

                    print(
                        f"[Security] Invalid memory ID: "
                        f"{memory_id}"
                    )

                    continue

                if content:

                    self.memoryStore.updateMemoryContent(
                        memory_id,
                        content
                    )

                    print(
                        f"[Memory Updated] "
                        f"ID {memory_id}: {content}"
                    )

            # ----------------------------------------------
            # DELETE
            # ----------------------------------------------

            elif operation_type == "delete":

                memory_id = operation.get(
                    "memory_id"
                )

                if memory_id not in valid_memory_ids:

                    print(
                        f"[Security] Invalid memory ID: "
                        f"{memory_id}"
                    )

                    continue

                self.memoryStore.deleteMemory(
                    memory_id
                )

                print(
                    f"[Memory Deleted] "
                    f"ID {memory_id}"
                )

    # --------------------------------------------------------
    # COMPLETE MEMORY PIPELINE
    # --------------------------------------------------------

    def process(self, task):

        # 1. Find relevant memory types
        memory_types = self.retrieveMemoryTypes(task)

        print(
            f"[Memory Types] {memory_types}"
        )

        # 2. Retrieve candidate memories
        memories = self.retrieveMemories(
            memory_types
        )

        print(
            f"[Candidate Memories] "
            f"{len(memories)}"
        )

        # 3. Ask Memory Manager what to do
        memory_operations = self.manageMemory(
            task,
            memories
        )

        # 4. Execute operations
        self.executeMemoryOperations(
            memory_operations,
            memories
        )

        # 5. Return memories that should be
        #    used as context by final agent.
        #
        #    Re-read them because memory may have
        #    been created/updated/deleted.

        updated_types = set(memory_types)

        for operation in memory_operations.get(
            "operations",
            []
        ):

            if operation.get("memory_type"):
                updated_types.add(
                    operation["memory_type"]
                )

        final_memories = self.retrieveMemories(
            list(updated_types)
        )

        return final_memories


# ============================================================
# AGENT MANAGER
# ============================================================

class AgentManager:

    def __init__(self):

        self.agents = {

            "research": ResearchAgent(),
            "coding": CodingAgent(),
            "writing": WritingAgent()
        }

        self.memorySystem = MemorySystem()

        self.currentAgent = None

    # --------------------------------------------------------
    # SHOW AGENTS
    # --------------------------------------------------------

    def showAgents(self):

        print("\nAvailable Agents:")

        for key, agent in self.agents.items():

            print(
                f"- {key}: "
                f"{agent.name} ({agent.role})"
            )

    # --------------------------------------------------------
    # SWITCH AGENT
    # --------------------------------------------------------

    def switchAgent(self, agent_name):

        if agent_name not in self.agents:

            print(
                f"Agent '{agent_name}' does not exist."
            )

            return False

        self.currentAgent = self.agents[
            agent_name
        ]

        print(
            f"\nSwitched to "
            f"{self.currentAgent.name} "
            f"({self.currentAgent.role})"
        )

        return True

    # --------------------------------------------------------
    # EXECUTE USER TASK
    # --------------------------------------------------------

    def executeTask(self, task):

        if self.currentAgent is None:

            print(
                "Please select an agent first."
            )

            return

        print("\n--- Memory System ---")

        memories = self.memorySystem.process(
            task
        )

        print(
            f"\n[Final Context Memories] "
            f"{len(memories)}"
        )

        # Convert memories to JSON
        memory_context = json.dumps(
            memories,
            indent=2,
            ensure_ascii=False
        )

        # ----------------------------------------------------
        # FINAL AGENT
        # ----------------------------------------------------

        final_prompt = f"""
{self.currentAgent.instructions}

IMPORTANT CONTEXT:

The following memories belong to the person making this request.
Use them only when relevant to the current task.

MEMORIES:

{memory_context}

CURRENT TASK:

{task}

Now perform the task.
"""

        print(
            f"\n--- {self.currentAgent.name} ---\n"
        )

        response = self.currentAgent.ask(
            final_prompt
        )

        print(response)


# ============================================================
# MAIN LOOP
# ============================================================

def main():

    print("======================================")
    print("       MEMORY-AWARE AGENT SYSTEM")
    print("======================================")

    agentManager = AgentManager()

    agentManager.showAgents()

    while True:

        print("\n--------------------------------------")

        command = input(
            "\nEnter agent name, 'agents', or 'exit': "
        ).strip().lower()

        # ----------------------------------------------------
        # EXIT
        # ----------------------------------------------------

        if command == "exit":

            print("Goodbye.")

            break

        # ----------------------------------------------------
        # SHOW AGENTS
        # ----------------------------------------------------

        if command == "agents":

            agentManager.showAgents()

            continue

        # ----------------------------------------------------
        # SWITCH AGENT
        # ----------------------------------------------------

        if command not in agentManager.agents:

            print(
                "Invalid agent."
            )

            continue

        agentManager.switchAgent(
            command
        )

        # ----------------------------------------------------
        # TASK LOOP
        # ----------------------------------------------------

        while True:

            task = input(
                "\nEnter task "
                "(type 'switch' to change agent, "
                "'exit' to quit):\n> "
            ).strip()

            if task == "exit":

                print("Goodbye.")

                return

            if task == "switch":

                break

            if not task:

                continue

            agentManager.executeTask(
                task
            )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()