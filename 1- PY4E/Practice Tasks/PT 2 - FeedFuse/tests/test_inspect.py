"""
Unit tests for inspect and map suggestion.
"""

from feedfuse.inspect import build_tree, suggest_map


def test_suggest_map_nested_dict():
    """suggest_map extracts leaf fields with correct dot paths and handles collisions."""
    data = {
        "current_weather": {
            "temperature": 29.1,
            "windspeed": 8.4,
            "units": {
                "temperature": "C",  # Collides with temperature above
            },
        },
        "meta": {
            "cached": None,  # null leaf should be skipped
        },
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},  # Beyond index 0 should not be suggested
        ],
    }

    yaml_block = suggest_map(data, max_depth=3)
    assert "map:" in yaml_block
    assert "temperature: current_weather.temperature" in yaml_block
    assert "windspeed: current_weather.windspeed" in yaml_block
    # Collision handled:
    assert "temperature_2: current_weather.units.temperature" in yaml_block
    # List index 0 leaf:
    assert "id: users.0.id" in yaml_block
    assert "name: users.0.name" in yaml_block
    # Null leaf skipped:
    assert "cached" not in yaml_block


def test_build_tree_constructs_rich_tree():
    """build_tree builds a valid Tree object without crashing."""
    data = {
        "title": "A" * 50,  # Long string to test truncation
        "count": 10,
        "items": [1, 2, 3],
        "nested": {"key": "val"},
    }
    tree = build_tree(data)
    assert tree is not None
    assert tree.label is not None
