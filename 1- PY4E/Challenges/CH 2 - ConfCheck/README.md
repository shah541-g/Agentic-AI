# ConfCheck 0.1.0

> A Python command-line config linter that parses `.ini`-style files **using only regular expressions** (no `configparser`), validates values against a schema, and reports errors with line numbers — suitable for CI pipelines.

---

## Table of Contents

1. [The Core Challenge Constraint](#the-core-challenge-constraint)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [CLI Reference](#cli-reference)
5. [Config File Syntax](#config-file-syntax)
6. [How the Parser Works — Regex Deep Dive](#how-the-parser-works--regex-deep-dive)
7. [Schema File Format](#schema-file-format)
8. [Error and Warning Code Reference](#error-and-warning-code-reference)
9. [Type Inference Rules](#type-inference-rules)
10. [Exit Codes](#exit-codes)
11. [Running Tests](#running-tests)
12. [Project Structure](#project-structure)
13. [CI Integration Example](#ci-integration-example)

---

## The Core Challenge Constraint

> **This project intentionally does NOT use `configparser` or any config/INI library.**

Every step that recognises structure in a file — identifying a section, extracting a key name, finding where an inline comment starts, detecting whether a value is a boolean — is done with **compiled regular expressions** from Python's `re` module. These patterns all live in one file: [`confcheck/patterns.py`](confcheck/patterns.py).

This is enforced with a one-line check:

```powershell
# Must print nothing
Select-String -Path "confcheck\*.py","tests\*.py" -Pattern "configparser"
```

---

## Installation

**Prerequisites:** Python 3.10+ and `pip`.

```powershell
# 1. Clone / navigate to the project folder
cd "D:\Notes\Personal\Agentic-AI\1- PY4E\Challenges\CH 1 - ConfCheck"

# 2. Install in editable mode (installs the `confcheck` command)
pip install -e .

# 3. Confirm it works
confcheck --version    # → confcheck 0.1.0
```

> [!NOTE]
> **Editable mode** (`-e`) means changes to the source code take effect immediately without reinstalling. The only runtime dependency is `rich` (for pretty terminal output).

---

## Quick Start

```powershell
# Parse and display a config file as a table
confcheck samples/app.ini

# Validate against a schema (checks required keys, types, ranges)
confcheck samples/app.ini --schema samples/schema.ini

# Output the parsed config as JSON (with correct Python types)
confcheck samples/app.ini --json

# Read a single value (great for shell scripts)
confcheck samples/app.ini --get server/port       # prints: 8080
confcheck samples/app.ini --get server/debug      # prints: true
confcheck samples/app.ini --get app_name          # prints: LogLens (global key)

# Treat all warnings as errors (strict CI mode)
confcheck samples/app.ini --schema samples/schema.ini --strict

# Read from stdin
Get-Content samples/app.ini | confcheck -

# Suppress the table, only show issues
confcheck samples/broken.ini --quiet
```

---

## CLI Reference

```
confcheck FILE [--schema SCHEMA_FILE] [--json] [--get PATH]
               [--strict] [--quiet] [--version]
```

| Flag | Description |
|------|-------------|
| `FILE` | Path to the `.ini` config file. Use `-` to read from stdin. |
| `--schema SCHEMA_FILE` | Path to a schema `.ini` file. Enables type checking, required-key enforcement, min/max bounds, and allowed-value lists. |
| `--json` | Print the fully typed config as JSON to stdout instead of a table. Issues still go to stderr. |
| `--get PATH` | Extract one value. `PATH` format: `section/key` for a sectioned key, or just `key` for a global key. Lists are printed one item per line. |
| `--strict` | Promote all warnings (W-codes) to errors. Exit code becomes 1 if any warnings exist. |
| `--quiet` | Suppress the Rich table. Only parse/validation issues are printed to stderr. |
| `--version` | Print `confcheck 0.1.0` and exit. |

---

## Config File Syntax

ConfCheck understands the following grammar:

```ini
; Full-line comment  ← starts with ; or # as the first non-whitespace character
# This is also a comment

app_name = LogLens        ; ← global key (before any section header)
version  = 1.2            ; inline comment — must have whitespace before ; or #

[server]                  ; ← section header
host     = 0.0.0.0
port     = 8080
debug    = yes            ; boolean: true/yes/on and false/no/off (case-insensitive)
allowed_hosts = localhost, 127.0.0.1, example.com   ; comma list

motd = "Welcome, \"friend\"\nEnjoy!"   ; ← quoted string with escape sequences

[database]
; '#' inside a URL is NOT a comment when there's no preceding whitespace
url        = postgres://user:pass@localhost/db#primary

description = This is a long description
    that continues on a second line     ; ← indented continuation line
    and a third line.

replicas =
    db1.internal
    db2.internal
    db3.internal

query = SELECT * \
    FROM users              ; ← backslash line continuation
```

### Syntax Rules at a Glance

| Element | Rule |
|---------|------|
| **Full-line comment** | First non-whitespace char is `;` or `#`. Entire line is ignored. |
| **Inline comment** | A `;` or `#` preceded by **at least one whitespace** character. Everything after is ignored. `#` with no leading space (e.g., in a URL) is **not** a comment. |
| **Section header** | `[name]` at column 0. Name: letters, digits, `_`, `.`, `-`, spaces (trimmed). Optional trailing comment. |
| **Global key** | A `key = value` or `key: value` line before any `[section]` header. |
| **Key name** | Starts with a letter or `_`, followed by letters, digits, `_`, `.`, `-`. |
| **Separator** | `=` or `:`, with optional surrounding spaces/tabs. |
| **Blank value** | `key =` with nothing after (or only a comment) starts a block list. |
| **Indented continuation** | A line starting with one or more spaces/tabs continues the previous key's value. |
| **Backslash continuation** | A line ending with ` \` (space + backslash) merges with the next line. |
| **Quoted string** | `"..."` or `'...'`. Escape sequences `\n`, `\t`, `\"`, `\'`, `\\` are decoded. |
| **Comma list** | A value containing `,` outside quotes is split into a `list`. |

---

## How the Parser Works — Regex Deep Dive

This section explains every pattern in [`confcheck/patterns.py`](confcheck/patterns.py) and how they fit together. If you only know regex, start here.

### What is a compiled regex?

```python
import re
pattern = re.compile(r'^\d+$')   # compile once
pattern.match('123')              # reuse many times — faster than re.match(r'...', text)
```

`re.compile` turns a pattern string into a `Pattern` object. ConfCheck compiles all patterns at import time so they are only processed once, no matter how many lines the file has.

### Named capture groups

The syntax `(?P<name>...)` gives a part of the pattern a name:

```python
m = re.match(r'^(?P<key>\w+)\s*=\s*(?P<value>.*)$', 'port = 8080')
m.group('key')    # 'port'
m.group('value')  # '8080'
```

ConfCheck uses named groups everywhere so the code reads like `m.group('name')` instead of `m.group(1)`.

---

### Pattern-by-Pattern Walkthrough

#### 1. `BLANK` — empty lines

```python
BLANK = re.compile(r'^\s*$')
```

| Part | Meaning |
|------|---------|
| `^` | Start of string |
| `\s*` | Zero or more whitespace characters (space, tab, `\r`, `\n`) |
| `$` | End of string |

A line is blank if it contains nothing but whitespace. These are skipped (they may end a continuation block, but generate no entry).

---

#### 2. `COMMENT` — full-line comments

```python
COMMENT = re.compile(r'^\s*[;#]')
```

| Part | Meaning |
|------|---------|
| `^\s*` | Leading whitespace (0 or more) |
| `[;#]` | A character class: either `;` or `#` |

If the first meaningful character is `;` or `#`, the whole line is a comment. No extraction needed — just skip it.

---

#### 3. `SECTION` — section headers

```python
SECTION = re.compile(
    r'^\[[ \t]*(?P<name>[A-Za-z0-9_.\\-](?:[A-Za-z0-9_.\\- ]*[A-Za-z0-9_.\\-])?)[ \t]*\][ \t]*(?:[;#].*)?$'
)
```

Breaking it down piece by piece:

| Part | Meaning |
|------|---------|
| `^\[` | Must start at column 0 with `[` |
| `[ \t]*` | Optional whitespace inside the bracket |
| `(?P<name>...)` | Named group called `name` |
| `[A-Za-z0-9_.\\-]` | First char: letter, digit, `_`, `.`, or `-` (no spaces at the start) |
| `(?:[A-Za-z0-9_.\\- ]*[A-Za-z0-9_.\\-])?` | Optional middle+end: spaces are allowed inside but the name must end with a non-space |
| `[ \t]*\]` | Optional whitespace then closing `]` |
| `[ \t]*` | Optional trailing spaces/tabs |
| `(?:[;#].*)?$` | Optional trailing comment, then end of line |

**Example matches:**
```
[server]           → name = "server"
[my section]       → name = "my section"
[db.primary-1]     → name = "db.primary-1"
```

**Does NOT match:**
```
[ ]                ← empty name (spaces don't count as the first char)
[section!]         ← `!` not in character class
  [server]         ← not at column 0 → triggers BAD_SECTION
```

#### 4. `BAD_SECTION` — invalid section header

```python
BAD_SECTION = re.compile(r'^\s*\[')
```

A line that starts (possibly with whitespace) with `[` but didn't match `SECTION`. This generates error **E003**.

---

#### 5. `KEY_VALUE` — key = value lines

```python
KEY_VALUE = re.compile(
    r'^(?P<key>[A-Za-z_][A-Za-z0-9_.\\-]*)[ \t]*(?P<sep>[=:])[ \t]*(?P<value>.*)$'
)
```

| Part | Meaning |
|------|---------|
| `^` | At column 0 (not indented) |
| `(?P<key>[A-Za-z_][A-Za-z0-9_.\\-]*)` | Key: starts with letter or `_`, then any alphanumeric/`_`/`.`/`-` |
| `[ \t]*` | Optional spaces/tabs before separator |
| `(?P<sep>[=:])` | The separator character, either `=` or `:` |
| `[ \t]*` | Optional spaces/tabs after separator |
| `(?P<value>.*)$` | The raw value (everything to end-of-line, including possible inline comments) |

The raw `value` is then cleaned up by `INLINE_COMMENT` before type inference.

---

#### 6. `CONTINUATION` — indented continuation lines

```python
CONTINUATION = re.compile(r'^[ \t]+(?P<text>\S.*)$')
```

| Part | Meaning |
|------|---------|
| `^[ \t]+` | One or more spaces or tabs at the start |
| `(?P<text>\S.*)` | Non-whitespace character followed by anything — ensures the line isn't just spaces |

This appends `text` to the current key's value buffer.

---

#### 7. `BACKSLASH_END` — line continuation marker

```python
BACKSLASH_END = re.compile(r'[ \t]*\\$')
```

Matches a line that ends with an optional space/tab then `\`. When a key's raw value (or continuation text) ends with this pattern, the `\` is removed and the next line is merged.

> [!NOTE]
> `$` in Python's `re` module matches at the end of the string *or* just before a trailing `\n`. Since ConfCheck strips `\r\n` before matching, this works reliably on Windows files too.

---

#### 8. `INLINE_COMMENT` — stripping trailing comments

This is the most complex pattern in the project:

```python
INLINE_COMMENT = re.compile(
    r'''^(?P<body>(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|(?!\s+[;#]).)*?)(?:\s+[;#].*)?$''',
    re.DOTALL,
)
```

**Why is it complex?** Because `; or # inside a quoted string is not a comment`:

```ini
motd = "Say \"hello\" ; warmly"   ; this IS the comment
url  = https://host/path#anchor   ; this IS the comment too (space before ;)
url2 = https://host/path#anchor   ; ← NOTE: '#' at column is NOT a comment
```

The pattern works by alternation inside the `body` group:

| Alternative | Matches |
|-------------|---------|
| `"(?:[^"\\]|\\.)*"` | A double-quoted span (including escaped chars inside) |
| `'(?:[^'\\]|\\.)*'` | A single-quoted span |
| `(?!\s+[;#]).` | Any single character that is **not** the start of `whitespace + ; or #` |

The `(?!\s+[;#])` is a **negative lookahead**: it says "only match this character if it's NOT followed by whitespace then a comment marker". This ensures that ` ;` or ` #` ends the body.

The `re.DOTALL` flag makes `.` match newlines too (needed for multi-line edge cases).

---

#### 9. `QUOTED` — fully quoted string values

```python
QUOTED = re.compile(r'''(?P<q>["'])(?P<body>(?:(?!(?P=q)|\\).|\\.)*)(?P=q)''', re.DOTALL)
```

| Part | Meaning |
|------|---------|
| `(?P<q>["'])` | Opening quote (saved as group `q`) |
| `(?P=q)` | Back-reference — same quote character that opened |
| `(?:(?!(?P=q)\|\\).` | Any char that is NOT the closing quote or a `\` |
| `\|\\.)` | OR: a backslash followed by any character (escape sequence) |
| `*` | Zero or more of the above |

This matches the entire string from opening to matching closing quote. After matching, `ESCAPE` decodes sequences like `\n → newline`, `\t → tab`, `\\ → \`.

---

#### 10. `LIST_ITEM` — splitting comma-separated lists

```python
LIST_ITEM = re.compile(r'''(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|[^,])+''')
```

`re.findall(LIST_ITEM, value)` returns all comma-separated tokens. Quoted spans are treated as atomic so a comma inside `"a, b"` does not split.

---

#### 11. `BOOL` — boolean detection

```python
BOOL = re.compile(r'^(?:(?P<true>true|yes|on)|(?P<false>false|no|off))$', re.IGNORECASE)
```

| Truthy | Falsy |
|--------|-------|
| `true`, `yes`, `on` | `false`, `no`, `off` |

The `re.IGNORECASE` flag means `True`, `YES`, `ON` all match. If `group('true')` is not `None`, the value becomes Python `True`.

---

#### 12. `INT` — integer detection

```python
INT = re.compile(r'^[+-]?\d+$')
```

Matches optional sign (`+` or `-`) followed by one or more digits. `\d+` requires at least one digit. `1.2` does NOT match (there's a `.`), so `version = 1.2` stays a string.

---

#### 13. `RULE` — schema rule declaration

```python
RULE = re.compile(
    r'^(?P<type>str|int|bool|list)(?:\[(?P<item>str|int|bool)\])?(?P<opts>(?:\s*,\s*[a-z]+(?:=[^,]*)?)*)\s*$'
)
```

Schema values look like:

```ini
port = int, required, min=1, max=65535
allowed_hosts = list[str], required
debug = bool
app_name = str, required
```

| Part | Matches |
|------|---------|
| `(?P<type>str\|int\|bool\|list)` | The base type keyword |
| `(?:\[(?P<item>str\|int\|bool)\])?` | Optional element type for lists: `list[int]`, `list[str]` |
| `(?P<opts>(?:\s*,\s*[a-z]+(?:=[^,]*)?)*)` | Zero or more `, option` or `, option=value` segments |

#### 14. `RULE_OPT` — parsing schema options

```python
RULE_OPT = re.compile(r'\s*,\s*(?P<name>[a-z]+)(?:=(?P<val>[^,]*))?')
```

`re.finditer(RULE_OPT, opts_string)` yields each option name and optional value from the `opts` group above. For example from `", required, min=1, max=65535"`:

| Match | `name` | `val` |
|-------|--------|-------|
| `, required` | `required` | `None` |
| `, min=1` | `min` | `1` |
| `, max=65535` | `max` | `65535` |

---

## Schema File Format

A schema is itself an `.ini` file. Each key's value describes how the matching config key should be validated.

```ini
; schema.ini

[_global]
app_name = str, required
version  = str

[server]
host          = str, required
port          = int, required, min=1, max=65535
debug         = bool
allowed_hosts = list[str], required

[database]
url       = str, required
pool_size = int, min=1, max=100, default=5
replicas  = list[str]
```

### Schema Options

| Option | Applies to | Description |
|--------|-----------|-------------|
| `required` | all | Error E101 if the key is missing from the config |
| `default=VALUE` | all | Inject this value if the key is absent |
| `min=N` | `int`, `list` | Minimum value (int) or minimum list length |
| `max=N` | `int`, `list` | Maximum value (int) or maximum list length |
| `choices=a\|b\|c` | `str`, `bool` | Allowed values (pipe-separated) |

### Type Coercion

When a schema rule specifies a type, `confcheck` tries to coerce the inferred value to it:

| Config value | Inferred type | Schema type | Result |
|-------------|---------------|-------------|--------|
| `8080` | `int` | `int` | ✅ `8080` |
| `yes` | `bool` | `bool` | ✅ `True` |
| `yes` | `bool` | `str` | ✅ `"yes"` (re-stringified) |
| `localhost, 127.0.0.1` | `list` | `list[str]` | ✅ `["localhost", "127.0.0.1"]` |
| `eighty` | `str` | `int` | ❌ E202 type mismatch |

---

## Error and Warning Code Reference

All issues are printed to **stderr** in the format:

```
<file>:<line>: <severity> <code>: <message>
```

Example:

```
samples/broken.ini:3: error E004: duplicate key 'host' in [server] (first defined at line 2)
```

### Parse Errors (E0xx) — from the parser

| Code | Severity | Trigger |
|------|----------|---------|
| **E001** | error | Invalid syntax — line is not a comment, blank, section, key-value, or continuation |
| **E002** | error | Unexpected indented line — continuation with no preceding key |
| **E003** | error | Invalid section header — starts with `[` but doesn't match `SECTION` pattern |
| **E004** | error | Duplicate key in the same section |

### Parse Warnings (W0xx) — from the parser

| Code | Severity | Trigger |
|------|----------|---------|
| **W001** | warning | Duplicate section — same `[section]` name appears more than once |

### Validation Errors (E1xx/E2xx) — from the schema validator

| Code | Severity | Trigger |
|------|----------|---------|
| **E101** | error | Required key is missing from the config |
| **E201** | error | Value is out of bounds (`min`/`max` violated) |
| **E202** | error | Value type does not match schema type |
| **E203** | error | Value not in allowed `choices` list |

### Validation Warnings (W1xx) — from the schema validator

| Code | Severity | Trigger |
|------|----------|---------|
| **W101** | warning | Unknown key — key exists in config but not defined in schema |
| **W102** | warning | Default value injected for a missing key |

> [!TIP]
> Run with `--strict` to promote all W-codes to errors (exit code 1). This is recommended for CI pipelines.

---

## Type Inference Rules

When no schema is provided, ConfCheck infers the Python type of every value automatically. The rules are tried in order:

```
1. Is the stripped value empty?             → str ""
2. Does BOOL match (true/yes/on etc.)?      → bool
3. Does INT match (optional sign + digits)? → int
4. Does the value contain a comma           → list[str]  (split by LIST_ITEM)
   (outside quotes)?
5. Otherwise                               → str
```

**Examples:**

| Raw value in file | Python type | Python value |
|-------------------|-------------|--------------|
| `8080` | `int` | `8080` |
| `yes` | `bool` | `True` |
| `no` | `bool` | `False` |
| `1.2` | `str` | `"1.2"` |
| `localhost, 127.0.0.1` | `list` | `["localhost", "127.0.0.1"]` |
| `"hello\nworld"` | `str` | `"hello\nworld"` (newline decoded) |
| `SELECT * FROM users` | `str` | `"SELECT * FROM users"` |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | No errors (warnings may still exist unless `--strict` is used) |
| `1` | At least one error was found (or at least one warning in `--strict` mode) |
| `2` | Bad arguments, file not found, permission denied, or invalid schema |
| `130` | Interrupted with Ctrl+C |

---

## Running Tests

```powershell
cd "D:\Notes\Personal\Agentic-AI\1- PY4E\Challenges\CH 1 - ConfCheck"

# Run all 37 tests
python -m pytest

# Verbose output (see each test name)
python -m pytest -v

# Run only one test module
python -m pytest tests/test_patterns.py -v
python -m pytest tests/test_values.py   -v
python -m pytest tests/test_parser.py  -v
python -m pytest tests/test_schema.py  -v
python -m pytest tests/test_validator.py -v
python -m pytest tests/test_cli.py     -v
```

Expected output:
```
37 passed in 0.31s
```

### Verify the no-configparser rule

```powershell
# Must produce no output
Select-String -Path "confcheck\*.py","tests\*.py" -Pattern "configparser"
```

---

## Project Structure

```
CH 1 - ConfCheck/
├── confcheck/
│   ├── __init__.py      # __version__ = "0.1.0"
│   ├── __main__.py      # enables: python -m confcheck
│   ├── cli.py           # argparse + main() — the entry point
│   ├── patterns.py      # ALL compiled regexes (the heart of the project)
│   ├── parser.py        # line-by-line state machine → ParseResult
│   ├── values.py        # strip_inline_comment, unquote, infer_value, ...
│   ├── models.py        # Entry, Issue, ParseResult, Rule, Schema dataclasses
│   ├── schema.py        # parse_rule(), load_schema()
│   ├── validator.py     # validate() → typed dict + issues
│   └── display.py       # print_issues(), show_table() using rich
├── tests/
│   ├── test_patterns.py   # 7 tests: each regex verified in isolation
│   ├── test_values.py     # 8 tests: type inference and string handling
│   ├── test_parser.py     # 6 tests: state machine, multiline, error codes
│   ├── test_schema.py     # 3 tests: rule parsing, schema loading
│   ├── test_validator.py  # 5 tests: type coercion, bounds, choices
│   └── test_cli.py        # 8 tests: end-to-end CLI, exit codes, --get, --json
├── samples/
│   ├── app.ini            # Feature showcase: all supported syntax
│   ├── broken.ini         # 4 deliberate errors (E001, E002, E003, E004)
│   └── schema.ini         # Schema for app.ini
├── pyproject.toml         # Build config + pytest settings
└── README.md              # This file
```

---

## CI Integration Example

```yaml
# .github/workflows/validate-config.yml
name: Validate Config

on: [push, pull_request]

jobs:
  confcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install ConfCheck
        run: pip install -e .
        working-directory: path/to/confcheck

      - name: Validate app config
        run: confcheck config/app.ini --schema config/schema.ini --strict
        # Exits 1 if any error OR warning found (--strict)
        # Exits 2 if schema file is missing or malformed
```

**Pre-commit hook example** (`.pre-commit-config.yaml`):

```yaml
repos:
  - repo: local
    hooks:
      - id: confcheck
        name: Validate INI configs
        language: system
        entry: confcheck
        args: [--schema, config/schema.ini, --strict]
        files: \.ini$
```

---

## Design Decisions

| Decision | Reason |
|----------|--------|
| No `configparser` | Challenge constraint — forces understanding of regex-based parsing |
| Generator / line-by-line | Memory safe for large log-sized files |
| Issues to stderr, data to stdout | Composable with pipes: `confcheck app.ini --json \| jq .server.port` |
| `_global` pseudo-section | Standard convention for keys before the first section header |
| `str` as default fallback | Avoids silent data corruption — only convert when confident |
| `rich` for display | Colour + table with zero boilerplate; suppressed automatically in pipes |
