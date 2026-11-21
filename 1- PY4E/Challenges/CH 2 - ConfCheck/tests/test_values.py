"""
Unit tests for comment stripping, unquoting, type inference, and conversions.
"""

import pytest
from confcheck.values import (
    ConversionError,
    convert_value,
    has_list_comma,
    infer_value,
    split_list,
    strip_inline_comment,
    unquote,
)


def test_strip_inline_comment():
    """Verify inline comments are stripped while keeping valid characters and URLs."""
    assert strip_inline_comment("value ; comment") == "value"
    assert strip_inline_comment("value # comment") == "value"
    assert strip_inline_comment("a;b") == "a;b"
    assert strip_inline_comment("http://x.com/#frag") == "http://x.com/#frag"
    assert strip_inline_comment('"a ; b" ; real') == '"a ; b"'
    assert strip_inline_comment("it's fine # c") == "it's fine"
    assert strip_inline_comment("   ") == ""


def test_unquote():
    """Verify quotes are removed and escapes resolved."""
    assert unquote(r'"a\"b"') == 'a"b'
    assert unquote("'x'") == "x"
    assert unquote(r'"line1\nline2"') == "line1\nline2"
    assert unquote("no quotes") == "no quotes"


def test_infer_integers():
    """Verify integer inference including leading zeros and signs."""
    assert infer_value("42", block=False) == (42, "int")
    assert infer_value("-7", block=False) == (-7, "int")
    assert infer_value("+3", block=False) == (3, "int")
    assert infer_value("007", block=False) == (7, "int")


def test_infer_booleans():
    """Verify boolean inference and differentiation from ints and strings."""
    assert infer_value("true", block=False) == (True, "bool")
    assert infer_value("YES", block=False) == (True, "bool")
    assert infer_value("Off", block=False) == (False, "bool")

    # "true" quoted stays str
    assert infer_value('"true"', block=False) == ("true", "str")

    # 1 and 0 are ints, not bools
    assert infer_value("1", block=False) == (1, "int")
    assert infer_value("0", block=False) == (0, "int")


def test_infer_strings_not_numbers():
    """Verify non-integer numbers, formats, and empty strings remain str."""
    assert infer_value("1.5", block=False) == ("1.5", "str")
    assert infer_value("1_000", block=False) == ("1_000", "str")
    assert infer_value("", block=False) == ("", "str")


def test_infer_lists():
    """Verify comma list inference with heterogeneous items and quotes."""
    assert infer_value("a, b, c", block=False) == (["a", "b", "c"], "list")
    assert infer_value("1, 2, 3", block=False) == ([1, 2, 3], "list")
    assert infer_value("1, two, true", block=False) == ([1, "two", True], "list")

    # Comma inside quotes does not split
    assert infer_value('"a, b"', block=False) == ("a, b", "str")
    assert infer_value('a, "b, c", d', block=False) == (["a", "b, c", "d"], "list")
    assert infer_value("a, b,", block=False) == (["a", "b"], "list")


def test_infer_block_list():
    """Verify block entries become lists."""
    assert infer_value("x\ny", block=True) == (["x", "y"], "list")
    assert infer_value("1\n2\n3", block=True) == ([1, 2, 3], "list")


def test_convert_value_schema_directed():
    """Verify schema-directed conversion adheres strictly to declared types."""
    # Declared str keeps 123 as string
    assert convert_value("123", block=False, type_="str") == "123"
    assert convert_value('"123"', block=False, type_="str") == "123"

    # Declared int
    assert convert_value("8080", block=False, type_="int") == 8080
    with pytest.raises(ConversionError, match="expected int"):
        convert_value("eighty", block=False, type_="int")

    # Declared bool
    assert convert_value("yes", block=False, type_="bool") is True
    assert convert_value("off", block=False, type_="bool") is False
    with pytest.raises(ConversionError, match="expected bool"):
        convert_value("maybe", block=False, type_="bool")

    # Declared list[int]
    assert convert_value("1, 2, 3", block=False, type_="list", item_type="int") == [1, 2, 3]
    with pytest.raises(ConversionError, match="item at index 1: expected int"):
        convert_value("1, x, 3", block=False, type_="list", item_type="int")

    # Scalar to list
    assert convert_value("80", block=False, type_="list", item_type="int") == [80]
    assert convert_value("", block=False, type_="list") == []
