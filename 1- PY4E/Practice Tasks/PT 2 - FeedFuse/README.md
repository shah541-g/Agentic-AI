# FeedFuse ⚡

> A small, fast Python command-line tool that fetches multiple JSON APIs concurrently, extracts and renames the fields you care about, merges everything into one clean result, and never crashes just because one API is down.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-40%20passed-brightgreen.svg)]()

---

## 📖 Table of Contents

1. [Overview & Problem Statement](#overview--problem-statement)
2. [Core Principles](#core-principles)
3. [Installation & Setup](#installation--setup)
4. [CLI Command Reference](#cli-command-reference)
5. [Configuration Guide (`sources.yaml`)](#configuration-guide-sourcesyaml)
   - [Basic Syntax & Defaults](#basic-syntax--defaults)
   - [Dot-Path Extraction](#dot-path-extraction)
   - [Environment Variables & Secrets](#environment-variables--secrets)
   - [Merge Modes: `combine` vs `join`](#merge-modes-combine-vs-join)
6. [Real Usage Examples with Terminal Output](#real-usage-examples-with-terminal-output)
   - [Morning Briefing (`combine` mode)](#1-morning-briefing-combine-mode)
   - [Relational API Join (`join` mode)](#2-relational-api-join-join-mode)
   - [Inspecting an API & Generating Mappings](#3-inspecting-an-api--generating-mappings)
   - [Fault Isolation & Exit Codes](#4-fault-isolation--exit-codes)
   - [Disk Caching with `--cache`](#5-disk-caching-with---cache)
   - [Exporting to JSON and CSV](#6-exporting-to-json-and-csv)
7. [Project Structure & Modules](#project-structure--modules)
8. [Running Tests](#running-tests)
9. [License](#license)

---

## Overview & Problem Statement

Developers frequently need to aggregate data across disparate APIs—such as weather conditions, GitHub repository metrics, market prices, and internal microservices. Writing ad-hoc scripts each time leads to repetitive boilerplate: managing timeouts, orchestrating concurrent requests, isolating network errors, and manually flattening nested JSON schemas.

**FeedFuse** replaces throwaway scripts with a single declarative YAML config and one CLI command:
- **Fetch Concurrently:** All APIs are requested simultaneously using `asyncio` and `httpx`.
- **Fault-Tolerant Isolation:** If one endpoint times out or returns a 500 error, other sources continue uninterrupted.
- **Config Over Code:** Extract and rename nested fields using intuitive dot paths (`current_weather.temperature`).
- **Two Merge Modes:** Aggregate standalone sources (`combine`) or link relational lists on a shared ID (`join`).
- **Zero Secret Leaks:** API keys and bearer tokens (`${ENV_VAR}`) are resolved at runtime and never written to output files, cache keys, or logs.

---

## Core Principles

1. **Config Over Code:** Define sources and field transformations entirely in YAML.
2. **Concurrent:** Non-blocking async execution means total run time equals the slowest API, not the sum.
3. **Fault Tolerant:** Every source reports its own independent status (`ok`, `cached`, `failed`, `timeout`). Partial results are always preserved.
4. **Secrets Stay Secret:** Sensitive tokens in headers or query params are replaced in-memory and hashed via SHA-256 for cache identification.
5. **Minimal Dependencies:** Standard library plus `httpx`, `pyyaml`, and `rich`.

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- `pip`

### Installation

Clone the repository and install FeedFuse in editable mode:

```bash
cd "D:\Notes\Personal\Agentic-AI\1- PY4E\Practice Tasks\PT 2 - FeedFuse"
pip install -e .
```

Verify the installation:

```bash
feedfuse --version
# Output: feedfuse 0.1.0
```

You can also run FeedFuse directly via Python module execution:

```bash
python -m feedfuse --version
```

---

## CLI Command Reference

### 1. `feedfuse run CONFIG`

Execute concurrent aggregation based on a YAML configuration file.

```text
usage: feedfuse run [-h] [--out PATH] [--cache SECONDS] [--no-table]
                    [--only NAME] [--timeout N] [--verbose]
                    config

positional arguments:
  config           Path to YAML configuration file (e.g. sources.yaml).

options:
  -h, --help       Show this help message and exit.
  --out PATH       Write result to .json or .csv.
  --cache SECONDS  Reuse cached responses younger than this (in seconds).
  --no-table       Do not print the rich table, only write to --out.
  --only NAME      Run only this source (repeatable).
  --timeout N      Override timeout in seconds for all sources.
  --verbose        Show retry attempts and timings.
```

### Exit Codes

| Code | Meaning |
|---|---|
| `0` | All sources succeeded |
| `2` | Partial failure: at least one source failed, but at least one succeeded |
| `1` | Configuration error, or every source failed |
| `130` | Interrupted by user (Ctrl+C) |

---

### 2. `feedfuse inspect URL`

Inspect an external JSON API endpoint, print a colorized schema tree, and generate a copy-paste ready YAML `map:` block.

```text
usage: feedfuse inspect [-h] [--header KEY:VALUE] [--param KEY=VALUE] url

positional arguments:
  url                 HTTP(S) URL to inspect.

options:
  -h, --help          Show this help message and exit.
  --header KEY:VALUE  Request header (repeatable, supports ${ENV_VAR}).
  --param KEY=VALUE   Query parameter (repeatable, supports ${ENV_VAR}).
```

---

## Configuration Guide (`sources.yaml`)

### Basic Syntax & Defaults

```yaml
defaults:                    # Optional: global fallback settings
  timeout: 10                # Timeout per request in seconds
  retries: 2                 # Number of retries on 5xx, 429, or timeout (0 to 5)

merge:
  mode: combine              # "combine" (default) or "join"

sources:
  - name: weather
    url: https://api.open-meteo.com/v1/forecast
    params:
      latitude: "31.5"
      longitude: "74.3"
      current_weather: "true"
    map:
      temp_c: current_weather.temperature
      wind_kmh: current_weather.windspeed
```

### Dot-Path Extraction

- `a.b.c`: Navigates nested dictionaries (`{"a": {"b": {"c": 42}}}`).
- `items.0.name`: Accesses list elements by zero-based integer index.
- If a path cannot be found, the mapped value is set to `null` and a non-fatal warning is attached to that source's status report.

### Environment Variables & Secrets

Embed environment variables directly inside strings:

```yaml
sources:
  - name: github_repo
    url: https://api.github.com/repos/python/cpython
    headers:
      Authorization: "Bearer ${GITHUB_TOKEN}"
    map:
      stars: stargazers_count
```

If `GITHUB_TOKEN` is unset in your environment, only that source reports `failed` with `"Missing environment variable GITHUB_TOKEN"`, allowing other public sources to complete successfully.

---

### Merge Modes: `combine` vs `join`

#### `combine` Mode (Default)
Each source contributes a separate key to the top-level `data` object:

```json
{
  "data": {
    "weather": { "temp_c": 25.3, "wind_kmh": 6.5 },
    "btc": { "price_usd": 64271 }
  },
  "status": {
    "weather": { "state": "ok", "ms": 280, "warnings": [] },
    "btc": { "state": "ok", "ms": 190, "warnings": [] }
  }
}
```

#### `join` Mode
Merges records from different endpoints on a shared key (e.g. `user_id`):

```yaml
merge:
  mode: join
  on: user_id
  join_type: inner           # "inner" (default) or "left"

sources:
  - name: users
    url: https://jsonplaceholder.typicode.com/users
    records: ""              # Root of response is a list
    map:
      user_id: id
      name: name
      city: address.city

  - name: todos
    url: https://jsonplaceholder.typicode.com/todos
    records: ""
    map:
      user_id: userId
      todo: title
      done: completed
```

- Each record from `users` is linked with matching records from `todos`.
- If field names collide (e.g. both sources have `title`), the latter source's field is automatically renamed to `<source>_<field>` (`todos_title`).

---

## Real Usage Examples with Terminal Output

### 1. Morning Briefing (`combine` mode)

Fetch weather, GitHub repository stats, and Bitcoin price simultaneously:

```bash
feedfuse run examples/dev-morning.yaml
```

**Real Terminal Output:**
```text
            Sources Status             
┌─────────────┬───────┬───────┬───────┐
│ Source      │ State │  Time │ Notes │
├─────────────┼───────┼───────┼───────┤
│ weather     │  ok   │ 806ms │ none  │
│ python_repo │  ok   │ 716ms │ none  │
│ btc         │  ok   │ 382ms │ none  │
└─────────────┴───────┴───────┴───────┘
  Source: weather   
┌──────────┬───────┐
│ Field    │ Value │
├──────────┼───────┤
│ temp_c   │ 25.3  │
│ wind_kmh │ 6.5   │
└──────────┴───────┘
  Source: python_repo   
┌─────────────┬────────┐
│ Field       │ Value  │
├─────────────┼────────┤
│ stars       │ 78307  │
│ open_issues │ 9304   │
│ language    │ Python │
└─────────────┴────────┘
     Source: btc     
┌───────────┬───────┐
│ Field     │ Value │
├───────────┼───────┤
│ price_usd │ 64271 │
└───────────┴───────┘
```

---

### 2. Relational API Join (`join` mode)

Perform an inner join between users and todos from JSONPlaceholder:

```bash
feedfuse run examples/users-todos-join.yaml
```

**Real Terminal Output:**
```text
          Sources Status          
┌────────┬───────┬───────┬───────┐
│ Source │ State │  Time │ Notes │
├────────┼───────┼───────┼───────┤
│ users  │  ok   │ 267ms │ none  │
│ todos  │  ok   │ 424ms │ none  │
└────────┴───────┴───────┴───────┘
                          Joined Records (200 total)                           
┌─────────┬──────────────────┬───────────────┬────────────────────────┬───────┐
│ user_id │ name             │ city          │ todo                   │ done  │
├─────────┼──────────────────┼───────────────┼────────────────────────┼───────┤
│ 1       │ Leanne Graham    │ Gwenborough   │ delectus aut autem     │ False │
│ 1       │ Leanne Graham    │ Gwenborough   │ quis ut nam facilis... │ False │
│ 1       │ Leanne Graham    │ Gwenborough   │ fugiat veniam minus    │ False │
│ 1       │ Leanne Graham    │ Gwenborough   │ et porro tempora       │ True  │
│ 2       │ Ervin Howell     │ Wisokyburgh   │ suscipit repellat...   │ False │
└─────────┴──────────────────┴───────────────┴────────────────────────┴───────┘
Showing first 50 of 200 rows
```

---

### 3. Inspecting an API & Generating Mappings

Inspect Open-Meteo's weather endpoint to visualize its hierarchy and obtain a ready-to-use `map:` block:

```bash
feedfuse inspect "https://api.open-meteo.com/v1/forecast" --param latitude=31.5 --param longitude=74.3 --param current_weather=true
```

**Real Terminal Output:**
```text
JSON Response Structure
├── latitude: float = 31.528997
├── longitude: float = 74.282295
├── generationtime_ms: float = 0.1176595687866211
├── utc_offset_seconds: int = 0
├── timezone: str = 'GMT'
├── elevation: float = 216.0
└── current_weather (dict)
    ├── time: str = '2026-11-17T09:00'
    ├── interval: int = 900
    ├── temperature: float = 25.3
    ├── windspeed: float = 6.5
    └── weathercode: int = 0
┌──────────────── Suggested map: block ────────────────┐
│ map:                                                 │
│   latitude: latitude                                 │
│   longitude: longitude                               │
│   generationtime_ms: generationtime_ms               │
│   elevation: elevation                               │
│   temperature: current_weather.temperature           │
│   windspeed: current_weather.windspeed               │
│   weathercode: current_weather.weathercode           │
└──────────────────────────────────────────────────────┘
```

---

### 4. Fault Isolation & Exit Codes

When an endpoint fails (e.g. invalid domain, 404, or network timeout), FeedFuse captures the error and displays it clearly while still extracting all available data from the healthy sources:

```text
            Sources Status             
┌─────────────┬─────────┬───────┬────────────────────────┐
│ Source      │ State   │  Time │ Notes                  │
├─────────────┼─────────┼───────┼────────────────────────┤
│ weather     │ ok      │ 320ms │ none                   │
│ btc         │ timeout │ 5000ms│ Timed out after 5s     │
└─────────────┴─────────┴───────┴────────────────────────┘
```

Exit code: `2` (indicating partial success).

---

### 5. Disk Caching with `--cache`

Pass `--cache <SECONDS>` to avoid duplicate API requests during repeated runs:

```bash
feedfuse run examples/dev-morning.yaml --cache 60
```

On subsequent runs within 60 seconds:
```text
            Sources Status             
┌─────────────┬────────┬──────┬───────┐
│ Source      │ State  │ Time │ Notes │
├─────────────┼────────┼──────┼───────┤
│ weather     │ cached │  0ms │ none  │
│ python_repo │ cached │  0ms │ none  │
│ btc         │ cached │  0ms │ none  │
└─────────────┴────────┴──────┴───────┘
```

---

### 6. Exporting to JSON and CSV

Export aggregated payloads directly to disk:

```bash
# Export combine mode to structured JSON
feedfuse run examples/dev-morning.yaml --out briefing.json

# Export relational join to clean CSV
feedfuse run examples/users-todos-join.yaml --out joined.csv
```

**Sample CSV Output (`joined.csv`):**
```csv
user_id,name,city,todo,done
1,Leanne Graham,Gwenborough,delectus aut autem,False
1,Leanne Graham,Gwenborough,quis ut nam facilis et officia qui,False
1,Leanne Graham,Gwenborough,fugiat veniam minus,False
1,Leanne Graham,Gwenborough,et porro tempora,True
```

---

## Project Structure & Modules

```
feedfuse/
├── feedfuse/
│   ├── __init__.py        # Version string (0.1.0)
│   ├── __main__.py        # python -m feedfuse entry
│   ├── cli.py             # CLI parser, subcommands & exit codes
│   ├── config.py          # YAML validation & env interpolation
│   ├── models.py          # Source, SourceResult, Config dataclasses
│   ├── fetcher.py         # Async concurrency, retries, backoff, and isolation
│   ├── cache.py           # Disk-backed cache with SHA-256 keys
│   ├── mapper.py          # Dot-path navigation & record extraction
│   ├── merger.py          # combine() and join() aggregation algorithms
│   ├── output.py          # Rich formatting, table styling, and JSON/CSV export
│   └── inspect.py         # Response tree visualization & map suggestion
├── tests/
│   ├── test_config.py     # Configuration parsing & validation tests
│   ├── test_mapper.py     # Dot-path & record extraction tests
│   ├── test_fetcher.py    # Mocked async HTTP fetching & retry tests
│   ├── test_cache.py      # Cache TTL & secret hashing tests
│   ├── test_merger.py     # Combine & relational join tests
│   ├── test_output.py     # JSON/CSV file export tests
│   ├── test_inspect.py    # Schema inspection & suggestion tests
│   └── test_cli.py        # End-to-end CLI & exit code tests
├── examples/
│   ├── dev-morning.yaml   # Weather + GitHub + Bitcoin (combine mode)
│   └── users-todos-join.yaml # JSONPlaceholder users + todos (join mode)
├── pyproject.toml
└── README.md
```

---

## Running Tests

The test suite runs entirely offline using `respx` to mock external HTTP traffic:

```bash
pytest -v
```

**Results:**
```text
collected 40 items

tests/test_cache.py .....                                                [ 12%]
tests/test_cli.py ........                                               [ 32%]
tests/test_config.py .......                                             [ 50%]
tests/test_fetcher.py .......                                            [ 67%]
tests/test_inspect.py ..                                                 [ 72%]
tests/test_mapper.py ....                                                [ 82%]
tests/test_merger.py ...                                                 [ 90%]
tests/test_output.py ....                                                [100%]

============================= 40 passed in 3.13s ==============================
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
