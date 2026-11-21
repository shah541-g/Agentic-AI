"""CLI integration tests and exit code verifications."""
import os
import pytest
from linkatlas.cli import run


def test_cli_invalid_depth_exits_2(capsys):
    code = run(["https://example.com", "--depth", "3"])
    assert code == 2
    captured = capsys.readouterr()
    assert "Error: --depth must be 0, 1 or 2" in captured.err


def test_cli_invalid_max_pages_exits_2(capsys):
    code = run(["https://example.com", "--max-pages", "0"])
    assert code == 2
    captured = capsys.readouterr()
    assert "Error: --max-pages must be at least 1" in captured.err


def test_cli_invalid_delay_exits_2(capsys):
    code = run(["https://example.com", "--delay", "-1"])
    assert code == 2
    captured = capsys.readouterr()
    assert "Error: --delay must be non-negative" in captured.err


def test_cli_fake_site_success(fake_site, tmp_path):
    fake_site.requests.clear()
    out_json = tmp_path / "out.json"
    out_csv = tmp_path / "out.csv"

    code = run([
        fake_site.url,
        "--depth", "1",
        "--delay", "0.0",
        "--timeout", "0.5",
        "--retries", "0",
        "--out", str(out_json),
        "--format", "json",
        "--format", "graphml",
        "--format", "dot",
        "--csv", str(out_csv),
        "--quiet",
    ])

    assert code == 0
    assert out_json.exists()
    assert (tmp_path / "out.graphml").exists()
    assert (tmp_path / "out.dot").exists()
    assert out_csv.exists()


def test_cli_unreachable_seed_exits_1(tmp_path):
    # Port 65432 should not be listening
    code = run([
        "http://127.0.0.1:65432/",
        "--depth", "0",
        "--timeout", "0.2",
        "--retries", "0",
        "--quiet",
    ])
    assert code == 1


def test_cli_output_write_error_exits_2(fake_site):
    # Non-existent or invalid directory path
    invalid_path = "Z:\\non_existent_drive_12345\\impossible\\graph.json"
    code = run([
        fake_site.url,
        "--depth", "0",
        "--delay", "0.0",
        "--out", invalid_path,
        "--quiet",
    ])
    assert code == 2
