# Chapter 12: Networked Programs — Notes

## 1. Overview

- Until now we mostly read local files. In this chapter we **pretend to be a web browser**: retrieve web pages using **HTTP** and then parse the data.
- Tools covered, from low level to high level: `socket` → `urllib` → regex / `BeautifulSoup` for parsing.

---

## 2. HTTP and Sockets

### Socket

- A **socket** is like a file, but it is a **two-way connection** between two programs. You can both read from it and write to it.
- Write → data is sent to the other application. Read → you receive what the other side sent.
- If you read when the other side hasn't sent anything, your program just **waits**. If both sides wait, they wait forever, which is why a **protocol** is needed.

### Protocol

- A **protocol** is a set of precise rules: who goes first, what they do, how the other side responds, who sends next, and so on. Think of it as a dance where neither side steps on the other's toes.
- HTTP is defined in RFC 2616 (176 pages). The `GET` syntax is around page 36.

### The GET Request

1. Connect to the server (for example `data.pr4e.org`) on **port 80**.
2. Send a line like this, followed by a **blank line**:

```
GET http://data.pr4e.org/romeo.txt HTTP/1.0
```

3. The server replies with **headers**, then a **blank line**, then the **document content**.

---

## 3. The World's Simplest Web Browser

```python
import socket

mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
mysock.connect(('data.pr4e.org', 80))
cmd = 'GET http://data.pr4e.org/romeo.txt HTTP/1.0\r\n\r\n'.encode()
mysock.send(cmd)

while True:
    data = mysock.recv(512)
    if len(data) < 1:
        break
    print(data.decode(), end='')

mysock.close()
```

**How it works**

- `\r\n` is an end-of-line (EOL). `\r\n\r\n` means two EOLs with nothing between them, which is the **blank line** HTTP requires after the request.
- `recv(512)` receives up to 512 characters at a time. When it returns an **empty** value, the server has closed the connection and the loop ends.

**Sample output structure**

```
HTTP/1.1 200 OK
Date: ...
Server: Apache/2.4.7 (Ubuntu)
Content-Length: 167
Content-Type: text/plain
(blank line)
But soft what light through yonder window breaks
...
```

- Headers describe the document. `Content-Type: text/plain` tells us it is plain text.
- A blank line marks the **end of the headers**, and the actual file content follows.
- Sockets can talk to web servers, mail servers, and many other kinds of servers. You just need the protocol documentation.

### Bytes vs. Strings

- HTTP data is sent and received as **bytes objects**, not strings.
- `encode()` converts string → bytes. `decode()` converts bytes → string.
- `b'...'` notation is equivalent to `.encode()`:

```python
>>> b'Hello world'
b'Hello world'
>>> 'Hello world'.encode()
b'Hello world'
```

---

## 4. Retrieving an Image over HTTP (with sockets)

Idea: accumulate all the data, **trim the headers**, and save the rest as a file.

```python
import socket
import time

HOST = 'data.pr4e.org'
PORT = 80
mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
mysock.connect((HOST, PORT))
mysock.sendall(b'GET http://data.pr4e.org/cover3.jpg HTTP/1.0\r\n\r\n')
count = 0
picture = b""

while True:
    data = mysock.recv(5120)
    if len(data) < 1: break
    #time.sleep(0.25)
    count = count + len(data)
    print(len(data), count)
    picture = picture + data

mysock.close()

# Look for the end of the header (2 CRLF)
pos = picture.find(b"\r\n\r\n")
print('Header length', pos)
print(picture[:pos].decode())

# Skip past the header and save the picture data
picture = picture[pos+4:]
fhand = open("stuff.jpg", "wb")
fhand.write(picture)
fhand.close()
```

**Key points**

- `Content-Type: image/jpeg` in the headers tells us the body is an image.
- The header ends at the first `\r\n\r\n`. We skip `pos + 4` bytes to get to the image data.
- `"wb"` opens a file for **writing binary** data.
- Each `recv()` returns **only what has arrived so far**, not necessarily the full 5120. Results depend on network speed.
- The last `recv()` returns the remaining bytes, and the next one returns an empty value, meaning the server closed the socket.

### Flow Control

- Uncommenting `time.sleep(0.25)` slows down our `recv()` calls so the server can "get ahead", and then we get full 5120-byte chunks (except the first and last).
- There is a **buffer** between the server's `send()` and our `recv()`. If the buffer fills, the server pauses until we start emptying it. This pausing of the sender or receiver is called **flow control**.

---

## 5. Retrieving Web Pages with `urllib`

- `urllib` handles all the HTTP details and headers. You treat a web page **like a file**.

```python
import urllib.request

fhand = urllib.request.urlopen('http://data.pr4e.org/romeo.txt')
for line in fhand:
    print(line.decode().strip())
```

- Headers are still sent, but `urllib` consumes them and gives you only the **data**.

### Example: Word Frequency from a Web Page

```python
import urllib.request, urllib.parse, urllib.error

fhand = urllib.request.urlopen('http://data.pr4e.org/romeo.txt')

counts = dict()
for line in fhand:
    words = line.decode().split()
    for word in words:
        counts[word] = counts.get(word, 0) + 1
print(counts)
```

---

## 6. Reading Binary Files with `urllib`

### Simple Version (reads everything into memory)

```python
import urllib.request, urllib.parse, urllib.error

img = urllib.request.urlopen('http://data.pr4e.org/cover3.jpg').read()
fhand = open('cover3.jpg', 'wb')
fhand.write(img)
fhand.close()
```

- `read()` downloads the whole file into the variable `img` in memory.
- Works only if the file is smaller than your available memory. Large audio or video files may crash the program or make it extremely slow.

### Better Version (in blocks / buffers)

```python
import urllib.request, urllib.parse, urllib.error

img = urllib.request.urlopen('http://data.pr4e.org/cover3.jpg')
fhand = open('cover3.jpg', 'wb')
size = 0
while True:
    info = img.read(100000)
    if len(info) < 1: break
    size = size + len(info)
    fhand.write(info)

print(size, 'characters copied.')
fhand.close()
```

- Reads **100,000 bytes at a time** and writes each block to disk before fetching the next one, so it can handle any file size.
- Output: `230210 characters copied.`

---

## 7. Web Scraping and Parsing HTML

- **Web scraping**: a program pretends to be a browser, retrieves pages, and examines the data in them for patterns.
- Search engines like Google fetch a page, extract its links, fetch those pages, and so on. This is called **spidering**.
- Google also uses how often other pages link to a page as one measure of how "important" it is.

### 7.1 Parsing HTML with Regular Expressions

Sample HTML:

```html
<h1>The First Page</h1>
<p>
If you like, you can switch to the
<a href="http://www.dr-chuck.com/page2.htm">
Second Page</a>.
</p>
```

Regex to find links:

```
href="http[s]?://.+?"
```

- `http[s]?` means `http` followed by **zero or one** `s`.
- `.+?` is a **non-greedy** match, so it finds the smallest possible string up to the next closing quote.
- Add parentheses `( )` to extract only the link itself.

```python
import urllib.request, urllib.parse, urllib.error
import re
import ssl

# Ignore SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = input('Enter - ')
html = urllib.request.urlopen(url, context=ctx).read()
links = re.findall(b'href="(http[s]?://.*?)"', html)
for link in links:
    print(link.decode())
```

**Notes**

- The `ssl` module lets the program access sites that strictly enforce HTTPS.
- `read()` returns the HTML as a **bytes object**, so the regex is written as `b'...'` and each link is `decode()`d.
- Regex works well only when the HTML is **well formatted and predictable**. Broken HTML can cause missed links or bad data.

### 7.2 Parsing HTML with BeautifulSoup

- Most HTML is "broken" in ways that make an XML parser reject the whole page.
- **BeautifulSoup** tolerates highly flawed HTML and still lets you extract the data you need.
- Install it with: `pip install beautifulsoup4`

```python
import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup
import ssl

# Ignore SSL/TLS certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = input('Enter - ')
html = urllib.request.urlopen(url, context=ctx).read()
soup = BeautifulSoup(html, 'html.parser')

# Retrieve all of the anchor tags
tags = soup('a')
for tag in tags:
    print(tag.get('href', None))
```

**Flow**: ask for a URL → open the page → read the data → pass it to BeautifulSoup → get all anchor (`a`) tags → print each `href`.

- The list is longer than the regex version because it includes **relative paths** (`tutorial/index.html`) and **in-page references** (`#`), which have no `http://` or `https://`.
- `html.parser` is the HTML parser included in Python 3's standard library.

### Extracting Different Parts of a Tag

```python
from urllib.request import urlopen
from bs4 import BeautifulSoup
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = input('Enter - ')
html = urlopen(url, context=ctx).read()
soup = BeautifulSoup(html, "html.parser")

tags = soup('a')
for tag in tags:
    print('TAG:', tag)
    print('URL:', tag.get('href', None))
    print('Contents:', tag.contents[0])
    print('Attrs:', tag.attrs)
```

| Expression | Gives you |
|------------|-----------|
| `tag` | the whole tag |
| `tag.get('href', None)` | value of the `href` attribute (or `None`) |
| `tag.contents[0]` | the text inside the tag |
| `tag.attrs` | all attributes of the tag |

---

## 8. Regex vs. BeautifulSoup

| | Regular Expressions | BeautifulSoup |
|---|---|---|
| Best for | clean, predictable HTML | real-world, messy HTML |
| Handles broken HTML | poorly | well |
| Returns | matched strings | tag objects with attributes and contents |

---

## 9. Bonus: Unix/Linux/Mac Commands

- `curl` stands for "copy URL". It downloads files over HTTP or FTP.
- `wget` works in a very similar way.

```bash
$ curl -O http://data.pr4e.org/cover3.jpg
$ wget http://data.pr4e.org/cover3.jpg
```

---

## 10. Glossary

- **BeautifulSoup**: a Python library for parsing HTML and extracting data. It compensates for the imperfections in HTML that browsers generally ignore.
- **Port**: a number that generally indicates which application you are contacting on a server. Web traffic usually uses **port 80**, email uses **port 25**.
- **Scrape**: when a program pretends to be a browser, retrieves a page, and examines its content, often following links to the next page.
- **Socket**: a network connection between two applications where data can be sent and received in both directions.
- **Spider**: a search engine retrieving a page and then all the pages linked from it, and so on, to build a search index.

---

## 11. Exercises

1. **Socket + URL input**: change `socket1.py` to prompt the user for a URL so it can read any web page. Use `split('/')` to extract the hostname, and add `try`/`except` for badly formatted or non-existent URLs.
2. **Count characters (socket)**: count the characters received and stop **displaying** text after 3000 characters. Still retrieve the whole document and print the total character count at the end.
3. **Same as Exercise 2, with `urllib`**: retrieve the document, display up to 3000 characters, and count the total characters. Ignore headers.
4. **Count `<p>` tags**: change `urllinks.py` to count paragraph (`p`) tags and print only the count. Test on small and large pages.
5. **(Advanced) Skip headers**: change the socket program so it only shows data **after the headers and the blank line** have been received. Remember that `recv` receives characters (newlines and all), not lines.

---

## Quick Recap

1. A **socket** is a two-way connection, and a **protocol** (here HTTP) defines the rules of the conversation.
2. An HTTP request is `GET <url> HTTP/1.0` + a blank line (`\r\n\r\n`). The response is headers + blank line + body.
3. Sockets send and receive **bytes**: use `encode()` / `decode()`.
4. `urllib.request.urlopen()` hides the HTTP details and lets you treat a URL like a file.
5. For big binary files, read and write in **blocks** instead of using one big `read()`.
6. Use regex for simple, clean HTML and **BeautifulSoup** for messy real-world HTML.

*Source: Python for Everybody, Chapter 12 — Charles R. Severance, CC BY 4.0*
