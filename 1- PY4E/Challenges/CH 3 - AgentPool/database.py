"""Thread-safe SQLite database storage for concurrent agent worker pools."""

import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional


class ThreadSafeDatabase:
    """Encapsulates SQLite access with a threading Lock to prevent database locked errors."""

    def __init__(self, db_path: str = "agent_pool.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")  # Write-Ahead Logging for high concurrency
        return conn

    def _init_db(self):
        with self._lock:
            with self._get_connection() as conn:
                conn.executescript("""
                CREATE TABLE IF NOT EXISTS pool_tasks (
                    task_id INTEGER PRIMARY KEY,
                    task_name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    assigned_agent TEXT,
                    status TEXT NOT NULL,
                    result TEXT,
                    duration_seconds REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS agent_metrics (
                    agent_name TEXT PRIMARY KEY,
                    tasks_completed INTEGER DEFAULT 0,
                    tasks_failed INTEGER DEFAULT 0,
                    total_runtime REAL DEFAULT 0.0
                );
                """)

    def record_task_start(self, task_id: int, agent_name: str):
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE pool_tasks SET assigned_agent = ?, status = 'IN_PROGRESS' WHERE task_id = ?",
                    (agent_name, task_id),
                )

    def record_task_completion(
        self,
        task_id: int,
        agent_name: str,
        status: str,
        result: str,
        duration: float,
    ):
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    UPDATE pool_tasks 
                    SET status = ?, result = ?, duration_seconds = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE task_id = ?
                    """,
                    (status, result, duration, task_id),
                )
                if status == "SUCCESS":
                    conn.execute(
                        """
                        INSERT INTO agent_metrics (agent_name, tasks_completed, total_runtime)
                        VALUES (?, 1, ?)
                        ON CONFLICT(agent_name) DO UPDATE SET
                            tasks_completed = tasks_completed + 1,
                            total_runtime = total_runtime + excluded.total_runtime
                        """,
                        (agent_name, duration),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO agent_metrics (agent_name, tasks_failed, total_runtime)
                        VALUES (?, 1, ?)
                        ON CONFLICT(agent_name) DO UPDATE SET
                            tasks_failed = tasks_failed + 1,
                            total_runtime = total_runtime + excluded.total_runtime
                        """,
                        (agent_name, duration),
                    )

    def seed_tasks(self, tasks: list[tuple[int, str, str]]):
        with self._lock:
            with self._get_connection() as conn:
                conn.executemany(
                    "INSERT OR REPLACE INTO pool_tasks (task_id, task_name, payload, status) VALUES (?, ?, ?, 'PENDING')",
                    tasks,
                )

    def get_summary(self) -> list[dict[str, Any]]:
        with self._lock:
            with self._get_connection() as conn:
                rows = conn.execute("SELECT * FROM agent_metrics").fetchall()
                return [dict(r) for r in rows]

    def get_all_tasks(self) -> list[dict[str, Any]]:
        with self._lock:
            with self._get_connection() as conn:
                rows = conn.execute("SELECT * FROM pool_tasks ORDER BY task_id ASC").fetchall()
                return [dict(r) for r in rows]
