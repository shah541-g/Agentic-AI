"""
Unit tests for the LogLens parser and presets module.
"""

import pytest
import re
from loglens.parser import parse_lines, compile_user_regex
from loglens.presets import PRESETS


def test_valid_nginx_line_parsed_correctly():
    """A valid nginx line returns the expected ip, status, method, path."""
    line = '192.168.1.5 - - [10/Oct/2025:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 1024 "-" "Mozilla/5.0"\n'
    results = list(parse_lines([line], PRESETS["nginx"]))
    assert len(results) == 1
    row, raw = results[0]
    assert row is not None
    assert row["ip"] == "192.168.1.5"
    assert row["status"] == "200"
    assert row["method"] == "GET"
    assert row["path"] == "/index.html"
    assert row["user"] == "-"
    assert row["time"] == "10/Oct/2025:13:55:36 +0000"
    assert raw == line.rstrip("\r\n")


def test_malformed_line_yields_none():
    """A malformed line yields None as its row."""
    bad_line = "This is a malformed log line that cannot match nginx format\n"
    results = list(parse_lines([bad_line], PRESETS["nginx"]))
    assert len(results) == 1
    row, raw = results[0]
    assert row is None
    assert raw == "This is a malformed log line that cannot match nginx format"


def test_blank_lines_are_skipped():
    """Completely blank and whitespace-only lines are skipped."""
    lines = [
        "\n",
        "   \n",
        '192.168.1.5 - - [10/Oct/2025:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 1024 "-" "Mozilla/5.0"\n',
        "\r\n",
        "  \t \n",
    ]
    results = list(parse_lines(lines, PRESETS["nginx"]))
    assert len(results) == 1
    assert results[0][0] is not None


def test_regex_with_no_named_groups_raises_value_error():
    """A regex with no named groups raises ValueError with a helpful message."""
    with pytest.raises(ValueError, match="Regex must contain at least one named group"):
        compile_user_regex(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")


def test_invalid_regex_syntax_raises_value_error():
    """Syntactically broken regex raises ValueError."""
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        compile_user_regex(r"(?P<unclosed_group>\d+")


def test_compile_user_regex_success():
    """Valid regex with named groups compiles cleanly."""
    pattern = compile_user_regex(r"(?P<level>\w+): (?P<msg>.*)")
    assert "level" in pattern.groupindex
    assert "msg" in pattern.groupindex
