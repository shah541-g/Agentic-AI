# Practice Tasks Hub (PT 1 – PT 3) 🧪

> **Roadmap Phase:** Days 14–16 (Practice Tasks Phase)  
> **Philosophy:** Focused, standalone software engineering tasks designed to test extraction, concurrency, and dynamic tool invocation without high-level agent frameworks.

---

## 🧭 Overview & Progression

```mermaid
flowchart LR
    PT1["PT 1: EmailHarvester\n(Regex Extraction & Grouping)"] --> PT2["PT 2: FeedFuse\n(Async Multi-API Aggregator)"]
    PT2 --> PT3["PT 3: ToolForge\n(Dynamic OOP Tool Calling)"]

    style PT1 fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#ffffff
    style PT2 fill:#0f172a,stroke:#4ade80,stroke-width:2px,color:#ffffff
    style PT3 fill:#0f172a,stroke:#fb923c,stroke-width:2px,color:#ffffff
```

---

## 📊 Practice Tasks Comparison Matrix

| Project | Location | Day | Key Technologies | Real-World Utility |
|---|---|---|---|---|
| **EmailHarvester** | [`PT 1 - EmailHarvester/`](PT%201%20-%20EmailHarvester) | Day 14 | Regex, Domain parsing, Case-insensitive deduplication, Multi-format exports | Extracts and deduplicates contact directories from unstructured communication data. |
| **FeedFuse** | [`PT 2 - FeedFuse/`](PT%202%20-%20FeedFuse) | Day 15 | `asyncio`, `httpx.AsyncClient`, Dot-notation paths, Secret masking (`${TOKEN}`), Disk TTL cache | Concurrently aggregates slow third-party APIs without crashing on individual timeouts. |
| **ToolForge** | [`PT 3 - ToolForge/`](PT%203%20-%20ToolForge) | Day 16 | Dynamic OOP Tool Hierarchy, `ToolBox`, ReAct Execution Loop, Custom XML Tag Parser | Powers autonomous agents with tool-calling abilities (Web Search, File Ops, Project Memory). |

---

## 📂 Sub-Projects Overview

- 📧 [**PT 1: EmailHarvester**](PT%201%20-%20EmailHarvester): Modular regex engine handling complex email variants (subdomains, plus-addressing `user+alias@gmail.com`) and generating structured JSON/CSV/TXT reports.
- ⚡ [**PT 2: FeedFuse**](PT%202%20-%20FeedFuse): Asynchronous REST API integration tool reading YAML task pipelines, executing parallel calls, and merging JSON keys via dot notation.
- 🔨 [**PT 3: ToolForge**](PT%203%20-%20ToolForge): The core engine of agentic tool execution. Provides structured XML tool dispatch (`<tool_call>...<file_content>`), memory persistence, and multi-step reasoning loops.
