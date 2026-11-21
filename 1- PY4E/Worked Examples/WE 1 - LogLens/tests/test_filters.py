"""
Unit tests for the LogLens filters module.
"""

import pytest
from loglens.filters import parse_where, apply_filters


def test_parse_where_valid():
    """parse_where correctly extracts field, operator, and value."""
    assert parse_where("status>=500") == ("status", ">=", "500")
    assert parse_where("method=POST") == ("method", "=", "POST")
    assert parse_where("path~admin") == ("path", "~", "admin")
    assert parse_where("path~/api/v1") == ("path", "~", "/api/v1")
    assert parse_where('user!="root"') == ("user", "!=", "root")


def test_parse_where_invalid_syntax():
    """Invalid syntax or unknown operators raise ValueError."""
    with pytest.raises(ValueError, match="Invalid operator '>>'"):
        parse_where("status>>5")

    with pytest.raises(ValueError, match="Invalid operator '=='"):
        parse_where("status==200")

    with pytest.raises(ValueError, match="Invalid filter expression"):
        parse_where("onlyfield")

    with pytest.raises(ValueError, match="Missing value"):
        parse_where("status>=")


def test_numeric_comparison_greater_than():
    """status>=500 compares numerically, so 1000 >= 500 is True."""
    rows = [
        {"ip": "1.1.1.1", "status": "200"},
        {"ip": "1.1.1.2", "status": "500"},
        {"ip": "1.1.1.3", "status": "502"},
        {"ip": "1.1.1.4", "status": "1000"},  # Alphabetically "1000" < "500", but numerically > 500
        {"ip": "1.1.1.5", "status": "404"},
    ]
    filtered = list(apply_filters(rows, [("status", ">=", "500")]))
    statuses = [r["status"] for r in filtered]
    assert statuses == ["500", "502", "1000"]


def test_case_insensitive_string_equality():
    """level=error matches ERROR case-insensitively."""
    rows = [
        {"level": "INFO", "msg": "ok"},
        {"level": "ERROR", "msg": "failed"},
        {"level": "error", "msg": "failed again"},
        {"level": "WARN", "msg": "caution"},
    ]
    filtered = list(apply_filters(rows, [("level", "=", "error")]))
    assert len(filtered) == 2
    assert all(r["level"].upper() == "ERROR" for r in filtered)


def test_regex_search_operator():
    """path~admin matches /admin/login case-insensitively."""
    rows = [
        {"path": "/index.html"},
        {"path": "/admin/login"},
        {"path": "/ADMIN/dashboard"},
        {"path": "/user/profile"},
    ]
    filtered = list(apply_filters(rows, [("path", "~", "admin")]))
    paths = [r["path"] for r in filtered]
    assert paths == ["/admin/login", "/ADMIN/dashboard"]


def test_multiple_filters_and_logic():
    """Multiple filters are combined with AND logic."""
    rows = [
        {"method": "GET", "status": "200"},
        {"method": "POST", "status": "500"},
        {"method": "POST", "status": "200"},
        {"method": "GET", "status": "500"},
    ]
    conditions = [("method", "=", "POST"), ("status", ">=", "400")]
    filtered = list(apply_filters(rows, conditions))
    assert len(filtered) == 1
    assert filtered[0] == {"method": "POST", "status": "500"}


def test_unknown_field_raises_value_error():
    """Specifying an unknown field in --where raises ValueError listing available fields."""
    rows = [{"status": "200", "path": "/"}]
    with pytest.raises(ValueError, match="Unknown field 'nonexistent'. Available fields: path, status"):
        list(apply_filters(rows, [("nonexistent", "=", "val")]))


def test_invalid_regex_in_filter_raises_value_error():
    """Malformed regex in ~ filter raises ValueError."""
    rows = [{"path": "/test"}]
    with pytest.raises(ValueError, match="Invalid regular expression"):
        list(apply_filters(rows, [("path", "~", "[unclosed")]))
