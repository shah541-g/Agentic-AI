"""Central logging setup.

Console : short, readable INFO lines (what is happening right now).
File    : logs/agent.log with full DEBUG detail (prompts, tool results, timings).
Set LOG_LEVEL=DEBUG in .env to see the detail on the console too.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_ROOT = "agent"


def _setup() -> None:
    root = logging.getLogger(_ROOT)
    if root.handlers:
        return
    root.setLevel(logging.DEBUG)
    root.propagate = False

    console_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(console_level)
    console.setFormatter(logging.Formatter("%(asctime)s | %(name)-10s | %(message)s", "%H:%M:%S"))
    root.addHandler(console)

    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / "agent.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)-10s | %(message)s")
    )
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    _setup()
    return logging.getLogger(f"{_ROOT}.{name}")


def clip(text: str, limit: int = 300) -> str:
    """One-line, length-limited version of a string for log messages."""
    flat = " ".join(str(text).split())
    return flat if len(flat) <= limit else flat[:limit] + f"... [+{len(flat) - limit} chars]"