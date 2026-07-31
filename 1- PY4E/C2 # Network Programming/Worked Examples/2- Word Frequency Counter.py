import urllib.request

url = 'http://data.pr4e.org/romeo.txt'
fhand = urllib.request.urlopen(url)

count = dict()
for line in fhand:
  words = line.decode().split()
  for word in words:
    count[word] = count.get(word,0) +1 

sortedCounts = sorted(count.items(), key=lambda pair: pair[1], reverse=True)

print("Top 5 words: ")
for word, count in sortedCounts[:5]:
  print(f'{word} -> {count}')