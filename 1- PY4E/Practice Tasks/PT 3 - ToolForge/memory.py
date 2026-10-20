"""Long-term memory: ONE user summary + a table of project details.

Nothing here calls an LLM. Retrieval is deterministic:
  - the summary and the project index are always injected into the prompt
  - full project details are fetched by the agent through a tool
"""
import re
import sqlite3
from typing import Any

from logger import get_logger

log = get_logger("memory")

SCHEMA = """
CREATE TABLE IF NOT EXISTS user_summary (
    id          INTEGER PRIMARY KEY CHECK (id = 1),
    summary     TEXT NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS project (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL UNIQUE,
    description  TEXT NOT NULL,   -- one line, shown in the always-on index
    details      TEXT NOT NULL,   -- full details, fetched on demand by a tool
    updated_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""

STOPWORDS = {"the", "a", "an", "of", "for", "to", "and", "in", "on", "my", "is", "it", "with", "about"}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"\w+", text.lower()) if len(t) > 2 and t not in STOPWORDS}


class MemoryStore:
    def __init__(self, path: str = "memory.db"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        log.info("Memory DB opened: %s (%d project(s), summary %s)", path,
                 len(self.project_index()), "present" if self.get_summary() else "empty")

    # ---- summary ---------------------------------------------------------
    def get_summary(self) -> str:
        row = self.conn.execute("SELECT summary FROM user_summary WHERE id = 1").fetchone()
        return row["summary"] if row else ""

    def set_summary(self, summary: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO user_summary (id, summary) VALUES (1, ?) "
                "ON CONFLICT(id) DO UPDATE SET summary = excluded.summary, "
                "updated_at = datetime('now', 'localtime')",
                (summary,),
            )
        log.info("User summary saved (%d chars)", len(summary))
        log.debug("User summary:\n%s", summary)

    # ---- projects --------------------------------------------------------
    def upsert_project(self, name: str, description: str, details: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO project (name, description, details) VALUES (?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET description = excluded.description, "
                "details = excluded.details, updated_at = datetime('now', 'localtime')",
                (name.strip(), description.strip(), details.strip()),
            )
        log.info("Project saved/updated: %s (%d chars of details)", name.strip(), len(details))

    def project_index(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT name, description FROM project ORDER BY name").fetchall()
        return [dict(r) for r in rows]

    def all_projects(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT name, description, details FROM project").fetchall()
        return [dict(r) for r in rows]

    def search_projects(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Keyword-overlap ranking. Swap for embeddings later without touching callers."""
        q = _tokens(query)
        scored = []
        for p in self.all_projects():
            name_tokens = _tokens(p["name"])
            body_tokens = _tokens(p["description"] + " " + p["details"])
            score = 3 * len(q & name_tokens) + len(q & body_tokens)
            if score > 0:
                scored.append((score, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:limit]]