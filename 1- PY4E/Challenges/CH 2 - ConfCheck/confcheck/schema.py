"""
Schema parsing and validation rules definition.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from confcheck.models import Rule, Schema
from confcheck.parser import parse_text
from confcheck.patterns import INT, RULE, RULE_OPT
from confcheck.values import ConversionError, convert_value


class SchemaError(ValueError):
    """Raised when a schema rule is invalid or schema syntax fails (E301)."""
    code = "E301"


def parse_rule(raw: str, where: str) -> Rule:
    """
    Parse a single schema rule string (e.g. 'int, required, min=1, max=65535').

    Args:
        raw: Rule string.
        where: Context description for error reporting (e.g. '[server] port').

    Returns:
        Rule dataclass instance.

    Raises:
        SchemaError: If rule syntax is invalid or options are incompatible.
    """
    m = RULE.match(raw.strip())
    if not m:
        raise SchemaError(f"invalid schema rule '{raw}' in {where}")

    type_ = m.group("type")
    item_type = m.group("item")
    opts_str = m.group("opts")

    if item_type is not None and type_ != "list":
        raise SchemaError(f"item type '[{item_type}]' is only allowed on list types, not '{type_}' in {where}")

    required = False
    has_default = False
    default_val: Any = None
    min_val: Optional[int] = None
    max_val: Optional[int] = None
    choices: Optional[List[str]] = None

    for opt_match in RULE_OPT.finditer(opts_str):
        name = opt_match.group("name")
        val = opt_match.group("val")

        if name == "required":
            required = True
        elif name == "default":
            if val is None:
                raise SchemaError(f"'default' option requires a value in {where}")
            has_default = True
            try:
                if type_ == "list":
                    # For lists, separate default items with |
                    converted_list_str = val.replace("|", ",")
                    default_val = convert_value(converted_list_str, block=False, type_="list", item_type=item_type)
                else:
                    default_val = convert_value(val, block=False, type_=type_, item_type=item_type)
            except ConversionError as err:
                raise SchemaError(f"invalid default value '{val}' in {where}: {err}") from err

        elif name == "min":
            if val is None or not INT.match(val):
                raise SchemaError(f"'min' option requires an integer in {where}")
            if type_ != "int" and not (type_ == "list" and item_type == "int"):
                raise SchemaError(f"'min' option only applies to int or list[int], not '{type_}' in {where}")
            min_val = int(val)

        elif name == "max":
            if val is None or not INT.match(val):
                raise SchemaError(f"'max' option requires an integer in {where}")
            if type_ != "int" and not (type_ == "list" and item_type == "int"):
                raise SchemaError(f"'max' option only applies to int or list[int], not '{type_}' in {where}")
            max_val = int(val)

        elif name == "choices":
            if val is None or not val.strip():
                raise SchemaError(f"'choices' option requires values separated by '|' in {where}")
            valid_type = type_ in ("str", "int") or (type_ == "list" and item_type in ("str", "int", None))
            if not valid_type:
                raise SchemaError(f"'choices' option cannot be applied to '{type_}' in {where}")
            choices = val.split("|")

        else:
            raise SchemaError(f"unknown schema option '{name}' in {where}")

    return Rule(
        type=type_,
        item_type=item_type,
        required=required,
        has_default=has_default,
        default=default_val,
        min=min_val,
        max=max_val,
        choices=choices,
    )


def load_schema(path: str) -> Schema:
    """
    Parse a schema file using the regex INI parser and build a Schema lookup.

    Args:
        path: Path to the schema .ini file.

    Returns:
        Schema dictionary {section_name: {key_name: Rule}}.

    Raises:
        SchemaError: If file not found, contains syntax errors, or defines invalid rules.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise SchemaError(f"Schema file not found: '{path}'")

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as err:
        raise SchemaError(f"Error reading schema file '{path}': {err}") from err

    parse_result = parse_text(content)
    errors = [i for i in parse_result.issues if i.severity == "error"]
    if errors:
        first = errors[0]
        raise SchemaError(f"Schema syntax error at line {first.line}: {first.message}")

    schema: Schema = {}
    for sec_name, entries in parse_result.sections.items():
        if sec_name not in schema:
            schema[sec_name] = {}
        for key_name, entry in entries.items():
            rule = parse_rule(entry.raw, where=f"[{sec_name}] {key_name}")
            schema[sec_name][key_name] = rule

    return schema
