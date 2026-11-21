"""
Value processing: comment stripping, unquoting, list splitting, type inference,
and schema-directed type conversion.
"""

import re
from typing import Any, List, Optional, Tuple

from confcheck.patterns import (
    BOOL,
    ESCAPE,
    INLINE_COMMENT,
    INT,
    LIST_ITEM,
    QUOTED,
    QUOTED_SPAN,
)


class ConversionError(ValueError):
    """Raised when a value cannot be converted to the schema's declared type."""
    pass


def strip_inline_comment(text: str) -> str:
    """
    Remove an inline comment (; or # preceded by whitespace outside quotes).
    Returns the body with trailing whitespace stripped.
    """
    m = INLINE_COMMENT.match(text)
    if m:
        return m.group("body").rstrip()
    return text.rstrip()


def _unescape_char(m: re.Match) -> str:
    """Escape translation: \\n -> newline, \\t -> tab, anything else -> char."""
    c = m.group(1)
    if c == "n":
        return "\n"
    if c == "t":
        return "\t"
    return c


def unquote(text: str) -> str:
    """
    If text is fully enclosed in matching quotes, remove quotes and resolve escapes.
    Otherwise return text unchanged.
    """
    m = QUOTED.match(text)
    if m:
        body = m.group("body")
        return ESCAPE.sub(_unescape_char, body)
    return text


def split_list(raw: str) -> List[str]:
    """
    Split a comma-separated list on commas outside quotes.
    Trims items and drops empty items; items retain their quotes.
    """
    items = []
    for match in LIST_ITEM.finditer(raw):
        item = match.group(0).strip()
        if item:
            items.append(item)
    return items


def has_list_comma(raw: str) -> bool:
    """
    Check if raw contains a comma outside quoted strings.
    """
    remaining = QUOTED_SPAN.sub("", raw)
    return "," in remaining


def _infer_single_item(item: str) -> Any:
    """Infer type of a list element using rules 1, 3, 4, else str."""
    if QUOTED.match(item):
        return unquote(item)
    m_bool = BOOL.match(item)
    if m_bool:
        return bool(m_bool.group("true"))
    if INT.match(item):
        return int(item)
    return item


def infer_value(raw: str, block: bool) -> Tuple[Any, str]:
    """
    Infer Python value and type name without a schema, following section 5 priority order:
    1. Fully quoted -> str
    2. Block list -> list
    3. BOOL -> bool (true/yes/on -> True, false/no/off -> False)
    4. INT -> int
    5. Comma outside quotes -> list
    6. Anything else -> str
    """
    # 1. Fully quoted -> str
    if QUOTED.match(raw):
        return unquote(raw), "str"

    # 2. Block list -> list
    if block:
        items = [line.strip() for line in raw.split("\n") if line.strip()]
        return [_infer_single_item(it) for it in items], "list"

    # 3. Matches BOOL -> bool
    m_bool = BOOL.match(raw)
    if m_bool:
        return bool(m_bool.group("true")), "bool"

    # 4. Matches INT -> int
    if INT.match(raw):
        return int(raw), "int"

    # 5. Contains a comma outside quotes -> list
    if has_list_comma(raw):
        items = split_list(raw)
        return [_infer_single_item(it) for it in items], "list"

    # 6. Anything else -> str
    return raw, "str"


def convert_value(raw: str, block: bool, type_: str, item_type: Optional[str] = None) -> Any:
    """
    Convert raw string to the declared schema type.

    Args:
        raw: Raw value string.
        block: True if this is a block list entry.
        type_: Declared type ("str", "int", "bool", "list").
        item_type: Optional list item type ("str", "int", "bool").

    Returns:
        Converted Python object.

    Raises:
        ConversionError: If the raw string cannot be converted to type_.
    """
    if type_ == "str":
        if QUOTED.match(raw):
            return unquote(raw)
        return raw

    if type_ == "int":
        trimmed = raw.strip()
        if not INT.match(trimmed):
            raise ConversionError(f"expected int, got {raw!r}")
        return int(trimmed)

    if type_ == "bool":
        trimmed = raw.strip()
        m = BOOL.match(trimmed)
        if not m:
            raise ConversionError(f"expected bool, got {raw!r}")
        return bool(m.group("true"))

    if type_ == "list":
        if block:
            items = [line.strip() for line in raw.split("\n") if line.strip()]
        elif has_list_comma(raw):
            items = split_list(raw)
        elif raw.strip() == "":
            items = []
        else:
            # Single scalar becomes a one-item list
            items = [raw.strip()]

        if item_type is None or item_type == "str":
            return [unquote(it) if QUOTED.match(it) else it for it in items]
        elif item_type == "int":
            res = []
            for idx, it in enumerate(items):
                clean = unquote(it) if QUOTED.match(it) else it
                clean_trimmed = clean.strip()
                if not INT.match(clean_trimmed):
                    raise ConversionError(f"item at index {idx}: expected int, got {it!r}")
                res.append(int(clean_trimmed))
            return res
        elif item_type == "bool":
            res = []
            for idx, it in enumerate(items):
                clean = unquote(it) if QUOTED.match(it) else it
                clean_trimmed = clean.strip()
                m = BOOL.match(clean_trimmed)
                if not m:
                    raise ConversionError(f"item at index {idx}: expected bool, got {it!r}")
                res.append(bool(m.group("true")))
            return res
        else:
            raise ConversionError(f"unknown list item type '{item_type}'")

    raise ConversionError(f"unknown type '{type_}'")
