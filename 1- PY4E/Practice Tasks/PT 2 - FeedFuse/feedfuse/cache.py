"""
Disk-based response caching with TTL.
"""

import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, Optional


def make_key(url: str, params: Dict[str, Any], headers: Dict[str, str]) -> str:
    """
    Generate SHA-256 hash key from URL, sorted params, and sorted headers.

    Secrets present in headers or params are securely hashed and never stored in plain text.
    """
    hasher = hashlib.sha256()
    hasher.update(url.encode("utf-8"))

    # Sort params and headers to ensure deterministic keys
    sorted_params = sorted((str(k), str(v)) for k, v in params.items())
    sorted_headers = sorted((str(k).lower(), str(v)) for k, v in headers.items())

    hasher.update(json.dumps(sorted_params, sort_keys=True).encode("utf-8"))
    hasher.update(json.dumps(sorted_headers, sort_keys=True).encode("utf-8"))
    return hasher.hexdigest()


class Cache:
    """Simple JSON-file disk cache with TTL."""

    def __init__(self, ttl_seconds: int, directory: Optional[Path] = None):
        self.ttl = ttl_seconds
        if directory is None:
            self.dir = Path.home() / ".cache" / "feedfuse"
        else:
            self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    def get(self, key: str) -> Any | None:
        """
        Retrieve raw response payload if cached and not expired.

        Returns None if cache is missing, expired, or corrupted.
        """
        path = self._file_path(key)
        if not path.is_file():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            saved_at = data.get("saved_at", 0)
            if time.time() - saved_at > self.ttl:
                # Expired: delete and return None
                try:
                    path.unlink()
                except OSError:
                    pass
                return None
            return data.get("payload")
        except Exception:
            # Corrupted file: clean up and return None
            try:
                path.unlink()
            except OSError:
                pass
            return None

    def set(self, key: str, value: Any) -> None:
        """Store raw response payload with current timestamp."""
        path = self._file_path(key)
        record = {
            "saved_at": time.time(),
            "payload": value,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False)
        except Exception:
            # Silently ignore write failures (e.g. disk full or permissions)
            pass
