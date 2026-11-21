"""
Terminal display and rendering module for LogLens using rich.

Renders parsed logs as formatted tables, unmatched lines in warning panels,
statistical summaries with text bar charts, and regex suggestion previews.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _format_cell_value(key: str, val: Any) -> Text:
    """Format and color a single table cell value based on column name and content."""
    text_val = "" if val is None else str(val)

    # Truncate long cells to 40 characters with ellipsis
    if len(text_val) > 40:
        display_val = text_val[:37] + "..."
    else:
        display_val = text_val

    # Color HTTP status codes
    if key.lower() == "status":
        if text_val.startswith("2"):
            return Text(display_val, style="bold green")
        elif text_val.startswith("3"):
            return Text(display_val, style="cyan")
        elif text_val.startswith("4"):
            return Text(display_val, style="yellow")
        elif text_val.startswith("5"):
            return Text(display_val, style="bold red")

    # Color Log levels
    if key.lower() == "level":
        upper = text_val.upper()
        if upper in {"ERROR", "CRITICAL", "FATAL"}:
            return Text(display_val, style="bold red")
        elif upper in {"WARN", "WARNING"}:
            return Text(display_val, style="bold yellow")
        elif upper == "INFO":
            return Text(display_val, style="green")
        elif upper == "DEBUG":
            return Text(display_val, style="dim")

    return Text(display_val)


def show_table(
    rows: List[Dict[str, str]],
    total_count: int,
    limit: int = 50,
    console: Optional[Console] = None,
) -> None:
    """
    Render parsed rows in a rich table with syntax colors and cell truncation.

    Args:
        rows: Rows to display (up to limit).
        total_count: Total count of matching rows before limit was applied.
        limit: Row display limit.
        console: Optional rich Console instance.
    """
    if console is None:
        console = Console()

    if not rows:
        console.print("[yellow]No matching log entries to display.[/yellow]")
        return

    # Derive column headers from the keys of the first row
    columns = list(rows[0].keys())

    table = Table(
        title="Parsed Logs",
        title_style="bold magenta",
        header_style="bold cyan",
        show_lines=False,
        pad_edge=False,
    )

    for col in columns:
        table.add_column(col)

    for row in rows[:limit]:
        row_cells = [_format_cell_value(col, row.get(col, "")) for col in columns]
        table.add_row(*row_cells)

    console.print(table)
    showing = min(len(rows), limit)
    console.print(f"[dim]Showing {showing} of {total_count} rows[/dim]\n")


def show_unmatched(
    unmatched_lines: List[Tuple[int, str]],
    total_unmatched: int,
    limit: int = 20,
    console: Optional[Console] = None,
) -> None:
    """
    Display lines that failed regex matching inside a red warning panel.

    Args:
        unmatched_lines: List of (line_number, line_content) tuples.
        total_unmatched: Total count of unmatched lines.
        limit: Maximum number of unmatched lines to print.
        console: Optional rich Console instance.
    """
    if console is None:
        console = Console()

    if not unmatched_lines:
        return

    lines_text = []
    for line_num, raw_line in unmatched_lines[:limit]:
        lines_text.append(f"[bold yellow]Line {line_num}:[/bold yellow] {raw_line}")

    if total_unmatched > limit:
        lines_text.append(
            f"\n[dim]... and {total_unmatched - limit} more unmatched lines (showing first {limit})[/dim]"
        )

    panel_content = "\n".join(lines_text)
    panel = Panel(
        panel_content,
        title=f"[bold red]Unmatched Lines ({total_unmatched} total)[/bold red]",
        border_style="red",
        expand=False,
    )
    console.print(panel)


def show_stats(stats: Dict[str, Any], console: Optional[Console] = None) -> None:
    """
    Display statistical summary panel and sub-tables for each detected metric.

    Includes a text bar chart for errors_per_minute scaled to 30 characters.

    Args:
        stats: Dictionary of statistics produced by stats.compute_stats().
        console: Optional rich Console instance.
    """
    if console is None:
        console = Console()

    # Overview panel
    summary_text = (
        f"[bold]Total Non-Empty Lines:[/bold] {stats.get('total_lines', 0)}\n"
        f"[bold green]Matched Rows:[/bold green]          {stats.get('matched', 0)}\n"
        f"[bold red]Unmatched Lines:[/bold red]       {stats.get('unmatched', 0)}\n"
        f"[bold cyan]Match Rate:[/bold cyan]            {stats.get('match_rate', 0.0)}%"
    )
    console.print(
        Panel(summary_text, title="[bold blue]LogLens Statistics Overview[/bold blue]", border_style="blue", expand=False)
    )

    # Top IPs
    if "top_ips" in stats and stats["top_ips"]:
        ip_table = Table(title="Top 5 Client IPs", header_style="bold green")
        ip_table.add_column("IP Address", style="bold")
        ip_table.add_column("Requests", justify="right")
        for ip, count in stats["top_ips"]:
            ip_table.add_row(ip, str(count))
        console.print(ip_table)

    # Status counts
    if "status_counts" in stats and stats["status_counts"]:
        status_table = Table(title="HTTP Status Code Distribution", header_style="bold yellow")
        status_table.add_column("Status Code", style="bold")
        status_table.add_column("Count", justify="right")
        for sc, count in stats["status_counts"].items():
            status_table.add_row(_format_cell_value("status", sc), str(count))
        console.print(status_table)

    # Top Paths
    if "top_paths" in stats and stats["top_paths"]:
        path_table = Table(title="Top 5 Requested Paths", header_style="bold magenta")
        path_table.add_column("Path", style="bold")
        path_table.add_column("Count", justify="right")
        for p, count in stats["top_paths"]:
            path_table.add_row(p, str(count))
        console.print(path_table)

    # Level counts
    if "level_counts" in stats and stats["level_counts"]:
        level_table = Table(title="Log Level Distribution", header_style="bold cyan")
        level_table.add_column("Level", style="bold")
        level_table.add_column("Count", justify="right")
        for lvl, count in stats["level_counts"].items():
            level_table.add_row(_format_cell_value("level", lvl), str(count))
        console.print(level_table)

    # Errors per minute text bar chart
    if "errors_per_minute" in stats and stats["errors_per_minute"]:
        epm = stats["errors_per_minute"]
        max_err = max(epm.values()) if epm else 1
        err_table = Table(title="Errors Per Minute (Status >= 500 or ERROR/CRITICAL/FATAL)", header_style="bold red")
        err_table.add_column("Minute Window", style="bold")
        err_table.add_column("Count", justify="right")
        err_table.add_column("Distribution")

        for minute_win, count in epm.items():
            # Scale bar up to 30 characters
            bar_len = int(round((count / max_err) * 30))
            bar_str = "█" * max(1, bar_len)
            err_table.add_row(minute_win, str(count), f"[red]{bar_str}[/red]")
        console.print(err_table)


def show_suggestion(regex_pattern: str, sample_line: str, console: Optional[Console] = None) -> None:
    """
    Display the suggested regex pattern and the extracted capture groups.

    Args:
        regex_pattern: The generated regular expression string.
        sample_line: The sample line it was derived from.
        console: Optional rich Console instance.
    """
    if console is None:
        console = Console()

    console.print(
        Panel(
            Text(regex_pattern, style="bold green"),
            title="[bold]Suggested Regular Expression[/bold]",
            border_style="green",
            expand=False,
        )
    )

    try:
        compiled = re.compile(regex_pattern)
        m = compiled.match(sample_line)
        if m:
            group_table = Table(title="Extracted Named Groups from Sample", header_style="bold cyan")
            group_table.add_column("Group Name", style="bold")
            group_table.add_column("Extracted Value")
            for name, val in m.groupdict().items():
                group_table.add_row(name, str(val) if val is not None else "")
            console.print(group_table)
    except re.error:
        pass
