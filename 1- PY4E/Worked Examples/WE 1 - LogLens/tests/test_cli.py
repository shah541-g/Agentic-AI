"""
End-to-end and integration tests for the LogLens CLI orchestration.
"""

import io
import sys
import pytest
from loglens.cli import main, run


def test_cli_suggest_exits_zero(capsys):
    """Running --suggest outputs suggested regex and exits 0."""
    sample = '192.168.1.5 - - [10/Oct/2025:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 1024'
    exit_code = main(["--suggest", sample])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Suggested Regular Expression" in captured.out
    assert "ip" in captured.out


def test_cli_missing_both_preset_and_regex(capsys):
    """Omitting both preset and regex prints a friendly error without traceback."""
    exit_code = main(["sample_logs/nginx.log"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Must specify exactly one of --preset or --regex" in captured.err


def test_cli_both_preset_and_regex(capsys):
    """Providing both preset and regex prints a friendly error."""
    exit_code = main(["sample_logs/nginx.log", "--preset", "nginx", "--regex", "(?P<x>.*)"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Must specify exactly one of --preset or --regex" in captured.err


def test_cli_missing_file_error(capsys):
    """Non-existent log file prints friendly error without traceback."""
    exit_code = main(["non_existent_file.log", "--preset", "nginx"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "Traceback" not in captured.err


def test_cli_parse_nginx_table(capsys):
    """Parsing sample_logs/nginx.log displays table with rows."""
    exit_code = main(["sample_logs/nginx.log", "--preset", "nginx"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Parsed Logs" in captured.out
    assert "Showing 17 of 17 rows" in captured.out
    assert "GET" in captured.out


def test_cli_parse_nginx_where_filter(capsys):
    """Filtering with --where 'status>=500' only outputs 5xx rows."""
    exit_code = main(["sample_logs/nginx.log", "--preset", "nginx", "--where", "status>=500"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "500" in captured.out or "502" in captured.out
    # 200 should not be in the status column of output
    assert "200" not in captured.out


def test_cli_parse_nginx_unmatched(capsys):
    """--show-unmatched displays the 3 malformed lines in a panel."""
    exit_code = main(["sample_logs/nginx.log", "--preset", "nginx", "--show-unmatched"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Unmatched Lines" in captured.out
    assert "MALFORMED LINE 1" in captured.out
    assert "BROKEN LINE 2" in captured.out
    assert "CORRUPTED LINE 3" in captured.out


def test_cli_parse_nginx_stats(capsys):
    """--stats displays summary, top IPs, and status code distribution."""
    exit_code = main(["sample_logs/nginx.log", "--preset", "nginx", "--stats"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "LogLens Statistics Overview" in captured.out
    assert "Top 5 Client IPs" in captured.out
    assert "Status Code" in captured.out
    assert "Errors Per Minute" in captured.out


def test_cli_export_csv_and_json(tmp_path, capsys):
    """--out correctly writes CSV and JSON files."""
    csv_out = tmp_path / "export.csv"
    exit_code = main(["sample_logs/nginx.log", "--preset", "nginx", "--out", str(csv_out)])
    assert exit_code == 0
    assert csv_out.exists()

    json_out = tmp_path / "export.json"
    exit_code = main(["sample_logs/nginx.log", "--preset", "nginx", "--out", str(json_out)])
    assert exit_code == 0
    assert json_out.exists()


def test_cli_stdin_reading(monkeypatch, capsys):
    """Piping lines into stdin works when file argument is omitted."""
    sample_content = "Oct 10 13:55:36 myhost sshd[1234]: Failed password for root from 10.0.0.9 port 22 ssh2\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(sample_content))
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)

    exit_code = main(["--preset", "syslog"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Parsed Logs" in captured.out
    assert "myhost" in captured.out
