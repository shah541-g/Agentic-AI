"""
End-to-end tests for the ConfCheck CLI.
"""

import io
import json
import pytest
from confcheck.cli import main


def test_cli_app_ini_success(capsys):
    """Parsing valid app.ini prints table and exits with code 0."""
    exit_code = main(["samples/app.ini"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Configuration Entries" in captured.out
    assert "server" in captured.out
    assert "8080" in captured.out


def test_cli_broken_ini_exit_code_1(capsys):
    """Parsing broken.ini reports four errors on stderr and exits with code 1."""
    exit_code = main(["samples/broken.ini"])
    assert exit_code == 1
    captured = capsys.readouterr()
    err = captured.err
    assert "error E004" in err
    assert "error E002" in err
    assert "error E001" in err
    assert "error E003" in err


def test_cli_missing_file_exit_code_2(capsys):
    """Non-existent file exits code 2 with friendly error."""
    exit_code = main(["non_existent.ini"])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "Traceback" not in captured.err


def test_cli_invalid_schema_exit_code_2(tmp_path, capsys):
    """Invalid schema file exits code 2."""
    bad_schema = tmp_path / "bad.ini"
    bad_schema.write_text("[s]\nk = invalid_rule", encoding="utf-8")

    exit_code = main(["samples/app.ini", "--schema", str(bad_schema)])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_cli_json_output(capsys):
    """--json outputs correctly structured and typed JSON."""
    exit_code = main(["samples/app.ini", "--schema", "samples/schema.ini", "--json"])
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert data["_global"]["app_name"] == "LogLens"
    assert data["server"]["port"] == 8080
    assert data["server"]["debug"] is True
    assert data["server"]["allowed_hosts"] == ["localhost", "127.0.0.1", "example.com"]
    # Schema default applied:
    assert data["server"]["log_level"] == "info"


def test_cli_get_int_bool_list(capsys):
    """--get extracts int, bool, and list (one item per line)."""
    # int
    code1 = main(["samples/app.ini", "--get", "server/port"])
    assert code1 == 0
    assert capsys.readouterr().out.strip() == "8080"

    # bool
    code2 = main(["samples/app.ini", "--get", "server/debug"])
    assert code2 == 0
    assert capsys.readouterr().out.strip() == "true"

    # list
    code3 = main(["samples/app.ini", "--get", "server/allowed_hosts"])
    assert code3 == 0
    out3 = capsys.readouterr().out.strip().splitlines()
    assert out3 == ["localhost", "127.0.0.1", "example.com"]

    # global key
    code4 = main(["samples/app.ini", "--get", "app_name"])
    assert code4 == 0
    assert capsys.readouterr().out.strip() == "LogLens"

    # missing key
    code5 = main(["samples/app.ini", "--get", "server/missing_key"])
    assert code5 == 1
    assert "Error: key 'server/missing_key' not found" in capsys.readouterr().err


def test_cli_stdin_reading(monkeypatch, capsys):
    """Reading from stdin via '-' works seamlessly."""
    sample_ini = "[app]\nname = TestStdin\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(sample_ini))

    exit_code = main(["-", "--json"])
    assert exit_code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["app"]["name"] == "TestStdin"


def test_cli_strict_mode(tmp_path, capsys):
    """--strict elevates unknown key warning W101 to error and exits 1."""
    cfg = tmp_path / "extra.ini"
    cfg.write_text("""
app_name = TestApp

[database]
url = postgres://localhost/db

[server]
host = 127.0.0.1
port = 8080
extra_setting = true
""", encoding="utf-8")

    # Without strict: exit 0, W101 is warning
    code_lenient = main([str(cfg), "--schema", "samples/schema.ini"])
    assert code_lenient == 0
    assert "warning W101" in capsys.readouterr().err

    # With strict: exit 1, W101 is error
    code_strict = main([str(cfg), "--schema", "samples/schema.ini", "--strict"])
    assert code_strict == 1
    assert "error W101" in capsys.readouterr().err
