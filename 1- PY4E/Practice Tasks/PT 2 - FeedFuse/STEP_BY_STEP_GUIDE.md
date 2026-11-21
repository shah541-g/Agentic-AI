# FeedFuse — Step-by-Step Beginner Guide & Notes ⚡
> **Level:** Intermediate Python  
> **Topic:** Asynchronous Programming (`asyncio`, `httpx`), YAML Configurations, JSON Data Wrangling, Fault Tolerance  
> **Goal:** Build a concurrent, resilient API Aggregator that merges multiple external JSON APIs simultaneously without crashing if any single source fails.

---

## 1. Why Build This? (The Real-World Motivation)

### The Real-World Scenario
Suppose you are developing a morning briefing dashboard or an automation bot that needs to present combined data from multiple independent services:
1. **Weather API:** Today's temperature and wind speed.
2. **GitHub API:** Star counts and open issue numbers for your repository.
3. **CoinGecko API:** Current Bitcoin price in USD.
4. **Internal Company API:** Unread notifications count.

If you write a standard Python script using synchronous libraries like `requests`:
```python
res1 = requests.get("https://api.open-meteo.com...")  # Blocks for 1.5 seconds
res2 = requests.get("https://api.github.com...")      # Blocks for 1.0 seconds
res3 = requests.get("https://api.coingecko.com...")   # Blocks for 2.0 seconds
# Total duration: 4.5 seconds!
```
This script executes **sequentially** (one after another). Your computer spends 4.5 seconds waiting for network packets to return over the internet, while the CPU sits completely idle.

Even worse: **If one API encounters an error (e.g. GitHub returns HTTP 500 or times out), the entire script crashes!** The user misses out on the weather and crypto data that succeeded.

### The Solution: FeedFuse
We build a robust command-line aggregator that:
1. **Fetches concurrently with `asyncio`:** Dispatches requests to all APIs simultaneously. The total time taken equals only the single slowest API (~2.0s instead of 4.5s).
2. **Provides error isolation:** Every source reports its own status (`ok`, `cached`, `failed`, `timeout`). If one fails, the others continue uninterrupted.
3. **Follows "Config over Code":** Users specify data sources in a simple YAML file (`sources.yaml`) without modifying any Python code.
4. **Performs dot-path field extraction:** Extracts deeply nested values into a clean, flat table (e.g., `current_weather.temperature` $\to$ `temp_c`).
5. **Protects secrets:** API tokens are populated from environment variables (`${GITHUB_TOKEN}`) and never leaked in output files or logs.
6. **Includes disk caching:** Caches API responses for $N$ seconds to avoid repeated rate-limited API calls.

---

## 2. What Are We Building? (The Product Blueprint)

### Input, Processing, and Output

```
┌──────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│     sources.yaml     │ ───► │     FeedFuse Engine     │ ───► │         Output          │
│ (URLs, Mappings, ...)│      │ (Async Concurrent Fetch)│      │ (Table, JSON, CSV File) │
└──────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

### 1. Configuration File Format (`sources.yaml`):

```yaml
defaults:
  timeout: 10
  retries: 2

merge:
  mode: combine   # or 'join'

sources:
  - name: weather
    url: https://api.open-meteo.com/v1/forecast
    params:
      latitude: 31.5
      longitude: 74.3
      current_weather: true
    map:
      temp_c: current_weather.temperature
      wind_kmh: current_weather.windspeed

  - name: btc
    url: https://api.coingecko.com/api/v3/simple/price
    params: { ids: bitcoin, vs_currencies: usd }
    map:
      price_usd: bitcoin.usd
```

### 2. CLI Command Examples:

```bash
# Fetch all configured sources and render the aggregated result table
feedfuse run sources.yaml

# Enable disk caching for 60 seconds (subsequent calls use cached data)
feedfuse run sources.yaml --cache 60

# Save the combined data as JSON or CSV
feedfuse run sources.yaml --out result.json

# Inspect command: Preview any unknown API's JSON structure and auto-suggest field mappings
feedfuse inspect https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd
```

---

## 3. Core Concepts to Understand First

### Concept 1: Synchronous vs Asynchronous (`async` & `await`)
- **Synchronous (Blocking):**
  Imagine a chef putting a pizza into an oven and standing still for 15 minutes waiting for it to bake. While waiting, no other dishes can be prepared.
- **Asynchronous (Non-Blocking Event Loop):**
  The chef places the pizza in the oven, sets a timer (`await`), and immediately begins prepping a salad for another table. When the oven timer rings, the chef returns to take out the pizza.

Python's `httpx.AsyncClient` and `asyncio.gather` apply this exact model to network requests:
```python
import asyncio
import httpx

async def fetch(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)  # Releases CPU to work on other tasks while waiting
        return response.json()

async def main():
    # Dispatches all network requests in parallel
    results = await asyncio.gather(
        fetch("https://api1..."),
        fetch("https://api2..."),
        fetch("https://api3..."),
        return_exceptions=True  # A failure in one task does NOT cancel the others!
    )
```

### Concept 2: Dot-Path Navigation in Nested Dictionaries (`mapper.py`)
APIs often return deeply nested structures:
```json
{
  "status": "success",
  "data": {
    "weather": {
      "temperature": 28.5
    }
  }
}
```
If the user specifies `data.weather.temperature`, our function must step through each key successively:
```python
def extract_path(data: dict, path: str):
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current
```

### Concept 3: Environment Variable Secrets Substitution (`${VAR}`)
Hardcoding API tokens in configuration files is dangerous.
In the YAML file, users write:
```yaml
headers:
  Authorization: "Bearer ${GITHUB_TOKEN}"
```
We search for `${VARIABLE_NAME}` using regular expressions and replace it with `os.environ.get("GITHUB_TOKEN")`.

---

## 4. File Structure (Architecture Blueprint)

```
feedfuse/
├── feedfuse/
│   ├── __init__.py      # Package version metadata
│   ├── __main__.py      # Enables execution via: python -m feedfuse
│   ├── models.py        # SourceConfig, SourceResult, and RunConfig dataclasses
│   ├── config.py        # YAML parsing with ${ENV_VAR} secret substitution
│   ├── fetcher.py       # Async HTTP client with retries and fault isolation
│   ├── cache.py         # Disk cache with TTL expiration
│   ├── mapper.py        # Dot-path extractor for nested JSON structures
│   ├── merger.py        # Aggregation strategies: 'combine' and 'join'
│   ├── inspect.py       # API preview tool with automatic mapping suggestions
│   ├── output.py        # Rich terminal tables, JSON, and CSV export formatting
│   └── cli.py           # Command-line interface orchestration
├── tests/               # 40 pytest tests using respx for async mocking
├── pyproject.toml       # Build definition and dependencies
└── README.md            # Technical documentation
```

---

## 5. Step-by-Step Implementation Guide

### Step 1: Data Models (`models.py`)
Dataclasses keep our internal data contracts strict and explicit:

```python
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class SourceConfig:
    name: str
    url: str
    params: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    map: dict[str, str] = field(default_factory=dict)
    timeout: float = 10.0
    retries: int = 1

@dataclass
class SourceResult:
    name: str
    status: str             # "ok" | "cached" | "failed" | "timeout"
    raw_data: Optional[Any] = None
    mapped_data: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    elapsed_ms: int = 0
```

---

### Step 2: Configuration Loader and Secret Injection (`config.py`)
Resolves environment variables before parsing the YAML document:

```python
import os
import re
import yaml

ENV_VAR_RE = re.compile(r'\$\{([A-Za-z0-9_]+)\}')

def substitute_env_vars(text: str) -> str:
    def replacer(match):
        var_name = match.group(1)
        val = os.environ.get(var_name)
        if val is None:
            raise ValueError(f"Missing required environment variable: {var_name}")
        return val
    return ENV_VAR_RE.sub(replacer, text)

def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        raw_text = f.read()
    resolved_text = substitute_env_vars(raw_text)
    return yaml.safe_load(resolved_text)
```

---

### Step 3: Concurrent Fetcher with Retries (`fetcher.py`)
Each source is requested concurrently with exponential backoff on transient errors:

```python
import asyncio
import httpx
from feedfuse.models import SourceConfig, SourceResult

async def fetch_source(client: httpx.AsyncClient, source: SourceConfig) -> SourceResult:
    for attempt in range(source.retries + 1):
        try:
            resp = await client.get(
                source.url,
                params=source.params,
                headers=source.headers,
                timeout=source.timeout
            )
            if resp.status_code == 200:
                return SourceResult(name=source.name, status="ok", raw_data=resp.json())
            else:
                if attempt == source.retries:
                    return SourceResult(name=source.name, status="failed", error=f"HTTP {resp.status_code}")
        except httpx.TimeoutException:
            if attempt == source.retries:
                return SourceResult(name=source.name, status="timeout", error="Timed out")
        except Exception as e:
            if attempt == source.retries:
                return SourceResult(name=source.name, status="failed", error=str(e))
        
        # Exponential backoff delay
        await asyncio.sleep(0.5 * (2 ** attempt))

async def fetch_all(sources: list[SourceConfig]) -> list[SourceResult]:
    async with httpx.AsyncClient() as client:
        tasks = [fetch_source(client, src) for src in sources]
        return await asyncio.gather(*tasks)
```

---

### Step 4: Merging Strategies (`merger.py`)
Two distinct merge modes are supported:
1. **`combine` mode:** Flattens all extracted dictionaries into a single combined dictionary:
   ```python
   # weather: {"temp_c": 28}, btc: {"price_usd": 95000}
   # Combined: {"temp_c": 28, "price_usd": 95000}
   ```
2. **`join` mode:** When sources return lists of items (e.g. users from API A, orders from API B), rows are joined on a common identifier (`on: user_id`).

---

## 6. How to Run and Test

Run the automated test suite using `pytest`:

```powershell
cd "D:\Notes\Personal\Agentic-AI\1- PY4E\Practice Tasks\PT 2 - FeedFuse"
python -m pytest -v
```

All 40 unit and integration tests use `respx` to mock HTTP endpoints locally without relying on real internet connectivity.

---

## 7. Key Takeaways for Beginners

1. **`async/await` transforms I/O performance:** For network-bound tasks, concurrency reduces wait times by factors of 3x to 5x.
2. **Never allow one error to crash the pipeline:** Use `return_exceptions=True` so that failing external dependencies do not disrupt healthy ones.
3. **YAML makes configuration accessible:** Non-programmers can easily modify endpoints and fields without touching code.
