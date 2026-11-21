"""
Line-by-line configuration parser driven exclusively by regular expressions.
"""

from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple

from confcheck.models import Entry, Issue, ParseResult
from confcheck.patterns import (
    BACKSLASH_END,
    BAD_SECTION,
    BLANK,
    COMMENT,
    CONTINUATION,
    KEY_VALUE,
    SECTION,
)
from confcheck.values import strip_inline_comment


class _OpenEntry:
    """Tracks an entry currently open for continuation lines."""

    def __init__(self, section: str, key: str, line: int, initial_val: str, has_backslash: bool):
        self.section = section
        self.key = key
        self.line = line
        self.first_line_empty = (initial_val.strip() == "")
        self.block = False
        # List of (join_mode, text_content): join_mode is 'init', 'newline', or 'space'
        self.parts: List[Tuple[str, str]] = [("init", initial_val)]
        self.pending_backslash = has_backslash


def parse_text(text: str) -> ParseResult:
    """
    Parse INI configuration text into structured sections, keys, and issues.

    Uses only compiled regular expressions from confcheck.patterns.
    """
    # Remove BOM if present
    text = text.lstrip("\ufeff")
    lines = text.splitlines()

    sections: Dict[str, Dict[str, Entry]] = {"_global": {}}
    issues: List[Issue] = []

    current_section = "_global"
    current_entry: Optional[_OpenEntry] = None
    discarding = False

    def close_current_entry() -> None:
        nonlocal current_entry
        if current_entry is None:
            return

        oe = current_entry
        current_entry = None

        # Build raw string
        # If block entry: drop initial empty line, join remaining lines with \n
        if oe.block:
            block_lines = []
            for mode, content in oe.parts:
                if mode == "init" and not content.strip():
                    continue
                block_lines.append(content.strip())
            raw = "\n".join(block_lines)
        else:
            # Join parts according to their join mode
            pieces = []
            for mode, content in oe.parts:
                if mode == "space":
                    pieces.append(" " + content)
                elif mode == "newline":
                    pieces.append("\n" + content)
                else:
                    pieces.append(content)
            raw = "".join(pieces).strip()

        entry = Entry(
            section=oe.section,
            key=oe.key,
            raw=raw,
            block=oe.block,
            line=oe.line,
        )
        # Store in sections (first definition is already saved)
        sections[oe.section][oe.key] = entry

    for line_num, line in enumerate(lines, start=1):
        # 1. Check pending backslash from previous line
        if current_entry is not None and current_entry.pending_backslash:
            # 2. Comment lines inside continuation do not break or append
            if COMMENT.match(line):
                continue

            stripped = line.strip()
            clean_text = strip_inline_comment(stripped)
            has_bs = bool(BACKSLASH_END.search(clean_text))
            if has_bs:
                clean_text = BACKSLASH_END.sub("", clean_text).rstrip()
                current_entry.pending_backslash = True
            else:
                current_entry.pending_backslash = False

            current_entry.parts.append(("space", clean_text))
            continue

        # 2. Full-line comment (ignored everywhere, does not close open value)
        if COMMENT.match(line):
            continue

        # 3. Blank line (closes the open value)
        if BLANK.match(line):
            close_current_entry()
            continue

        # 4. Continuation line (indented with space or tab)
        m_cont = CONTINUATION.match(line)
        if m_cont:
            if current_entry is not None:
                text_part = m_cont.group("text")
                clean_text = strip_inline_comment(text_part)

                # Check if this continuation ends with a backslash
                has_bs = bool(BACKSLASH_END.search(clean_text))
                if has_bs:
                    clean_text = BACKSLASH_END.sub("", clean_text).rstrip()
                    current_entry.pending_backslash = True
                else:
                    current_entry.pending_backslash = False

                # If first line was empty and this is the first continuation, mark as block list
                if current_entry.first_line_empty and len(current_entry.parts) == 1:
                    current_entry.block = True

                current_entry.parts.append(("newline", clean_text))
            else:
                issues.append(
                    Issue(
                        code="E002",
                        severity="error",
                        line=line_num,
                        message="unexpected indented line",
                    )
                )
            continue

        # 5. Valid section header
        m_sec = SECTION.match(line)
        if m_sec:
            close_current_entry()
            sec_name = m_sec.group("name").strip()
            current_section = sec_name
            discarding = False
            if sec_name in sections:
                if sec_name == "_global" and len(sections["_global"]) == 0:
                    pass
                else:
                    issues.append(
                        Issue(
                            code="W001",
                            severity="warning",
                            line=line_num,
                            message=f"duplicate section [{sec_name}] (merged)",
                        )
                    )
            else:
                sections[sec_name] = {}
            continue

        # 6. Malformed section header (starts with [ but not SECTION)
        if BAD_SECTION.match(line):
            close_current_entry()
            issues.append(
                Issue(
                    code="E003",
                    severity="error",
                    line=line_num,
                    message="invalid section header",
                )
            )
            discarding = True
            continue

        # 7. Key-value definition
        m_kv = KEY_VALUE.match(line)
        if m_kv:
            close_current_entry()
            if discarding:
                continue

            key = m_kv.group("key")
            raw_val = m_kv.group("value")
            clean_val = strip_inline_comment(raw_val)

            has_bs = bool(BACKSLASH_END.search(clean_val))
            if has_bs:
                clean_val = BACKSLASH_END.sub("", clean_val).rstrip()

            # Check for duplicate key in current section
            if key in sections[current_section]:
                first_line = sections[current_section][key].line
                issues.append(
                    Issue(
                        code="E004",
                        severity="error",
                        line=line_num,
                        message=f"duplicate key '{key}' in [{current_section}] (first defined at line {first_line})",
                    )
                )
                # Keep first value: do not open new entry for duplicate key
                continue

            current_entry = _OpenEntry(
                section=current_section,
                key=key,
                line=line_num,
                initial_val=clean_val,
                has_backslash=has_bs,
            )
            continue

        # 8. Otherwise -> invalid syntax E001
        close_current_entry()
        issues.append(
            Issue(
                code="E001",
                severity="error",
                line=line_num,
                message="invalid syntax",
            )
        )

    close_current_entry()
    return ParseResult(sections=sections, issues=issues)


def parse_file(path: str) -> ParseResult:
    """
    Parse an INI file from path (or stdin if path is "-").
    """
    if path == "-":
        content = sys.stdin.read()
    else:
        file_path = Path(path)
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: '{path}'")
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

    return parse_text(content)
