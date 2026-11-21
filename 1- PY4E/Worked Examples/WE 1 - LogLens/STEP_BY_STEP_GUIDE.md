# LogLens — Step-by-Step Beginner Guide & Notes 🚀
> **Level:** Beginner to Intermediate Python  
> **Topic:** Text Processing, Regular Expressions, Python Generators, Memory-Safe Streaming CLI  
> **Goal:** Build a production-ready Regex Log Parser from scratch.

---

## 1. Why Build This? (The Real-World Motivation)

### The Real-World Scenario
Imagine you are working as a software developer or system administrator. Suddenly, alerts start firing: your web application has crashed or slowed to a crawl! You SSH into the production server and navigate to the log directory, only to find an `access.log` file that is **2 GB or even 50 GB** in size.

Every second, thousands of raw text lines are being appended to this file:
```text
192.168.1.5 - - [10/Oct/2025:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 1024
192.168.1.6 - - [10/Oct/2025:13:55:37 +0000] "POST /api/login HTTP/1.1" 500 512
```

To diagnose the problem, you need immediate answers:
1. **How many 500-level internal server errors occurred?**
2. **Which client IP addresses are flooding the server?**
3. **Which URLs are triggering 404 Not Found errors?**

If you try to open a 2 GB file in Notepad or VS Code, your computer will freeze. If you write a standard Python script using `file.readlines()`, Python will attempt to allocate space for the entire file in RAM simultaneously, causing a fatal `MemoryError` crash.

### The Solution: LogLens
We build a dedicated, memory-safe command-line tool that:
- **Operates safely with tiny memory usage:** Whether the log file is 10 MB or 50 GB, RAM usage remains constant at ~15 MB because it uses Python **generators** (`yield`) to stream line by line.
- **Includes built-in presets:** Ready-to-use regular expressions for Nginx, Apache, Syslog, and generic formats.
- **Enables flexible filtering:** Filter rows on the fly with flags like `--where "status>=500"`.
- **Calculates summary statistics:** Total lines parsed, error rates, top IP addresses, and total bandwidth sent.
- **Supports exports:** Clean exports to formatted terminal tables, CSV, or JSON.
- **Never drops unmatched lines silently:** Lines that fail to match the regex can be inspected with `--show-unmatched`.

---

## 2. What Are We Building? (The Product Blueprint)

### Input, Processing, and Output

```
┌────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│       Input Log        │ ───► │     LogLens Engine      │ ───► │         Output          │
│ (File, Gzip, or stdin) │      │ (Regex + Stream Filter) │      │ (Table, CSV, JSON, CLI) │
└────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

### CLI Command Examples

```bash
# 1. Parse an Nginx access log and render the first 50 rows in a formatted terminal table
loglens access.log --preset nginx

# 2. Filter for server errors only
loglens access.log --preset nginx --where "status>=500"

# 3. Apply multiple filters simultaneously (AND logic)
loglens access.log --preset nginx --where "status>=400" --where "method=POST"

# 4. Stream input via Unix pipe from standard input (stdin)
cat /var/log/syslog | loglens --preset syslog --limit 20

# 5. Compute summary statistics (status codes breakdown, top IPs, bandwidth)
loglens access.log --preset nginx --stats

# 6. Export filtered data to CSV or JSON
loglens access.log --preset nginx --where "status>=500" --out errors.csv

# 7. Regex suggestion: provide a sample line and let LogLens suggest the regex
loglens --suggest '192.168.1.5 - - [10/Oct/2025:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 1024'
```

---

## 3. Core Concepts to Understand First

If you have just learned basic Python, these 3 core concepts are essential for building this tool:

### Concept 1: Python Generators and `yield` (Memory Safety)
- **The Naive Approach (`return`):**
  ```python
  def read_all_lines(path):
      lines = []
      with open(path) as f:
          for line in f:
              lines.append(line)  # Every single line stays in RAM!
      return lines  # 2 GB of memory consumed immediately
  ```
- **The Streaming Approach (`yield`):**
  ```python
  def stream_lines(path):
      with open(path) as f:
          for line in f:
              yield line  # Only ONE line exists in RAM at any given millisecond!
  ```
  When the caller loops over `stream_lines()`, Python yields control back after each line. A 50 GB log file uses no more memory than a 10 KB file.

### Concept 2: Regex Named Capture Groups `(?P<name>...)`
Standard regular expression capture groups use numeric indices (`match.group(1)`, `match.group(2)`), which makes code fragile and hard to read.
Named capture groups associate a descriptive key with each captured portion:
```python
import re

pattern = re.compile(
    r'^(?P<ip>\S+) - - \[(?P<time>[^\]]+)\] "(?P<method>\w+) (?P<path>\S+) HTTP/\d\.\d" (?P<status>\d+)'
)
match = pattern.match('192.168.1.5 - - [10/Oct/2025:13:55:36 +0000] "GET /index.html HTTP/1.1" 200')

print(match.groupdict())
# Result:
# {
#   'ip': '192.168.1.5',
#   'time': '10/Oct/2025:13:55:36 +0000',
#   'method': 'GET',
#   'path': '/index.html',
#   'status': '200'
# }
```
Using `match.groupdict()`, each raw log line is transformed instantly into a Python dictionary.

### Concept 3: Dynamic Expression Filtering (`--where "status>=500"`)
When a user passes `--where "status>=500"`, the string must be parsed into:
1. **Field name:** `status`
2. **Comparison operator:** `>=`
3. **Target value:** `500`

Our filter engine inspects the dictionary value `row["status"]`. If both the row value and the target value can be parsed as numbers, numeric comparison is performed (`500 >= 500`). Otherwise, lexicographical string comparison is used.

---

## 4. File Structure (Architecture Blueprint)

Rather than placing all functionality into a single monolithic script, we divide the responsibilities across modular files:

```
loglens/
├── loglens/
│   ├── __init__.py      # Package metadata (__version__ = "0.1.0")
│   ├── __main__.py      # Enables execution via: python -m loglens
│   ├── presets.py       # Compiled regex presets (Nginx, Apache, Syslog, Generic)
│   ├── parser.py        # Line-by-line streaming generator that applies regex
│   ├── filters.py       # Dynamic condition evaluator for --where filters
│   ├── stats.py         # Summary metrics accumulator (status codes, top IPs, bandwidth)
│   ├── export.py        # CSV and JSON file writers
│   ├── suggest.py       # Heuristic regex generator from a sample log line
│   ├── display.py       # Terminal table and stats rendering using the Rich library
│   └── cli.py           # Argument parsing with argparse and workflow orchestration
├── tests/               # 34 pytest unit and integration tests
├── pyproject.toml       # Build configuration and dependencies
└── README.md            # Technical documentation
```

---

## 5. Step-by-Step Implementation Guide

### Step 1: Packaging Configuration (`pyproject.toml`)
We configure standard packaging so the tool can be installed into our environment using `pip install -e .`:

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "loglens"
version = "0.1.0"
description = "A regex log parser with presets, filters, stats, and exports."
requires-python = ">=3.10"
dependencies = [
    "rich>=13.0.0",  # Beautiful terminal formatting
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
]

[project.scripts]
loglens = "loglens.cli:main"  # Generates the executable command
```

---

### Step 2: Compiled Presets (`presets.py`)
Pre-compiled patterns for common log standards:

```python
import re

PRESETS = {
    "nginx": re.compile(
        r'^(?P<remote_addr>\S+)\s+-\s+(?P<remote_user>\S+)\s+'
        r'\[(?P<time_local>[^\]]+)\]\s+"(?P<request>[^"]*)"\s+'
        r'(?P<status>\d{3})\s+(?P<body_bytes_sent>\d+)'
    ),
    "apache": re.compile(
        r'^(?P<host>\S+)\s+\S+\s+(?P<user>\S+)\s+'
        r'\[(?P<time>[^\]]+)\]\s+"(?P<request>[^"]*)"\s+'
        r'(?P<status>\d{3})\s+(?P<bytes>\S+)'
    ),
    "syslog": re.compile(
        r'^(?P<timestamp>[A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+'
        r'(?P<host>\S+)\s+(?P<process>[^:\[]+)(?:\[(?P<pid>\d+)\])?:\s+'
        r'(?P<message>.*)$'
    ),
}
```

---

### Step 3: Streaming Parser (`parser.py`)
This function reads lines lazily and yields structured records without accumulating them in memory:

```python
from typing import Generator, TextIO, Tuple, Optional, Pattern

def parse_lines(
    file_obj: TextIO,
    pattern: Pattern,
) -> Generator[Tuple[int, Optional[dict], str], None, None]:
    """
    Reads a text stream line-by-line, matches against the regex,
    and yields: (line_number, parsed_dictionary_or_None, raw_line).
    """
    for line_no, raw_line in enumerate(file_obj, start=1):
        line = raw_line.rstrip("\r\n")
        match = pattern.match(line)
        if match:
            yield line_no, match.groupdict(), line
        else:
            yield line_no, None, line
```

---

### Step 4: Filtering Engine (`filters.py`)
Evaluates user conditions like `--where "status>=500"`:

```python
import re

FILTER_RE = re.compile(r'^(?P<field>[A-Za-z0-9_]+)\s*(?P<op>>=|<=|!=|=|>|<)\s*(?P<val>.*)$')

def match_filter(row: dict, field: str, op: str, target_val: str) -> bool:
    if field not in row:
        return False
    val = str(row[field])

    # Attempt numeric comparison first
    try:
        num_val = float(val)
        num_target = float(target_val)
        if op == "=": return num_val == num_target
        if op == "!=": return num_val != num_target
        if op == ">": return num_val > num_target
        if op == ">=": return num_val >= num_target
        if op == "<": return num_val < num_target
        if op == "<=": return num_val <= num_target
    except ValueError:
        # Fallback to string comparison
        if op == "=": return val == target_val
        if op == "!=": return val != target_val
        if op == ">": return val > target_val
        if op == ">=": return val >= target_val
        if op == "<": return val < target_val
        if op == "<=": return val <= target_val

    return False
```

---

### Step 5: Exporting Results (`export.py`)
Writing parsed dictionaries to standard structured files:

```python
import csv
import json

def export_csv(rows: list[dict], path: str) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def export_json(rows: list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
```

---

### Step 6: CLI Orchestration (`cli.py`)
Using `argparse` to wire all modules together into a unified terminal tool:

```python
import argparse
import sys
from loglens.presets import PRESETS
from loglens.parser import parse_lines

def main():
    parser = argparse.ArgumentParser(prog="loglens", description="Regex Log Parser")
    parser.add_argument("file", nargs="?", help="Path to log file (reads stdin if omitted)")
    parser.add_argument("--preset", choices=PRESETS.keys(), default="generic")
    parser.add_argument("--regex", help="Custom regex pattern with named groups")
    parser.add_argument("--where", action="append", help="Filter condition (e.g. status>=500)")
    parser.add_argument("--stats", action="store_true", help="Print summary statistics")
    parser.add_argument("--out", help="Export matching rows to .csv or .json")
    parser.add_argument("--limit", type=int, default=50, help="Maximum table rows to display")

    args = parser.parse_args()
    # Open input stream, stream through parser, apply filters, and render display
```

---

## 6. How to Run and Test

### Running the Tests:
```powershell
cd "D:\Notes\Personal\Agentic-AI\1- PY4E\Worked Examples\WE 1 - LogLens"
python -m pytest -v
```

All 34 unit tests verify:
- Matching accuracy across Nginx, Apache, and Syslog presets.
- Numeric and string comparison logic in `--where` filters.
- Detection and reporting of unmatched lines.
- CSV and JSON export formatting.

---

## 7. Key Takeaways for Beginners

1. **`yield` guarantees constant memory usage:** Never call `.read()` or `.readlines()` on arbitrary-sized files.
2. **Named regex groups create instant structure:** `(?P<field>...)` transforms raw text directly into clean Python dictionaries.
3. **Respect Unix standards:** Supporting both file paths and stdin pipes (`cat log | loglens`) makes CLI tools highly composable.
