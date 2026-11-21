# ConfCheck — Step-by-Step Beginner Guide & Notes 🛡️
> **Level:** Intermediate to Advanced Python  
> **Topic:** Parser Engineering, State Machines, Regular Expressions (`re`), CI/CD Linters, Schema Validation  
> **Goal:** Build an INI configuration parser & linter from scratch **using ONLY regular expressions** (without `configparser` or any external parsing library).

---

## 1. Why Build This? (The Real-World Motivation)

### The Real-World Scenario
In production software engineering, configuration mistakes are among the leading causes of downtime:
- A developer accidentally types: `port = eighty` (a string where a number is required).
- A boolean setting is misspelled: `debug = maybe`.
- A critical setting is left out: `database_url` is omitted entirely.
- The same setting is defined twice with conflicting values (duplicate keys).

Python's built-in `configparser` module is notoriously forgiving:
1. It treats every value strictly as a string (`8080` and `true` are both returned as strings).
2. It does not validate value types or numeric bounds.
3. It does not report exact line numbers and syntax error codes suitable for CI linting.

In a CI/CD pipeline (such as GitHub Actions), you need a strict linter that catches these errors *before* deployment:
```
app.ini:7: error E004: duplicate key 'port' in [server] (first defined at line 6)
app.ini:14: error E202: expected int for 'pool_size', got str 'eighty'
```

### The Hard Challenge: Zero `configparser`
To deeply understand how programming languages, compilers, and lexers parse unstructured text, we enforce a strict rule: **Zero external config libraries**. Every recognizing, tokenizing, and type-inferring step must be implemented using compiled regular expressions from Python's standard `re` module.

---

## 2. What Are We Building? (The Product Blueprint)

### Supported INI Syntax:

```ini
; Full-line comment (or using #)
app_name = LogLens             ; Global key (before any [section])
version = 1.2                  ; Inline comment (requires preceding whitespace)

[server]
host = 0.0.0.0
port = 8080                    ; Inferred as int
debug = yes                    ; Inferred as boolean True
allowed_hosts = localhost, 127.0.0.1, example.com   ; Inferred as list

motd = "Welcome, \"friend\"\nEnjoy!"   ; Quoted string with escape sequences

[database]
url = postgres://user:pass@localhost/db#primary  ; '#' without space is NOT a comment!
description = This is a long description
    that continues on a second line              ; Indented continuation line
    and a third line.
query = SELECT * \
    FROM users                                   ; Backslash line continuation
```

### CLI Command Examples:

```bash
# 1. Parse a config file and display the inferred types in a terminal table
confcheck app.ini

# 2. Validate against a strict schema file
confcheck app.ini --schema schema.ini

# 3. Extract a single typed value for shell scripts
confcheck app.ini --get server/port    # prints: 8080

# 4. Strict CI mode: promote all warnings to errors (exits with code 1)
confcheck app.ini --schema schema.ini --strict

# 5. Output typed configuration as JSON
confcheck app.ini --json
```

---

## 3. Core Concepts to Understand First

### Concept 1: The Line-by-Line State Machine
As our parser iterates through the lines of a file, it acts as a **State Machine**. It tracks contextual state:
- What is the current active section? (Defaults to `_global`).
- Which key is currently buffering multi-line values?
- Does the current line have indentation connecting it to the previous line?

```
Line 1: [server]        --> State: current_section = "server", current_key = None
Line 2: port = 8080     --> State: current_key = "port", buffer = ["8080"]
Line 3: description = A --> State: current_key = "description", buffer = ["A"]
Line 4:     continues B --> Indented! Appends "continues B" to buffer!
Line 5: [database]      --> New section header! Finalize "description", reset state.
```

### Concept 2: Regex Negative Lookahead `(?!\s+[;#])`
A common beginner mistake is stripping comments with `line.split("#")[0]`.
Consider this line:
`url = https://example.com/db#primary`
Here, `#primary` is an anchor in the URL, **not** a comment. A comment is only valid if preceded by whitespace:
`url = https://example.com/db ; this is an inline comment`

We solve this using a **Negative Lookahead** assertion:
```python
INLINE_COMMENT = re.compile(
    r'''^(?P<body>(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|(?!\s+[;#]).)*?)(?:\s+[;#].*)?$''',
    re.DOTALL
)
```
This pattern matches characters one by one, but halts the body capture the moment it encounters whitespace followed by `;` or `#`.

### Concept 3: Type Inference Hierarchy
When no schema is provided, the parser infers Python types in order of precedence:
1. **Empty string?** $\to$ `""`
2. **Boolean literal?** Case-insensitive `true`/`yes`/`on` $\to$ `True`; `false`/`no`/`off` $\to$ `False`.
3. **Integer literal?** `^[+-]?\d+$` $\to$ `int(val)`. (`1.2` contains a dot, so it remains `str`).
4. **Comma-separated list?** If an unquoted comma exists $\to$ `list[str]`.
5. **Fallback:** Normal `str` (with escaped sequences decoded).

---

## 4. File Structure (Architecture Blueprint)

```
confcheck/
├── confcheck/
│   ├── __init__.py     # Package version metadata
│   ├── __main__.py     # Enables: python -m confcheck
│   ├── patterns.py     # All compiled regular expressions (the engine core)
│   ├── models.py       # Entry, Issue, Rule, and Schema dataclasses
│   ├── values.py       # Inline comment stripping, unquoting, type inference & coercion
│   ├── parser.py       # Line-by-line state machine -> ParseResult (E001-E004, W001)
│   ├── schema.py       # Schema loader (type, required, min, max, choices, default)
│   ├── validator.py    # Schema validation engine (E101, E201, E202, E203, W101, W102)
│   ├── display.py      # Rich tables and stderr diagnostic output
│   └── cli.py          # Command-line interface and exit codes (0/1/2/130)
├── tests/              # 37 comprehensive pytest tests
├── pyproject.toml      # Build configuration
└── README.md           # Documentation
```

---

## 5. Step-by-Step Implementation Guide

### Step 1: Centralized Regular Expressions (`patterns.py`)
All tokenizing and pattern matching logic is defined in one place:

```python
import re

BLANK = re.compile(r'^\s*$')
COMMENT = re.compile(r'^\s*[;#]')
SECTION = re.compile(r'^\[\s*(?P<name>[A-Za-z0-9_.\-](?:[A-Za-z0-9_.\- ]*[A-Za-z0-9_.\-])?)\s*\][ \t]*(?:[;#].*)?$')
BAD_SECTION = re.compile(r'^\s*\[')
KEY_VALUE = re.compile(r'^(?P<key>[A-Za-z_][A-Za-z0-9_.\-]*)[ \t]*(?P<sep>[=:])[ \t]*(?P<value>.*)$')
CONTINUATION = re.compile(r'^[ \t]+(?P<text>\S.*)$')
BACKSLASH_END = re.compile(r'[ \t]*\\$')
BOOL = re.compile(r'^(?:(?P<true>true|yes|on)|(?P<false>false|no|off))$', re.IGNORECASE)
INT = re.compile(r'^[+-]?\d+$')
```

---

### Step 2: Value Cleaning & Type Inference (`values.py`)

```python
from confcheck.patterns import BOOL, INT, INLINE_COMMENT

def strip_inline_comment(text: str) -> str:
    m = INLINE_COMMENT.match(text)
    return m.group("body").rstrip() if m else text.rstrip()

def infer_value(raw: str):
    stripped = raw.strip()
    if not stripped:
        return ""
    
    # 1. Check boolean
    m_bool = BOOL.match(stripped)
    if m_bool:
        return m_bool.group("true") is not None
        
    # 2. Check integer
    if INT.match(stripped):
        return int(stripped)
        
    # 3. Check list
    if "," in stripped:
        return [s.strip() for s in stripped.split(",")]
        
    return stripped
```

---

### Step 3: Line-by-Line State Machine (`parser.py`)

```python
def parse_text(text: str, filename: str = "<stdin>"):
    lines = text.splitlines()
    current_section = "_global"
    current_key = None
    value_lines = []
    
    for line_no, raw_line in enumerate(lines, start=1):
        # Blank line terminates continuation
        if BLANK.match(raw_line):
            finalize_current_key()
            continue
            
        # Full-line comment
        if COMMENT.match(raw_line):
            continue
            
        # Section header
        m_sec = SECTION.match(raw_line)
        if m_sec:
            finalize_current_key()
            current_section = m_sec.group("name")
            continue
            
        # Key-value definition
        m_kv = KEY_VALUE.match(raw_line)
        if m_kv:
            finalize_current_key()
            current_key = m_kv.group("key")
            value_lines = [m_kv.group("value")]
            continue
            
        # Indented continuation line
        m_cont = CONTINUATION.match(raw_line)
        if m_cont and current_key:
            value_lines.append(m_cont.group("text"))
            continue
            
        # Syntax error
        report_error("E001", "invalid syntax", line_no)
```

---

### Step 4: Schema Validation (`validator.py`)
Validates each parsed value against declared schema rules:
- `required`: Triggers **Error E101** if absent.
- `min` / `max`: Triggers **Error E201** if outside numeric or list length bounds.
- `type`: Triggers **Error E202** on type mismatch.
- `choices`: Triggers **Error E203** if value is not in the allowed list.
- Unknown keys: Emits **Warning W101** (or Error in `--strict` mode).

---

## 6. How to Run and Test

```powershell
cd "D:\Notes\Personal\Agentic-AI\1- PY4E\Challenges\CH 2 - ConfCheck"

# Run all 37 tests
python -m pytest -v

# Verification check: Ensure no reference to configparser exists anywhere
Select-String -Path "confcheck\*.py","tests\*.py" -Pattern "configparser"
# Should produce zero output!
```

---

## 7. Key Takeaways for Beginners

1. **Parsers are State Machines:** Processing text sequentially while maintaining contextual state is the core mechanism behind interpreters and compilers.
2. **Regex Lookaheads:** `(?=...)` and `(?!...)` check subsequent text without consuming it.
3. **CI/CD Exit Codes:**
   - `0`: Success (deploy pipeline passes).
   - `1`: Lint or schema errors detected (blocks pull request).
   - `2`: Usage error or unreadable file.
