"""
Command Line Interface orchestration module for LogLens.

Parses command-line arguments using argparse, coordinates parser, filter, stats,
export, and display pipelines, and provides user-friendly error handling.
"""

import argparse
from contextlib import nullcontext
import os
import sys
from typing import List, Optional

from rich.console import Console

from loglens import __version__
from loglens.display import show_stats, show_suggestion, show_table, show_unmatched
from loglens.export import export_rows
from loglens.filters import apply_filters, parse_where
from loglens.parser import compile_user_regex, parse_lines
from loglens.presets import PRESETS
from loglens.stats import compute_stats
from loglens.suggest import suggest_regex


class _LineTracker:
    """Wraps an iterable of lines to track the current 1-based line number."""

    def __init__(self, stream):
        self.stream = stream
        self.current_line_no = 0

    def __iter__(self):
        for line_no, line in enumerate(self.stream, start=1):
            self.current_line_no = line_no
            yield line


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser for LogLens."""
    parser = argparse.ArgumentParser(
        prog="loglens",
        description="A fast CLI log parser that turns messy logs into structured tables.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Log file to parse (if omitted, reads from stdin).",
    )
    parser.add_argument(
        "--preset",
        choices=["nginx", "apache", "syslog", "generic"],
        help="Use a pre-defined regex pattern (nginx, apache, syslog, generic).",
    )
    parser.add_argument(
        "--regex",
        type=str,
        help="Custom regex with named capture groups, e.g. '(?P<time>\\S+) (?P<level>\\w+)'",
    )
    parser.add_argument(
        "--where",
        action="append",
        default=[],
        metavar="EXPR",
        help="Filter parsed rows, e.g. --where 'status>=500' or --where 'method=POST' (repeatable).",
    )
    parser.add_argument(
        "--show-unmatched",
        action="store_true",
        help="Display lines that did not match the regex pattern.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display summary statistics and metrics.",
    )
    parser.add_argument(
        "--out",
        type=str,
        metavar="PATH",
        help="Export parsed/filtered rows to a .csv or .json file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        metavar="N",
        help="Maximum rows to display in table output (default: 50).",
    )
    parser.add_argument(
        "--suggest",
        type=str,
        metavar="SAMPLE",
        help="Suggest a regex pattern from a sample log line and exit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"loglens {__version__}",
        help="Show program version and exit.",
    )
    return parser


def run(argv: Optional[List[str]] = None) -> int:
    """
    Core execution logic for LogLens CLI.

    Args:
        argv: Command-line arguments list (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 on success, non-zero on failure).
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    console = Console()

    # 1. If --suggest: run suggestion, display, and exit 0
    if args.suggest:
        pattern_str = suggest_regex(args.suggest)
        show_suggestion(pattern_str, args.suggest, console=console)
        return 0

    # 2. Require exactly one of --preset / --regex
    if bool(args.preset) == bool(args.regex):
        raise ValueError("Must specify exactly one of --preset or --regex.")

    if args.limit < 0:
        raise ValueError("--limit must be a non-negative integer.")

    if args.preset:
        pattern = PRESETS[args.preset]
    else:
        pattern = compile_user_regex(args.regex)

    # 3. Open the file or read sys.stdin
    if args.file:
        file_ctx = open(args.file, "r", encoding="utf-8", errors="replace")
    else:
        if sys.stdin.isatty():
            parser.print_help()
            return 1
        file_ctx = nullcontext(sys.stdin)

    with file_ctx as stream:
        tracker = _LineTracker(stream)
        matched_rows: List[dict] = []
        unmatched_samples = []
        unmatched_count = 0
        total_non_blank = 0

        # 4. Run parse_lines
        for row_dict, raw_line in parse_lines(tracker, pattern):
            total_non_blank += 1
            if row_dict is not None:
                matched_rows.append(row_dict)
            else:
                unmatched_count += 1
                if len(unmatched_samples) < 1000:
                    unmatched_samples.append((tracker.current_line_no, raw_line))

    # 5. Apply --where filters
    conditions = [parse_where(expr) for expr in args.where]
    filtered_rows = list(apply_filters(matched_rows, conditions))

    # 6. Depending on flags: show table, --show-unmatched, --stats, --out
    # 7. Stats are computed over all filtered rows (before --limit)
    if args.stats:
        stats_data = compute_stats(
            filtered_rows, total_lines=total_non_blank, unmatched=unmatched_count
        )
        show_stats(stats_data, console=console)

    if args.out:
        exported_count = export_rows(filtered_rows, args.out)
        console.print(f"[bold green]Exported {exported_count} rows to '{args.out}'.[/bold green]")

    if not args.stats and not args.out:
        show_table(filtered_rows, total_count=len(filtered_rows), limit=args.limit, console=console)

    if args.show_unmatched:
        show_unmatched(unmatched_samples, total_unmatched=unmatched_count, limit=20, console=console)

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point with user-friendly error wrapping."""
    err_console = Console(stderr=True)
    try:
        return run(argv)
    except KeyboardInterrupt:
        err_console.print("\n[yellow]Operation aborted by user.[/yellow]")
        return 130
    except (FileNotFoundError, PermissionError, ValueError) as err:
        err_console.print(f"[bold red]Error:[/bold red] {err}")
        return 1
