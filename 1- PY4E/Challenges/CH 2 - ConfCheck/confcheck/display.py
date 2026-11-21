"""
Formatting and terminal rendering module using rich.
"""

from typing import Any, Dict, List, Optional
import sys
from rich.console import Console
from rich.table import Table

from confcheck.models import Entry, Issue


def print_issues(issues: List[Issue], filename: str, file=None) -> None:
    """
    Print issues in standard compiler-compatible format:
        <file>:<line>: <severity> <code>: <message>
    For line 0 (missing required keys), omit line number:
        <file>: <severity> <code>: <message>
    """
    if file is None:
        file = sys.stderr
    for iss in issues:
        if iss.line > 0:
            print(f"{filename}:{iss.line}: {iss.severity} {iss.code}: {iss.message}", file=file)
        else:
            print(f"{filename}: {iss.severity} {iss.code}: {iss.message}", file=file)


def show_table(
    typed_data: Dict[str, Dict[str, Any]],
    raw_sections: Dict[str, Dict[str, Entry]],
    console: Optional[Console] = None,
) -> None:
    """
    Display configuration entries in a Rich table.

    Columns: Section | Key | Type | Value | Line
    Long values truncated to 50 characters.
    Lists formatted as [a, b, c].
    """
    if console is None:
        console = Console()

    table = Table(title="Configuration Entries", header_style="bold magenta")
    table.add_column("Section", style="bold cyan")
    table.add_column("Key", style="bold")
    table.add_column("Type", justify="center")
    table.add_column("Value")
    table.add_column("Line", justify="right")

    for sec_name, keys in typed_data.items():
        for key_name, val in keys.items():
            type_name = type(val).__name__

            if isinstance(val, list):
                val_str = "[" + ", ".join(str(x) for x in val) + "]"
            elif isinstance(val, bool):
                val_str = str(val).lower()
            else:
                val_str = str(val)

            if len(val_str) > 50:
                val_str = val_str[:47] + "..."

            # Line number from original entry if present
            line_no = "-"
            if sec_name in raw_sections and key_name in raw_sections[sec_name]:
                line_no = str(raw_sections[sec_name][key_name].line)

            table.add_row(sec_name, key_name, type_name, val_str, line_no)

    console.print(table)
