import urllib.request

url = "https://people.sc.fsu.edu/~jburkardt/data/csv/airtravel.csv"

fhand = urllib.request.urlopen(url)

for line in fhand:
  decodedLine = line.decode()
  