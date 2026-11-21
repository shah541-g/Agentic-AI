"""
Schema validation and typed value resolution engine.
"""

from typing import Any, Dict, List, Optional, Tuple

from confcheck.models import Issue, ParseResult, Schema
from confcheck.values import ConversionError, convert_value, infer_value


def validate(
    result: ParseResult,
    schema: Optional[Schema],
    strict: bool = False,
) -> Tuple[Dict[str, Dict[str, Any]], List[Issue]]:
    """
    Validate parsed configuration against an optional schema.

    If schema is None:
        Types are inferred automatically, no schema issues are produced.
    If schema is provided:
        Types are coerced according to declared rules, required keys are enforced,
        defaults are applied, and bounds/choices are checked.

    Args:
        result: ParseResult from parser.
        schema: Optional parsed Schema.
        strict: If True, all warnings are elevated to errors.

    Returns:
        (typed_data, issues) where issues are sorted with line 0 last.
    """
    issues: List[Issue] = list(result.issues)
    typed_data: Dict[str, Dict[str, Any]] = {}

    if schema is None:
        # Schema-less type inference
        for sec_name, entries in result.sections.items():
            typed_data[sec_name] = {}
            for key_name, entry in entries.items():
                val, _ = infer_value(entry.raw, entry.block)
                typed_data[sec_name][key_name] = val
    else:
        # Validate against schema
        for sec_name, entries in result.sections.items():
            typed_data[sec_name] = {}
            if sec_name not in schema:
                # W102: unknown section
                if sec_name == "_global" and not entries:
                    pass
                else:
                    first_line = next(iter(entries.values())).line if entries else 0
                    issues.append(
                        Issue(
                            code="W102",
                            severity="warning",
                            line=first_line,
                            message=f"unknown section [{sec_name}]",
                        )
                    )
                for key_name, entry in entries.items():
                    val, _ = infer_value(entry.raw, entry.block)
                    typed_data[sec_name][key_name] = val
            else:
                sec_schema = schema[sec_name]
                for key_name, entry in entries.items():
                    if key_name not in sec_schema:
                        # W101: key not in schema
                        issues.append(
                            Issue(
                                code="W101",
                                severity="warning",
                                line=entry.line,
                                message=f"unknown key '{key_name}' in [{sec_name}]",
                            )
                        )
                        val, _ = infer_value(entry.raw, entry.block)
                        typed_data[sec_name][key_name] = val
                    else:
                        rule = sec_schema[key_name]
                        try:
                            converted = convert_value(entry.raw, entry.block, rule.type, rule.item_type)
                        except ConversionError as err:
                            issues.append(
                                Issue(
                                    code="E201",
                                    severity="error",
                                    line=entry.line,
                                    message=f"type mismatch for '{key_name}' in [{sec_name}]: {err}",
                                )
                            )
                            continue

                        # Bounds checking: min / max (E202)
                        bounds_err = False
                        if rule.type == "int":
                            if rule.min is not None and converted < rule.min:
                                issues.append(
                                    Issue(
                                        code="E202",
                                        severity="error",
                                        line=entry.line,
                                        message=f"value {converted} is below minimum {rule.min} for '{key_name}' in [{sec_name}]",
                                    )
                                )
                                bounds_err = True
                            elif rule.max is not None and converted > rule.max:
                                issues.append(
                                    Issue(
                                        code="E202",
                                        severity="error",
                                        line=entry.line,
                                        message=f"value {converted} is above maximum {rule.max} for '{key_name}' in [{sec_name}]",
                                    )
                                )
                                bounds_err = True
                        elif rule.type == "list" and rule.item_type == "int" and isinstance(converted, list):
                            for idx, it_val in enumerate(converted):
                                if rule.min is not None and it_val < rule.min:
                                    issues.append(
                                        Issue(
                                            code="E202",
                                            severity="error",
                                            line=entry.line,
                                            message=f"item at index {idx} ({it_val}) is below minimum {rule.min} for '{key_name}' in [{sec_name}]",
                                        )
                                    )
                                    bounds_err = True
                                elif rule.max is not None and it_val > rule.max:
                                    issues.append(
                                        Issue(
                                            code="E202",
                                            severity="error",
                                            line=entry.line,
                                            message=f"item at index {idx} ({it_val}) is above maximum {rule.max} for '{key_name}' in [{sec_name}]",
                                        )
                                    )
                                    bounds_err = True

                        # Choices checking (E203)
                        choices_err = False
                        if rule.choices is not None:
                            if rule.type in ("str", "int"):
                                if str(converted) not in rule.choices:
                                    issues.append(
                                        Issue(
                                            code="E203",
                                            severity="error",
                                            line=entry.line,
                                            message=f"value '{converted}' is not one of allowed choices {rule.choices} for '{key_name}' in [{sec_name}]",
                                        )
                                    )
                                    choices_err = True
                            elif rule.type == "list" and isinstance(converted, list):
                                for idx, it_val in enumerate(converted):
                                    if str(it_val) not in rule.choices:
                                        issues.append(
                                            Issue(
                                                code="E203",
                                                severity="error",
                                                line=entry.line,
                                                message=f"item at index {idx} ('{it_val}') is not one of allowed choices {rule.choices} for '{key_name}' in [{sec_name}]",
                                            )
                                        )
                                        choices_err = True

                        if not bounds_err and not choices_err:
                            typed_data[sec_name][key_name] = converted

        # Check for missing required keys and apply defaults
        for sec_name, sec_rules in schema.items():
            if sec_name not in typed_data:
                typed_data[sec_name] = {}

            for key_name, rule in sec_rules.items():
                key_present = (sec_name in result.sections and key_name in result.sections[sec_name])
                if not key_present:
                    if rule.has_default:
                        typed_data[sec_name][key_name] = rule.default
                    elif rule.required:
                        # E101: required key missing
                        issues.append(
                            Issue(
                                code="E101",
                                severity="error",
                                line=0,
                                message=f"required key '{key_name}' missing in [{sec_name}]",
                            )
                        )

    # Clean empty _global if not declared in schema and empty in config
    if "_global" in typed_data and not typed_data["_global"]:
        if schema is None or "_global" not in schema:
            del typed_data["_global"]

    # In strict mode, elevate all warnings to errors
    if strict:
        for iss in issues:
            if iss.severity == "warning":
                iss.severity = "error"

    # Sort issues: line 1..N first, then line 0 (unbound lines) last
    issues.sort(key=lambda x: (x.line == 0, x.line, x.code))
    return typed_data, issues
