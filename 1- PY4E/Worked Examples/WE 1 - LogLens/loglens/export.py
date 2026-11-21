"""
Data export module for LogLens.

Exports parsed log records to CSV or JSON formats.
"""

import csv
import json
import os
from typing import Dict, Iterable


def export_rows(rows: Iterable[Dict[str, str]], path: str) -> int:
    """
    Write parsed rows to the specified file path.

    The format is determined by the file extension (.csv or .json).

    Args:
        rows: Iterable of row dictionaries.
        path: Output file path.

    Returns:
        Number of rows exported.

    Raises:
        ValueError: If the file extension is not .csv or .json.
    """
    lower_path = path.lower()
    if not (lower_path.endswith(".csv") or lower_path.endswith(".json")):
        raise ValueError(
            f"Unsupported export format for '{path}'. Supported formats are .csv and .json"
        )

    # Ensure parent directory exists if a directory path was provided
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    if lower_path.endswith(".csv"):
        iterator = iter(rows)
        try:
            first_row = next(iterator)
        except StopIteration:
            # Empty rows: create an empty file
            with open(path, "w", newline="", encoding="utf-8"):
                pass
            return 0

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(first_row.keys()))
            writer.writeheader()
            writer.writerow(first_row)
            count = 1
            for row in iterator:
                writer.writerow(row)
                count += 1
            return count

    else:  # .json
        rows_list = list(rows)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows_list, f, indent=2, ensure_ascii=False)
        return len(rows_list)
