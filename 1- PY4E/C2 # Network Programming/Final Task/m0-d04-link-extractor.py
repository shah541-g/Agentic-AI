from urllib import request
from bs4 import BeautifulSoup
response = request.urlopen("https://books.toscrape.com")
header = response.headers
body = response.read().decode()
soup = BeautifulSoup(body,'html.parser')
links = soup.find_all('a')
for link in links:
  if link.get('title') is not None:
    print(link.get('title'))