"""
Statistical aggregation module for LogLens.

Computes summaries and metrics across parsed log rows in a single memory-safe pass.
Uses standard library collections.Counter and datetime.
"""

from collections import Counter
from datetime import datetime
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

DATE_FORMATS = [
    "%d/%b/%Y:%H:%M:%S %z",  # Nginx / Combined: 10/Oct/2025:13:55:36 +0000
    "%Y-%m-%d %H:%M:%S",     # Standard ISO: 2025-10-10 13:55:36
    "%Y-%m-%dT%H:%M:%S",     # ISO with T: 2025-10-10T13:55:36
]

# Syslog timestamp regex: Oct 10 13:55:36
SYSLOG_TIME_RE = re.compile(r"^[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}")


def _parse_time_to_minute(time_str: str) -> Optional[str]:
    """
    Extract a minute-resolution key from a log timestamp string.

    Tries standard formats in order, then falls back to syslog style time[:12].
    Returns None if all parsing attempts fail without raising an exception.
    """
    if not time_str or not isinstance(time_str, str):
        return None

    clean_str = time_str.strip()

    # Try standard formats
    # Strip subsecond parts if present (e.g. 2025-10-10 13:55:36.123 -> 2025-10-10 13:55:36)
    clean_for_iso = clean_str
    if "." in clean_for_iso:
        clean_for_iso = clean_for_iso.split(".")[0]
    elif "," in clean_for_iso:
        clean_for_iso = clean_for_iso.split(",")[0]

    for fmt in DATE_FORMATS:
        try:
            # Check with clean_str first (e.g. with timezone offset)
            dt = datetime.strptime(clean_str, fmt)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass
        try:
            # Check with subseconds stripped
            dt = datetime.strptime(clean_for_iso, fmt)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass

    # Check for syslog format (has no year, e.g. "Oct 10 13:55:36")
    if SYSLOG_TIME_RE.match(clean_str) and len(clean_str) >= 12:
        return clean_str[:12]

    return None


def compute_stats(rows: Iterable[Dict[str, str]], total_lines: int, unmatched: int) -> Dict[str, Any]:
    """
    Compute statistical metrics over parsed rows in a single pass.

    Args:
        rows: Iterable of parsed row dicts.
        total_lines: Total non-blank lines encountered.
        unmatched: Total lines that failed regex matching.

    Returns:
        Dict with keys:
            total_lines, matched, unmatched, match_rate (float with 1 decimal)
            top_ips (optional): list of (ip, count) top 5
            status_counts (optional): dict of status -> count sorted by status
            top_paths (optional): list of (path, count) top 5
            level_counts (optional): dict of level -> count
            errors_per_minute (optional): dict of "YYYY-MM-DD HH:MM" -> count
    """
    ip_counter = Counter()
    status_counter = Counter()
    path_counter = Counter()
    level_counter = Counter()
    errors_counter = Counter()

    seen_fields = set()
    matched_count = 0

    error_levels = {"ERROR", "CRITICAL", "FATAL"}

    for row in rows:
        matched_count += 1
        seen_fields.update(row.keys())

        if "ip" in row and row["ip"]:
            ip_counter[row["ip"]] += 1

        if "status" in row and row["status"]:
            status_counter[row["status"]] += 1

        if "path" in row and row["path"]:
            path_counter[row["path"]] += 1

        if "level" in row and row["level"]:
            level_counter[row["level"].upper()] += 1

        # Check for error condition: level in {ERROR, CRITICAL, FATAL} or status >= 500
        is_error = False
        if "level" in row and row["level"].upper() in error_levels:
            is_error = True
        elif "status" in row and row["status"]:
            try:
                if float(row["status"]) >= 500:
                    is_error = True
            except (ValueError, TypeError):
                pass

        if is_error and "time" in row:
            minute_key = _parse_time_to_minute(row["time"])
            if minute_key:
                errors_counter[minute_key] += 1

    match_rate = round((matched_count / total_lines * 100), 1) if total_lines > 0 else 0.0

    stats: Dict[str, Any] = {
        "total_lines": total_lines,
        "matched": matched_count,
        "unmatched": unmatched,
        "match_rate": match_rate,
    }

    if "ip" in seen_fields:
        stats["top_ips"] = ip_counter.most_common(5)

    if "status" in seen_fields:
        stats["status_counts"] = dict(sorted(status_counter.items(), key=lambda item: str(item[0])))

    if "path" in seen_fields:
        stats["top_paths"] = path_counter.most_common(5)

    if "level" in seen_fields:
        stats["level_counts"] = dict(level_counter)

    if "time" in seen_fields:
        stats["errors_per_minute"] = dict(sorted(errors_counter.items()))

    return stats
