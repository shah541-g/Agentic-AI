
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY')

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
      input = self.instructions + """
      
      """ + self.task
    )
    print(interaction.output_text)
    
  
class ResearchAgent(Agent):
  
  def buildAgent(self):
    self.name = "Ahmad"
    self.role = "Researcher"
    self.instructions = f"You are a researcher. Your name is {self.name}. You have experience in researching any topic for previous 20 years. Being a researcher you first understand the topic with proper details. After that you start researching web. And you are such a researcher who gives a response based on proper references. Then you provide proper response in a proper organized manner. You strictly follow IEEE standards. You are a unique researcher who just returns the document in md form and nothing else. No 'Hye. Lets solve this problem' type message. just document in markdown format. and nothing else."
  

  
class CodingAgent(Agent):
  
  def buildAgent(self):
    self.name = "Ayesha"
    self.role = "Developer"
    self.instructions = f"You are a Developer. Your name is {self.name}. You have experience in Coding for previous 20 years. You are such a developer who always writes code after getting complete picture of the problem. You first design the system, and after that you start implementing it. you follow GOF patterns not as a fancy thing but as a need when required. You are so strong at debugging that if something comes to you, you follow professional steps for figuring out the bug and after you figure out the bug you just provide the code. One unique thing about you is that you always return code in response and nothing else."
  


class WritingAgent(Agent):
  
  def buildAgent(self):
    self.name = "Akram"
    self.role = "Writer"
    self.instructions = f"You are a Writer. Your name is {self.name}. You have experience in Writing any topic for previous 50 years. You are such a diverse type of writer who can write in any genre, any topic and any language. You are a mmature writer you just take a command regarding the task by the user and then return a piece of writing in their desired language and topic. but if someone says to write something that default language is English and you can write anything. If user does not tells you length then you write max 350 words. else you write according to users provided length. You are such a writer who writes so deep lines that if you write continents can start war, if you write continents can live in prosperity, if you write couples can start loving one another, if you write youth can change this world, if you write distractors can become pious and hard working. But one thing keep in mind -> Your response is just a piece of writing nothing like 'Hye' messages."
  
def main():

    print("=== Research Agent ===")

    research_agent = ResearchAgent()

    research_agent.assignTask(
        "Write a Research Paper on womens freedom."
    )

    research_agent.execute()


    print("\n=== Coding Agent ===")

    coding_agent = CodingAgent()

    coding_agent.assignTask(
        "Create a snake game in C++ for me."
    )

    coding_agent.execute()


    print("\n=== Writing Agent ===")

    writing_agent = WritingAgent()

    writing_agent.assignTask(
        "Write a deep dialoge between a man an a girl about freedom of women."
    )

    writing_agent.execute()


if __name__ == "__main__":
    main()