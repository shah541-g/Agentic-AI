"""
Terminal formatting via rich and data export to JSON/CSV.
"""

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table

from feedfuse.models import SourceResult


def show_status_table(results: List[SourceResult], console: Optional[Console] = None) -> None:
    """
    Display a summary status table for all fetched sources.

    Columns: Source | State | Time | Notes
    Colors: ok (green), cached (cyan), timeout (yellow), failed (red).
    """
    if console is None:
        console = Console()

    table = Table(title="Sources Status", header_style="bold magenta")
    table.add_column("Source", style="bold")
    table.add_column("State", justify="center")
    table.add_column("Time", justify="right")
    table.add_column("Notes")

    for res in results:
        # State styling
        if res.state == "ok":
            state_text = "[bold green]ok[/bold green]"
        elif res.state == "cached":
            state_text = "[bold cyan]cached[/bold cyan]"
        elif res.state == "timeout":
            state_text = "[bold yellow]timeout[/bold yellow]"
        else:  # failed
            state_text = "[bold red]failed[/bold red]"

        time_text = f"{res.ms}ms"

        # Notes (error or warnings)
        notes = []
        if res.error:
            notes.append(f"[red]{res.error}[/red]")
        if res.warnings:
            notes.append(f"[yellow]{'; '.join(res.warnings)}[/yellow]")
        notes_text = " | ".join(notes) if notes else "[dim]none[/dim]"

        table.add_row(res.name, state_text, time_text, notes_text)

    console.print(table)


def show_combined(merged: Dict[str, Any], console: Optional[Console] = None) -> None:
    """
    Display one rich table per successful source in combine mode.
    """
    if console is None:
        console = Console()

    data = merged.get("data", {})
    if not data:
        console.print("[yellow]No data returned from any source.[/yellow]")
        return

    for source_name, payload in data.items():
        table = Table(title=f"Source: {source_name}", header_style="bold cyan")
        table.add_column("Field", style="bold")
        table.add_column("Value")

        if isinstance(payload, dict):
            for k, v in payload.items():
                val_str = str(v) if v is not None else "[dim]null[/dim]"
                table.add_row(k, val_str)
        else:
            table.add_row("value", str(payload))

        console.print(table)


def show_joined(rows: List[Dict[str, Any]], limit: int = 50, console: Optional[Console] = None) -> None:
    """
    Display a single table for joined records.
    """
    if console is None:
        console = Console()

    if not rows:
        console.print("[yellow]No joined rows to display.[/yellow]")
        return

    # Collect unique columns in order
    all_cols = []
    for r in rows:
        for k in r.keys():
            if k not in all_cols:
                all_cols.append(k)

    table = Table(title=f"Joined Records ({len(rows)} total)", header_style="bold cyan")
    for col in all_cols:
        table.add_column(col)

    for row in rows[:limit]:
        row_cells = []
        for col in all_cols:
            val = row.get(col)
            val_str = str(val) if val is not None else "[dim]null[/dim]"
            if len(val_str) > 40:
                val_str = val_str[:37] + "..."
            row_cells.append(val_str)
        table.add_row(*row_cells)

    console.print(table)
    if len(rows) > limit:
        console.print(f"[dim]Showing first {limit} of {len(rows)} rows[/dim]\n")


def export(merged: Dict[str, Any], path: str) -> None:
    """
    Export merged results to JSON or CSV.

    Args:
        merged: Combined or joined result dict.
        path: Destination file path (.json or .csv).

    Raises:
        ValueError: If file extension is not .json or .csv.
    """
    lower = path.lower()
    if not (lower.endswith(".json") or lower.endswith(".csv")):
        raise ValueError(f"Unsupported output format for '{path}'. Only .json and .csv are supported.")

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if lower.endswith(".json"):
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
        return

    # CSV Export
    data = merged.get("data")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        if isinstance(data, list):
            # Joined mode
            if not data:
                return
            # Collect unique field names
            fieldnames = []
            for r in data:
                if isinstance(r, dict):
                    for k in r.keys():
                        if k not in fieldnames:
                            fieldnames.append(k)
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                if isinstance(row, dict):
                    writer.writerow(row)
        elif isinstance(data, dict):
            # Combine mode: columns source, field, value
            writer = csv.DictWriter(f, fieldnames=["source", "field", "value"])
            writer.writeheader()
            for source_name, payload in data.items():
                if isinstance(payload, dict):
                    for field_name, val in payload.items():
                        writer.writerow({
                            "source": source_name,
                            "field": field_name,
                            "value": val if val is not None else "",
                        })
                else:
                    writer.writerow({
                        "source": source_name,
                        "field": "value",
                        "value": payload if payload is not None else "",
                    })
