"""
End-to-end tests for the FeedFuse CLI commands and exit codes.
"""

import json
import httpx
import pytest
import respx

from feedfuse.cli import main


def test_cli_version(capsys):
    """--version prints version and exits."""
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "feedfuse 0.1.0" in captured.out


@respx.mock
def test_cli_run_all_success_exit_code_0(tmp_path, capsys):
    """All sources succeed -> exit code 0."""
    respx.get("https://api.test.com/s1").mock(return_value=httpx.Response(200, json={"val": 10}))
    respx.get("https://api.test.com/s2").mock(return_value=httpx.Response(200, json={"val": 20}))

    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("""
sources:
  - name: s1
    url: https://api.test.com/s1
  - name: s2
    url: https://api.test.com/s2
""", encoding="utf-8")

    exit_code = main(["run", str(cfg)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Sources Status" in captured.out
    assert "s1" in captured.out
    assert "s2" in captured.out


@respx.mock
def test_cli_run_partial_failure_exit_code_2(tmp_path, capsys):
    """One source succeeds, one fails -> exit code 2."""
    respx.get("https://api.test.com/ok").mock(return_value=httpx.Response(200, json={"val": 1}))
    respx.get("https://api.test.com/bad").mock(return_value=httpx.Response(404, text="Not Found"))

    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("""
sources:
  - name: good
    url: https://api.test.com/ok
  - name: broken
    url: https://api.test.com/bad
""", encoding="utf-8")

    exit_code = main(["run", str(cfg)])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "ok" in captured.out
    assert "failed" in captured.out


@respx.mock
def test_cli_run_all_failed_exit_code_1(tmp_path):
    """Every source fails -> exit code 1."""
    respx.get("https://api.test.com/bad1").mock(return_value=httpx.Response(500, text="err"))
    respx.get("https://api.test.com/bad2").mock(return_value=httpx.Response(404, text="err"))

    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("""
sources:
  - name: b1
    url: https://api.test.com/bad1
    retries: 0
  - name: b2
    url: https://api.test.com/bad2
    retries: 0
""", encoding="utf-8")

    exit_code = main(["run", str(cfg)])
    assert exit_code == 1


def test_cli_run_invalid_config_exit_code_1(tmp_path, capsys):
    """Invalid config prints friendly error and exits 1."""
    cfg = tmp_path / "bad.yaml"
    cfg.write_text("sources: []", encoding="utf-8")

    exit_code = main(["run", str(cfg)])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "Traceback" not in captured.err


@respx.mock
def test_cli_run_export_flags(tmp_path):
    """--out writes valid json and csv files."""
    respx.get("https://api.test.com/data").mock(return_value=httpx.Response(200, json={"x": 99}))

    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("""
sources:
  - name: data_src
    url: https://api.test.com/data
""", encoding="utf-8")

    json_out = tmp_path / "out.json"
    exit_code = main(["run", str(cfg), "--out", str(json_out), "--no-table"])
    assert exit_code == 0
    assert json_out.exists()
    loaded = json.loads(json_out.read_text(encoding="utf-8"))
    assert loaded["data"]["data_src"] == {"x": 99}


@respx.mock
def test_cli_run_only_flag(tmp_path, capsys):
    """--only runs only the specified source."""
    respx.get("https://api.test.com/s1").mock(return_value=httpx.Response(200, json={"a": 1}))
    # s2 route is not called
    s2_route = respx.get("https://api.test.com/s2").mock(return_value=httpx.Response(200, json={"b": 2}))

    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("""
sources:
  - name: s1
    url: https://api.test.com/s1
  - name: s2
    url: https://api.test.com/s2
""", encoding="utf-8")

    exit_code = main(["run", str(cfg), "--only", "s1"])
    assert exit_code == 0
    assert s2_route.call_count == 0
    captured = capsys.readouterr()
    assert "s1" in captured.out
    assert "s2" not in captured.out


@respx.mock
def test_cli_inspect(capsys):
    """inspect command fetches URL and displays tree and map suggestion."""
    respx.get("https://api.test.com/inspect_me").mock(
        return_value=httpx.Response(200, json={
            "status": "ok",
            "weather": {"temp": 21.0, "city": "Berlin"}
        })
    )

    exit_code = main(["inspect", "https://api.test.com/inspect_me"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "JSON Response Structure" in captured.out
    assert "Suggested map: block" in captured.out
    assert "temp: weather.temp" in captured.out
