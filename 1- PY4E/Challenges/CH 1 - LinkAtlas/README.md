# LinkAtlas

> A polite, depth-limited recursive web crawler that maps a website's link architecture up to **2 levels deep**, discovers all **unique external links**, and exports the resulting structure as a **directed graph** (JSON node-link, GraphML, DOT, CSV).

---

## Table of Contents

1. [Overview & Problem](#overview--problem)
2. [Politeness Policy (Non-Negotiable)](#politeness-policy-non-negotiable)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [CLI Reference](#cli-reference)
6. [How It Works](#how-it-works)
   - [Scope & Internal vs External](#scope--internal-vs-external)
   - [Depth Rules & Breadth-First Traversal](#depth-rules--breadth-first-traversal)
   - [URL Normalisation](#url-normalisation)
   - [Robots.txt & Crawl-Delay Policy](#robotstxt--crawl-delay-policy)
   - [Skipped Extensions & Ignored Schemes](#skipped-extensions--ignored-schemes)
7. [Graph Data Model & Exporters](#graph-data-model--exporters)
   - [JSON Node-Link Format (NetworkX / D3)](#json-node-link-format-networkx--d3)
   - [GraphML (Gephi / yEd)](#graphml-gephi--yed)
   - [Graphviz DOT](#graphviz-dot)
   - [CSV Link Export](#csv-link-export)
8. [Real Crawl Example (`quotes.toscrape.com`)](#real-crawl-example-quotestoscrapecom)
9. [Graph Analysis in Python](#graph-analysis-in-python)
10. [Error & State Handling](#error--state-handling)
11. [Running Tests](#running-tests)
12. [Project Structure](#project-structure)

---

## Overview & Problem

Modern websites reference dozens of third-party domains — analytics, CDNs, social widgets, ad networks, and external references. Over time, outbound links rot and external dependencies multiply without tracking.

**LinkAtlas** answers three key questions:
1. *Which external domains and URLs does my website link to?*
2. *From which specific pages are those external links referenced?*
3. *Are any of my internal pages broken (404s, timeouts, server errors)?*

---

## Politeness Policy (Non-Negotiable)

LinkAtlas is designed from the ground up to be a responsible citizen of the web:

1. **Strictly obeys `robots.txt`:** Checked for every origin before any page request. There is **no flag or setting to bypass robots.txt**.
2. **Clear self-identification:** Sends an explicit `User-Agent` (`LinkAtlas/0.1 (+https://github.com/your-username/linkatlas)`).
3. **One request at a time:** Entirely synchronous (no concurrent scraping) with a default 1.0s delay between requests to the same host, or the host's `Crawl-delay` if larger (capped at 10s).
4. **Never requests external URLs:** External URLs are recorded as graph nodes and outbound edges, but **never fetched**.
5. **Honours `rel="nofollow"`, meta robots, and headers:** Links with `rel="nofollow"`, `<meta name="robots" content="nofollow">`, or `X-Robots-Tag: nofollow` are recorded as nodes but never followed.
6. **Honours `Retry-After`:** On HTTP 429 (Too Many Requests) or 503, respects `Retry-After` up to 10 seconds. If greater than 10 seconds, it gives up on that page instead of hammering the server.
7. **Safety limits:** Hard depth cap of 2, body size cap of 2 MB, request timeouts, and skippable binary extensions.

---

## Installation

**Prerequisites:** Python 3.10+

```powershell
# Navigate to the project directory
cd "D:\Notes\Personal\Agentic-AI\1- PY4E\Challenges\CH 1 - LinkAtlas"

# Install in editable mode
pip install -e .

# Verify installation
linkatlas --version    # prints: linkatlas 0.1.0
```

---

## Quick Start

```powershell
# Crawl a site up to depth 2 with a polite 1.0s delay
linkatlas https://quotes.toscrape.com

# Crawl depth 1 with custom delay and page limit
linkatlas example.com --depth 1 --delay 2 --max-pages 50

# Export multiple formats (JSON, GraphML for Gephi, DOT for Graphviz)
linkatlas https://example.com --format json --format graphml --format dot

# Export a clean CSV list of unique outbound external links
linkatlas https://example.com --csv outbound.csv

# Include subdomains (e.g., blog.example.com considered internal)
linkatlas https://example.com --include-subdomains
```

---

## CLI Reference

```
linkatlas URL [--depth {0,1,2}] [--max-pages N] [--delay SECONDS]
              [--timeout SECONDS] [--retries N] [--max-bytes N]
              [--include-subdomains] [--user-agent TEXT]
              [--out PATH] [--format {json,graphml,dot}] [--csv PATH]
              [--quiet] [--version]
```

| Argument / Flag | Default | Description |
|---|---|---|
| `url` | *required* | Target seed URL (scheme optional, defaults to `https://`). |
| `--depth N` | `2` | Maximum crawl depth. Only `0`, `1`, or `2` permitted. |
| `--max-pages N` | `200` | Maximum page requests allowed before stopping gracefully. |
| `--delay SECONDS` | `1.0` | Politeness sleep between requests to the same host. |
| `--timeout SECONDS`| `10.0` | Connection & read timeout per request. |
| `--retries N` | `1` | Retries on 5xx or network errors (0 to 3). |
| `--max-bytes N` | `2000000` | Maximum response body size (2 MB limit). |
| `--include-subdomains` | off | Treats subdomains of the seed host as internal. |
| `--user-agent TEXT` | LinkAtlas | Custom User-Agent string. |
| `--out PATH` | `linkatlas-<host>.json` | Base output file path. Other formats reuse the stem. |
| `--format {json,graphml,dot}` | `json` | Output graph format (repeatable). |
| `--csv PATH` | off | Export unique external URLs to CSV. |
| `--quiet` | off | Suppress real-time per-page output. |
| `--version` | | Show program version and exit. |

---

## How It Works

### Scope & Internal vs External

- **Seed:** Starting URL. Scheme defaults to `https://` if omitted.
- **Site Key:** Hostname lowercased with leading `www.` stripped (`www.Example.com` $\to$ `example.com`).
- **Internal URL:** A URL whose site key matches the seed's site key. With `--include-subdomains`, subdomains like `blog.example.com` are also considered internal.
- **External URL:** Any other HTTP/HTTPS URL. Recorded in the graph, but **never fetched**.
- **Non-HTTP Schemes:** `mailto:`, `tel:`, `javascript:`, `data:`, `ftp:` are ignored and counted under `summary.ignored_links`.

### Depth Rules & Breadth-First Traversal

```
Seed (depth 0)
 │
 ├── Internal page (depth 1) ──────► Fetched
 │    ├── Internal page (depth 2) ─► Fetched
 │    │    └── Internal page (depth 3) ─► Recorded as "not_crawled" (NOT fetched)
 │    └── External URL ────────────► Recorded as external node (NOT fetched)
 └── External URL ─────────────────► Recorded as external node (NOT fetched)
```

- **Depth 0:** Seed URL.
- **Depth 1:** Links discovered on depth-0 pages.
- **Depth 2:** Links discovered on depth-1 pages.
- **Depth 3:** Internal links discovered on depth-2 pages are added to the graph with state `not_crawled` and **never fetched**.
- **Redirects:** HTTP redirects (301, 302, 303, 307, 308) **do not consume depth**. The target is queued at the same depth as the source.

### URL Normalisation

Every URL undergoes standardisation via `linkatlas.urls.normalize_url`:
1. Resolves relative paths using `<base href>` (if present) or the current page URL.
2. Rejects non-HTTP(S) schemes and URLs longer than 2,000 characters.
3. Lowercases scheme and hostname; drops default ports (`:80` for http, `:443` for https).
4. Strips fragment anchors (`#section`).
5. Converts empty path to `/`.
6. Strips tracking query parameters (`utm_*`, `fbclid`, `gclid`, `msclkid`, `mc_cid`, `mc_eid`) while preserving all application query parameters in their original order.

### Robots.txt & Crawl-Delay Policy

Before any origin is requested, `<origin>/robots.txt` is fetched and cached:
- **Status 200:** Parsed with `RobotFileParser`. Rules matching `LinkAtlas` take precedence, falling back to `*`.
- **Status 404 / 4xx:** Allows all pages (state `missing`).
- **Status 401 / 403:** Disallows all pages (state `forbidden`).
- **Status 5xx / Timeout:** Retried once. If still failing, disallows all pages conservatively (state `unreachable`).
- **Crawl-delay:** Effective delay = $\min(10, \max(\text{delay}, \text{robots\_crawl\_delay}))$.
- If the seed URL itself is disallowed by robots.txt, LinkAtlas halts with exit code 1.

### Skipped Extensions & Ignored Schemes

Internal links matching skippable static/binary file extensions are never requested:
`.pdf`, `.jpg`, `.jpeg`, `.png`, `.gif`, `.svg`, `.webp`, `.ico`, `.bmp`, `.zip`, `.gz`, `.tar`, `.rar`, `.7z`, `.mp3`, `.mp4`, `.avi`, `.mov`, `.wmv`, `.css`, `.js`, `.json`, `.xml`, `.woff`, `.woff2`, `.ttf`, `.exe`, `.dmg`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`

These are marked as `skipped_extension` in the graph.

---

## Graph Data Model & Exporters

The link graph is directed and deterministic:
- **Page Nodes:** Contain `id` (normalized URL), `depth`, `state`, `status` (HTTP code), `title`, and `redirect_to`.
- **External Nodes:** Contain `id` (normalized URL) and `domain` (normalized hostname).
- **Edges:** Directed connections with `source`, `target`, `kind` (`internal`, `external`, `redirect`), `count` (occurrences), `text` (first anchor text), and `nofollow` (boolean AND of all occurrences).

### JSON Node-Link Format (NetworkX / D3)

Directly compatible with NetworkX:

```json
{
  "directed": true,
  "multigraph": false,
  "meta": {
    "tool": "linkatlas",
    "version": "0.1.0",
    "seed": "https://example.com/",
    "started_at": "2026-11-17T10:00:00Z",
    "finished_at": "2026-11-17T10:01:12Z",
    "options": { ... },
    "robots": { "https://example.com": "ok" },
    "truncated": false,
    "interrupted": false
  },
  "nodes": [
    { "id": "https://example.com/", "type": "page", "depth": 0, "state": "ok", "status": 200, "title": "Home" },
    { "id": "https://external.org/page", "type": "external", "domain": "external.org" }
  ],
  "edges": [
    { "source": "https://example.com/", "target": "https://external.org/page", "kind": "external", "count": 1, "text": "Partner", "nofollow": false }
  ],
  "summary": { ... }
}
```

### GraphML (Gephi / yEd)

Exported with declared typed XML keys (`d_depth`, `d_state`, `d_status`, `d_title`, `e_kind`, `e_nofollow`), compatible with Gephi, yEd, and Cytoscape.

### Graphviz DOT

Renderable directly with Graphviz:

```powershell
# Generate SVG visualization
dot -Tsvg linkatlas-example.com.dot -o graph.svg
```

### CSV Link Export

Header: `external_url,domain,linked_from_count,first_found_on`

---

## Real Crawl Example (`quotes.toscrape.com`)

Running LinkAtlas on `https://quotes.toscrape.com`:

```powershell
linkatlas https://quotes.toscrape.com --depth 1 --delay 1.0 --max-pages 5
```

### Live Terminal Output:

```
[d0] 200 https://quotes.toscrape.com/
[d1] 200 https://quotes.toscrape.com/login
[d1] 308 redirect https://quotes.toscrape.com/author/Albert-Einstein -> http://quotes.toscrape.com/author/Albert-Einstein/
[d1] 200 https://quotes.toscrape.com/tag/change/page/1/
[d1] 200 https://quotes.toscrape.com/tag/deep-thoughts/page/1/

                     LinkAtlas Crawl Summary                      
┌──────────────────────────┬─────────────────────────────────────┐
│ Metric                   │                               Value │
├──────────────────────────┼─────────────────────────────────────┤
│ Seed URL                 │        https://quotes.toscrape.com/ │
│ Pages Requested          │                                   5 │
│ Pages OK                 │                                   4 │
│ Page States              │ ok: 4, redirect: 1, not_crawled: 43 │
│ Unique External URLs     │                                   2 │
│ Unique External Domains  │                                   2 │
│ Ignored Links (non-http) │                                   0 │
│ Elapsed Time             │                               4.27s │
│ Notice                   │           Truncated (hit max pages) │
└──────────────────────────┴─────────────────────────────────────┘

               Top External Domains                
┌───────────────┬─────────────┬───────────────────┐
│ Domain        │ Unique URLs │ Linked From Pages │
├───────────────┼─────────────┼───────────────────┤
│ goodreads.com │           1 │                 4 │
│ zyte.com      │           1 │                 4 │
└───────────────┴─────────────┴───────────────────┘

Files written:
  • linkatlas-quotes.toscrape.com.json
```

---

## Graph Analysis in Python

Once a crawl is complete, analyze the graph with NetworkX:

```python
import json
import networkx as nx

# 1. Load graph data
with open("linkatlas-quotes.toscrape.com.json", "r", encoding="utf-8") as f:
    data = json.load(f)

G = nx.node_link_graph(data, edges="edges")

# 2. Extract external nodes
external_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "external"]
print(f"Total unique external URLs: {len(external_nodes)}")

# 3. Find most linked external domains
in_degrees = sorted(G.in_degree(external_nodes), key=lambda x: x[1], reverse=True)
print("\nTop referenced external URLs:")
for url, count in in_degrees[:5]:
    print(f"  {count} links -> {url}")
```

---

## Error & State Handling

Every page node is tagged with a deterministic state:

| State | Condition | Retried? |
|---|---|---|
| `ok` | HTTP 2xx, HTML content type, body parsed successfully | No |
| `redirect` | 301/302/303/307/308 with valid `Location` header | No (target queued) |
| `http_error` | 404, 403, 500, etc. (status code preserved) | Only 429/500/502/503/504 |
| `timeout` | Connection, read, or download timeout | Yes, up to `--retries` |
| `connection_error` | DNS failure, refused socket, network reset | Yes, up to `--retries` |
| `ssl_error` | TLS / Certificate verification failure | No |
| `robots_disallowed`| Blocked by `robots.txt` rules (never requested) | No |
| `non_html` | Content-Type is not HTML (body never downloaded) | No |
| `too_large` | Response body exceeded `--max-bytes` limit | No |
| `skipped_extension`| File matches binary/static extension (e.g. `.pdf`) | No |
| `not_crawled` | Discovered at depth limit or truncated by max pages | No |

### Exit Codes

- `0`: Crawl finished successfully.
- `1`: Seed URL could not be crawled (blocked by robots.txt, connection refused, or 0 OK pages).
- `2`: Usage error, invalid CLI flags, or output file write error.
- `130`: Interrupted by user (Ctrl+C). **Partial graph is saved before exit.**

---

## Running Tests

LinkAtlas includes a comprehensive test suite (85 tests) with zero external network dependencies:

```powershell
cd "D:\Notes\Personal\Agentic-AI\1- PY4E\Challenges\CH 1 - LinkAtlas"

# Run all 85 tests
python -m pytest -v

# Run individual module tests
python -m pytest tests/test_urls.py -v
python -m pytest tests/test_extractor.py -v
python -m pytest tests/test_robots.py -v
python -m pytest tests/test_fetcher.py -v
python -m pytest tests/test_graph.py -v
python -m pytest tests/test_exporters.py -v
python -m pytest tests/test_crawler.py -v
python -m pytest tests/test_cli.py -v
```

All integration tests run against a local `ThreadingHTTPServer` mock fixture (`conftest.py`), verifying the exact request sequence, robots handling, delay compliance, timeout behaviour, redirect resolution, and edge deduplication.

---

## Project Structure

```
CH 1 - LinkAtlas/
├── linkatlas/
│   ├── __init__.py        # __version__ = "0.1.0"
│   ├── __main__.py        # Enables: python -m linkatlas
│   ├── cli.py             # CLI parser, orchestration, exit codes
│   ├── models.py          # CrawlConfig, FetchResult, ExtractResult, RawLink
│   ├── urls.py            # normalize_url, site_key, is_internal, extensions
│   ├── robots.py          # RobotsCache, RobotsPolicy per origin
│   ├── fetcher.py         # Polite Fetcher (robots, delay, retries)
│   ├── extractor.py       # HTML link & title extractor (BeautifulSoup)
│   ├── graph.py           # Graph data structure & summary analytics
│   ├── crawler.py         # Breadth-first crawl engine (BFS)
│   ├── exporters.py       # JSON, GraphML, DOT, CSV exporters
│   └── display.py         # Rich terminal output & summary tables
├── tests/
│   ├── conftest.py        # Local fake site HTTP test server
│   ├── test_urls.py       # URL normalization and matching tests (38 tests)
│   ├── test_extractor.py  # Link and title extraction tests (8 tests)
│   ├── test_robots.py     # Robots.txt caching & policy tests (8 tests)
│   ├── test_fetcher.py    # Polite fetcher & retry tests (11 tests)
│   ├── test_graph.py      # Graph deduplication & stats tests (5 tests)
│   ├── test_exporters.py  # Exporter tests (JSON, GraphML, DOT, CSV) (4 tests)
│   ├── test_crawler.py    # Full BFS integration tests on fake site (5 tests)
│   └── test_cli.py        # CLI option & exit code tests (6 tests)
├── pyproject.toml         # Build definition & dependencies
└── README.md              # Project documentation
```

## License

MIT
