"""
Data models for ConfCheck parsed configuration, issues, and schema rules.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Entry:
    """Represents a single parsed key-value entry in a section."""
    section: str
    key: str
    raw: str          # final logical value text (comments removed, continuations joined)
    block: bool       # True for the "key =" + indented lines list form
    line: int         # line number of the key


@dataclass
class Issue:
    """Represents a syntax error, validation error, or warning."""
    code: str
    severity: str     # "error" | "warning"
    line: int         # 0 when not tied to a line (e.g. E101)
    message: str


@dataclass
class ParseResult:
    """Result of parsing configuration text."""
    sections: Dict[str, Dict[str, Entry]]   # insertion-ordered
    issues: List[Issue]


@dataclass
class Rule:
    """Validation rule parsed from schema."""
    type: str                         # "str" | "int" | "bool" | "list"
    item_type: Optional[str] = None   # for list: str, int, bool
    required: bool = False
    has_default: bool = False
    default: Any = None               # already converted to target type
    min: Optional[int] = None
    max: Optional[int] = None
    choices: Optional[List[str]] = None


Schema = Dict[str, Dict[str, Rule]]
