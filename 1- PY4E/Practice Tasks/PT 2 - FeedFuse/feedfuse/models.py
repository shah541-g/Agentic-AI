"""
Data models for FeedFuse configuration and execution results.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Source:
    """Represents a single API endpoint to fetch."""
    name: str
    url: str
    params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    map: Optional[Dict[str, str]] = None
    records: Optional[str] = None
    timeout: float = 10.0
    retries: int = 2


@dataclass
class SourceResult:
    """Represents the outcome of fetching and mapping a single source."""
    name: str
    state: str                 # "ok" | "cached" | "failed" | "timeout"
    data: Any = None           # mapped data (dict, or list of dicts in join mode)
    ms: int = 0
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class Config:
    """Aggregated configuration parsed from YAML."""
    sources: List[Source]
    merge_mode: str = "combine"
    join_on: Optional[str] = None
    join_type: str = "inner"
