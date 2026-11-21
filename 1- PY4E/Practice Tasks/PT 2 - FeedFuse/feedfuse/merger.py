"""
Data merger implementing combine and join modes.
"""

from collections import defaultdict
from typing import Any, Dict, List
from feedfuse.models import SourceResult


def combine(results: List[SourceResult]) -> Dict[str, Any]:
    """
    Merge results in 'combine' mode.

    Returns:
        {"data": {source_name: mapped_data, ...}, "status": {source_name: status_info, ...}}
    """
    data: Dict[str, Any] = {}
    status: Dict[str, Any] = {}

    for res in results:
        status_entry: Dict[str, Any] = {
            "state": res.state,
            "ms": res.ms,
        }
        if res.state in ("ok", "cached"):
            status_entry["warnings"] = res.warnings
            data[res.name] = res.data
        else:
            if res.error:
                status_entry["error"] = res.error
            if res.warnings:
                status_entry["warnings"] = res.warnings

        status[res.name] = status_entry

    return {
        "data": data,
        "status": status,
    }


def join(results: List[SourceResult], on: str, join_type: str = "inner") -> Dict[str, Any]:
    """
    Merge record lists from multiple sources on a shared key.

    Args:
        results: List of SourceResult objects.
        on: Field name to join on (present in each source's map).
        join_type: "inner" or "left" (preserves first source's rows).

    Returns:
        {"data": [ ...merged rows... ], "status": {...}}
    """
    status: Dict[str, Any] = {}
    valid_results: List[SourceResult] = []

    for res in results:
        status_entry: Dict[str, Any] = {
            "state": res.state,
            "ms": res.ms,
        }
        if res.state in ("ok", "cached"):
            status_entry["warnings"] = res.warnings
            if isinstance(res.data, list):
                valid_results.append(res)
            else:
                status_entry["warnings"].append(f"Source '{res.name}' data is not a list of records")
        else:
            if res.error:
                status_entry["error"] = res.error
            if res.warnings:
                status_entry["warnings"] = res.warnings

        status[res.name] = status_entry

    output: Dict[str, Any] = {
        "data": [],
        "status": status,
    }

    if len(valid_results) == 0:
        output["warnings"] = ["No sources succeeded in join mode"]
        return output

    if len(valid_results) == 1:
        output["data"] = valid_results[0].data
        output["warnings"] = ["Fewer than 2 sources succeeded in join mode"]
        return output

    # Sequential join across valid sources
    current_rows: List[Dict[str, Any]] = [dict(r) for r in valid_results[0].data if isinstance(r, dict)]
    existing_fields = set()
    for row in current_rows:
        existing_fields.update(row.keys())

    for next_res in valid_results[1:]:
        next_rows = [r for r in next_res.data if isinstance(r, dict)]
        renamed_next_rows: List[Dict[str, Any]] = []

        # Handle field collisions (rename collided fields to <source>_<field>)
        for row in next_rows:
            renamed_row: Dict[str, Any] = {}
            for k, v in row.items():
                if k != on and k in existing_fields:
                    renamed_row[f"{next_res.name}_{k}"] = v
                else:
                    renamed_row[k] = v
            renamed_next_rows.append(renamed_row)

        # Index next rows by string representation of the join key
        lookup = defaultdict(list)
        for row in renamed_next_rows:
            key_val = row.get(on)
            if key_val is not None:
                lookup[str(key_val)].append(row)

        merged_step: List[Dict[str, Any]] = []
        for left_row in current_rows:
            left_key = left_row.get(on)
            str_key = str(left_key) if left_key is not None else None
            matches = lookup.get(str_key, [])

            if matches:
                for match_row in matches:
                    merged = dict(left_row)
                    merged.update(match_row)
                    merged_step.append(merged)
            else:
                if join_type == "left":
                    merged_step.append(dict(left_row))

        current_rows = merged_step
        for row in current_rows:
            existing_fields.update(row.keys())

    output["data"] = current_rows
    return output
