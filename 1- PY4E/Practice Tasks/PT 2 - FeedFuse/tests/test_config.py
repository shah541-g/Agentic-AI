"""
Unit tests for configuration loader and environment variable interpolation.
"""

import os
import pytest
from feedfuse.config import ConfigError, MissingEnvError, interpolate_env, load_config


def test_valid_config_loads_with_defaults(tmp_path):
    """Valid YAML config loads correctly and applies defaults."""
    cfg_file = tmp_path / "valid.yaml"
    cfg_file.write_text("""
defaults:
  timeout: 5.5
  retries: 3

sources:
  - name: test_api
    url: https://api.example.com/data
    map:
      val: item.value
""", encoding="utf-8")

    config = load_config(str(cfg_file))
    assert len(config.sources) == 1
    src = config.sources[0]
    assert src.name == "test_api"
    assert src.url == "https://api.example.com/data"
    assert src.timeout == 5.5
    assert src.retries == 3
    assert src.map == {"val": "item.value"}
    assert config.merge_mode == "combine"


def test_duplicate_source_names_raise_error(tmp_path):
    """Duplicate source names raise ConfigError."""
    cfg_file = tmp_path / "dup.yaml"
    cfg_file.write_text("""
sources:
  - name: my_source
    url: https://api.example.com/1
  - name: my_source
    url: https://api.example.com/2
""", encoding="utf-8")

    with pytest.raises(ConfigError, match="Duplicate source name 'my_source'"):
        load_config(str(cfg_file))


def test_missing_url_raises_error(tmp_path):
    """Source without url raises ConfigError."""
    cfg_file = tmp_path / "no_url.yaml"
    cfg_file.write_text("""
sources:
  - name: my_source
""", encoding="utf-8")

    with pytest.raises(ConfigError, match="missing a required 'url'"):
        load_config(str(cfg_file))


def test_bad_url_scheme_raises_error(tmp_path):
    """URL without http or https raises ConfigError."""
    cfg_file = tmp_path / "bad_url.yaml"
    cfg_file.write_text("""
sources:
  - name: my_source
    url: ftp://files.example.com/data.json
""", encoding="utf-8")

    with pytest.raises(ConfigError, match="Must start with 'http://' or 'https://'"):
        load_config(str(cfg_file))


def test_invalid_merge_mode_raises_error(tmp_path):
    """Invalid merge mode raises ConfigError."""
    cfg_file = tmp_path / "bad_mode.yaml"
    cfg_file.write_text("""
merge:
  mode: invalid_mode

sources:
  - name: s1
    url: https://api.example.com
""", encoding="utf-8")

    with pytest.raises(ConfigError, match="Invalid merge mode 'invalid_mode'"):
        load_config(str(cfg_file))


def test_join_mode_requires_on_and_fields(tmp_path):
    """Join mode without 'on' or missing records/map raises ConfigError."""
    # Missing on
    cfg_file1 = tmp_path / "join_no_on.yaml"
    cfg_file1.write_text("""
merge:
  mode: join

sources:
  - name: s1
    url: https://api.example.com
""", encoding="utf-8")

    with pytest.raises(ConfigError, match="Merge mode 'join' requires 'merge.on'"):
        load_config(str(cfg_file1))

    # Missing records
    cfg_file2 = tmp_path / "join_no_records.yaml"
    cfg_file2.write_text("""
merge:
  mode: join
  on: id

sources:
  - name: s1
    url: https://api.example.com
    map: { id: user_id }
""", encoding="utf-8")

    with pytest.raises(ConfigError, match="must specify 'records'"):
        load_config(str(cfg_file2))

    # Missing on key in map
    cfg_file3 = tmp_path / "join_no_key_in_map.yaml"
    cfg_file3.write_text("""
merge:
  mode: join
  on: id

sources:
  - name: s1
    url: https://api.example.com
    records: ""
    map: { other: user_id }
""", encoding="utf-8")

    with pytest.raises(ConfigError, match="must include the join key 'id' in its 'map'"):
        load_config(str(cfg_file3))


def test_interpolate_env_success_and_missing(monkeypatch):
    """interpolate_env replaces ${VAR} and raises MissingEnvError if missing."""
    monkeypatch.setenv("TEST_KEY", "secret_123")
    assert interpolate_env("Bearer ${TEST_KEY}") == "Bearer secret_123"
    assert interpolate_env("Prefix_${TEST_KEY}_suffix") == "Prefix_secret_123_suffix"

    with pytest.raises(MissingEnvError, match="Missing environment variable NON_EXISTENT_VAR"):
        interpolate_env("Bearer ${NON_EXISTENT_VAR}")
