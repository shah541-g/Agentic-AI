"""
Unit tests for the regex-only INI parser.
"""

from confcheck.parser import parse_text


def test_parser_basic_sections_and_keys():
    """Verify sections, keys with = and :, and global keys in _global."""
    text = """
app_name = ConfCheck
version : 1.0

[server]
host = 127.0.0.1
port: 8080
"""
    res = parse_text(text)
    assert len(res.issues) == 0
    assert "_global" in res.sections
    assert res.sections["_global"]["app_name"].raw == "ConfCheck"
    assert res.sections["_global"]["version"].raw == "1.0"
    assert res.sections["server"]["host"].raw == "127.0.0.1"
    assert res.sections["server"]["port"].raw == "8080"


def test_parser_comments_ignored_inside_multiline():
    """Verify full-line comments are ignored everywhere, even inside multi-line values."""
    text = """
[app]
query = SELECT *
    ; comment inside
    # another comment
    FROM users
"""
    res = parse_text(text)
    assert len(res.issues) == 0
    raw = res.sections["app"]["query"].raw
    assert "comment" not in raw
    assert raw == "SELECT *\nFROM users"


def test_parser_multiline_types():
    """Verify indentation continuation, backslash continuation, and block lists."""
    text = r"""
[data]
desc = Line one
    Line two
    Line three

query = SELECT * \
    FROM table

replicas =
    db1.internal
    db2.internal
"""
    res = parse_text(text)
    assert len(res.issues) == 0

    # Indentation multiline
    assert res.sections["data"]["desc"].raw == "Line one\nLine two\nLine three"
    assert res.sections["data"]["desc"].block is False

    # Backslash continuation (joined with single space)
    assert res.sections["data"]["query"].raw == "SELECT * FROM table"

    # Block list (block=True, leading empty line dropped)
    assert res.sections["data"]["replicas"].raw == "db1.internal\ndb2.internal"
    assert res.sections["data"]["replicas"].block is True


def test_parser_blank_line_ends_multiline_then_e002():
    """Blank line ends open value; a following indented line gives E002."""
    text = """
[app]
key = val

  unexpected indented line
"""
    res = parse_text(text)
    assert len(res.issues) == 1
    issue = res.issues[0]
    assert issue.code == "E002"
    assert issue.line == 5
    assert issue.severity == "error"


def test_parser_error_codes():
    """Verify E001, E003 (with discard), E004 (first value kept), and W001."""
    text = """
[server]
host = 1.1.1.1
host = 2.2.2.2
= novalue
[bad_header
discarded_key = val
[server]
other = ok
"""
    res = parse_text(text)
    codes = [i.code for i in res.issues]

    assert "E004" in codes  # Duplicate key
    assert "E001" in codes  # Invalid syntax
    assert "E003" in codes  # Bad section
    assert "W001" in codes  # Duplicate section merged

    # E004 kept the first value
    assert res.sections["server"]["host"].raw == "1.1.1.1"
    # discarded_key was skipped without cascading errors
    assert "discarded_key" not in res.sections.get("bad_header", {})
    assert "other" in res.sections["server"]


def test_parser_windows_endings_and_bom():
    """Verify parsing handles CRLF and leading UTF-8 BOM."""
    text = "\ufeff[server]\r\nport = 8080\r\nhost = localhost\r\n"
    res = parse_text(text)
    assert len(res.issues) == 0
    assert res.sections["server"]["port"].raw == "8080"
    assert res.sections["server"]["host"].raw == "localhost"
