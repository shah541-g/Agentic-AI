"""
Configuration loader, validator, and environment variable interpolation.
"""

import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import yaml

from feedfuse.models import Config, Source

NAME_REGEX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
ENV_REGEX = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class ConfigError(Exception):
    """Raised when configuration parsing or validation fails."""
    pass


class MissingEnvError(Exception):
    """Raised when an environment variable referenced in configuration is not set."""
    def __init__(self, var_name: str):
        super().__init__(f"Missing environment variable {var_name}")
        self.var_name = var_name


def interpolate_env(value: str) -> str:
    """
    Replace ${VAR} occurrences in value with os.environ['VAR'].

    Args:
        value: String potentially containing ${VAR} templates.

    Returns:
        String with environment variables substituted.

    Raises:
        MissingEnvError: If any referenced environment variable is not defined.
    """
    if not isinstance(value, str):
        return value

    def _replace(match: re.Match) -> str:
        var_name = match.group(1)
        if var_name not in os.environ:
            raise MissingEnvError(var_name)
        return os.environ[var_name]

    return ENV_REGEX.sub(_replace, value)


def interpolate_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively interpolate environment variables in a dictionary.

    Args:
        data: Dictionary of headers or parameters.

    Returns:
        New dictionary with string values interpolated.
    """
    result = {}
    for k, v in data.items():
        if isinstance(v, str):
            result[k] = interpolate_env(v)
        elif isinstance(v, dict):
            result[k] = interpolate_dict(v)
        elif isinstance(v, list):
            result[k] = [interpolate_env(x) if isinstance(x, str) else x for x in v]
        else:
            result[k] = v
    return result


def load_config(path: str) -> Config:
    """
    Read YAML file from path, validate structure and fields, and apply defaults.

    Args:
        path: Path to YAML configuration file.

    Returns:
        Validated Config dataclass instance.

    Raises:
        ConfigError: If file is missing, invalid YAML, or fails validation rules.
    """
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigError(f"Configuration file not found: {path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
    except yaml.YAMLError as err:
        raise ConfigError(f"Invalid YAML in configuration file '{path}': {err}") from err
    except Exception as err:
        raise ConfigError(f"Error reading configuration file '{path}': {err}") from err

    if not isinstance(raw_data, dict):
        raise ConfigError(f"Configuration file '{path}' must define a top-level mapping.")

    # Defaults block
    defaults = raw_data.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ConfigError("'defaults' must be a dictionary if provided.")

    default_timeout = float(defaults.get("timeout", 10.0))
    default_retries = int(defaults.get("retries", 2))
    if default_timeout <= 0:
        raise ConfigError("Default 'timeout' must be positive.")
    if not (0 <= default_retries <= 5):
        raise ConfigError("Default 'retries' must be between 0 and 5.")

    # Merge block
    merge_info = raw_data.get("merge", {})
    if not isinstance(merge_info, dict):
        raise ConfigError("'merge' must be a dictionary if provided.")

    merge_mode = merge_info.get("mode", "combine")
    if merge_mode not in ("combine", "join"):
        raise ConfigError(f"Invalid merge mode '{merge_mode}'. Must be 'combine' or 'join'.")

    # In YAML 1.1, unquoted 'on' can be parsed as boolean True
    join_on = merge_info.get("on")
    if join_on is None and True in merge_info:
        join_on = merge_info[True]

    join_type = merge_info.get("join_type", "inner")
    if merge_mode == "join":
        if not join_on or not isinstance(join_on, (str, int)) or not str(join_on).strip():
            raise ConfigError("Merge mode 'join' requires 'merge.on' to be specified.")
        join_on = str(join_on).strip()
        if join_type not in ("inner", "left"):
            raise ConfigError(f"Invalid join_type '{join_type}'. Must be 'inner' or 'left'.")

    # Sources block
    raw_sources = raw_data.get("sources")
    if not raw_sources or not isinstance(raw_sources, list):
        raise ConfigError("Configuration must define a non-empty 'sources' list.")

    seen_names = set()
    sources: List[Source] = []

    for idx, src in enumerate(raw_sources):
        if not isinstance(src, dict):
            raise ConfigError(f"Source at index {idx} must be a dictionary.")

        name = src.get("name")
        if not name or not isinstance(name, str):
            raise ConfigError(f"Source at index {idx} is missing a required 'name'.")

        if not NAME_REGEX.match(name):
            raise ConfigError(
                f"Source '{name}' has an invalid name. Must match '^[A-Za-z_][A-Za-z0-9_]*$'."
            )

        if name in seen_names:
            raise ConfigError(f"Duplicate source name '{name}'. Names must be unique.")
        seen_names.add(name)

        url = src.get("url")
        if not url or not isinstance(url, str):
            raise ConfigError(f"Source '{name}' is missing a required 'url'.")

        if not (url.startswith("http://") or url.startswith("https://")):
            raise ConfigError(
                f"Source '{name}' has invalid URL '{url}'. Must start with 'http://' or 'https://'."
            )

        # Timeout & retries
        src_timeout = float(src.get("timeout", default_timeout))
        if src_timeout <= 0:
            raise ConfigError(f"Source '{name}' has invalid timeout {src_timeout}. Must be > 0.")

        src_retries = int(src.get("retries", default_retries))
        if not (0 <= src_retries <= 5):
            raise ConfigError(f"Source '{name}' has invalid retries {src_retries}. Must be between 0 and 5.")

        params = src.get("params", {})
        if not isinstance(params, dict):
            raise ConfigError(f"Source '{name}' params must be a dictionary.")

        headers = src.get("headers", {})
        if not isinstance(headers, dict):
            raise ConfigError(f"Source '{name}' headers must be a dictionary.")

        map_dict = src.get("map")
        if map_dict is not None and not isinstance(map_dict, dict):
            raise ConfigError(f"Source '{name}' 'map' must be a dictionary.")

        records = src.get("records")
        if records is not None and not isinstance(records, str):
            raise ConfigError(f"Source '{name}' 'records' must be a string path.")

        # Join mode validations
        if merge_mode == "join":
            if records is None:
                raise ConfigError(
                    f"Source '{name}' in join mode must specify 'records' (use \"\" if the response itself is a list)."
                )
            if not map_dict or join_on not in map_dict:
                raise ConfigError(
                    f"Source '{name}' in join mode must include the join key '{join_on}' in its 'map'."
                )

        sources.append(
            Source(
                name=name,
                url=url,
                params=params,
                headers=headers,
                map=map_dict,
                records=records,
                timeout=src_timeout,
                retries=src_retries,
            )
        )

    return Config(
        sources=sources,
        merge_mode=merge_mode,
        join_on=join_on,
        join_type=join_type,
    )
