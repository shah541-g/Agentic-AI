"""
Unit tests for dot-path traversal, map application, and record extraction.
"""

from feedfuse.mapper import apply_map, extract_records, get_by_path


def test_get_by_path_nested_and_list_index():
    """get_by_path handles nested dictionaries and list indices."""
    data = {
        "weather": {
            "temp": 25.5,
            "forecast": ["sunny", "cloudy"],
        },
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ],
    }

    val, found = get_by_path(data, "weather.temp")
    assert found is True
    assert val == 25.5

    val, found = get_by_path(data, "weather.forecast.1")
    assert found is True
    assert val == "cloudy"

    val, found = get_by_path(data, "users.0.name")
    assert found is True
    assert val == "Alice"

    # Empty path returns root
    val, found = get_by_path(data, "")
    assert found is True
    assert val == data


def test_get_by_path_missing_paths():
    """get_by_path returns (None, False) for missing keys and out-of-range indices."""
    data = {"a": {"b": 1}, "c": [10, 20]}

    val, found = get_by_path(data, "a.missing")
    assert found is False
    assert val is None

    val, found = get_by_path(data, "c.5")
    assert found is False
    assert val is None

    val, found = get_by_path(data, "c.not_a_number")
    assert found is False
    assert val is None


def test_apply_map_with_warnings():
    """apply_map transforms keys and returns warnings for missing paths."""
    data = {
        "user": {"name": "Charlie", "age": 30},
        "status": "active",
    }
    mapping = {
        "username": "user.name",
        "user_age": "user.age",
        "email": "user.email",  # missing
    }

    mapped, warnings = apply_map(data, mapping)
    assert mapped == {
        "username": "Charlie",
        "user_age": 30,
        "email": None,
    }
    assert len(warnings) == 1
    assert "Path 'user.email' not found" in warnings[0]


def test_extract_records():
    """extract_records extracts top-level or nested lists, and handles non-lists."""
    # Direct list at root
    root_list = [{"id": 1}, {"id": 2}]
    records, warnings = extract_records(root_list, "")
    assert records == root_list
    assert warnings == []

    # Nested list
    nested_data = {"data": {"items": [10, 20, 30]}}
    records, warnings = extract_records(nested_data, "data.items")
    assert records == [10, 20, 30]
    assert warnings == []

    # Non-list returns [] and warning
    not_a_list = {"items": "not a list"}
    records, warnings = extract_records(not_a_list, "items")
    assert records == []
    assert len(warnings) == 1
    assert "did not resolve to a list" in warnings[0]

    # Missing path returns [] and warning
    records, warnings = extract_records(not_a_list, "nonexistent")
    assert records == []
    assert len(warnings) == 1
    assert "Path 'nonexistent' not found" in warnings[0]
