# Chapter 1: Regular Expressions for Agentic AI 🔍

> **Roadmap Alignment:** Days 1–2 (Ch 11: Regex Basics & Regex Advanced)  
> **Primary Goals:** Master string matching, tokenization, greedy vs. non-greedy extraction, named capture groups, and structured entity parsing from raw unstructured text.

---

## 🧠 Why Regex is Critical in Agentic AI

In modern AI engineering, LLMs generate natural language mixed with code fences, JSON blocks, citation tags, and tool calls. A production AI Agent relies heavily on regex to:
1. **Extract Tool Calls:** Isolate `<tool_call>{"tool": "name", "args": {...}}</tool_call>` blocks from raw model outputs.
2. **Clean Reasoning Traces:** Strip `<think>...</think>` internal chain-of-thought tokens before returning responses to end users.
3. **Parse Semi-Structured Logs:** Analyze server logs (Apache, Nginx, syslog) to diagnose execution failures.
4. **Validate Outputs:** Verify that an agent-generated output satisfies email, URL, or JSON schema formats.

---

## 📚 Core Concepts & Metacharacters Reference

| Character | Meaning | Agentic Example |
|---|---|---|
| `^` | Matches beginning of line | `r"^From:"` to detect message sender |
| `$` | Matches end of line | `r"```$"` to detect closing code fence |
| `.` | Any character (except newline) | `r"tool: .*"` match tool description |
| `*` | 0 or more occurrences (Greedy) | `r"\s*"` match optional whitespace |
| `*?` | 0 or more occurrences (Non-greedy) | `r"<think>(.*?)</think>"` extract thought content |
| `+` | 1 or more occurrences (Greedy) | `r"\d+"` match numeric ID or token count |
| `+?` | 1 or more occurrences (Non-greedy) | `r'\{"tool":.*?\}(?=\s|$)'` isolate JSON object |
| `\s` | Any whitespace character | `r"\s+"` tokenize whitespace |
| `\S` | Any non-whitespace character | `r"\S+@\S+"` extract email pattern |
| `[a-z0-9]` | Character set / range | Match alphanumeric identifiers |
| `()` | Capture group (extracts substring) | `r"^From: (\S+@\S+)"` extracts email only |
| `(?P<name>...)` | Named capture group | `r"(?P<ip>\d{1,3}(?:\.\d{1,3}){3})"` |

---

## 📖 Dr. Chuck's Official Study Resources

Before diving into code, review Dr. Charles Severance's lecture slides and study guides located in [`Content/By Dr.Chuck/`](Content/By%20Dr.Chuck):
- 📄 [**Pythonlearn-11-Regex.pdf**](Content/By%20Dr.Chuck/1-%20Pythonlearn-11-Regex.pdf) — Complete lecture slide deck covering regular expressions, metacharacters, and extraction patterns.
- 📝 [**Python_Regex_Guide.docx**](Content/By%20Dr.Chuck/1-%20Python_Regex_Guide.docx) — Dr. Chuck's quick-reference guide and syntax summary.
- 📓 [**Notes.md**](Content/Notes.md) — Comprehensive chapter lecture summary.

---

## 📂 Chapter Contents & Structure

```text
C1 # Regular Expressions/
├── Content/
│   ├── Notes.md                     <-- Core theoretical notes on regex
│   └── By Dr.Chuck/                 <-- Dr. Chuck's lecture slides (PDF) & study guide (DOCX)
├── Source Code/
│   ├── practice/                    <-- Micro-practice scripts (p1.py - p13.py)
│   └── Project/                     <-- Chapter Capstone Project
│       ├── code.py                  <-- OOP-driven email & DSPAM log parser
│       └── mini-box.txt             <-- Sample mail log dataset
├── README.md                        <-- You are here (Chapter Overview)
└── STEP_BY_STEP_GUIDE.md            <-- Step-by-step implementation guide
```

---

## 🏃 Practice Scripts Quick Walkthrough (`practice/`)

The `Source Code/practice/` directory contains 13 progressive micro-exercises:
- **`p1.py` – `p4.py`:** Exploring basic `re.search()` vs string `.find()`, line prefix matching with `^`.
- **`p5.py` – `p8.py`:** Greedy vs non-greedy matching (`^F.+?:` vs `^F.+?:?`), character ranges `[0-9]+`.
- **`p9.py` – `p11.py`:** `re.findall()` for extraction, extracting emails from headers and sentences.
- **`p12.py` – `p13.py`:** Combining parenthesis `()` for selective extraction, extracting domain names (`@([^ ]*)`).

---

## 🏆 Chapter Project: Structured Mail Log Parser

Located in [`Source Code/Project/code.py`](Source%20Code/Project/code.py).

This project takes raw server email headers (`mini-box.txt`) and parses them into an Object-Oriented data model:
- `Email`: Extracts username and host domain.
- `DateDetails`: Extracts day of week, month, date, timestamp, and year.
- `Score` (`CScore`, `PScore`): Extracts DSPAM confidence and probability metrics.
- `PLogsList`: Provides CRUD operations (`create`, `readByPerson`, `delete`, `displayAll`).

👉 For full building instructions, read the [**Step-by-Step Implementation Guide**](STEP_BY_STEP_GUIDE.md).
