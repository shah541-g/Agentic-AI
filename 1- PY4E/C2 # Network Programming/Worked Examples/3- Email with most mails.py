import urllib.request
import re

url = "http://data.pr4e.org/mbox-short.txt"
fhand = urllib.request.urlopen(url)

mailSendersFreqMap = dict()

startingFrom = 0
for line in fhand:
  words = line.decode().split()
  if re.match(r"^From",line.decode()):
    startingFrom+=1
  for word in words:
    if re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$',word):
      mailSendersFreqMap[word] = mailSendersFreqMap.get(word,0) + 1
      

sortedItems = sorted(mailSendersFreqMap.items(),key=lambda pair: pair[1], reverse=True)

for email, freq in sortedItems[:5]:
  print(f'{email}->{freq}')
  
uniqueEmailIds = set(sortedItems)
print("-------------------")
print("Unique Mail Ids")
print("-------------------")
print(uniqueEmailIds.__len__())
print("-------------------")
print("Starting from Count")
print("-------------------")
print(startingFrom)