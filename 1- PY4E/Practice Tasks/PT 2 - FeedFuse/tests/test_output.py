"""
Unit tests for export and output functions.
"""

import csv
import json
import pytest
from feedfuse.output import export


def test_export_json(tmp_path):
    """export writes valid JSON format matching merged dictionary."""
    data = {
        "data": {"weather": {"temp": 25}},
        "status": {"weather": {"state": "ok", "ms": 120}},
    }
    out_file = tmp_path / "result.json"
    export(data, str(out_file))

    assert out_file.exists()
    with open(out_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == data


def test_export_csv_combine_mode(tmp_path):
    """export writes valid CSV in combine mode with columns source, field, value."""
    data = {
        "data": {
            "weather": {"temp": 25, "city": "NYC"},
            "crypto": {"price": 50000},
        },
        "status": {},
    }
    out_file = tmp_path / "result.csv"
    export(data, str(out_file))

    assert out_file.exists()
    with open(out_file, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 3
    assert rows[0] == {"source": "weather", "field": "temp", "value": "25"}
    assert rows[1] == {"source": "weather", "field": "city", "value": "NYC"}
    assert rows[2] == {"source": "crypto", "field": "price", "value": "50000"}


def test_export_csv_join_mode(tmp_path):
    """export writes valid CSV in join mode with record field headers."""
    data = {
        "data": [
            {"id": 1, "name": "Alice", "todo": "Task 1"},
            {"id": 2, "name": "Bob", "todo": "Task 2"},
        ],
        "status": {},
    }
    out_file = tmp_path / "joined.csv"
    export(data, str(out_file))

    assert out_file.exists()
    with open(out_file, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert rows[0] == {"id": "1", "name": "Alice", "todo": "Task 1"}
    assert rows[1] == {"id": "2", "name": "Bob", "todo": "Task 2"}


def test_unsupported_export_extension(tmp_path):
    """Exporting to unsupported extension raises ValueError."""
    bad_file = tmp_path / "result.txt"
    with pytest.raises(ValueError, match="Unsupported output format"):
        export({"data": {}}, str(bad_file))
