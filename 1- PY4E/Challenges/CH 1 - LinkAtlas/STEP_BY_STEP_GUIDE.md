# LinkAtlas — Step-by-Step Beginner Guide & Notes 🕸️
> **Level:** Advanced Python  
> **Topic:** Recursive Web Crawling, Graph Data Structures (Nodes & Edges), Networking (`requests`, `robots.txt`), Breadth-First Search (BFS), Multi-format Serialization  
> **Goal:** Build a polite, depth-limited web crawler that maps website link architecture and exports it as a directed graph.

---

## 1. Why Build This? (The Real-World Motivation)

### The Real-World Scenario
Imagine you are an SEO specialist, web developer, or cybersecurity auditor responsible for a large website containing hundreds of pages.
Over time, web pages link out to dozens of external services, references, partner websites, and social media links.

As websites evolve:
1. **Link Rot:** External sites change URLs or expire, leaving dead 404 links on your website that hurt SEO rankings.
2. **Security & Supply-Chain Audits:** You need an accurate inventory of every third-party domain your site references or depends on.
3. **Broken Internal Pages:** Internal links get broken during redesigns, leading to 404 Not Found errors or server timeouts for your users.

You need an automated tool that:
- Recursively discovers and traverses internal pages (Crawling).
- Enforces a **strict depth cap (up to 2 levels)** so it doesn't wander indefinitely across the internet.
- **Never fetches external sites:** External links must only be recorded as graph nodes, never requested over the network.
- Exports a complete **Directed Graph** ready for analysis in NetworkX, Gephi, or Graphviz.

---

## 2. What Are We Building? (The Product Blueprint)

### Input, Processing, and Output

```
┌──────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│       Seed URL       │ ───► │    LinkAtlas Engine     │ ───► │      Directed Graph     │
│ (https://example.com)│      │(BFS, robots.txt, Delays)│      │(JSON, GraphML, DOT, CSV)│
└──────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

### CLI Command Examples:

```bash
# 1. Crawl a target website up to depth 2 with a polite 1.0s delay
linkatlas https://quotes.toscrape.com

# 2. Export the graph in multiple formats simultaneously (JSON, GraphML for Gephi, DOT for Graphviz)
linkatlas https://example.com --format json --format graphml --format dot

# 3. Export a clean CSV list of unique outbound external links
linkatlas https://example.com --csv outbound_links.csv

# 4. Set custom crawl delay and maximum page limit
linkatlas https://example.com --delay 2.0 --max-pages 100
```

---

## 3. Core Concepts to Understand First

### Concept 1: Web Scraper vs Web Crawler
- **Scraper:** Given a single page URL, it extracts specific content (such as product prices or tables) from that one page.
- **Crawler (Spider):** Given a starting seed URL, it fetches the page, discovers all links within it, and recursively queues those newly found links to crawl subsequent pages.

### Concept 2: Breadth-First Search (BFS) Traversal
A crawler can explore pages in two ways:
- **DFS (Depth-First Search):** Follows link 1 to its end, then link 2 to its end. In web crawling, DFS easily gets lost down infinite URL paths.
- **BFS (Breadth-First Search) — Our Strategy:**
  First, it fetches all direct links found on the Seed page (Depth 1).
  Next, it fetches all links found on Depth 1 pages (Depth 2).
  At Depth 2, internal links are recorded in the graph but **never requested**.

We implement BFS using a First-In, First-Out (FIFO) queue with `collections.deque`:
```python
from collections import deque

queue = deque([(seed_url, 0)])  # Stores (url, depth)
seen = {seed_url}

while queue:
    url, depth = queue.popleft()  # First In, First Out!
    result = fetcher.fetch(url)
    
    for next_url in extract_links(result.content):
        if is_internal(next_url) and next_url not in seen:
            seen.add(next_url)
            if depth < max_depth:
                queue.append((next_url, depth + 1))
```

### Concept 3: Politeness and `robots.txt`
A professional crawler must practice web citizenship:
1. **Always obey `robots.txt`:** Before making any page request, `<origin>/robots.txt` is fetched and parsed. If the target URL is disallowed, **no HTTP request is ever made**.
2. **Per-host crawl delay:** Sending 100 requests per second can overwhelm target servers. We enforce an inter-request delay (default 1.0s, or the site's `Crawl-delay`).
3. **Never fetch external sites:** External links are recorded as targets in the graph, but LinkAtlas never sends HTTP requests to external domains.

### Concept 4: Directed Graphs (Nodes & Edges)
- **Node:** Represents an individual unique URL.
  - Page Node: An internal page on the seed domain (`type="page"`, `status=200`, `depth=1`).
  - External Node: An external domain or link (`type="external"`, `domain="github.com"`).
- **Edge:** Represents a directed link from a source page to a target page:
  - Attributes: `source`, `target`, `kind` (`internal`, `external`, `redirect`), `count`, and `text` (anchor text).

---

## 4. File Structure (Architecture Blueprint)

```
linkatlas/
├── linkatlas/
│   ├── __init__.py      # Package version metadata
│   ├── __main__.py      # Enables execution via: python -m linkatlas
│   ├── models.py        # CrawlConfig, FetchResult, ExtractResult, RawLink
│   ├── urls.py          # normalize_url, is_internal, skippable_extensions, query strippers
│   ├── robots.py        # RobotsCache & RobotsPolicy per origin
│   ├── fetcher.py       # Polite HTTP fetcher (robots check, delay, retries, 429 Retry-After)
│   ├── extractor.py     # BeautifulSoup HTML link parser (<base href>, nofollow, title)
│   ├── graph.py         # Graph data structure (nodes, edges, summary stats, problem reports)
│   ├── crawler.py       # BFS crawl engine
│   ├── exporters.py     # JSON, GraphML (Gephi), DOT (Graphviz), CSV writers
│   ├── display.py       # Rich real-time progress lines & summary tables
│   └── cli.py           # Command-line interface and exit codes (0/1/2/130)
├── tests/
│   ├── conftest.py      # Local multi-threaded HTTP test server fixture
│   └── test_*.py        # 85 comprehensive pytest tests
├── pyproject.toml       # Build configuration
└── README.md            # Technical documentation
```

---

## 5. Step-by-Step Implementation Guide

### Step 1: URL Normalization (`urls.py`)
To prevent infinite crawl loops and duplicate nodes, every URL is normalized:

```python
from urllib.parse import urlparse, urlunparse, urljoin, parse_qsl, urlencode

def normalize_url(url: str, base: str | None = None) -> str | None:
    if base:
        url = urljoin(base, url)
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        return None
        
    host = (parsed.hostname or "").lower()
    # Strip default ports (:80 for http, :443 for https)
    port = parsed.port
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        port = None
    netloc = host if port is None else f"{host}:{port}"
    
    path = parsed.path or "/"
    
    # Strip tracking parameters (utm_*, fbclid, etc.)
    params = [(k, v) for k, v in parse_qsl(parsed.query) if not k.startswith("utm_") and k != "fbclid"]
    query = urlencode(params)
    
    # Strip fragment (#section)
    return urlunparse((scheme, netloc, path, "", query, ""))
```

---

### Step 2: Robots.txt Policy Caching (`robots.py`)

```python
from urllib.robotparser import RobotFileParser
import requests

class RobotsCache:
    def __init__(self, session, user_agent="LinkAtlas/0.1"):
        self.session = session
        self.user_agent = user_agent
        self.cache = {}

    def policy_for(self, url: str):
        origin = get_origin(url) # e.g. "https://example.com"
        if origin in self.cache:
            return self.cache[origin]
            
        resp = self.session.get(f"{origin}/robots.txt", timeout=10)
        rfp = RobotFileParser()
        if resp.status_code == 200:
            rfp.parse(resp.text.splitlines())
            policy = RobotsPolicy("ok", rfp=rfp)
        elif resp.status_code in (401, 403):
            policy = RobotsPolicy("forbidden") # Block all
        else:
            policy = RobotsPolicy("missing")   # Allow all
            
        self.cache[origin] = policy
        return policy
```

---

### Step 3: Polite HTTP Fetcher (`fetcher.py`)

```python
class Fetcher:
    def fetch(self, url: str) -> FetchResult:
        # 1. Check robots.txt
        policy = self.robots.policy_for(url)
        if not policy.allowed(url):
            return FetchResult(url=url, state="robots_disallowed")

        # 2. Enforce inter-request politeness delay
        host = urlparse(url).hostname
        self.enforce_delay(host)

        # 3. HTTP GET (allow_redirects=False to track redirect edges explicitly)
        resp = self.session.get(url, allow_redirects=False, timeout=10)
        
        # 4. Handle redirects
        if resp.status_code in (301, 302, 307, 308):
            return FetchResult(url=url, state="redirect", redirect_to=resp.headers.get("Location"))
            
        # 5. Content-Type check
        if "text/html" not in resp.headers.get("Content-Type", ""):
            return FetchResult(url=url, state="non_html")
            
        return FetchResult(url=url, state="ok", content=resp.content, status=resp.status_code)
```

---

### Step 4: BFS Traversal Loop (`crawler.py`)

```python
class Crawler:
    def run(self):
        queue = deque([(self.seed, 0)])
        seen = {self.seed}
        
        while queue and pages_requested < self.max_pages:
            url, depth = queue.popleft()
            result = self.fetcher.fetch(url)
            
            if result.state == "redirect":
                # Add redirect edge to target
                continue
                
            if result.state != "ok":
                continue
                
            # Extract links with BeautifulSoup
            page = extract_links(result.content, url)
            
            for link in page.links:
                if is_internal(link.url, self.seed):
                    if link.url not in seen:
                        seen.add(link.url)
                        if depth < self.max_depth and not link.nofollow:
                            queue.append((link.url, depth + 1))
                    self.graph.add_edge(url, link.url, kind="internal")
                else:
                    self.graph.add_external(link.url)
                    self.graph.add_edge(url, link.url, kind="external")
```

---

## 6. Graph Analysis with NetworkX

After crawling, inspect the generated graph file (`linkatlas-quotes.toscrape.com.json`) with NetworkX:

```python
import json
import networkx as nx

with open("linkatlas-quotes.toscrape.com.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Load into NetworkX
G = nx.node_link_graph(data, edges="edges")

# Total external links
externals = [n for n, d in G.nodes(data=True) if d.get("type") == "external"]
print(f"Total unique external URLs: {len(externals)}")

# Top 5 most-referenced external URLs
for url, in_degree in sorted(G.in_degree(externals), key=lambda x: x[1], reverse=True)[:5]:
    print(f"Referenced {in_degree} times: {url}")
```

---

## 7. Key Takeaways for Beginners

1. **BFS controls crawl scope:** Use a queue to explore level-by-level so your crawler respects depth boundaries.
2. **Web Politeness is essential:** Always respect `robots.txt`, maintain request delays, and never request external domains.
3. **Directed Graphs model the web:** Modeling pages as nodes and links as edges makes graph algorithms, visualization, and link auditing straightforward.
