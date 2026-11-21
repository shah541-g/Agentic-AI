"""
Command Line Interface orchestration module for ConfCheck.
"""

import argparse
import json
import sys
from typing import List, Optional
from rich.console import Console

from confcheck import __version__
from confcheck.display import print_issues, show_table
from confcheck.parser import parse_file
from confcheck.schema import SchemaError, load_schema
from confcheck.validator import validate


def build_arg_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser for ConfCheck."""
    parser = argparse.ArgumentParser(
        prog="confcheck",
        description="A regex-only INI config parser, validator, and linter.",
    )
    parser.add_argument(
        "file",
        help="Config file to check (use '-' to read from stdin).",
    )
    parser.add_argument(
        "--schema",
        metavar="SCHEMA_FILE",
        help="Validate against an INI schema file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output typed configuration as JSON to stdout.",
    )
    parser.add_argument(
        "--get",
        metavar="PATH",
        help="Extract a single value, e.g. 'server/port' or 'app_name'.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: treat all warnings as errors.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress table output (only issues are printed).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"confcheck {__version__}",
        help="Show program version and exit.",
    )
    return parser


def run(argv: Optional[List[str]] = None) -> int:
    """Core CLI logic returning integer exit code."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    console = Console()

    # 1. Load schema if specified (SchemaError or FileNotFoundError exits 2)
    schema = None
    if args.schema:
        schema = load_schema(args.schema)

    # 2. Parse config file (or stdin)
    parse_result = parse_file(args.file)

    # 3. Validate and resolve typed data
    typed_data, issues = validate(parse_result, schema, strict=args.strict)

    # 4. Print issues to stderr
    display_filename = args.file if args.file != "-" else "<stdin>"
    print_issues(issues, display_filename)

    has_errors = any(i.severity == "error" for i in issues)

    # 5. Handle --get mode
    if args.get:
        if has_errors:
            return 1
        expr = args.get
        if "/" in expr:
            sec, k = expr.split("/", 1)
        else:
            sec, k = "_global", expr

        if sec not in typed_data or k not in typed_data[sec]:
            print(f"Error: key '{expr}' not found in configuration", file=sys.stderr)
            return 1

        val = typed_data[sec][k]
        if isinstance(val, bool):
            print("true" if val else "false")
        elif isinstance(val, list):
            for item in val:
                print(str(item))
        else:
            print(str(val))
        return 0

    # 6. Handle --json mode
    if args.json:
        print(json.dumps(typed_data, indent=2, ensure_ascii=False))
        return 1 if has_errors else 0

    # 7. Render Rich table unless --quiet is requested
    if not args.quiet:
        show_table(typed_data, parse_result.sections, console=console)

    return 1 if has_errors else 0


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point with error handling and compliant exit codes."""
    try:
        return run(argv)
    except KeyboardInterrupt:
        print("\nOperation aborted by user.", file=sys.stderr)
        return 130
    except (FileNotFoundError, PermissionError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2
    except SchemaError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2
    except Exception as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2
