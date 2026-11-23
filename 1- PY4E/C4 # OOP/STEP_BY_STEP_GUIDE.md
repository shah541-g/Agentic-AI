# Step-by-Step Guide: Building the OOP Agent Hierarchy 🛠️

> **Target File:** [`Deliverable/m0-d07-oop agent.py`](Deliverable/m0-d07-oop%20agent.py)  
> **Key Objective:** Build a clean, scalable Object-Oriented agent framework connecting to the Google Gemini API to orchestrate specialist autonomous agents.

---

## 🏗️ Step 1: Environment & Client Setup

### Prerequisites
Install the official Google GenAI SDK and dotenv:
```bash
pip install google-genai python-dotenv
```

Create a `.env` file containing your Gemini API key:
```env
API_KEY=your_gemini_api_key_here
```

Load credentials in Python:
```python
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError("API_KEY environment variable is missing. Check your .env file.")
```

---

## 🏗️ Step 2: Designing the `Agent` Base Class

The base class establishes the universal interface for all agents. It holds the client instance, configuration hook, task assigner, and execution method:

```python
class Agent:
    def __init__(self):
        self.buildAgent()
        self.client = genai.Client(api_key=API_KEY)
        self.task = ""

    def buildAgent(self):
        """Hook method overridden by subclasses to configure name, role, and system instructions."""
        self.name = "GenericAgent"
        self.role = "Assistant"
        self.instructions = "You are a helpful assistant."

    def assignTask(self, task: str):
        """Assigns the natural language goal to the agent."""
        self.task = task

    def execute(self) -> str:
        """Executes the task against the LLM, combining instructions and prompt."""
        if not self.task:
            raise ValueError(f"Agent {self.name} has no task assigned.")

        prompt = f"{self.instructions}\n\nTask: {self.task}"
        
        response = self.client.interactions.create(
            model="gemini-3.5-flash-lite",
            input=prompt
        )
        
        output = response.output_text
        print(f"\n[{self.role}: {self.name}]\n{output}")
        return output
```

---

## 🏗️ Step 3: Subclassing Specialist Agents

By overriding `buildAgent()`, each subclass injects specialized domain rules, constraints, and output formats.

### 1. The Research Specialist
```python
class ResearchAgent(Agent):
    def buildAgent(self):
        self.name = "Ahmad"
        self.role = "Researcher"
        self.instructions = (
            f"You are a Senior Academic Researcher named {self.name} with 20 years of experience. "
            "Formulate detailed, structured findings strictly adhering to IEEE style guidelines. "
            "Cite sources and provide evidence-based arguments. "
            "Output ONLY the markdown report. Do not include introductory pleasantries or greetings."
        )
```

### 2. The Developer Specialist
```python
class CodingAgent(Agent):
    def buildAgent(self):
        self.name = "Ayesha"
        self.role = "Developer"
        self.instructions = (
            f"You are a Principal Software Engineer named {self.name} with 20 years of coding experience. "
            "You apply clean architecture and Gang of Four (GoF) design patterns where appropriate. "
            "You write complete, bug-free, production-ready code with explanatory inline comments. "
            "Output ONLY runnable code blocks. Never include conversational chat."
        )
```

### 3. The Creative Writing Specialist
```python
class WritingAgent(Agent):
    def buildAgent(self):
        self.name = "Akram"
        self.role = "Writer"
        self.instructions = (
            f"You are a master essayist and dialogue writer named {self.name}. "
            "You adapt tone and cadence to evoke deep resonance and emotional depth. "
            "If the user specifies a length, obey it strictly; otherwise write a concise, powerful piece under 350 words. "
            "Output ONLY the narrative text. Do not include conversational preambles."
        )
```

---

## 🏗️ Step 4: Orchestration & Execution

In `main()`, instantiate the agents, assign them distinct tasks, and trigger `.execute()`:

```python
def main():
    print("=== 1. Invoking Research Agent ===")
    researcher = ResearchAgent()
    researcher.assignTask("Write an academic overview on the societal impacts of autonomous AI systems.")
    researcher.execute()

    print("\n=== 2. Invoking Coding Agent ===")
    coder = CodingAgent()
    coder.assignTask("Implement a classic Snake game in Python using pygame with scoring and collision detection.")
    coder.execute()

    print("\n=== 3. Invoking Writing Agent ===")
    writer = WritingAgent()
    writer.assignTask("Write a profound philosophical dialogue between a scientist and an artist on the definition of consciousness.")
    writer.execute()

if __name__ == "__main__":
    main()
```

---

## 💡 Key Architectural Insights for Future Multi-Agent Systems

1. **Prompt Injection Guarding:** Notice how `instructions` specify negative constraints (*"Do not include conversational greetings"*). Autonomous agents chained in multi-agent pipelines must produce pure outputs; otherwise conversational text (`"Sure! Here is the code..."`) will corrupt syntax checkers or downstream parsers.
2. **Template Method Pattern:** `__init__` calls `buildAgent()`. This is the classic GoF Template Method pattern, allowing subclasses to redefine specific configuration hooks without rewriting instantiation logic.
3. **Pluggable LLM Backends:** Because `self.client` lives inside `Agent`, you can easily subclass `Agent` to create an `AzureAgent`, an `OllamaAgent`, or a `ClaudeAgent` while keeping `assignTask` and `execute` consistent across all agents.
