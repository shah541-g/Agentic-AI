"""
Command Line Interface orchestration module for FeedFuse.
"""

import argparse
import asyncio
from pathlib import Path
import sys
from typing import List, Optional

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from feedfuse import __version__
from feedfuse.cache import Cache
from feedfuse.config import ConfigError, interpolate_env, load_config
from feedfuse.fetcher import fetch_all
from feedfuse.inspect import build_tree, suggest_map
from feedfuse.merger import combine, join
from feedfuse.output import export, show_combined, show_joined, show_status_table


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser with subcommands run and inspect."""
    parser = argparse.ArgumentParser(
        prog="feedfuse",
        description="A concurrent JSON API aggregator with fault tolerance, mapping, and merging.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"feedfuse {__version__}",
        help="Show program version and exit.",
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Subcommand: run
    run_parser = subparsers.add_parser("run", help="Run aggregation based on a YAML config file.")
    run_parser.add_argument(
        "config",
        type=str,
        help="Path to YAML configuration file (e.g. sources.yaml).",
    )
    run_parser.add_argument(
        "--out",
        type=str,
        metavar="PATH",
        help="Write result to .json or .csv.",
    )
    run_parser.add_argument(
        "--cache",
        type=int,
        metavar="SECONDS",
        default=None,
        help="Reuse cached responses younger than this (in seconds).",
    )
    run_parser.add_argument(
        "--no-table",
        action="store_true",
        help="Do not print the rich table, only write to --out.",
    )
    run_parser.add_argument(
        "--only",
        action="append",
        metavar="NAME",
        default=None,
        help="Run only this source (repeatable).",
    )
    run_parser.add_argument(
        "--timeout",
        type=float,
        metavar="N",
        default=None,
        help="Override timeout in seconds for all sources.",
    )
    run_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show retry attempts and timings.",
    )

    # Subcommand: inspect
    inspect_parser = subparsers.add_parser("inspect", help="Inspect a JSON API URL structure and suggest a map block.")
    inspect_parser.add_argument(
        "url",
        type=str,
        help="HTTP(S) URL to inspect.",
    )
    inspect_parser.add_argument(
        "--header",
        action="append",
        metavar="KEY:VALUE",
        default=[],
        help="Request header (repeatable, supports ${ENV_VAR}).",
    )
    inspect_parser.add_argument(
        "--param",
        action="append",
        metavar="KEY=VALUE",
        default=[],
        help="Query parameter (repeatable, supports ${ENV_VAR}).",
    )

    return parser


def run_command(args: argparse.Namespace, console: Console) -> int:
    """Execute the 'run' subcommand."""
    config = load_config(args.config)

    # Filter sources if --only is specified
    if args.only:
        selected = set(args.only)
        all_names = {s.name for s in config.sources}
        for name in selected:
            if name not in all_names:
                raise ConfigError(f"Source '{name}' specified in --only not found in configuration.")
        sources_to_run = [s for s in config.sources if s.name in selected]
    else:
        sources_to_run = config.sources

    if not sources_to_run:
        raise ConfigError("No sources selected to run.")

    # Override timeout if --timeout is provided
    if args.timeout is not None:
        if args.timeout <= 0:
            raise ConfigError("--timeout must be greater than 0.")
        for s in sources_to_run:
            s.timeout = args.timeout

    # Setup disk cache if requested
    cache_instance: Optional[Cache] = None
    if args.cache is not None:
        if args.cache < 0:
            raise ConfigError("--cache TTL must be non-negative.")
        cache_instance = Cache(ttl_seconds=args.cache)

    # Fetch sources concurrently
    results = asyncio.run(fetch_all(sources_to_run, cache=cache_instance, verbose=args.verbose))

    # Merge results
    if config.merge_mode == "join":
        merged = join(results, on=config.join_on or "", join_type=config.join_type)
    else:
        merged = combine(results)

    # Export if requested
    if args.out:
        export(merged, args.out)

    # Display tables unless --no-table is set
    if not args.no_table:
        show_status_table(results, console=console)
        if config.merge_mode == "join":
            show_joined(merged.get("data", []), limit=50, console=console)
        else:
            show_combined(merged, console=console)

    # Exit codes:
    # 0 = all succeeded
    # 2 = at least one failed and at least one succeeded
    # 1 = every source failed
    succeeded_count = sum(1 for r in results if r.state in ("ok", "cached"))
    if succeeded_count == len(results):
        return 0
    elif succeeded_count > 0:
        return 2
    else:
        return 1


def inspect_command(args: argparse.Namespace, console: Console) -> int:
    """Execute the 'inspect' subcommand."""
    headers = {}
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            headers[k.strip()] = interpolate_env(v.strip())
        else:
            raise ValueError(f"Invalid header format '{h}'. Expected 'Key: Value'")

    params = {}
    for p in args.param:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k.strip()] = interpolate_env(v.strip())
        else:
            params[p.strip()] = ""

    async def _fetch():
        client_headers = {"User-Agent": f"feedfuse/{__version__}"}
        client_headers.update(headers)
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(args.url, params=params, headers=client_headers, timeout=15.0)
            if resp.status_code != 200:
                raise ValueError(f"HTTP request failed with status {resp.status_code}: {resp.text}")
            try:
                return resp.json()
            except Exception as err:
                raise ValueError(f"Response is not valid JSON: {err}") from err

    data = asyncio.run(_fetch())

    # Build and print structure tree
    tree = build_tree(data)
    console.print(tree)

    # Build and print suggested map
    map_yaml = suggest_map(data)
    console.print(
        Panel(
            Syntax(map_yaml, "yaml", theme="monokai", line_numbers=False),
            title="[bold green]Suggested map: block[/bold green]",
            border_style="green",
            expand=False,
        )
    )
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point with user-friendly error wrapping."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    console = Console()
    err_console = Console(stderr=True)

    try:
        if args.subcommand == "run":
            return run_command(args, console)
        elif args.subcommand == "inspect":
            return inspect_command(args, console)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        err_console.print("\n[yellow]Operation aborted by user.[/yellow]")
        return 130
    except (FileNotFoundError, PermissionError, ConfigError, ValueError) as err:
        err_console.print(f"[bold red]Error:[/bold red] {err}")
        return 1
    except Exception as err:
        err_console.print(f"[bold red]Error:[/bold red] {err}")
        return 1
