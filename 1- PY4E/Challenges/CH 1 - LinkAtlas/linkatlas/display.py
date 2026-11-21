"""Terminal formatting and Rich table presentation."""
from __future__ import annotations
from typing import Any
from rich.console import Console
from rich.table import Table

from linkatlas.models import FetchResult


def print_page_event(result: FetchResult, depth: int, console: Console | None = None) -> None:
    """Print one status line per fetched page as it happens."""
    con = console or Console()
    st = result.state
    url = result.url

    if st == "ok":
        con.print(f"[dim]\\[d{depth}][/dim] [green]{result.status or 200}[/green] {url}")
    elif st == "redirect":
        con.print(f"[dim]\\[d{depth}][/dim] [cyan]{result.status or 301} redirect[/cyan] {url} -> {result.redirect_to}")
    elif st == "robots_disallowed":
        con.print(f"[dim]\\[d{depth}][/dim] [yellow]blocked by robots.txt[/yellow] {url}")
    elif st == "timeout":
        con.print(f"[dim]\\[d{depth}][/dim] [red]timeout[/red] {url}")
    elif st == "http_error":
        con.print(f"[dim]\\[d{depth}][/dim] [red]{result.status or 'error'}[/red] {url}")
    else:
        con.print(f"[dim]\\[d{depth}][/dim] [red]{st}[/red] {url}")


def show_summary(
    summary: dict[str, Any],
    meta: dict[str, Any],
    files_written: list[str],
    elapsed_sec: float,
    console: Console | None = None,
) -> None:
    """Print end-of-crawl summary tables and files written."""
    con = console or Console()

    # 1. Summary Metrics Table
    summary_table = Table(title="LinkAtlas Crawl Summary", show_header=True, header_style="bold magenta")
    summary_table.add_column("Metric", style="dim")
    summary_table.add_column("Value", justify="right")

    summary_table.add_row("Seed URL", str(meta.get("seed", "")))
    summary_table.add_row("Pages Requested", str(summary.get("pages_requested", 0)))
    summary_table.add_row("Pages OK", f"[green]{summary.get('pages_ok', 0)}[/green]")

    # State counts
    state_counts = summary.get("state_counts", {})
    state_str = ", ".join(f"{k}: {v}" for k, v in state_counts.items())
    summary_table.add_row("Page States", state_str or "none")

    summary_table.add_row("Unique External URLs", str(summary.get("external_unique_urls", 0)))
    summary_table.add_row("Unique External Domains", str(summary.get("external_unique_domains", 0)))
    summary_table.add_row("Ignored Links (non-http)", str(summary.get("ignored_links", 0)))
    summary_table.add_row("Elapsed Time", f"{elapsed_sec:.2f}s")
    if meta.get("truncated"):
        summary_table.add_row("Notice", "[yellow]Truncated (hit max pages)[/yellow]")
    if meta.get("interrupted"):
        summary_table.add_row("Notice", "[yellow]Interrupted by user (Ctrl+C)[/yellow]")

    con.print(summary_table)

    # 2. Top External Domains Table
    top_domains = summary.get("top_external_domains", [])
    if top_domains:
        domain_table = Table(title="Top External Domains", show_header=True, header_style="bold cyan")
        domain_table.add_column("Domain", style="bold")
        domain_table.add_column("Unique URLs", justify="right")
        domain_table.add_column("Linked From Pages", justify="right")

        for d in top_domains:
            domain_table.add_row(
                d["domain"],
                str(d["urls"]),
                str(d["linked_from_pages"]),
            )
        con.print(domain_table)

    # 3. Problem Pages Table
    problems = summary.get("problems", [])
    if problems:
        prob_table = Table(title="Problem Pages", show_header=True, header_style="bold red")
        prob_table.add_column("URL", style="dim")
        prob_table.add_column("State", justify="center")
        prob_table.add_column("Status", justify="center")
        prob_table.add_column("Linked From (Referrers)", style="dim")

        for p in problems:
            refs = p.get("linked_from", [])
            ref_str = ", ".join(refs[:3])
            if len(refs) > 3:
                ref_str += f" (+{len(refs) - 3} more)"
            prob_table.add_row(
                p["url"],
                p.get("state", ""),
                str(p.get("status") or "-"),
                ref_str or "-",
            )
        con.print(prob_table)

    # 4. Output Files List
    if files_written:
        con.print("\n[bold green]Files written:[/bold green]")
        for fpath in files_written:
            con.print(f"  • {fpath}")
