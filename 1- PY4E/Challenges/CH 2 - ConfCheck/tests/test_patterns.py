"""
Unit tests validating compiled regular expression patterns.
"""

from confcheck.patterns import (
    BACKSLASH_END,
    BLANK,
    BOOL,
    COMMENT,
    CONTINUATION,
    INLINE_COMMENT,
    INT,
    KEY_VALUE,
    LIST_ITEM,
    QUOTED,
    QUOTED_SPAN,
    RULE,
    RULE_OPT,
    SECTION,
)


def test_blank_and_comment():
    """Verify BLANK and COMMENT match appropriate lines."""
    assert BLANK.match("")
    assert BLANK.match("   \t  ")
    assert not BLANK.match("not blank")

    assert COMMENT.match("; comment")
    assert COMMENT.match("# comment")
    assert COMMENT.match("   ; indented comment")
    assert not COMMENT.match("key = val ; inline")


def test_section():
    """Verify SECTION matches valid headers and extracts clean names."""
    m = SECTION.match("[server]")
    assert m and m.group("name") == "server"

    m = SECTION.match("[ database.primary ] ; comment")
    assert m and m.group("name") == "database.primary"

    m = SECTION.match("[my-app_v1]")
    assert m and m.group("name") == "my-app_v1"

    assert SECTION.match("[database") is None
    assert SECTION.match("database]") is None


def test_key_value():
    """Verify KEY_VALUE matches valid key definitions."""
    m = KEY_VALUE.match("port = 8080")
    assert m and m.group("key") == "port" and m.group("sep") == "=" and m.group("value") == "8080"

    m = KEY_VALUE.match("host: localhost")
    assert m and m.group("key") == "host" and m.group("sep") == ":" and m.group("value") == "localhost"

    # Cannot start with =
    assert KEY_VALUE.match("= novalue") is None


def test_inline_comment_stripping():
    """Verify INLINE_COMMENT regex accurately isolates the body from comments."""
    cases = [
        ("value ; comment", "value"),
        ("value # comment", "value"),
        ("a;b", "a;b"),
        ("http://x.com/#frag", "http://x.com/#frag"),
        ('"a ; b" ; real', '"a ; b"'),
        ("it's fine # c", "it's fine"),
        ("   ", ""),
    ]
    for text, expected in cases:
        m = INLINE_COMMENT.match(text)
        assert m is not None, f"Failed to match: {text}"
        body = m.group("body").rstrip()
        assert body == expected, f"Expected {expected!r}, got {body!r} for input {text!r}"


def test_quoted():
    """Verify QUOTED matches fully quoted values with escapes."""
    assert QUOTED.match('"hello"')
    assert QUOTED.match("'single'")
    assert QUOTED.match('"with \\"escaped\\" quotes"')
    assert not QUOTED.match('"start" and "end"')
    assert not QUOTED.match("unquoted")


def test_bool_and_int():
    """Verify BOOL and INT matching."""
    for b in ["true", "True", "YES", "on", "false", "no", "Off"]:
        assert BOOL.match(b)

    for nb in ["1", "0", "maybe", "123"]:
        assert BOOL.match(nb) is None

    for i in ["42", "-7", "+3", "007", "0"]:
        assert INT.match(i)

    for ni in ["1.5", "1_000", "abc"]:
        assert INT.match(ni) is None


def test_rule_pattern():
    """Verify RULE and RULE_OPT parse schema definitions."""
    m = RULE.match("str, required")
    assert m and m.group("type") == "str"
    opts = [opt.group("name") for opt in RULE_OPT.finditer(m.group("opts"))]
    assert opts == ["required"]

    m2 = RULE.match("list[int], min=1, max=100")
    assert m2 and m2.group("type") == "list" and m2.group("item") == "int"
    opt_dict = {opt.group("name"): opt.group("val") for opt in RULE_OPT.finditer(m2.group("opts"))}
    assert opt_dict == {"min": "1", "max": "100"}
