import re

class Email:
   def __init__(self,host:str,username:str):
     self.host = host
     self.username = username

class Score:
  def __init__(self,score:str):
    self.score=score

class CScore(Score):
  def __init__(self,score:str):
    super().__init__(score)
    self.type = "Confidence-Score"

class PScore(Score):
  def __init__(self,score:str):
    super().__init__(score)
    self.type = 'Probability-Score'  

class Person:
  def __init__(self,email:Email):
    self.mail = email
    
class DateDetails:
  def __init__(self,day,month,date,time,year):
    self.day = day
    self.month = month
    self.date = date
    self.time = time
    self.year = year
    
class PLog:
  def __init__(self,person:Person,dateDetails:DateDetails,scores = None):
    self.person = person
    self.dateDetails = dateDetails
    self.scores = scores if scores is not None else []
    
class PLogsList:
  def __init__(self):
    self.logs = []
  
  def create(self, log: PLog):
    self.logs.append(log)
  
  def readByPerson(self, username):
    filteredLogs = []
    for x in self.logs:
      if x.person.mail.username == username:
        filteredLogs.append(x)
    return filteredLogs
  
  def readAll(self):
    return [].extend(self.logs)
  
  def delete(self, username):
    filteredLogs = []
    for x in self.logs:
      if x.person.mail.username != username:
        filteredLogs.append(x)
    self.logs = filteredLogs
    return True
  
  def displayAll(self):
    for x in self.logs:
      print(f"""
            ============================================
                        Person Details
            ============================================
            Person Email Username: {x.person.mail.username},
            Person Email Host: {x.person.mail.host},
            
            ============================================
                        Date Details
            ============================================
            Day: {x.dateDetails.day},
            Month: {x.dateDetails.month},
            Date: {x.dateDetails.date},
            Time: {x.dateDetails.time},
            year: {x.dateDetails.year}
            
            ============================================
                        Scores Details
            ============================================
            Confidence Score: {x.scores[0].score},
            Probability Score: {x.scores[0].score}
            """)
  
  


with open("mini-box.txt",'r') as logsFile:
  content = logsFile.read()

logs : PLogsList = PLogsList()
gEmail = None
gDateDetails = None
gConfidence = None
gProbability = None
for line in content.splitlines():
  if re.search(r'^From', line):
    data = re.findall(r'^From\s+(\S+)@(\S+)\s+(\w+)\s+(\w+)\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})\s+(\d{4})', line)

    if data:
        username, host, day, month, date, time, year = data[0]

        gEmail = Email(host, username)
        gDateDetails = DateDetails(day, month, date, time, year)
  elif re.search('^X-DSPAM-Confidence: ', line):
    data = re.findall(r'^X-DSPAM-Confidence: (\d+\.?\d*)', line)
    gConfidence = CScore(data[0])
  elif re.search('^X-DSPAM-Probability: ', line):
    data = re.findall(r'^X-DSPAM-Probability: (\d+\.?\d*)', line)
    gProbability = PScore(data[0])
  else:
     if gEmail and gDateDetails and gConfidence and gProbability:
      person = Person(gEmail)
      log = PLog(person,gDateDetails,[gConfidence, gProbability])
      logs.create(log)
    
logs.displayAll()
    


    
    