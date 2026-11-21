"""
Log parser module for LogLens.

This module is responsible for:
1. Validating and compiling custom regex patterns provided by the user.
2. Iterating through log lines using a memory-efficient generator.
3. Extracting named capture groups from matching lines into dictionary records.

For Regex Practitioners:
- In Python regex, named groups are defined as `(?P<name>...)`.
- `pattern.groupindex` contains a mapping of group names to their internal indices.
- `match.groupdict()` returns a dictionary of all named groups and their captured substrings.
- Optional groups that did not match evaluate to `None`; LogLens normalizes these to `""`.
"""

import re
from typing import Dict, Iterable, Iterator, Optional, Tuple


def compile_user_regex(pattern_str: str) -> re.Pattern:
    """
    Compile a user-supplied regular expression string.

    Args:
        pattern_str: The raw regex string provided by the user.

    Returns:
        Compiled re.Pattern object with at least one named capture group.

    Raises:
        ValueError: If the regex syntax is invalid.
        ValueError: If the pattern does not contain any named capture groups
                    (?P<name>...).
    """
    try:
        pattern = re.compile(pattern_str)
    except re.error as err:
        raise ValueError(f"Invalid regex pattern: {err}") from err

    # Check if the regex defines any named groups (?P<name>...)
    if not pattern.groupindex:
        raise ValueError("Regex must contain at least one named group, e.g. (?P<ip>\\S+)")

    return pattern


def parse_lines(
    lines: Iterable[str], pattern: re.Pattern
) -> Iterator[Tuple[Optional[Dict[str, str]], str]]:
    """
    Parse an iterable of log lines against a compiled regex pattern.

    This function is a pure generator: it processes one line at a time
    without buffering the entire log file in memory.

    Args:
        lines: Iterable of strings (e.g. open file handle or sys.stdin).
        pattern: Compiled regex pattern with named groups.

    Yields:
        Tuple of (row_dict, raw_line):
        - row_dict: Dict mapping group names to captured strings if matched,
                    with None values replaced by "". Returns None if unmatched.
        - raw_line: The original line stripped of trailing newline characters.
                    Completely blank lines are skipped entirely.
    """
    for line in lines:
        raw_line = line.rstrip("\r\n")
        # Skip completely blank or whitespace-only lines
        if not raw_line.strip():
            continue

        match = pattern.search(raw_line)
        if match:
            # Replace unmatched optional groups (None) with empty string ""
            row_dict = {
                key: (val if val is not None else "")
                for key, val in match.groupdict().items()
            }
        else:
            row_dict = None

        yield (row_dict, raw_line)
