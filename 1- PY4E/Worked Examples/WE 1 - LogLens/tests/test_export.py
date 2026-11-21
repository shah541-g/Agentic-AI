"""
Unit tests for the LogLens export module.
"""

import csv
import json
import pytest
from loglens.export import export_rows


def test_export_csv_round_trip(tmp_path):
    """Exporting to CSV produces valid CSV that matches input rows."""
    sample_rows = [
        {"ip": "192.168.1.1", "status": "200", "path": "/index.html"},
        {"ip": "192.168.1.2", "status": "404", "path": "/missing"},
    ]
    out_file = tmp_path / "result.csv"
    count = export_rows(sample_rows, str(out_file))
    assert count == 2
    assert out_file.exists()

    with open(out_file, "r", newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert reader == sample_rows


def test_export_json_round_trip(tmp_path):
    """Exporting to JSON produces valid JSON that matches input rows."""
    sample_rows = [
        {"ip": "10.0.0.1", "level": "ERROR", "message": "Failed"},
        {"ip": "10.0.0.2", "level": "INFO", "message": "OK"},
    ]
    out_file = tmp_path / "result.json"
    count = export_rows(sample_rows, str(out_file))
    assert count == 2
    assert out_file.exists()

    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data == sample_rows


def test_export_empty_results(tmp_path):
    """Exporting empty results creates valid empty files."""
    csv_file = tmp_path / "empty.csv"
    count_csv = export_rows([], str(csv_file))
    assert count_csv == 0
    assert csv_file.exists()
    assert csv_file.read_text(encoding="utf-8") == ""

    json_file = tmp_path / "empty.json"
    count_json = export_rows([], str(json_file))
    assert count_json == 0
    assert json_file.exists()
    assert json.loads(json_file.read_text(encoding="utf-8")) == []


def test_unsupported_extension_raises_value_error(tmp_path):
    """Exporting with unsupported file extensions raises ValueError."""
    bad_file = tmp_path / "result.txt"
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_rows([{"a": "b"}], str(bad_file))
