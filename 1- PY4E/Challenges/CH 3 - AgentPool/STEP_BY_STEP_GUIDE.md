# Step-by-Step Guide: Building a Thread-Safe Agent Worker Pool 🛠️

> **Target Directory:** [`Challenges/CH 3 - AgentPool/`](README.md)  
> **Key Objective:** Build a robust multi-threaded worker pool executing 20 tasks concurrently across 5 agents with deadlock prevention and thread-safe SQLite persistence.

---

## 🏗️ Step 1: Solving SQLite Concurrency (`database.py`)

### The Problem
SQLite does not permit concurrent writes from multiple threads over the same connection. Attempting to write from multiple threads results in `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread` or `database is locked`.

### The Solution: Mutex Lock + Write-Ahead Logging (WAL)
1. **WAL Mode:** Enables readers not to block writers and writers not to block readers.
2. **`threading.Lock()`:** Serializes database write operations across threads safely.

```python
import sqlite3
import threading

class ThreadSafeDatabase:
    def __init__(self, db_path: str = "agent_pool.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        # check_same_thread=False allows sharing if synchronized by lock
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def record_task_completion(self, task_id: int, agent_name: str, status: str, result: str, duration: float):
        with self._lock:  # Mutex ensures exactly ONE thread writes at a time
            with self._get_connection() as conn:
                conn.execute(
                    """
                    UPDATE pool_tasks 
                    SET status = ?, result = ?, duration_seconds = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE task_id = ?
                    """,
                    (status, result, duration, task_id)
                )
```

---

## 🏗️ Step 2: The Agent Worker Thread & Poison Pill Pattern (`pool.py`)

### What is a Poison Pill?
To shut down worker threads cleanly without forcibly killing them (which could corrupt files or leave database locks dangling), we put a sentinel token `None` into the queue. When a worker receives `None`, it exits its `while True` loop gracefully.

```python
import queue
import threading
import time

STOP_TOKEN = None

class AgentWorker(threading.Thread):
    def __init__(self, agent_id: int, name: str, task_queue: queue.Queue, db):
        super().__init__(name=name, daemon=True)
        self.agent_name = name
        self.task_queue = task_queue
        self.db = db

    def run(self):
        while True:
            try:
                task = self.task_queue.get(timeout=2.0)
            except queue.Empty:
                continue

            # Check for poison pill termination signal
            if task is STOP_TOKEN:
                self.task_queue.task_done()
                break

            task_id = task["task_id"]
            start_time = time.perf_counter()
            self.db.record_task_start(task_id, self.agent_name)

            try:
                # Execute work
                result = f"Task completed by {self.agent_name}"
                duration = time.perf_counter() - start_time
                self.db.record_task_completion(task_id, self.agent_name, "SUCCESS", result, duration)
            except Exception as e:
                duration = time.perf_counter() - start_time
                self.db.record_task_completion(task_id, self.agent_name, "FAILED", str(e), duration)
            finally:
                # Mark task as processed in queue
                self.task_queue.task_done()
```

---

## 🏗️ Step 3: Managing the Pool (`pool.py`)

The `AgentPool` spawns $N$ workers and coordinates dispatch and shutdown:

```python
class AgentPool:
    def __init__(self, size: int = 5, db_path: str = "agent_pool.db"):
        self.size = size
        self.task_queue = queue.Queue()
        self.db = ThreadSafeDatabase(db_path)
        self.workers = []
        for i in range(size):
            worker = AgentWorker(i + 1, f"Agent-{i+1}", self.task_queue, self.db)
            self.workers.append(worker)
            worker.start()

    def submit_task(self, task_id: int, task_name: str, payload: str):
        self.task_queue.put({"task_id": task_id, "task_name": task_name, "payload": payload})

    def wait_completion(self):
        # Blocks until every item in queue has had .task_done() called
        self.task_queue.join()

    def shutdown(self):
        # Broadcast one poison pill per worker
        for _ in self.workers:
            self.task_queue.put(STOP_TOKEN)
        for worker in self.workers:
            worker.join(timeout=2.0)
```

---

## 🏗️ Step 4: Dispatching 20 Tasks & Measuring Performance (`main.py`)

In `main.py`, seed 20 tasks, dispatch them into the pool, and time the total throughput:

```python
def main():
    pool = AgentPool(size=5)
    
    # Pre-seed tasks
    tasks = [(i + 1, f"Task-{i+1}", f"Simulate processing item {i+1}") for i in range(20)]
    pool.db.seed_tasks(tasks)

    # Dispatch concurrently
    for t_id, name, payload in tasks:
        pool.submit_task(t_id, name, payload)

    # Await all workers
    pool.wait_completion()
    pool.shutdown()

    # Display metrics
    for m in pool.db.get_summary():
        print(f"Agent {m['agent_name']}: {m['tasks_completed']} completed in {m['total_runtime']:.2f}s")

if __name__ == "__main__":
    main()
```

---

## 💡 Key Concurrency Lessons for AI Engineers

1. **`queue.Queue` is Inherently Thread-Safe:** Python's `queue.Queue` internally manages condition variables (`threading.Condition`), eliminating the need to manually write mutex locks around `.get()` and `.put()`.
2. **Never Call `worker.kill()`:** Python threads cannot be safely killed from the outside. Always use the cooperative Poison Pill pattern so workers finish ongoing file writes or database transactions before exiting.
3. **Deadlock Avoidance Rule:** If a thread acquires Lock A, it must never try to acquire Lock B unless there is a strictly enforced global lock ordering across the entire system.
