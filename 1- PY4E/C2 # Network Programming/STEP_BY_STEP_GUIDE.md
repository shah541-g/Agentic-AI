# Step-by-Step Guide: Network Fetchers & HTML Link Scrapers 🛠️

> **Target Files:**
> - Day 3: [`Final Task/m0-d03-url-fetcher.py`](Final%20Task/m0-d03-url-fetcher.py)
> - Day 4: [`Final Task/m0-d04-link-extractor.py`](Final%20Task/m0-d04-link-extractor.py)
>
> **Key Objective:** Build reliable, production-ready network tools for autonomous agents to inspect HTTP communication and scrape web links cleanly.

---

## 🏗️ Project 1: Building `m0-d03-url-fetcher.py` (Day 3)

### Goal
Create a Python script that connects to any target website over HTTPS, extracts HTTP headers, decodes the body payload using UTF-8, and writes a structured diagnostic report to `output.txt`.

### Step 1: Open the Connection with Context Management
Always wrap network connections in `with` blocks to ensure sockets are closed even if an exception occurs:

```python
from urllib import request, error

url = "https://www.youtube.com/"

try:
    with request.urlopen(url) as response:
        # response.headers is an HTTPMessage object containing all response headers
        headers = response.headers
        # Read the raw byte content and decode to UTF-8
        body = response.read().decode("utf-8", errors="replace")
        status_code = response.status
except error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.reason}")
    headers = e.headers
    body = e.read().decode("utf-8", errors="replace")
except error.URLError as e:
    print(f"Failed to reach server: {e.reason}")
    exit(1)
```

### Step 2: Format and Persist Diagnostics
Write headers and body to an output file for analysis:

```python
with open("output.txt", "w", encoding="utf-8") as file:
    file.write(f"""
====================
    H E A D E R
====================
{headers}

====================
    B O D Y  (Preview)
====================
{body[:2000]}
""")

print(f"Successfully fetched {url} (Status: 200). Saved to output.txt")
```

---

## 🏗️ Project 2: Building `m0-d04-link-extractor.py` (Day 4)

### Goal
Fetch a live web page (`https://books.toscrape.com`) and parse its DOM structure with `BeautifulSoup4` to extract titles, relative URLs, and resolve them into absolute URLs.

### Step 1: Install BeautifulSoup
```bash
pip install beautifulsoup4
```

### Step 2: Fetch and Parse DOM Tree
```python
from urllib import request, parse
from bs4 import BeautifulSoup

target_url = "https://books.toscrape.com"

# Fetch page content
req = request.Request(
    target_url,
    headers={"User-Agent": "AgenticWebCrawler/1.0"}
)

with request.urlopen(req) as response:
    html_content = response.read().decode("utf-8")

# Parse with html.parser
soup = BeautifulSoup(html_content, "html.parser")
```

### Step 3: Extract Links with Robust Attribute Handling
In raw web scraping, elements may lack expected attributes. Never assume an attribute exists:

```python
links = soup.find_all("a")
extracted_items = []

for link in links:
    href = link.get("href")
    title = link.get("title")
    anchor_text = link.text.strip()
    
    if href:
        # Resolve relative URLs like "catalogue/page-1.html" to absolute URLs
        absolute_url = parse.urljoin(target_url, href)
        
        extracted_items.append({
            "title": title or anchor_text or "No Title",
            "url": absolute_url
        })

print(f"Extracted {len(extracted_items)} links from {target_url}:")
for item in extracted_items[:10]:
    print(f"- {item['title']}: {item['url']}")
```

---

## 💡 Agentic Engineering Takeaways

1. **User-Agent Spoofing:** Many production websites reject default `Python-urllib/3.x` requests with HTTP 403 Forbidden. Always configure a custom `User-Agent` header.
2. **`urljoin()` for Normalization:** Agents crawling external links frequently receive relative paths (`/about`, `../contact.html`). Using `urllib.parse.urljoin(base, relative)` ensures fully-qualified URIs.
3. **Graceful Error Handling:** In multi-step agent research, dead links (404) or server errors (500) must not crash the orchestrator. Catch `urllib.error.HTTPError` and `urllib.error.URLError` and return structured failure messages.
