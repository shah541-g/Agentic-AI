"""
Unit tests for schema validation, bounds checking, and strict mode.
"""

from confcheck.models import Rule
from confcheck.parser import parse_text
from confcheck.validator import validate


def test_validator_type_conversions_and_bounds():
    """Verify type coercions, E201 type mismatches, and E202 range violations."""
    text = """
[server]
port = 99999
invalid_int = abc
debug = maybe
num_as_str = 123
"""
    schema = {
        "server": {
            "port": Rule(type="int", min=1, max=65535),
            "invalid_int": Rule(type="int"),
            "debug": Rule(type="bool"),
            "num_as_str": Rule(type="str"),
        }
    }
    res = parse_text(text)
    data, issues = validate(res, schema)
    codes = [i.code for i in issues]

    assert "E202" in codes  # 99999 > 65535
    assert "E201" in codes  # abc not int, maybe not bool
    assert data["server"]["num_as_str"] == "123"


def test_validator_list_element_mismatch():
    """Verify list[int] with a bad element produces E201 mentioning item index."""
    text = """
[app]
ports = 1, x, 3
"""
    schema = {"app": {"ports": Rule(type="list", item_type="int")}}
    res = parse_text(text)
    _, issues = validate(res, schema)
    assert len(issues) == 1
    assert issues[0].code == "E201"
    assert "item at index 1" in issues[0].message


def test_validator_scalar_to_list():
    """Scalar value with declared list type becomes a one-element list."""
    text = """
[app]
ports = 80
"""
    schema = {"app": {"ports": Rule(type="list", item_type="int")}}
    res = parse_text(text)
    data, issues = validate(res, schema)
    assert len(issues) == 0
    assert data["app"]["ports"] == [80]


def test_validator_defaults_and_required_and_choices():
    """Verify defaults are applied, required missing raises E101, and choices violation E203."""
    text = """
[app]
env = staging
"""
    schema = {
        "app": {
            "env": Rule(type="str", choices=["development", "production"]),
            "api_key": Rule(type="str", required=True),
            "retries": Rule(type="int", has_default=True, default=3),
        }
    }
    res = parse_text(text)
    data, issues = validate(res, schema)
    codes = [i.code for i in issues]

    assert "E203" in codes  # staging not in choices
    assert "E101" in codes  # api_key required but missing
    assert data["app"]["retries"] == 3


def test_validator_unknown_key_and_strict():
    """Unknown keys produce W101, elevated to error with strict=True."""
    text = """
[app]
unknown_opt = 42
"""
    schema = {"app": {}}
    res = parse_text(text)

    # Without strict -> warning W101
    _, issues = validate(res, schema, strict=False)
    assert len(issues) == 1
    assert issues[0].code == "W101"
    assert issues[0].severity == "warning"

    # With strict -> error W101
    _, issues_strict = validate(res, schema, strict=True)
    assert len(issues_strict) == 1
    assert issues_strict[0].code == "W101"
    assert issues_strict[0].severity == "error"
