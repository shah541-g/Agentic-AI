"""
Unit tests for the LogLens suggest module.
"""

import re
from loglens.suggest import suggest_regex


def test_suggest_regex_matches_sample_lines_from_spec():
    """Verify suggest_regex produces a working regex for all section 9 sample lines."""
    sample_lines = [
        '192.168.1.5 - - [10/Oct/2025:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 1024 "-" "Mozilla/5.0"',
        "Oct 10 13:55:36 myhost sshd[1234]: Failed password for root from 10.0.0.9 port 22 ssh2",
        "2025-10-10 13:55:36 ERROR Database connection timed out",
    ]

    for line in sample_lines:
        pat_str = suggest_regex(line)
        compiled = re.compile(pat_str)
        m = compiled.match(line)
        assert m is not None, f"Suggested pattern '{pat_str}' failed to match line: '{line}'"
        # Must have extracted at least one named group
        assert len(m.groupdict()) > 0


def test_suggest_fallback_on_unusual_input():
    """Fallback to generic pattern if regex assembly cannot match."""
    # Blank or edge-case string
    pat = suggest_regex("")
    assert pat == r"^(?P<line>.*)$"
    assert re.match(pat, "") is not None
