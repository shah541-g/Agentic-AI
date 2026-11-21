"""
Inspection utility: JSON structure visualization and map suggestion.
"""

import re
from typing import Any, List, Set, Tuple
from rich.tree import Tree


def _format_sample(val: Any) -> str:
    """Format and truncate sample value for tree display."""
    if val is None:
        return "null"
    if isinstance(val, str):
        if len(val) > 30:
            return repr(val[:27] + "...")
        return repr(val)
    return repr(val)


def build_tree(data: Any, max_depth: int = 4) -> Tree:
    """
    Build a rich.tree.Tree visualizing JSON structure, types, and sample values.

    Args:
        data: Parsed JSON data (dict or list).
        max_depth: Maximum tree traversal depth.

    Returns:
        rich.tree.Tree instance.
    """
    root = Tree("[bold magenta]JSON Response Structure[/bold magenta]")

    def _walk(node: Tree, obj: Any, depth: int) -> None:
        if depth > max_depth:
            node.add("[dim]... (depth limit reached)[/dim]")
            return

        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, dict):
                    child = node.add(f"[bold cyan]{k}[/bold cyan] [dim](dict)[/dim]")
                    _walk(child, v, depth + 1)
                elif isinstance(v, list):
                    child = node.add(f"[bold cyan]{k}[/bold cyan] [dim](list[{len(v)}])[/dim]")
                    if v:
                        _walk(child, v[0], depth + 1)
                else:
                    sample = _format_sample(v)
                    v_type = "null" if v is None else type(v).__name__
                    node.add(f"[bold cyan]{k}[/bold cyan]: [yellow]{v_type}[/yellow] = [green]{sample}[/green]")

        elif isinstance(obj, list):
            if not obj:
                node.add("[dim]empty list[/dim]")
            else:
                child = node.add(f"[dim]element 0 (of {len(obj)})[/dim]")
                _walk(child, obj[0], depth + 1)
        else:
            sample = _format_sample(obj)
            obj_type = "null" if obj is None else type(obj).__name__
            node.add(f"[yellow]{obj_type}[/yellow] = [green]{sample}[/green]")

    _walk(root, data, depth=1)
    return root


def suggest_map(data: Any, max_depth: int = 3) -> str:
    """
    Generate a YAML 'map:' block suggesting mappings for leaf fields up to depth 3.

    Names are built from the last path segment with numeric suffixes on collision.
    Skips null leaves and does not inspect list items beyond index 0.

    Args:
        data: Parsed JSON data.
        max_depth: Maximum path depth to inspect.

    Returns:
        YAML formatted 'map:' block string.
    """
    leaves: List[Tuple[str, str]] = []  # (field_name, dot_path)
    used_names: Set[str] = set()

    def _collect_leaves(obj: Any, current_path: str, depth: int) -> None:
        if depth > max_depth or obj is None:
            return

        if isinstance(obj, dict):
            for k, v in obj.items():
                p = f"{current_path}.{k}" if current_path else str(k)
                if isinstance(v, (dict, list)):
                    _collect_leaves(v, p, depth + 1)
                else:
                    # Leaf value (skip None/null)
                    if v is not None:
                        _add_leaf(k, p)

        elif isinstance(obj, list):
            if obj and isinstance(obj[0], (dict, list)):
                p = f"{current_path}.0" if current_path else "0"
                _collect_leaves(obj[0], p, depth + 1)

    def _add_leaf(raw_key: str, dot_path: str) -> None:
        # Generate safe identifier name from last segment
        base_name = re.sub(r"[^A-Za-z0-9_]", "_", str(raw_key))
        if not base_name or not base_name[0].isalpha() and base_name[0] != '_':
            base_name = f"field_{base_name}"

        candidate = base_name
        if candidate in used_names:
            i = 2
            while f"{base_name}_{i}" in used_names:
                i += 1
            candidate = f"{base_name}_{i}"

        used_names.add(candidate)
        leaves.append((candidate, dot_path))

    _collect_leaves(data, "", depth=1)

    if not leaves:
        return "map: {}"

    lines = ["map:"]
    for name, path in leaves:
        lines.append(f"  {name}: {path}")

    return "\n".join(lines)
