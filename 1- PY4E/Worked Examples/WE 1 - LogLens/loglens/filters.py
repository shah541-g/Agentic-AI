"""
Filtering engine for LogLens parsed log rows.

Supports filtering conditions specified via --where flags, such as:
    --where "status>=500"
    --where "method=POST"
    --where "path~admin"

For Regex Practitioners:
- The `~` operator performs a case-insensitive regex search (`re.search(val, row_val, re.IGNORECASE)`).
- Multiple --where conditions are evaluated with boolean AND logic.
- Numeric fields (convertible to float) are compared mathematically rather than lexicographically,
  preventing classic string sorting bugs (e.g. "1000" > "500").
"""

import re
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

VALID_OPERATORS = (">=", "<=", "!=", "=", ">", "<", "~")


def parse_where(expr: str) -> Tuple[str, str, str]:
    """
    Parse a single where expression into (field, operator, value).

    Supported operators:
        >=, <=, !=, =, >, <, ~ (regex search, case-insensitive)

    Args:
        expr: Expression string, e.g. "status>=500" or "method=POST"

    Returns:
        Tuple of (field_name, operator, value)

    Raises:
        ValueError: If expression syntax is malformed, operator is invalid,
                    or value is missing.
    """
    if not expr or not expr.strip():
        raise ValueError("Empty filter expression provided.")

    # Match field name, followed by operator symbols, followed by value
    match = re.match(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([><=!~]+)\s*(.*)$", expr)
    if not match:
        raise ValueError(
            f"Invalid filter expression: '{expr}'. Expected format: <field><operator><value>, e.g. status>=500"
        )

    field, op, val = match.groups()

    if op not in VALID_OPERATORS:
        raise ValueError(
            f"Invalid operator '{op}' in expression '{expr}'. "
            f"Supported operators are: {', '.join(VALID_OPERATORS)}"
        )

    val = val.strip()
    if not val:
        raise ValueError(f"Missing value in filter expression: '{expr}'")

    # Strip matching outer quotes if provided: 'val' or "val"
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        val = val[1:-1]

    return field, op, val


def _evaluate_condition(
    row_val: str,
    op: str,
    cond_val: str,
    compiled_regex: Optional[re.Pattern] = None,
) -> bool:
    """Evaluate a single condition against a row value."""
    # Regex match (~ operator)
    if op == "~":
        if compiled_regex is not None:
            return bool(compiled_regex.search(row_val))
        return bool(re.search(cond_val, row_val, re.IGNORECASE))

    # Check if both can be compared numerically
    try:
        num_row = float(row_val)
        num_cond = float(cond_val)
        is_numeric = True
    except (ValueError, TypeError):
        is_numeric = False

    if is_numeric:
        if op == "=":
            return num_row == num_cond
        elif op == "!=":
            return num_row != num_cond
        elif op == ">=":
            return num_row >= num_cond
        elif op == "<=":
            return num_row <= num_cond
        elif op == ">":
            return num_row > num_cond
        elif op == "<":
            return num_row < num_cond
    else:
        # String comparison: = and != are case-insensitive
        if op == "=":
            return row_val.lower() == cond_val.lower()
        elif op == "!=":
            return row_val.lower() != cond_val.lower()
        elif op == ">=":
            return row_val >= cond_val
        elif op == "<=":
            return row_val <= cond_val
        elif op == ">":
            return row_val > cond_val
        elif op == "<":
            return row_val < cond_val

    return False


def apply_filters(
    rows: Iterable[Dict[str, str]], conditions: List[Tuple[str, str, str]]
) -> Iterator[Dict[str, str]]:
    """
    Filter rows where ALL conditions must pass (AND logic).

    Memory-safe generator that yields matching rows one by one.
    Field names are validated against the first row once.

    Args:
        rows: Iterable of parsed row dictionaries.
        conditions: List of (field, operator, value) tuples.

    Yields:
        Filtered row dictionaries.

    Raises:
        ValueError: If a condition references a field not present in the rows,
                    or if a regex pattern in a ~ condition is invalid.
    """
    if not conditions:
        yield from rows
        return

    # Pre-compile any regex search patterns for performance & early error detection
    compiled_conditions: List[Tuple[str, str, str, Optional[re.Pattern]]] = []
    for field, op, val in conditions:
        pattern: Optional[re.Pattern] = None
        if op == "~":
            try:
                pattern = re.compile(val, re.IGNORECASE)
            except re.error as err:
                raise ValueError(
                    f"Invalid regular expression in filter '{field}~{val}': {err}"
                ) from err
        compiled_conditions.append((field, op, val, pattern))

    iterator = iter(rows)
    try:
        first_row = next(iterator)
    except StopIteration:
        return

    # Validate conditions against first row's field names once
    available_fields = set(first_row.keys())
    for field, _, _, _ in compiled_conditions:
        if field not in available_fields:
            avail_str = ", ".join(sorted(available_fields))
            raise ValueError(
                f"Unknown field '{field}'. Available fields: {avail_str}"
            )

    # Check and yield first row if it matches
    if all(
        _evaluate_condition(first_row.get(f, ""), op, val, pat)
        for f, op, val, pat in compiled_conditions
    ):
        yield first_row

    # Check and yield remaining rows
    for row in iterator:
        if all(
            _evaluate_condition(row.get(f, ""), op, val, pat)
            for f, op, val, pat in compiled_conditions
        ):
            yield row
