"""Thread-Safe Agent Pool Implementation using queue.Queue and threading."""

import queue
import threading
import time
import random
from typing import Callable, Optional
from database import ThreadSafeDatabase


# Sentinel token used to gracefully terminate worker threads (Poison Pill pattern)
STOP_TOKEN = None


class AgentWorker(threading.Thread):
    """Worker thread representing an individual agent instance in the pool."""

    def __init__(
        self,
        agent_id: int,
        name: str,
        task_queue: queue.Queue,
        db: ThreadSafeDatabase,
        work_fn: Optional[Callable[[dict], str]] = None,
    ):
        super().__init__(name=name, daemon=True)
        self.agent_id = agent_id
        self.agent_name = name
        self.task_queue = task_queue
        self.db = db
        self.work_fn = work_fn or self._default_work

    def _default_work(self, task: dict) -> str:
        """Simulate autonomous agent reasoning, web scraping, and code analysis."""
        payload = task["payload"]
        # Simulate variable workload (0.1 to 0.4 seconds)
        duration = random.uniform(0.1, 0.4)
        time.sleep(duration)
        
        # Simulate potential edge-case transient failure on specific payloads
        if "error" in payload.lower():
            raise ValueError(f"Agent {self.agent_name} encountered an unrecoverable payload error.")
            
        return f"Processed '{payload}' by {self.agent_name} in {duration:.2f}s"

    def run(self):
        while True:
            try:
                # Wait for next available task
                task = self.task_queue.get(timeout=3.0)
            except queue.Empty:
                # Idle check; continue waiting
                continue

            # Poison pill received: signal to cleanly exit thread loop
            if task is STOP_TOKEN:
                self.task_queue.task_done()
                break

            task_id = task["task_id"]
            start_time = time.perf_counter()
            self.db.record_task_start(task_id, self.agent_name)

            try:
                result_str = self.work_fn(task)
                duration = time.perf_counter() - start_time
                self.db.record_task_completion(task_id, self.agent_name, "SUCCESS", result_str, duration)
            except Exception as e:
                duration = time.perf_counter() - start_time
                self.db.record_task_completion(task_id, self.agent_name, "FAILED", str(e), duration)
            finally:
                self.task_queue.task_done()


class AgentPool:
    """Manages a pool of concurrent agent threads, task distribution, and graceful shutdown."""

    def __init__(self, size: int = 5, db_path: str = "agent_pool.db"):
        self.size = size
        self.task_queue = queue.Queue()
        self.db = ThreadSafeDatabase(db_path)
        self.workers: list[AgentWorker] = []
        self._spawn_workers()

    def _spawn_workers(self):
        roles = ["Researcher-Agent", "Analyst-Agent", "Coder-Agent", "Writer-Agent", "Reviewer-Agent"]
        for i in range(self.size):
            name = roles[i % len(roles)] + f"-{i+1}"
            worker = AgentWorker(
                agent_id=i + 1,
                name=name,
                task_queue=self.task_queue,
                db=self.db,
            )
            self.workers.append(worker)
            worker.start()

    def submit_task(self, task_id: int, task_name: str, payload: str):
        self.task_queue.put({
            "task_id": task_id,
            "task_name": task_name,
            "payload": payload,
        })

    def wait_completion(self):
        """Block until all tasks in the queue have been processed."""
        self.task_queue.join()

    def shutdown(self):
        """Broadcast poison pills to all workers and join threads."""
        for _ in self.workers:
            self.task_queue.put(STOP_TOKEN)
        for worker in self.workers:
            worker.join(timeout=2.0)
