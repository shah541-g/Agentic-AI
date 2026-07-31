import urllib.request

url = "https://www.gutenberg.org/files/100/100-0.txt"
fhand = urllib.request.urlopen(url)



freqMap = dict()
longestWord = ""
totalWordsLength = 0
charFreqMap = dict()
sentenceCount = 0


def updateCharFreq(word):
  for c in word:
    charFreqMap[c] = charFreqMap.get(c,0) + 1

totalWords = 0
for line in fhand:
  sentenceCount +=1 
  for word in line.decode().split():
    freqMap[word] = freqMap.get(word,0)+1
    totalWordsLength+=len(word)
    totalWords+=1
    updateCharFreq(word)
    if len(word) > len(longestWord):
      longestWord = word

sortedWordsList = sorted(freqMap.items(),key=lambda pair:pair[1], reverse=True)

avgWordLength = totalWordsLength/totalWords
print("---------------")
print("Top 20 Words")
print("---------------")
for word in sortedWordsList[:20]:
  print(word)
print("---------------")
print("Longest Word")
print("---------------")
print(longestWord)
print("---------------")
print("Average Word Length")
print("---------------")
print(avgWordLength)
print("---------------")
print("Sentence Count")
print("---------------")
print(sentenceCount)