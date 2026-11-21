"""
Automatic regex suggestion module for LogLens.

Generates a regular expression with named capture groups from a single sample log line.
"""

import re
from typing import Dict, List, Optional, Set, Tuple

# Pre-compiled recognition patterns
IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}\b")
TIME_BRACKET_RE = re.compile(r"^\[(?P<ts>[^\]]*\d{2}:\d{2}:\d{2}[^\]]*)\]")
TIME_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?\b")
TIME_SYSLOG_RE = re.compile(r"^[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b")
LEVEL_RE = re.compile(r"^(?:DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b")
METHOD_RE = re.compile(r"^(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\b")
PATH_RE = re.compile(r"^/[^\s\"'>]*")
DIGITS_3_RE = re.compile(r"^\d{3}\b")
INTEGER_RE = re.compile(r"^\d+\b")


def suggest_regex(sample: str) -> str:
    """
    Return a regex string with named groups built from one sample log line.

    Scans the sample left to right and replaces recognized tokens according to
    priority rules. Guarantees that the returned regex matches the sample.

    Args:
        sample: A raw log line string.

    Returns:
        A compiled-ready regex pattern starting with ^ and ending with $.
    """
    sample = sample.rstrip("\r\n")
    if not sample.strip():
        return r"^(?P<line>.*)$"

    pos = 0
    n = len(sample)
    tokens: List[str] = []
    used_names: Set[str] = set()
    num_counter = 1
    after_quote = False

    def get_group_name(base: str) -> str:
        """Ensure unique named groups (e.g. ip, ip2, etc.)."""
        if base not in used_names:
            used_names.add(base)
            return base
        i = 2
        while f"{base}{i}" in used_names:
            i += 1
        name = f"{base}{i}"
        used_names.add(name)
        return name

    while pos < n:
        # Check for whitespace
        if sample[pos].isspace():
            # Consume all consecutive whitespace
            start = pos
            while pos < n and sample[pos].isspace():
                pos += 1
            tokens.append(r"\s+")
            continue

        substr = sample[pos:]

        # 1. Timestamp inside brackets [...]
        m = TIME_BRACKET_RE.match(substr)
        if m:
            gname = get_group_name("time")
            tokens.append(rf"\[(?P<{gname}>[^\]]+)\]")
            pos += len(m.group(0))
            after_quote = False
            continue

        # 2. ISO timestamp
        m = TIME_ISO_RE.match(substr)
        if m:
            gname = get_group_name("time")
            tokens.append(rf"(?P<{gname}>\d{{4}}-\d{{2}}-\d{{2}}[ T]\d{{2}}:\d{{2}}:\d{{2}})")
            pos += len(m.group(0))
            after_quote = False
            continue

        # 3. Syslog timestamp
        m = TIME_SYSLOG_RE.match(substr)
        if m:
            gname = get_group_name("time")
            tokens.append(rf"(?P<{gname}>[A-Za-z]{{3}}\s+\d{{1,2}}\s+\d{{2}}:\d{{2}}:\d{{2}})")
            pos += len(m.group(0))
            after_quote = False
            continue

        # 4. IPv4 address
        m = IPV4_RE.match(substr)
        if m:
            gname = get_group_name("ip")
            tokens.append(rf"(?P<{gname}>\d{{1,3}}(?:\.\d{{1,3}}){{3}})")
            pos += len(m.group(0))
            after_quote = False
            continue

        # 5. Log level word
        m = LEVEL_RE.match(substr)
        if m:
            gname = get_group_name("level")
            tokens.append(rf"(?P<{gname}>DEBUG|INFO|WARN(?:ING)?|ERROR|CRITICAL|FATAL)")
            pos += len(m.group(0))
            after_quote = False
            continue

        # 6. HTTP method
        m = METHOD_RE.match(substr)
        if m:
            gname = get_group_name("method")
            tokens.append(rf"(?P<{gname}>[A-Z]+)")
            pos += len(m.group(0))
            after_quote = False
            continue

        # 7. URL path starting with / (must be preceded by whitespace, quote, or start of line)
        if pos == 0 or sample[pos - 1].isspace() or sample[pos - 1] in ('"', "'"):
            m = PATH_RE.match(substr)
            if m and len(m.group(0)) > 1:
                gname = get_group_name("path")
                tokens.append(rf"(?P<{gname}>\S+)")
                pos += len(m.group(0))
                after_quote = False
                continue

        # 8. 3-digit status code right after a quoted request
        if after_quote:
            m = DIGITS_3_RE.match(substr)
            if m:
                gname = get_group_name("status")
                tokens.append(rf"(?P<{gname}>\d{{3}})")
                pos += len(m.group(0))
                after_quote = False
                continue

        # 9. Other integers
        m = INTEGER_RE.match(substr)
        if m:
            gname = get_group_name(f"num{num_counter}")
            num_counter += 1
            tokens.append(rf"(?P<{gname}>\d+)")
            pos += len(m.group(0))
            after_quote = False
            continue

        # 10. Remaining characters / words
        # Check if this character is a quote
        char = sample[pos]
        if char == '"':
            after_quote = True
            tokens.append(r'"')
            pos += 1
            continue

        # Match word chunk or non-space symbols
        chunk_m = re.match(r"^(\w+|[^\w\s\"])", substr)
        if chunk_m:
            chunk = chunk_m.group(0)
            tokens.append(re.escape(chunk))
            pos += len(chunk)
            after_quote = False
        else:
            tokens.append(re.escape(char))
            pos += 1
            after_quote = False

    pattern = "^" + "".join(tokens) + "$"

    # Verification: Pattern must compile and match the sample line
    try:
        compiled = re.compile(pattern)
        if compiled.match(sample) and compiled.groupindex:
            return pattern
    except re.error:
        pass

    # Safe fallback if rule assembly didn't match
    return r"^(?P<line>.*)$"
