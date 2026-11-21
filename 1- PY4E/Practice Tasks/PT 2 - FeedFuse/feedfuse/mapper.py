"""
Field extraction, dot-path navigation, and data mapping.
"""

from typing import Any, Dict, List, Optional, Tuple


def get_by_path(data: Any, path: str) -> Tuple[Any, bool]:
    """
    Traverse nested dictionaries and lists using dot-separated keys and integer indices.

    Args:
        data: Root object (usually dict or list).
        path: Dot path, e.g. "current_weather.temperature" or "items.0.name".
              An empty string "" returns data itself.

    Returns:
        (value, found): Tuple where found is True if the path exists, False otherwise.
    """
    if path == "" or path is None:
        return data, True

    segments = path.split(".")
    curr = data

    for seg in segments:
        if isinstance(curr, dict):
            if seg in curr:
                curr = curr[seg]
            else:
                return None, False
        elif isinstance(curr, list):
            try:
                idx = int(seg)
            except ValueError:
                return None, False
            if 0 <= idx < len(curr):
                curr = curr[idx]
            else:
                return None, False
        else:
            return None, False

    return curr, True


def apply_map(data: Any, mapping: Optional[Dict[str, str]]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Apply field mapping dictionary {output_name: dot.path} to data.

    If mapping is None or empty, returns data as-is (if dict) with no warnings.
    If a path is missing, maps the field to None and adds a warning.

    Args:
        data: The raw JSON response object.
        mapping: Optional dictionary mapping output keys to dot-paths.

    Returns:
        (mapped_dict, warnings): The transformed dictionary and list of warning strings.
    """
    if mapping is None:
        if isinstance(data, dict):
            return dict(data), []
        return data, []

    result: Dict[str, Any] = {}
    warnings: List[str] = []

    for out_key, dot_path in mapping.items():
        val, found = get_by_path(data, dot_path)
        if found:
            result[out_key] = val
        else:
            result[out_key] = None
            warnings.append(f"Path '{dot_path}' not found")

    return result, warnings


def extract_records(data: Any, path: str) -> Tuple[List[Any], List[str]]:
    """
    Extract a list of records from data for join mode.

    Args:
        data: The raw JSON response object.
        path: Dot path to a list inside data (use "" if response is itself a list).

    Returns:
        (records_list, warnings): The extracted list and any warnings.
    """
    if path == "" or path is None:
        if isinstance(data, list):
            return data, []
        return [], [f"Records path '{path}' did not resolve to a list (got {type(data).__name__})"]

    val, found = get_by_path(data, path)
    if not found:
        return [], [f"Path '{path}' not found"]

    if not isinstance(val, list):
        return [], [f"Records path '{path}' did not resolve to a list (got {type(val).__name__})"]

    return val, []
