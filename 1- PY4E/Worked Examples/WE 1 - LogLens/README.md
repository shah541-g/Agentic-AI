# LogLens 🔍

> A fast, lightweight Python command-line tool that turns messy log files into clean, filterable, exportable tables using regex presets, custom regex, and automatic regex suggestion.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-34%20passed-brightgreen.svg)]()

---

## 📖 Table of Contents

1. [Overview & Problem Statement](#overview--problem-statement)
2. [Regex Practitioner's Mental Model (Read This First!)](#regex-practitioners-mental-model-read-this-first)
3. [Architecture & Design Principles](#architecture--design-principles)
4. [Installation & Setup](#installation--setup)
5. [CLI Reference & Options](#cli-reference--options)
6. [Built-in Presets Explained (Regex Breakdown)](#built-in-presets-explained-regex-breakdown)
7. [Comprehensive Usage Examples with Real Terminal Outputs](#comprehensive-usage-examples-with-real-terminal-outputs)
   - [Basic Parsing with Built-in Presets](#1-basic-parsing-with-built-in-presets)
   - [Filtering Rows with `--where`](#2-filtering-rows-with---where)
   - [Combining Multiple Filters (AND Logic)](#3-combining-multiple-filters-and-logic)
   - [Inspecting Malformed / Unmatched Lines](#4-inspecting-malformed--unmatched-lines)
   - [Statistical Summaries & ASCII Bar Charts](#5-statistical-summaries--ascii-bar-charts)
   - [Exporting to CSV and JSON](#6-exporting-to-csv-and-json)
   - [Streaming Logs via Stdin (UNIX Pipe / PowerShell)](#7-streaming-logs-via-stdin-unix-pipe--powershell)
   - [Custom Regex with Named Capture Groups](#8-custom-regex-with-named-capture-groups)
   - [Automatic Regex Suggestion from a Sample Line](#9-automatic-regex-suggestion-from-a-sample-line)
8. [Module Reference](#module-reference)
9. [Running Tests](#running-tests)
10. [Dedicated Regex Guide](#dedicated-regex-guide)

---

## Overview & Problem Statement

Developers, students, and system administrators inspect Nginx, Apache, Syslog, and custom application logs daily. Reading raw logs by eye is exhausting, and manually writing complex `awk`/`sed`/`grep` pipelines is error-prone.

**LogLens** solves this by providing:
- **Instant Structured Tables:** Automatically parses raw lines into colored tables in your terminal.
- **Dynamic Schema via Named Groups:** Regex capture group names automatically become table headers and CSV/JSON fields.
- **Zero Heavy Infrastructure:** No ELK stack, no Splunk, no local database, and no web server required.
- **Streaming & Memory Safe:** Operates via Python generators (`yield`) line by line—never reads entire multi-gigabyte log files into RAM.
- **Privacy & Offline:** 100% local, no network requests.

---

## Regex Practitioner's Mental Model (Read This First!)

If you know regular expressions, you already know 90% of LogLens! Here is how your regex expertise maps directly to LogLens concepts:

### 1. Named Capture Groups Define Table Columns
In standard PCRE and Python regular expressions, you define named groups with:
```regex
(?P<column_name>pattern)
```
Whenever a log line matches your regex, LogLens calls Python's `match.groupdict()`. Every named group becomes a **column** in the rendered terminal table and a **field** in CSV/JSON exports:

```
Regex:  ^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>[A-Z]+) (?P<path>\S+)
                  │                 │                    │               │
Table:   ┌───────────────┬──────────────────────────┬──────────────┬──────────────┐
         │ ip            │ time                     │ method       │ path         │
```

### 2. Non-Capturing Groups Structure Without Cluttering
Use `(?:...)` when you need grouping or alternation without creating unwanted columns:
```regex
(?:\[(?P<pid>\d+)\])?
```
Here, `pid` becomes a table column, while the outer brackets and optional marker `?` do not create redundant table columns.

### 3. Anchors & Exact Line Matching
All built-in presets use `^` (start of line) and `$` (end of line). If a single character fails to match, LogLens flags the line as **unmatched** rather than silently truncating or yielding broken columns.

### 4. How `--where` Filters Regex Groups
Filter expressions like `--where "status>=500"` or `--where "path~admin"` operate directly on the strings captured by your named groups:
- **`=` and `!=`**: Case-insensitive string equality (or mathematical equality if numeric).
- **`>` `<` `>=` `<=`**: Numerical comparison if both sides are numbers (e.g. `"1000"` is greater than `"500"`), otherwise lexicographical.
- **`~`**: **Full Regex Search!** `--where "path~admin"` executes `re.search("admin", row["path"], re.IGNORECASE)`.

---

## Architecture & Design Principles

```
                    ┌────────────────────────┐
                    │ Raw Log (File / Stdin) │
                    └───────────┬────────────┘
                                │ (Line-by-line streaming)
                                ▼
                    ┌────────────────────────┐
                    │ parser.parse_lines()   │ ◄─── PRESETS / Custom Regex
                    └─────┬────────────┬─────┘
          (Matched rows)  │            │ (Unmatched lines, max 1000 kept)
                          ▼            ▼
             ┌──────────────────┐   ┌──────────────────────┐
             │ filters.py       │   │ display.py           │
             │ apply_filters()  │   │ show_unmatched()     │
             └────────┬─────────┘   └──────────────────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
  ┌────────────┐┌────────────┐┌────────────┐
  │ display.py ││ stats.py   ││ export.py  │
  │ show_table ││ show_stats ││ .csv/.json │
  └────────────┘└────────────┘└────────────┘
```

1. **Simple:** One single command with intuitive flags and helpful defaults.
2. **Memory Safe:** Uses Python generator functions (`Iterator[tuple[dict | None, str]]`). Memory usage remains constant even when analyzing 50GB log files.
3. **Debug Friendly:** Unmatched lines are never dropped. `--show-unmatched` preserves raw line content and 1-based original file line numbers.
4. **Minimal Dependencies:** Built strictly using the Python Standard Library (`re`, `csv`, `json`, `argparse`, `collections`, `datetime`) plus `rich` for formatting.

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- `pip`

### Step 1: Clone or Navigate to the Repository
```bash
cd "path/to/loglens"
```

### Step 2: Install in Editable Mode
```bash
pip install -e .
```

### Step 3: Verify Installation
```bash
loglens --version
# Output: loglens 0.1.0
```

Alternatively, you can run LogLens directly without installation via Python's module runner:
```bash
python -m loglens --version
```

---

## CLI Reference & Options

```text
usage: loglens [-h] [--preset {nginx,apache,syslog,generic}] [--regex REGEX]
               [--where EXPR] [--show-unmatched] [--stats] [--out PATH]
               [--limit N] [--suggest SAMPLE] [--version]
               [file]

A fast CLI log parser that turns messy logs into structured tables.

positional arguments:
  file                  Log file to parse (if omitted, reads from stdin).

options:
  -h, --help            Show this help message and exit.
  --preset {nginx,apache,syslog,generic}
                        Use a pre-defined regex pattern.
  --regex REGEX         Custom regex with named capture groups, e.g. '(?P<time>\S+) (?P<level>\w+)'.
  --where EXPR          Filter parsed rows, e.g. --where 'status>=500' or --where 'method=POST' (repeatable).
  --show-unmatched      Display lines that did not match the regex pattern.
  --stats               Display summary statistics and metrics.
  --out PATH            Export parsed/filtered rows to a .csv or .json file.
  --limit N             Maximum rows to display in table output (default: 50).
  --suggest SAMPLE      Suggest a regex pattern from a sample log line and exit.
  --version             Show program version and exit.
```

---

## Built-in Presets Explained (Regex Breakdown)

Every preset in `loglens/presets.py` is an optimized compiled regular expression. Here is the exact regex anatomy for each preset:

### 1. `nginx` / `apache` (Combined Log Format)
```regex
^(?P<ip>\S+) \S+ (?P<user>\S+) \[(?P<time>[^\]]+)\] "(?P<method>[A-Z]+) (?P<path>\S+) (?P<protocol>[^"]+)" (?P<status>\d{3}) (?P<size>\d+|-) "(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)"$
```
- `^(?P<ip>\S+)`: Matches client IP address up to first space.
- `\S+`: Consumes the identity check (typically `-`).
- `(?P<user>\S+)`: Captures authenticated user (or `-`).
- `\[(?P<time>[^\]]+)\]`: Captures everything between `[` and `]` as timestamp (e.g. `10/Oct/2025:13:55:36 +0000`).
- `"(?P<method>[A-Z]+) (?P<path>\S+) (?P<protocol>[^"]+)"`: Parses the HTTP request line inside quotes into three named groups: `method`, `path`, and `protocol`.
- `(?P<status>\d{3})`: Exactly 3 digits for HTTP status code (`200`, `404`, `500`).
- `(?P<size>\d+|-)`: Response body size in bytes or `-`.
- `"(?P<referrer>[^"]*)"`: HTTP Referrer URL inside quotes.
- `"(?P<user_agent>[^"]*)"$`: Client User-Agent string anchored to end of line.

### 2. `syslog` (RFC 3164)
```regex
^(?P<time>\w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2}) (?P<host>\S+) (?P<process>[^\[:]+)(?:\[(?P<pid>\d+)\])?: (?P<message>.*)$
```
- `^(?P<time>\w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2})`: Captures month name, day, and time (`Oct 10 13:55:36`).
- `(?P<host>\S+)`: Captures the logging hostname.
- `(?P<process>[^\[:]+)`: Daemon/program name (e.g. `sshd`, `systemd`).
- `(?:\[(?P<pid>\d+)\])?`: Optional non-capturing group containing named group `pid`. Matches `[1234]` if present, or sets `pid` to `""` if absent.
- `: (?P<message>.*)$`: Consumes the separator and captures the rest of the line as `message`.

### 3. `generic` (Standard Application Logs)
```regex
^(?P<time>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)\s+\[?(?P<level>DEBUG|INFO|WARN(?:ING)?|ERROR|CRITICAL|FATAL)\]?\s+(?P<message>.*)$
```
- `^(?P<time>...)`: Matches ISO timestamps with space or `T`, and optional millisecond/microsecond fractions.
- `\[?(?P<level>...)\]?`: Matches severity levels with or without enclosing brackets `[INFO]` or `INFO`.
- `(?P<message>.*)$`: Captures the rest of the application log payload.

---

## Comprehensive Usage Examples with Real Terminal Outputs

### 1. Basic Parsing with Built-in Presets
Parse an Nginx log file and render it as a syntax-colored table:

```bash
loglens sample_logs/nginx.log --preset nginx --limit 5
```

**Terminal Output:**
```text
                                  Parsed Logs                                  
┌───────┬───────┬───────┬───────┬───────┬───────┬───────┬──────┬───────┬──────┐
│ip     │ user  │ time  │ meth… │ path  │ prot… │ stat… │ size │ refe… │ user…│
├───────┼───────┼───────┼───────┼───────┼───────┼───────┼──────┼───────┼──────┤
│192.1… │ -     │ 10/O… │ GET   │ /ind… │ HTTP… │ 200   │ 1024 │ -     │ Mozi…│
│       │       │ +0000 │       │       │       │       │      │       │      │
│192.1… │ frank │ 10/O… │ POST  │ /api… │ HTTP… │ 200   │ 512  │ http… │ Mozi…│
│       │       │ +0000 │       │       │       │       │      │       │      │
│192.1… │ -     │ 10/O… │ GET   │ /old… │ HTTP… │ 301   │ 0    │ -     │ curl…│
│       │       │ +0000 │       │       │       │       │      │       │      │
│10.0.… │ -     │ 10/O… │ GET   │ /ima… │ HTTP… │ 200   │ 452… │ http… │ Mozi…│
│       │       │ +0000 │       │       │       │       │      │       │      │
│10.0.… │ -     │ 10/O… │ GET   │ /not… │ HTTP… │ 404   │ 153  │ -     │ Mozi…│
│       │       │ +0000 │       │       │       │       │      │       │      │
└───────┴───────┴───────┴───────┴───────┴───────┴───────┴──────┴───────┴──────┘
Showing 5 of 17 rows
```

*(Note: In terminal windows, status codes are colored automatically: 2xx green, 3xx cyan, 4xx yellow, 5xx red).*

---

### 2. Filtering Rows with `--where`
Filter rows numerically (e.g. status code 500 and higher):

```bash
loglens sample_logs/nginx.log --preset nginx --where "status>=500"
```

**Terminal Output:**
```text
                                  Parsed Logs                                  
┌───────┬──────┬───────┬───────┬───────┬───────┬───────┬──────┬───────┬───────┐
│ip     │ user │ time  │ meth… │ path  │ prot… │ stat… │ size │ refe… │ user_…│
├───────┼──────┼───────┼───────┼───────┼───────┼───────┼──────┼───────┼───────┤
│192.1… │ -    │ 10/O… │ POST  │ /api… │ HTTP… │ 500   │ 245  │ http… │ Mozil…│
│       │      │ +0000 │       │       │       │       │      │       │       │
│10.0.… │ -    │ 10/O… │ GET   │ /api… │ HTTP… │ 502   │ 0    │ -     │ curl/…│
│       │      │ +0000 │       │       │       │       │      │       │       │
│10.0.… │ -    │ 10/O… │ POST  │ /api… │ HTTP… │ 500   │ 412  │ -     │ Mozil…│
│       │      │ +0000 │       │       │       │       │      │       │       │
│192.1… │ -    │ 10/O… │ PUT   │ /api… │ HTTP… │ 502   │ 128  │ http… │ Mozil…│
│       │      │ +0000 │       │       │       │       │      │       │       │
└───────┴──────┴───────┴───────┴───────┴───────┴───────┴──────┴───────┴───────┘
Showing 4 of 4 rows
```

---

### 3. Combining Multiple Filters (AND Logic)
Combine status code checks with regex pattern searches (`~`) on URL paths:

```bash
loglens sample_logs/nginx.log --preset nginx --where "method=POST" --where "path~/api"
```

---

### 4. Inspecting Malformed / Unmatched Lines
When a log file has corrupt lines or non-standard entries, LogLens flags them without crashing. Use `--show-unmatched`:

```bash
loglens sample_logs/nginx.log --preset nginx --show-unmatched
```

**Terminal Output:**
```text
┌───────────────────────── Unmatched Lines (3 total) ─────────────────────────┐
│ Line 7: MALFORMED LINE 1: This is total garbage from an interrupted         │
│ connection                                                                  │
│ Line 12: BROKEN LINE 2: [10/Oct/2025:13:56:22 +0000] Missing IP and user    │
│ info                                                                        │
│ Line 18: CORRUPTED LINE 3: 192.168.1.99 - - "BAD_REQUEST_NO_TIMESTAMP" 400  │
└─────────────────────────────────────────────────────────────────────────────┘
```

Notice that original file line numbers (`Line 7`, `Line 12`, `Line 18`) are accurately reported!

---

### 5. Statistical Summaries & ASCII Bar Charts
Compute request totals, top client IPs, status distribution, top endpoints, and errors-per-minute with `--stats`:

```bash
loglens sample_logs/nginx.log --preset nginx --stats
```

**Terminal Output:**
```text
┌─ LogLens Statistics Overview ─┐
│ Total Non-Empty Lines: 20     │
│ Matched Rows:          17     │
│ Unmatched Lines:       3      │
│ Match Rate:            85.0%  │
└───────────────────────────────┘
     Top 5 Client IPs     
┌─────────────┬──────────┐
│ IP Address  │ Requests │
├─────────────┼──────────┤
│ 192.168.1.5 │        4 │
│ 10.0.0.2    │        4 │
│ 192.168.1.6 │        1 │
│ 192.168.1.7 │        1 │
│ 10.0.0.5    │        1 │
└─────────────┴──────────┘
   HTTP Status Code    
     Distribution      
┌─────────────┬───────┐
│ Status Code │ Count │
├─────────────┼───────┤
│ 200         │    10 │
│ 301         │     1 │
│ 404         │     2 │
│ 500         │     2 │
│ 502         │     2 │
└─────────────┴───────┘
   Top 5 Requested Paths    
┌──────────────────┬───────┐
│ Path             │ Count │
├──────────────────┼───────┤
│ /index.html      │     2 │
│ /api/inventory   │     2 │
│ /api/login       │     1 │
│ /old-page        │     1 │
│ /images/logo.png │     1 │
└──────────────────┴───────┘
  Errors Per Minute (Status >= 500 or ERROR/CRITICAL/FATAL)  
┌──────────────────┬───────┬────────────────────────────────┐
│ Minute Window    │ Count │ Distribution                   │
├──────────────────┼───────┼────────────────────────────────┤
│ 2025-10-10 13:56 │     4 │ ██████████████████████████████ │
└──────────────────┴───────┴────────────────────────────────┘
```

---

### 6. Exporting to CSV and JSON
Export filtered results directly to CSV or JSON using `--out`:

```bash
# Export all 5xx server errors to CSV
loglens sample_logs/nginx.log --preset nginx --where "status>=500" --out errors.csv

# Export application errors to JSON
loglens sample_logs/app.log --preset generic --where "level=ERROR" --out errors.json
```

**Content of `errors.json`:**
```json
[
  {
    "time": "2025-10-10 13:55:36",
    "level": "ERROR",
    "message": "Database connection timed out"
  },
  {
    "time": "2025-10-10 13:56:35",
    "level": "ERROR",
    "message": "Payment gateway returned status code 503"
  },
  {
    "time": "2025-10-10 13:57:35",
    "level": "ERROR",
    "message": "Failed to dispatch webhook to endpoint https://webhook.site/notify"
  }
]
```

---

### 7. Streaming Logs via Stdin (UNIX Pipe / PowerShell)
LogLens seamlessly accepts standard input when piping from other commands:

```bash
# UNIX / Linux / macOS:
cat sample_logs/syslog.log | loglens --preset syslog --limit 5

# Windows PowerShell:
Get-Content sample_logs/syslog.log | loglens --preset syslog --limit 5
```

**Terminal Output:**
```text
                                  Parsed Logs                                  
┌────────────────┬────────┬─────────┬──────┬──────────────────────────────────┐
│time            │ host   │ process │ pid  │ message                          │
├────────────────┼────────┼─────────┼──────┼──────────────────────────────────┤
│Oct 10 13:55:36 │ myhost │ sshd    │ 1234 │ Failed password for root from    │
│                │        │         │      │ 10.0.0....                       │
│Oct 10 13:55:38 │ myhost │ sshd    │ 1234 │ Failed password for root from    │
│                │        │         │      │ 10.0.0....                       │
│Oct 10 13:55:40 │ myhost │ sshd    │ 1234 │ Accepted publickey for ubuntu    │
│                │        │         │      │ from 19...                       │
│Oct 10 13:55:45 │ myhost │ systemd │ 1    │ Starting Daily apt upgrade and   │
│                │        │         │      │ clean ...                        │
│Oct 10 13:55:50 │ myhost │ cron    │ 567  │ (root) CMD                       │
│                │        │         │      │ (/usr/local/bin/backup.sh ...    │
└────────────────┴────────┴─────────┴──────┴──────────────────────────────────┘
Showing 5 of 15 rows
```

---

### 8. Custom Regex with Named Capture Groups
Have a custom proprietary log format? Simply pass your regex with named capture groups using `--regex`:

```bash
loglens sample_logs/app.log --regex "^(?P<timestamp>\S+ \S+) (?P<severity>\w+) (?P<details>.*)$"
```

If you forget to provide named groups, LogLens guides you with an immediate friendly error:
```text
Error: Regex must contain at least one named group, e.g. (?P<ip>\S+)
```

---

### 9. Automatic Regex Suggestion from a Sample Line
Don't want to write regex from scratch? Pass a sample line to `--suggest`:

```bash
loglens --suggest '192.168.1.5 - - [10/Oct/2025:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 1024'
```

**Terminal Output:**
```text
┌─────────────────────── Suggested Regular Expression ────────────────────────┐
│ ^(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s+\-\s+\-\s+\[(?P<time>[^\]]+)\]\s+"(?P<me │
│ thod>[A-Z]+)\s+(?P<path>\S+)\s+HTTP/(?P<num1>\d+)\.(?P<num2>\d+)"\s+(?P<sta │
│ tus>\d{3})\s+(?P<num3>\d+)$                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
    Extracted Named Groups from Sample     
┌────────────┬────────────────────────────┐
│ Group Name │ Extracted Value            │
├────────────┼────────────────────────────┤
│ ip         │ 192.168.1.5                │
│ time       │ 10/Oct/2025:13:55:36 +0000 │
│ method     │ GET                        │
│ path       │ /index.html                │
│ num1       │ 1                          │
│ num2       │ 1                          │
│ status     │ 200                        │
│ num3       │ 1024                       │
└────────────┴────────────────────────────┘
```

---

## Module Reference

The code is organized into modular single-responsibility units:

| File | Purpose | Key Functions / Classes |
|---|---|---|
| `loglens/__init__.py` | Package version declaration (`__version__ = "0.1.0"`) | `__version__` |
| `loglens/__main__.py` | Enables execution via `python -m loglens` | `main()` |
| `loglens/presets.py` | Pre-compiled regex patterns for standard logs | `PRESETS` dict |
| `loglens/parser.py` | Memory-efficient streaming generator | `compile_user_regex()`, `parse_lines()` |
| `loglens/filters.py` | Filtering logic with numerical and regex support | `parse_where()`, `apply_filters()` |
| `loglens/stats.py` | Aggregates counts, top entities, and errors/min | `compute_stats()` |
| `loglens/export.py` | Serializes records to `.csv` or `.json` | `export_rows()` |
| `loglens/suggest.py` | Rule-based regex tokenizer and generator | `suggest_regex()` |
| `loglens/display.py` | Terminal styling and Rich components | `show_table()`, `show_unmatched()`, `show_stats()`, `show_suggestion()` |
| `loglens/cli.py` | CLI argument parsing, execution flow & error handling | `main()`, `run()` |

---

## Running Tests

All modules include unit tests with 100% core test coverage. To execute the test suite:

```bash
pytest -v
```

**Test Suite Summary:**
```text
collected 34 items

tests/test_cli.py::test_cli_suggest_exits_zero PASSED                    [  2%]
tests/test_cli.py::test_cli_missing_both_preset_and_regex PASSED         [  5%]
tests/test_cli.py::test_cli_both_preset_and_regex PASSED                 [  8%]
tests/test_cli.py::test_cli_missing_file_error PASSED                    [ 11%]
tests/test_cli.py::test_cli_parse_nginx_table PASSED                     [ 14%]
tests/test_cli.py::test_cli_parse_nginx_where_filter PASSED              [ 17%]
tests/test_cli.py::test_cli_parse_nginx_unmatched PASSED                 [ 20%]
tests/test_cli.py::test_cli_parse_nginx_stats PASSED                     [ 23%]
tests/test_cli.py::test_cli_export_csv_and_json PASSED                   [ 26%]
tests/test_cli.py::test_cli_stdin_reading PASSED                         [ 29%]
tests/test_export.py::test_export_csv_round_trip PASSED                  [ 32%]
tests/test_export.py::test_export_json_round_trip PASSED                 [ 35%]
tests/test_export.py::test_export_empty_results PASSED                   [ 38%]
tests/test_export.py::test_unsupported_extension_raises_value_error PASSED [ 41%]
tests/test_filters.py::test_parse_where_valid PASSED                     [ 44%]
tests/test_filters.py::test_parse_where_invalid_syntax PASSED           [ 47%]
tests/test_filters.py::test_numeric_comparison_greater_than PASSED       [ 50%]
tests/test_filters.py::test_case_insensitive_string_equality PASSED      [ 52%]
tests/test_filters.py::test_regex_search_operator PASSED                 [ 55%]
tests/test_filters.py::test_multiple_filters_and_logic PASSED            [ 58%]
tests/test_filters.py::test_unknown_field_raises_value_error PASSED      [ 61%]
tests/test_filters.py::test_invalid_regex_in_filter_raises_value_error PASSED [ 64%]
tests/test_parser.py::test_valid_nginx_line_parsed_correctly PASSED     [ 67%]
tests/test_parser.py::test_malformed_line_yields_none PASSED             [ 70%]
tests/test_parser.py::test_blank_lines_are_skipped PASSED                [ 73%]
tests/test_parser.py::test_regex_with_no_named_groups_raises_value_error PASSED [ 76%]
tests/test_parser.py::test_invalid_regex_syntax_raises_value_error PASSED [ 79%]
tests/test_parser.py::test_compile_user_regex_success PASSED            [ 82%]
tests/test_stats.py::test_compute_stats_counts_and_metrics PASSED        [ 85%]
tests/test_stats.py::test_unparseable_time_does_not_crash_errors_per_minute PASSED [ 88%]
tests/test_stats.py::test_syslog_timestamp_errors_per_minute PASSED     [ 91%]
tests/test_stats.py::test_empty_rows PASSED                              [ 94%]
tests/test_suggest.py::test_suggest_regex_matches_sample_lines_from_spec PASSED [ 97%]
tests/test_suggest.py::test_suggest_fallback_on_unusual_input PASSED    [100%]

============================= 34 passed in 0.49s ==============================
```

---

## Dedicated Regex Guide

For an in-depth reference written specifically for developers who already understand regex and want to write complex filters or extract nested patterns, see [REGEX_GUIDE.md](REGEX_GUIDE.md).

---

## License

MIT License. See [LICENSE](LICENSE) for details.
