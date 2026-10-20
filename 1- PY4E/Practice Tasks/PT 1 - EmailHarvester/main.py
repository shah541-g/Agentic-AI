
import argparse
import json
import sys
import time
from pathlib import Path

from analyzer import analyze_contacts
from config import DEFAULT_INPUT, OUTPUT_DIR, TEXT_FIELDS
from exporters import export_all
from normalizer import build_contacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract unique email addresses and analyze domains."
    )

    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to the input JSON file.",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory for generated reports.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = time.perf_counter()

    try:
        with args.input.open("r", encoding="utf-8-sig") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("The JSON root must be an object.")

        records = data.get("emails")

        if not isinstance(records, list):
            raise ValueError("The JSON file must contain an 'emails' list.")

        if not all(isinstance(record, dict) for record in records):
            raise ValueError("Every item in 'emails' must be an object.")

        contacts, total_matches, invalid_count = build_contacts(
            records,
            fields=TEXT_FIELDS,
        )

        elapsed = time.perf_counter() - start

        report = analyze_contacts(
            contacts=contacts,
            input_file=str(args.input.resolve()),
            total_email_records=len(records),
            total_matches=total_matches,
            invalid_candidates_rejected=invalid_count,
            processing_seconds=elapsed,
        )

        export_all(contacts, report, args.output_dir)

        print("\nEmailHarvester completed successfully.")
        print(f"Input records:       {report.total_email_records}")
        print(f"Email matches:       {report.total_matches}")
        print(f"Unique addresses:    {report.unique_addresses}")
        print(f"Duplicate matches:   {report.duplicate_matches_removed}")
        print(f"Distinct domains:    {report.distinct_domains}")
        print(f"Processing time:     {report.processing_seconds:.4f}s")
        print(f"Output directory:    {args.output_dir.resolve()}")

        print("\nGenerated files:")
        print(f"  {args.output_dir / 'emails_by_domain.txt'}")
        print(f"  {args.output_dir / 'emails.csv'}")
        print(f"  {args.output_dir / 'report.json'}")

        return 0

    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        return 1

    except json.JSONDecodeError as error:
        print(f"Error: Invalid JSON: {error}", file=sys.stderr)
        return 1

    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
