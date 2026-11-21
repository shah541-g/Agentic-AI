"""
Unit tests for schema rule parsing and schema loading.
"""

import pytest
from confcheck.schema import SchemaError, load_schema, parse_rule


def test_parse_rule_valid_types_and_options():
    """Verify parse_rule correctly parses various valid rules."""
    r1 = parse_rule("str, required", where="test")
    assert r1.type == "str"
    assert r1.required is True

    r2 = parse_rule("int, min=1, max=65535, default=80", where="test")
    assert r2.type == "int"
    assert r2.min == 1
    assert r2.max == 65535
    assert r2.default == 80
    assert r2.has_default is True

    r3 = parse_rule("list[int], default=1|2|3", where="test")
    assert r3.type == "list"
    assert r3.item_type == "int"
    assert r3.default == [1, 2, 3]

    r4 = parse_rule("str, default=info, choices=debug|info|warn", where="test")
    assert r4.type == "str"
    assert r4.default == "info"
    assert r4.choices == ["debug", "info", "warn"]


def test_parse_rule_invalid_options_raise_schema_error():
    """Verify invalid options, wrong types, or garbage rules raise SchemaError."""
    # Unknown option
    with pytest.raises(SchemaError, match="unknown schema option 'unknown'"):
        parse_rule("str, unknown=123", where="test")

    # min on a str
    with pytest.raises(SchemaError, match="'min' option only applies to int"):
        parse_rule("str, min=5", where="test")

    # item type on non-list
    with pytest.raises(SchemaError, match="only allowed on list types"):
        parse_rule("int[str]", where="test")

    # garbage rule
    with pytest.raises(SchemaError, match="invalid schema rule"):
        parse_rule("unsupported_type", where="test")


def test_load_schema_from_file(tmp_path):
    """Verify load_schema reads an INI schema file and creates rule dictionary."""
    schema_file = tmp_path / "schema.ini"
    schema_file.write_text("""
[server]
port = int, required, min=1, max=65535
debug = bool, default=false
""", encoding="utf-8")

    schema = load_schema(str(schema_file))
    assert "server" in schema
    assert "port" in schema["server"]
    assert schema["server"]["port"].type == "int"
    assert schema["server"]["debug"].type == "bool"
    assert schema["server"]["debug"].default is False
