"""Command line interface orchestration for LinkAtlas."""
from __future__ import annotations
import argparse
import os
import sys
import time
from urllib.parse import urlparse
from rich.console import Console

from linkatlas import __version__
from linkatlas.crawler import Crawler
from linkatlas.display import print_page_event, show_summary
from linkatlas.exporters import export_csv, export_dot, export_graphml, export_json
from linkatlas.fetcher import Fetcher
from linkatlas.graph import Graph
from linkatlas.models import CrawlConfig, DEFAULT_UA
from linkatlas.urls import domain_of, normalize_url


def build_arg_parser() -> argparse.ArgumentParser:
    """Build LinkAtlas argument parser."""
    parser = argparse.ArgumentParser(
        prog="linkatlas",
        description="A polite depth-limited web crawler that maps external links as a graph.",
    )
    parser.add_argument(
        "url",
        help="Seed URL to crawl (scheme optional, e.g. example.com).",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Maximum crawl depth (0, 1, or 2; default: 2).",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=200,
        help="Maximum number of pages to request (default: 200).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Politeness delay in seconds between requests to the same host (default: 1.0).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP request timeout in seconds (default: 10.0).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=1,
        help="Number of retries on 5xx or network errors (0 to 3, default: 1).",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=2_000_000,
        help="Maximum body size in bytes before aborting (default: 2000000).",
    )
    parser.add_argument(
        "--include-subdomains",
        action="store_true",
        help="Treat subdomains of the seed host as internal.",
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_UA,
        help=f"Custom User-Agent header (default: {DEFAULT_UA}).",
    )
    parser.add_argument(
        "--out",
        metavar="PATH",
        help="Base output file path (default: linkatlas-<host>.json).",
    )
    parser.add_argument(
        "--format",
        action="append",
        choices=["json", "graphml", "dot"],
        help="Output graph format (repeatable, choices: json, graphml, dot; default: json).",
    )
    parser.add_argument(
        "--csv",
        metavar="PATH",
        help="Export unique external links to a CSV file.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress real-time page progress lines.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"linkatlas {__version__}",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    """Core CLI routine returning an integer exit code."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    console = Console()

    # Validate argument bounds per specifications
    if args.depth not in (0, 1, 2):
        print(f"Error: --depth must be 0, 1 or 2 (got {args.depth})", file=sys.stderr)
        return 2

    if args.max_pages < 1:
        print(f"Error: --max-pages must be at least 1 (got {args.max_pages})", file=sys.stderr)
        return 2

    if args.delay < 0:
        print(f"Error: --delay must be non-negative (got {args.delay})", file=sys.stderr)
        return 2

    if args.delay < 0.5 and not args.quiet:
        console.print("[yellow]Warning: Crawl delay < 0.5s may place high load on target server.[/yellow]")

    if args.timeout <= 0:
        print(f"Error: --timeout must be positive (got {args.timeout})", file=sys.stderr)
        return 2

    if not (0 <= args.retries <= 3):
        print(f"Error: --retries must be between 0 and 3 (got {args.retries})", file=sys.stderr)
        return 2

    # Normalise seed URL
    seed = args.url
    if not urlparse(seed).scheme:
        seed = "https://" + seed
    norm_seed = normalize_url(seed)
    if not norm_seed:
        norm_seed = seed

    config = CrawlConfig(
        seed=norm_seed,
        max_depth=args.depth,
        max_pages=args.max_pages,
        delay=args.delay,
        timeout=args.timeout,
        retries=args.retries,
        max_bytes=args.max_bytes,
        include_subdomains=args.include_subdomains,
        user_agent=args.user_agent,
    )

    graph = Graph()
    fetcher = Fetcher(config=config)

    # Check robots.txt for seed directly to provide informative error if blocked
    seed_policy = fetcher.robots.policy_for(norm_seed)
    if not seed_policy.allowed(norm_seed):
        reason = "blocked by robots.txt rules"
        if seed_policy.state == "forbidden":
            reason = "robots.txt returned 401/403 (forbidden)"
        elif seed_policy.state == "unreachable":
            reason = "robots.txt returned 5xx or timed out (unreachable)"
        print(f"Error: Seed URL {norm_seed} cannot be crawled ({reason}).", file=sys.stderr)
        return 1

    def on_page_cb(res, depth):
        if not args.quiet:
            print_page_event(res, depth, console=console)

    crawler = Crawler(config=config, fetcher=fetcher, graph=graph, on_page=on_page_cb)

    start_time = time.monotonic()
    result = crawler.run()
    elapsed_sec = time.monotonic() - start_time

    meta = result["meta"]
    summary = result["summary"]
    graph_dict = graph.to_dict(meta, summary)

    # Determine output file paths
    formats = args.format or ["json"]
    # Deduplicate preserving order
    unique_formats = list(dict.fromkeys(formats))

    host = domain_of(norm_seed) or "site"
    if args.out:
        base_out = args.out
        if base_out.endswith(".json") or base_out.endswith(".graphml") or base_out.endswith(".dot"):
            stem, _ = os.path.splitext(base_out)
        else:
            stem = base_out
    else:
        stem = f"linkatlas-{host}"

    files_written: list[str] = []

    try:
        for fmt in unique_formats:
            if fmt == "json":
                out_path = args.out if (args.out and args.out.endswith(".json")) else f"{stem}.json"
                export_json(graph_dict, out_path)
                files_written.append(out_path)
            elif fmt == "graphml":
                out_path = f"{stem}.graphml"
                export_graphml(graph_dict, out_path)
                files_written.append(out_path)
            elif fmt == "dot":
                out_path = f"{stem}.dot"
                export_dot(graph_dict, out_path)
                files_written.append(out_path)

        if args.csv:
            export_csv(graph_dict, args.csv)
            files_written.append(args.csv)

    except (OSError, IOError) as err:
        print(f"Error writing output file: {err}", file=sys.stderr)
        return 2

    # Display final summary tables
    show_summary(
        summary=summary,
        meta=meta,
        files_written=files_written,
        elapsed_sec=elapsed_sec,
        console=console,
    )

    if result.get("interrupted"):
        return 130

    if summary.get("pages_ok", 0) == 0:
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint."""
    try:
        return run(argv)
    except KeyboardInterrupt:
        print("\nCrawl interrupted by user.", file=sys.stderr)
        return 130
    except Exception as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2
