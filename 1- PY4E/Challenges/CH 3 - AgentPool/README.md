# CH 3: Thread-Safe Multi-Worker Agent Pool 🧵⚡

> **Target Directory:** [`Challenges/CH 3 - AgentPool/`](Readme.md)  
> **Roadmap Alignment:** Day 19 (Commit Target: `m0-ch03-agent-pool/`)  
> **Key Architecture:** Thread-Safe Worker Pool, `queue.Queue` Task Buffering, Mutex-Protected SQLite Storage, Poison Pill Graceful Termination, and Deadlock Prevention.

---

## 🧭 System Overview

In production multi-agent systems, agents cannot run sequentially on a single thread—doing so leaves multicore CPUs idle and creates unacceptable latency. However, running agents across multiple OS threads introduces dangerous concurrency challenges:
1. **Race Conditions:** Two threads modifying the same data structure simultaneously.
2. **SQLite Locking Errors:** SQLite throws `sqlite3.OperationalError: database is locked` when multiple threads attempt concurrent writes without synchronization.
3. **Deadlocks:** Threads waiting on each other indefinitely due to unmanaged queue contention.

**CH 3: AgentPool** implements a production-grade, thread-safe agent worker pool. It spins up 5 concurrent daemon agent workers, distributes 20 heterogeneous tasks through a thread-safe `queue.Queue`, records metrics in SQLite with Write-Ahead Logging (WAL) and mutex locking, and handles graceful termination using the Poison Pill pattern.

---

## 🏛️ Thread Pool Architecture

```mermaid
flowchart TD
    Tasks["20 Heterogeneous Tasks\n(Research, Coding, Analysis, Security)"] --> Queue["queue.Queue(FIFO)\nThread-Safe Task Buffer"]
    
    subgraph Pool["Agent Worker Pool (5 Concurrent Threads)"]
        W1["Agent 1: Researcher"]
        W2["Agent 2: Analyst"]
        W3["Agent 3: Coder"]
        W4["Agent 4: Writer"]
        W5["Agent 5: Reviewer"]
    end

    Queue -->|get()| W1
    Queue -->|get()| W2
    Queue -->|get()| W3
    Queue -->|get()| W4
    Queue -->|get()| W5

    subgraph Storage["ThreadSafeDatabase (WAL + Lock)"]
        DB[("SQLite: agent_pool.db\npool_tasks & agent_metrics")]
    end

    W1 -->|Thread Lock| DB
    W2 -->|Thread Lock| DB
    W3 -->|Thread Lock| DB
    W4 -->|Thread Lock| DB
    W5 -->|Thread Lock| DB

    style Pool fill:none,stroke:#a78bfa,stroke-width:2px,stroke-dasharray: 4 4
    style Storage fill:none,stroke:#22c55e,stroke-width:2px,stroke-dasharray: 4 4

    style Tasks fill:#0f172a,stroke:#f87171,stroke-width:2px,color:#ffffff
    style Queue fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#ffffff
    style W1 fill:#0f172a,stroke:#c084fc,stroke-width:1.5px,color:#ffffff
    style W2 fill:#0f172a,stroke:#c084fc,stroke-width:1.5px,color:#ffffff
    style W3 fill:#0f172a,stroke:#c084fc,stroke-width:1.5px,color:#ffffff
    style W4 fill:#0f172a,stroke:#c084fc,stroke-width:1.5px,color:#ffffff
    style W5 fill:#0f172a,stroke:#c084fc,stroke-width:1.5px,color:#ffffff
    style DB fill:#0f172a,stroke:#4ade80,stroke-width:2px,color:#ffffff
```

---

## 📂 Project Structure

```text
CH 3 - AgentPool/
├── pool.py                          <-- AgentWorker thread & AgentPool orchestrator
├── database.py                      <-- Thread-safe SQLite manager (WAL mode + Mutex lock)
├── main.py                          <-- 20-task execution harness and terminal reporter
├── agent_pool.db                    <-- SQLite database with tasks and agent metrics
├── README.md                        <-- You are here (Project Overview)
└── STEP_BY_STEP_GUIDE.md            <-- Step-by-step build & concurrency tutorial
```

---

## 🏃 Running the Challenge

Run the entry point:

```bash
python main.py
```

### Output:
```text
=================================================================
    CHALLENGE 3: THREAD-SAFE AGENT WORKER POOL (5 AGENTS / 20 TASKS)    
=================================================================
[*] Initialized pool with 5 concurrent daemon agents.
[*] Pre-seeded 20 tasks in 'agent_pool.db'.

[*] Dispatching 20 tasks into queue.Queue()...

[+] All 20 tasks processed in 1.54 seconds.
[+] Agent pool shut down cleanly.

=================================================================
                  AGENT PERFORMANCE METRICS                     
=================================================================
Agent Name                | Completed  | Failed   | Total Time (s)
-----------------------------------------------------------------
Analyst-Agent-2           | 4          | 0        | 1.04          
Coder-Agent-3             | 4          | 0        | 1.08          
Researcher-Agent-1        | 4          | 0        | 1.36          
Reviewer-Agent-5          | 4          | 0        | 1.37          
Writer-Agent-4            | 3          | 1        | 1.16          
```

👉 For a comprehensive engineering guide on thread synchronization, race condition avoidance, and SQLite WAL configuration, read [**STEP_BY_STEP_GUIDE.md**](STEP_BY_STEP_GUIDE.md).
