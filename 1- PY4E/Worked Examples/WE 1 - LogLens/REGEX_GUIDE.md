# A Regex Practitioner's Guide to LogLens

If you know Regular Expressions, you already have the most important skill needed to use LogLens effectively. This document is written specifically for you: it translates standard regex concepts into LogLens concepts and explains everything happening under the hood.

---

## 1. How LogLens Bridges Regex and Structured Tables

Normally, using regex in terminal log analysis involves tools like `grep`, `sed`, or `awk`:

```bash
# Traditional approach: complex, fragile, manual column cuts
grep "ERROR" app.log | awk '{print $1, $2, $3}'
```

LogLens changes this paradigm using **Python's Named Capture Groups**:

```
Raw String:  2025-10-10 13:55:36 ERROR Database connection timed out
Regex:       ^(?P<time>\S+ \S+) (?P<level>\w+) (?P<message>.*)$
```

When Python's `re.search()` matches this line, it produces a match dictionary via `match.groupdict()`:

```python
{
    "time": "2025-10-10 13:55:36",
    "level": "ERROR",
    "message": "Database connection timed out"
}
```

LogLens intercepts this dictionary:
1. **Keys** (`time`, `level`, `message`) become the **columns** of a Rich terminal table, the **header row** of a `.csv`, or the **keys** of a `.json` object.
2. **Values** become the cells under those columns.

---

## 2. Python Regex Dialect vs Other Flavors

If you are coming from PCRE (Perl/PHP), JavaScript, Go, or POSIX `grep`/`sed`, keep these Python-specific details in mind:

| Feature | Python Syntax | PCRE / Oniguruma Syntax | JavaScript / Go Syntax |
|---|---|---|---|
| **Named capture group** | `(?P<name>pattern)` | `(?<name>pattern)` or `(?'name'pattern)` | `(?<name>pattern)` |
| **Non-capturing group** | `(?:pattern)` | `(?:pattern)` | `(?:pattern)` |
| **Negative lookahead** | `(?!pattern)` | `(?!pattern)` | `(?!pattern)` |
| **Positive lookahead** | `(?=pattern)` | `(?=pattern)` | `(?=pattern)` |
| **Case-insensitivity** | `re.IGNORECASE` | `(?i)` flag | `i` flag |

> **Key Rule in LogLens:** Always use the Python standard syntax `(?P<name>...)` for your custom capture groups when running `--regex`.

---

## 3. Dissecting the Built-in Presets

### A. Nginx & Apache Combined Format
```regex
^(?P<ip>\S+) \S+ (?P<user>\S+) \[(?P<time>[^\]]+)\] "(?P<method>[A-Z]+) (?P<path>\S+) (?P<protocol>[^"]+)" (?P<status>\d{3}) (?P<size>\d+|-) "(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)"$
```

Let's break down each regex element:

1. `^`: Anchor matching the start of the string.
2. `(?P<ip>\S+)`: Matches one or more non-whitespace characters (`\S+`), assigned to column `ip`.
3. ` \S+ `: Matches a space, followed by the RFC 1413 identd identity (often `-`), followed by a space. Not captured.
4. `(?P<user>\S+)`: Captures the HTTP authenticated user (or `-`).
5. `\[(?P<time>[^\]]+)\]`:
   - `\[` and `\]`: Escaped literal brackets.
   - `[^\]]+`: Negated character class matching everything up to the closing `]`. Captured as `time`.
6. `" `: Literal quote and space beginning the request line.
7. `(?P<method>[A-Z]+)`: Captures HTTP verb (`GET`, `POST`, `PUT`, `DELETE`).
8. `(?P<path>\S+)`: Captures the URI path (e.g. `/index.html`, `/api/v1/users`).
9. `(?P<protocol>[^"]+)`: Captures protocol version (`HTTP/1.1`, `HTTP/2.0`).
10. `" `: Closing quote and space.
11. `(?P<status>\d{3})`: Exactly 3 digits (`\d{3}`) representing HTTP response code (`200`, `404`, `500`).
12. `(?P<size>\d+|-)`: Alternation matching either digits (`\d+`) or a dash (`-`) for zero bytes.
13. `"(?P<referrer>[^"]*)"`: Zero or more non-quote characters inside quotes.
14. `"(?P<user_agent>[^"]*)"`: Zero or more non-quote characters inside quotes.
15. `$`: Anchor matching the end of the line.

---

### B. Syslog RFC 3164 Format
```regex
^(?P<time>\w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2}) (?P<host>\S+) (?P<process>[^\[:]+)(?:\[(?P<pid>\d+)\])?: (?P<message>.*)$
```

1. `(?P<time>\w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2})`:
   - `\w{3}`: 3-letter month (`Oct`, `Nov`, `Dec`).
   - `\s+`: One or two spaces (days 1-9 have leading space in syslog).
   - `\d{1,2}`: Day of month.
   - `\d{2}:\d{2}:\d{2}`: Hour, minute, second.
2. `(?P<host>\S+)`: Logging machine hostname.
3. `(?P<process>[^\[:]+)`: Process name up to a bracket or colon.
4. `(?:\[(?P<pid>\d+)\])?`:
   - The outer `(?:...)?` is an **optional non-capturing group**.
   - The inner `(?P<pid>\d+)` captures the numeric process ID if present.
   - If the syslog line has no PID (e.g. `kernel: [UFW BLOCK]`), LogLens sets `pid = ""`.
5. `: (?P<message>.*)$`: Literal colon-space followed by greedy capture of the rest of the message.

---

### C. Generic Application Log Format
```regex
^(?P<time>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)\s+\[?(?P<level>DEBUG|INFO|WARN(?:ING)?|ERROR|CRITICAL|FATAL)\]?\s+(?P<message>.*)$
```

1. `(?P<time>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)`:
   - `\d{4}-\d{2}-\d{2}`: Year, month, day.
   - `[ T]`: Character class allowing space or ISO 8601 `T`.
   - `\d{2}:\d{2}:\d{2}`: Hour, minute, second.
   - `(?:[.,]\d+)?`: Optional sub-second milliseconds/microseconds.
2. `\[?(?P<level>DEBUG|INFO|WARN(?:ING)?|ERROR|CRITICAL|FATAL)\]?`:
   - `\[?` and `\]?`: Optional surrounding brackets (matches `[INFO]` or `INFO`).
   - `WARN(?:ING)?`: Matches either `WARN` or `WARNING`.
3. `(?P<message>.*)$`: The application log message body.

---

## 4. How `--where` Filters Leverage Regex

LogLens provides filtering over any parsed column. The supported operators are:

| Operator | Type | Description |
|---|---|---|
| `=` | String / Numeric | Case-insensitive equality (`row[col].lower() == val.lower()`) |
| `!=` | String / Numeric | Case-insensitive inequality |
| `>` `<` `>=` `<=` | Numeric / String | Mathematical comparison if both sides are numbers, else lexical |
| `~` | **Regex Search** | Evaluates `re.search(val, row[col], re.IGNORECASE)` |

### Using the `~` Regex Operator
Because `~` invokes Python's regex engine, you can use full regex patterns inside your filter:

```bash
# Match paths starting with /api/v1 or /api/v2
loglens access.log --preset nginx --where "path~^/api/v[12]/"

# Find messages containing either "timeout" or "refused"
loglens app.log --preset generic --where "message~timeout|refused"

# Match IPs in the 192.168.1.0/24 subnet
loglens access.log --preset nginx --where "ip~^192\.168\.1\."
```

### Numerical Comparison Advantage
In standard `grep` or text tools, `"1000"` is alphabetically *smaller* than `"500"` because `'1' < '5'`.
In LogLens, `--where "status>=500"` or `--where "size>1048576"` automatically detects numbers and compares them **mathematically**.

---

## 5. Unmatched Lines & Strict Anchoring

Why do presets use `^` and `$`?

```
Line in file:
192.168.1.99 - - "BAD_REQUEST_NO_TIMESTAMP" 400
```

If the preset did not have `^` and `$`, a partial match might extract pieces of this garbage line and create a broken table row.
Because of strict anchors:
1. The regex engine fails to match the entire line.
2. `parser.parse_lines()` yields `(None, raw_line)`.
3. The unmatched line counter increments.
4. When you pass `--show-unmatched`, LogLens displays the raw line alongside its 1-based line number in the original file.

---

## 6. How `--suggest` Builds Regexes Automatically

When you run `loglens --suggest "<sample line>"`, LogLens acts as a rule-based regex compiler:

1. **Left-to-Right Token Scanner:** It inspects character sequences in the sample log.
2. **Priority Matcher:**
   - Detects IPv4 addresses (`\d{1,3}(?:\.\d{1,3}){3}`) -> creates group `(?P<ip>...)`
   - Detects Bracketed Timestamps (`\[(?P<time>[^\]]+)\]`)
   - Detects ISO Timestamps (`\d{4}-\d{2}-\d{2}[ T]...`)
   - Detects HTTP Methods (`GET`, `POST`, etc.) -> creates group `(?P<method>...)`
   - Detects URL Paths (`/path...`) -> creates group `(?P<path>...)`
   - Detects HTTP status codes right after quotes -> creates group `(?P<status>\d{3})`
   - Detects remaining numbers -> creates groups `(?P<num1>\d+)`, `(?P<num2>\d+)`
   - Escapes remaining literals via `re.escape()`
3. **Verification Step:** Before printing, LogLens runs `re.compile(generated_regex).match(sample)`. If the suggested pattern does not match the sample line, it falls back to `^(?P<line>.*)$`.

---

## 7. Writing Custom Regex Patterns for Real-World Logs

Here are copy-pasteable regex recipes for common custom logs:

### Spring Boot / Java Logs
```text
2025-10-10 13:55:36.789 [http-nio-8080-exec-1] INFO  c.e.service.UserService - User 1042 logged in
```
**LogLens Command:**
```bash
loglens app.log --regex "^(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+\[(?P<thread>[^\]]+)\]\s+(?P<level>[A-Z]+)\s+(?P<logger>\S+)\s+-\s+(?P<message>.*)$"
```

### Key-Value / Logfmt Format
```text
ts=2025-10-10T13:55:36Z level=info method=GET path=/metrics status=200 duration=12ms
```
**LogLens Command:**
```bash
loglens app.log --regex "^ts=(?P<time>\S+)\s+level=(?P<level>\S+)\s+method=(?P<method>\S+)\s+path=(?P<path>\S+)\s+status=(?P<status>\d+)\s+duration=(?P<duration>\S+)$"
```

### Envoy / Kubernetes Ingress Log
```text
[2025-10-10T13:55:36.123Z] "GET /api HTTP/1.1" 200 - 120 452 15 14 "-" "curl/7.68.0" "internal-service"
```
**LogLens Command:**
```bash
loglens envoy.log --regex "^\[(?P<time>[^\]]+)\] \"(?P<method>[A-Z]+) (?P<path>\S+) [^\"]+\" (?P<status>\d{3}) - (?P<bytes_sent>\d+) (?P<bytes_received>\d+) (?P<duration>\d+)"
```

---

## Summary Checklist for Regex Users

1. **Named Groups:** `(?P<name>pattern)` creates a column.
2. **Column Names:** Alphanumeric + underscore: `(?P<client_ip>\S+)`.
3. **Optional Content:** Wrap in `(?:...)?` to avoid blank column warnings.
4. **Testing Regex:** Use `loglens --suggest "<sample>"` to get a starting pattern, then refine it.
5. **Searching Inside Groups:** Use `--where "column~regex_pattern"`.
