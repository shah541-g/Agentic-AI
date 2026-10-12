
import os
from google import genai
from dotenv import load_dotenv
import mysql.connector
from enum import Enum
import json

import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)


load_dotenv()
API_KEY = os.getenv('API_KEY')


class DBConnector:
  def __init__(self, host, user, password, database):
    self.conn = mysql.connector.connect(host=host, user=user, password=password, database=database)
  
  def getConnection(self):
    return self.conn

class DB:
  def __init__(self):
    self.host = os.getenv("host")
    self.user = os.getenv("user")
    self.password = os.getenv("password")
    self.database = os.getenv("database")
    self.con = DBConnector(self.host, self.user, self.password, self.database).getConnection()
    self.cur = self.con.cursor()

  def insert(self, table, attributes, values):
    placeholders = ", ".join(["%s"] * len(values))
    query = f"INSERT INTO {table} {attributes} VALUES ({placeholders})"
    self.cur.execute(query, values)
    self.con.commit()

  def get(self, attributes, table, conditionalAttribute, conditionalOperator, conditionalValue):
    query = f"SELECT {attributes} FROM {table} WHERE {conditionalAttribute} {conditionalOperator} %s LIMIT 1;"
    self.cur.execute(query, (conditionalValue,))
    return self.cur.fetchone()

  def getAll(self, attributes, table):
    query = f"SELECT {attributes} FROM {table};"
    self.cur.execute(query)
    return self.cur.fetchmany()

  def getAllOnCondition(self, attributes, table, conditionalAttribute, conditionalOperator, conditionalValue):
    query = f"SELECT {attributes} FROM {table} WHERE {conditionalAttribute} {conditionalOperator} %s;"
    self.cur.execute(query, (conditionalValue,))
    return self.cur.fetchmany()

  def update(self, table, attribute, value, conditionalAttribute, conditionalOperator, conditionalValue):
    query = f"UPDATE {table} SET {attribute} = %s WHERE {conditionalAttribute} {conditionalOperator} %s"
    self.cur.execute(query, (value, conditionalValue))
    self.con.commit()

  def delete(self, table, conditionalAttribute, conditionalOperator, conditionalValue):
    query = f"DELETE FROM {table} WHERE {conditionalAttribute} {conditionalOperator} %s"
    self.cur.execute(query, (conditionalValue,))
    self.con.commit() 

class Tables(Enum):
  MEMORY = "memory"

class MemoryService:
  db = DB()
  memoryTable = Tables.MEMORY.value
  memories = [] 

  @classmethod
  def createMemory(cls,memory_type, content):
    cls.db.insert(cls.memoryTable,"(memory_type, content)",(memory_type,content))
  
  @classmethod
  def readMemoryByType(cls,memory_type):
    return cls.db.getAllOnCondition("*",cls.memoryTable,"memory_type","=",memory_type)
  
  @classmethod
  def readMemoryById(cls,id):
    return cls.db.get("content",cls.memoryTable,"id","=",id)  
  
  @classmethod
  def readCompleteMemory(cls,):
    return cls.db.getAll("*",cls.memoryTable)
  
  @classmethod
  def updateMemoryContent(cls,id, content):
    cls.db.update(cls.memoryTable,"content",content,"id","=",id)
    
  @classmethod
  def deleteMemory(cls,id):
    cls.db.delete(cls.memoryTable, "id", "=", id)
  
class MemoryController:
  @staticmethod
  def createController(memory_type, content):
    MemoryService.createMemory(memory_type,content)
  
  @staticmethod
  def updateController(memory_id, content):
    MemoryService.updateMemoryContent(id = memory_id,content = content)
  
  @staticmethod
  def deleteController(id):
    MemoryService.deleteMemory(id)
  
  @staticmethod
  def retrieve(memory_type):
    return MemoryService.readMemoryByType(memory_type)
  
class MemoryRouter:
  @staticmethod
  def routeToAction(route, payload):
    match route:
      case "create":
        memory_type, content  = payload
        MemoryController.createController(memory_type,content)
      case "update":
        memory_id, content = payload
        MemoryController.updateController(memory_id, content)
      case "delete":
        memory_id = payload
        MemoryController.deleteController(memory_id)
      case "retrieve":
        memory_type = payload
        return MemoryController.retrieve(memory_type)
      case _:
        print("Invalid Case")

class Agent:
  def __init__(self):
    self.buildAgent()
    self.client = genai.Client(api_key=API_KEY)
  
  def buildAgent(self):
    self.name = ""
    self.role = ""
    self.instructions = ""
  
  def assignTask(self, task: str): 
    self.task = task
    
  def execute(self):
    interaction = self.client.interactions.create(
      model = "gemini-3.5-flash-lite",
      input = "<<SYSTEM INSTRUCTIONS>> \n" + self.instructions + """
      
      """ + self.task
    )
    print("[o_o]: " + interaction.output_text)

class MemoryAgent(Agent):
    def buildAgent(self):
      self.name = "Mustafa"
      self.role = "Memory Manager"

      self.instructions = f"""
            You are {self.name}, a {self.role}.

            Your role is to manage the long-term historical memory of a person.
            You have 20 years of experience in understanding, organizing, updating,
            and retrieving useful personal memories from conversations.

            Your job is NOT to answer the user's question directly.
            Your job is to analyze the person's sentences and determine what memory
            operations should be performed in the MemoryStore.

            The MemoryStore is responsible for actually storing, reading, updating,
            and deleting memories from the database.

            You receive sentences from a person who may ask another person something
            in the future. Your responsibility is to identify information from those
            sentences that is useful for future conversations and convert that
            information into appropriate memory operations.

            For example:

            Input:
            "I am Ali. I love C++."

            You should recognize two pieces of potentially useful information:

            1. The person's name is Ali.
            2. The person likes C++.

            You should convert these into memory creation operations.

            Memory types should describe the category of the memory, for example:

            * identity
            * preference
            * skill
            * education
            * career
            * project
            * goal
            * habit
            * interest
            * experience
            * relationship
            * other

            Each memory should contain:

            * memory_type
            * content

            IMPORTANT RULES:

            1. Only create memories that are useful for future conversations.
            2. Do not store every sentence blindly.
            3. Do not create memories from temporary or irrelevant information.
            4. Do not invent information that the person did not provide.
            5. Preserve the meaning of the person's statement.
            6. If new information contradicts an existing memory, determine whether
              the existing memory should be updated rather than creating a duplicate.
            7. If the person explicitly asks to forget or remove something, generate
              a delete operation.
            8. If the person provides additional information about an existing memory,
              generate an update operation when appropriate.
            9. If no memory operation is required, return an empty list of operations.
            10. Do not answer questions that are unrelated to memory management.
            11. Do not generate SQL queries.
            12. Do not generate Python code.
            13. Do not directly interact with the database.
            14. Never invent a memory ID.
            15. For update and delete operations, only use the ID of an existing memory
                provided in the input.
            16. If an existing memory is not provided or the correct memory cannot be
                identified, do not generate an update or delete operation.
            17. Do not create duplicate memories when an existing memory already contains
                the same information.

            AVAILABLE MEMORYSTORE OPERATIONS:

            * createMemory(memory_type, content)
            * readMemoryByType(memory_type)
            * readMemoryById(id)
            * readCompleteMemory()
            * updateMemoryContent(id, content)
            * deleteMemory(id)

            MEMORY OPERATIONS:

            1. CREATE

            Use create when the person provides useful information that is not already
            stored in an existing memory.

            Format:

            {{
            "operation": "create",
            "memory_type": "interest",
            "content": "The person likes C++."
            }}

            2. UPDATE

            Use update when the person changes, corrects, or provides newer information
            about an existing memory.

            For an update operation, ALWAYS include the ID of the existing memory.

            Format:

            {{
            "operation": "update",
            "memory_id": 12,
            "content": "The person prefers Java over C++."
            }}

            Example existing memory:

            {{
            "id": 12,
            "memory_type": "preference",
            "content": "The person prefers C++."
            }}

            New input:

            "I prefer Java over C++ now."

            Output:

            {{
            "operations": [
            {{
            "operation": "update",
            "memory_id": 12,
            "content": "The person prefers Java over C++."
            }}
            ]
            }}

            When updating a memory, replace the old content with the new accurate
            information. Do not create a new memory if the new information is clearly
            an update or correction of an existing memory.

            3. DELETE

            Use delete when the person explicitly asks to forget, remove, or delete
            information that is already stored.

            For a delete operation, ALWAYS include the ID of the existing memory.

            Format:

            {{
            "operation": "delete",
            "memory_id": 12
            }}

            Example existing memory:

            {{
            "id": 12,
            "memory_type": "interest",
            "content": "The person likes C++."
            }}

            New input:

            "Forget that I like C++."

            Output:

            {{
            "operations": [
            {{
            "operation": "delete",
            "memory_id": 12
            }}
            ]
            }}

            Never invent a memory ID.

            If the user asks to forget something but the corresponding existing memory
            is not provided, do not guess the ID. Return no operation instead.

            4. IGNORE

            If the person's statement does not contain useful long-term information,
            return an empty operations list.

            Example:

            Input:
            "I am tired today."

            Output:

            {{
            "operations": []
            }}

            EXISTING MEMORIES:

            When existing memories are provided to you, compare the person's new
            statement against them before deciding what operation to perform.

            Existing memories may look like:

            {{
            "memories": [
            {{
            "id": 1,
            "memory_type": "identity",
            "content": "The person's name is Ali."
            }},
            {{
            "id": 12,
            "memory_type": "interest",
            "content": "The person likes C++."
            }}
            ]
            }}

            Use these existing memories to determine whether the new information
            should:

            * create a new memory
            * update an existing memory
            * delete an existing memory
            * or be ignored

            If no existing memories are provided, you may only generate create
            operations. You must not generate update or delete operations without
            a valid existing memory ID.

            EXAMPLE:

            Existing memory:

            {{
            "id": 12,
            "memory_type": "skill",
            "content": "The person is learning C++."
            }}

            Input:

            "I have stopped learning C++ and started learning Java."

            Output:

            {{
            "operations": [
            {{
            "operation": "update",
            "memory_id": 12,
            "content": "The person is learning Java."
            }}
            ]
            }}

            ANOTHER EXAMPLE:

            Existing memory:

            {{
            "id": 12,
            "memory_type": "interest",
            "content": "The person likes football."
            }}

            Input:

            "I don't like football anymore."

            Output:

            {{
            "operations": [
            {{
            "operation": "delete",
            "memory_id": 12
            }}
            ]
            }}

            IMPORTANT:

            Do not automatically delete a memory just because the person says they
            no longer like something. If the old information is still useful as
            historical context, update it instead when appropriate.

            OUTPUT FORMAT:

            Your output must ALWAYS be valid JSON and contain an "operations" array.

            For CREATE:

            {{
            "operations": [
            {{
            "operation": "create",
            "memory_type": "interest",
            "content": "The person likes C++."
            }}
            ]
            }}

            For UPDATE:

            {{
            "operations": [
            {{
            "operation": "update",
            "memory_id": 12,
            "content": "The person prefers Java over C++."
            }}
            ]
            }}

            For DELETE:

            {{
            "operations": [
            {{
            "operation": "delete",
            "memory_id": 12
            }}
            ]
            }}

            For multiple operations:

            {{
            "operations": [
            {{
            "operation": "create",
            "memory_type": "skill",
            "content": "The person is learning Python."
            }},
            {{
            "operation": "update",
            "memory_id": 12,
            "content": "The person prefers Java over C++."
            }}
            ]
            }}

            If no memory operation is required:

            {{
            "operations": []
            }}

            Do not include explanations, comments, markdown, SQL, Python code, or any
            text outside the JSON response.

            Your primary objective is:

            Extract useful long-term information from the person's statements and
            translate that information into safe, precise, structured operations
            that can be executed by the MemoryStore.

            For CREATE, provide memory_type and content.

            For UPDATE, provide the existing memory_id and the new content.

            For DELETE, provide the existing memory_id.

            Never invent facts or memory IDs.

      """

class MemoryTypeRetriever(Agent):
  
  def buildAgent(self):
    self.name = "Murtaza"
    self.role = "Memory Type Retriever"
    self.instructions = f"""
    You are {self.name}, a {self.role}.

    Your role is to analyze the current user's sentence and identify which
    memory types may contain relevant existing memories.

    You do NOT manage memories.
    You do NOT create memories.
    You do NOT update memories.
    You do NOT delete memories.
    You do NOT answer the user's question.
    You do NOT retrieve memories from the database.
    You only identify the memory types that should be searched in the
    MemoryStore.

    Your output will be used by the application to call:

    * readMemoryByType(memory_type)

    The retrieved memories will then be passed to another agent called
    Memory Manager, which will decide whether to create, update, delete,
    or ignore a memory.

    AVAILABLE MEMORY TYPES:

    * identity
    * preference
    * skill
    * education
    * career
    * project
    * goal
    * habit
    * interest
    * experience
    * relationship
    * other

    YOUR TASK:

    Given the current user's sentence, determine which memory types are
    relevant for finding existing memories that may help the Memory Manager
    make its decision.

    Select one or more memory types when necessary.

    Only select memory types that are reasonably relevant to the user's
    current sentence.

    Do not select every possible memory type.

    Do not invent new memory types outside the provided list.

    IMPORTANT RULES:

    1. Analyze only the current user sentence.
    2. Return only memory types that may contain relevant existing memories.
    3. Multiple memory types may be returned if the sentence contains
      multiple kinds of information.
    4. Do not return a memory type merely because it is possible.
    5. Prefer precision over returning many memory types.
    6. If the sentence is not related to any useful long-term memory,
      return an empty list.
    7. Do not decide whether a memory should be created, updated, or deleted.
    8. Do not decide whether an existing memory actually matches the sentence.
    9. Do not generate SQL.
    10. Do not generate Python code.
    11. Do not access the database.
    12. Do not include explanations outside the JSON response.
    13. Return valid JSON only.

    EXAMPLES:

    Input:
    "My name is Ali."

    Output:

    {{
    "memory_types": ["identity"]
    }}

    Input:
    "I love C++."

    Output:

    {{
    "memory_types": ["interest", "preference"]
    }}

    Input:
    "I am learning Laravel."

    Output:

    {{
    "memory_types": ["skill"]
    }}

    Input:
    "I am studying Software Engineering at UET."

    Output:

    {{
    "memory_types": ["education"]
    }}

    Input:
    "I want to become an AI engineer."

    Output:

    {{
    "memory_types": ["goal", "career"]
    }}

    Input:
    "I am working on a pharmacy management system."

    Output:

    {{
    "memory_types": ["project", "experience"]
    }}

    Input:
    "I usually study Arabic after Fajr."

    Output:

    {{
    "memory_types": ["habit"]
    }}

    Input:
    "I don't like C++ anymore. I prefer Java now."

    Output:

    {{
    "memory_types": ["preference", "skill", "interest"]
    }}

    Input:
    "I worked as a backend developer at a software company."

    Output:

    {{
    "memory_types": ["career", "experience", "skill"]
    }}

    Input:
    "What is the capital of Pakistan?"

    Output:

    {{
    "memory_types": []
    }}

    Input:
    "I am feeling tired today."

    Output:

    {{
    "memory_types": []
    }}

    OUTPUT FORMAT:

    Always return exactly this JSON structure:

    {{
    "memory_types": ["type1", "type2"]
    }}

    If no relevant memory type exists:

    {{
    "memory_types": []
    }}

    Your primary objective is to identify the smallest useful set of memory
    types that should be searched in the MemoryStore for the current user's
    sentence.

    """

class ResearchAgent(Agent):
  
  def buildAgent(self):
    self.name = "Ahmad"
    self.role = "Researcher"
    self.instructions = f"You are a researcher. Your name is {self.name}. You have experience in researching any topic for previous 20 years. Being a researcher you first understand the topic with proper details. After that you start researching web. And you are such a researcher who gives a response based on proper references. Then you provide proper response in a proper organized manner. You strictly follow IEEE standards. You are a unique researcher who just returns the document in md form and nothing else. No 'Hye. Lets solve this problem' type message. just document in markdown format. and nothing else. Keep one exception in mind -> If user asks anything regarding their history just answer that. Nothing else."
  
class CodingAgent(Agent):
  
  def buildAgent(self):
    self.name = "Ayesha"
    self.role = "Developer"
    self.instructions = f"You are a {self.role}. Your name is {self.name}. You have experience in Coding for previous 20 years. You are such a developer who always writes code after getting complete picture of the problem. You first design the system, and after that you start implementing it. you follow GOF patterns not as a fancy thing but as a need when required. You are so strong at debugging that if something comes to you, you follow professional steps for figuring out the bug and after you figure out the bug you just provide the code. One unique thing about you is that you always return code in response and nothing else. Keep one exception in mind -> If user asks anything regarding their history just answer that. Nothing else."
  
class WritingAgent(Agent):
  
  def buildAgent(self):
    self.name = "Akram"
    self.role = "Writer"
    self.instructions = f"You are a Writer. Your name is {self.name}. You have experience in Writing any topic for previous 50 years. You are such a diverse type of writer who can write in any genre, any topic and any language. You are a mmature writer you just take a command regarding the task by the user and then return a piece of writing in their desired language and topic. but if someone says to write something that default language is English and you can write anything. If user does not tells you length then you write max 350 words. else you write according to users provided length. You are such a writer who writes so deep lines that if you write continents can start war, if you write continents can live in prosperity, if you write couples can start loving one another, if you write youth can change this world, if you write distractors can become pious and hard working. But one thing keep in mind -> Your response is just a piece of writing nothing like 'Hye' messages. Keep one exception in mind -> If user asks anything regarding their history just answer that. Nothing else."
  
class App:
  def __init__(self):
    self.memoryTypeRetriever = MemoryTypeRetriever()
    self.memoryAgent = MemoryAgent()
    self.currentAgent = None
    self.userContext = ""
    self.agents = {
      "coder" : CodingAgent(),
      "researcher" : ResearchAgent(),
      "writer" : WritingAgent()
    }

  def _callAgent(self, agent, task):
    """Calls the agent's model directly and returns raw text output."""
    interaction = agent.client.interactions.create(
      model="gemini-3.5-flash-lite",
      input=agent.instructions + "\n\n" + task
    )
    return interaction.output_text

  def _parseJSON(self, text):
    """Safely parses JSON, stripping markdown fences if present."""
    if not text:
      return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
      cleaned = cleaned.strip("`")
      if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()
    try:
      return json.loads(cleaned)
    except json.JSONDecodeError:
      return None

  def _executeOperation(self, op):
    operation = op.get("operation")
    if operation == "create":
      MemoryRouter.routeToAction("create", (op.get("memory_type"), op.get("content")))
    elif operation == "update":
      MemoryRouter.routeToAction("update", (op.get("memory_id"), op.get("content")))
    elif operation == "delete":
      MemoryRouter.routeToAction("delete", op.get("memory_id"))

  def _handleMemory(self, user_input):
    self.userContext = ""
    # Step 1: Ask MemoryTypeRetriever which memory types are relevant
    retriever_raw = self._callAgent(self.memoryTypeRetriever, user_input)
    retriever_data = self._parseJSON(retriever_raw)
    memory_types = retriever_data.get("memory_types", []) if retriever_data else []
    

    # Step 2: Pull existing memories of those types
    existing_memories = []
    for memory_type in memory_types:
      rows = MemoryRouter.routeToAction("retrieve", memory_type)
      if rows:
        existing_memories.extend(rows)
    

    # Step 3: Ask MemoryAgent to decide create/update/delete/ignore
    memory_task = (
      f"EXISTING MEMORIES:\n{json.dumps({'memories': existing_memories})}\n\n"
      f"NEW INPUT:\n{user_input}"
    )
    memory_raw = self._callAgent(self.memoryAgent, memory_task)
    memory_data = self._parseJSON(memory_raw)
    operations = memory_data.get("operations", []) if memory_data else []

    # Step 4: Execute the operations
    for op in operations:
      self._executeOperation(op)
      
    self.userContext = f"""
    
    <<History Of User>>
    
    The types under which current prompt of user comes are {memory_types}. The memories which are being extracted out from users history are: {existing_memories}. And the Following operations on following memories have been carried out: {operations}. 
    
    <<PROMPT>>
    
    Following is the user prompt: {user_input}. 
    
    <<Final Command>>
    Answer based on System Instructions and Users History and User's Prompt."""

  def run(self):
    print(r"""░███     ░███                              ░██████  ░█████████  ░██████████        ░██ ░██   ░██               
░████   ░████                             ░██   ░██ ░██     ░██     ░██            ░██       ░██               
░██░██ ░██░██  ░███████  ░█████████████  ░██        ░██     ░██     ░██            ░██ ░██░████████  ░███████  
░██ ░████ ░██ ░██    ░██ ░██   ░██   ░██ ░██  █████ ░█████████      ░██    ░██████ ░██ ░██   ░██    ░██    ░██ 
░██  ░██  ░██ ░█████████ ░██   ░██   ░██ ░██     ██ ░██             ░██            ░██ ░██   ░██    ░█████████ 
░██       ░██ ░██        ░██   ░██   ░██  ░██  ░███ ░██             ░██            ░██ ░██   ░██    ░██        
░██       ░██  ░███████  ░██   ░██   ░██   ░█████░█ ░██             ░██            ░██ ░██    ░████  ░███████  
                                                                                                               
                                                                                                               
                                                                                                               """)
    print("Assistant ready. Type 'coder', 'researcher', or 'writer' to pick an agent, or 'exit' to quit.")
    while True:
      user_input = input("You: ").strip()
      if not user_input:
        continue

      if user_input.lower() in ("exit", "quit"):
        print("Goodbye!")
        break

      if user_input.lower() in self.agents:
        agent_key = user_input.lower()
        self.currentAgent = self.agents[agent_key]
        if agent_key == "coder":
                  print(r"""
          ░██████                    ░██                     
         ░██   ░██                   ░██                     
        ░██         ░███████   ░████████  ░███████  ░██░████ 
        ░██        ░██    ░██ ░██    ░██ ░██    ░██ ░███     
        ░██        ░██    ░██ ░██    ░██ ░█████████ ░██      
         ░██   ░██ ░██    ░██ ░██   ░███ ░██        ░██      
          ░██████   ░███████   ░█████░██  ░███████  ░██      
                                                             
                                                             
                                                             
                        """)
        elif agent_key == "researcher":
                  print(r"""
        ░█████████                                                                  ░██                            
        ░██     ░██                                                                 ░██                            
        ░██     ░██  ░███████   ░███████   ░███████   ░██████   ░██░████  ░███████  ░████████   ░███████  ░██░████ 
        ░█████████  ░██    ░██ ░██        ░██    ░██       ░██  ░███     ░██    ░██ ░██    ░██ ░██    ░██ ░███     
        ░██   ░██   ░█████████  ░███████  ░█████████  ░███████  ░██      ░██        ░██    ░██ ░█████████ ░██      
        ░██    ░██  ░██               ░██ ░██        ░██   ░██  ░██      ░██    ░██ ░██    ░██ ░██        ░██      
        ░██     ░██  ░███████   ░███████   ░███████   ░█████░██ ░██       ░███████  ░██    ░██  ░███████  ░██      
                                                                                                                   
                                                                                                                   
                                                                                                                   
                        """)
        elif agent_key == "writer":
                  print(r"""
        ░██       ░██          ░██   ░██                        
        ░██       ░██                ░██                        
        ░██  ░██  ░██ ░██░████ ░██░████████  ░███████  ░██░████ 
        ░██ ░████ ░██ ░███     ░██   ░██    ░██    ░██ ░███     
        ░██░██ ░██░██ ░██      ░██   ░██    ░█████████ ░██      
        ░████   ░████ ░██      ░██   ░██    ░██        ░██      
        ░███     ░███ ░██      ░██    ░████  ░███████  ░██      
                                                                
                                                                
                                                                
                        """)
        continue

      # Memory pipeline runs on every message
      self._handleMemory(user_input)

      if self.currentAgent is None:
        print("No task agent selected yet. Type 'coder', 'researcher', or 'writer' first.")
        continue

      self.currentAgent.assignTask(self.userContext)
      self.currentAgent.execute()

def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()