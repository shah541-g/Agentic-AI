"""Exporters for GraphML, DOT, JSON, and CSV link formats."""
from __future__ import annotations
import csv
import json
import os
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from typing import Any


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def export_json(data: dict[str, Any], path: str) -> None:
    """Export graph data as indented JSON."""
    _ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def export_graphml(data: dict[str, Any], path: str) -> None:
    """Export graph data as standard GraphML (compatible with Gephi, yEd, networkx)."""
    _ensure_parent_dir(path)

    NS = "http://graphml.graphdrawing.org/xmlns"
    ET.register_namespace("", NS)

    root = ET.Element(f"{{{NS}}}graphml")

    # Define node attribute keys
    node_keys = [
        ("d_type", "type", "string"),
        ("d_depth", "depth", "int"),
        ("d_state", "state", "string"),
        ("d_status", "status", "int"),
        ("d_title", "title", "string"),
        ("d_redirect_to", "redirect_to", "string"),
        ("d_domain", "domain", "string"),
    ]
    for key_id, name, type_name in node_keys:
        k = ET.SubElement(root, f"{{{NS}}}key", id=key_id, attrib={"for": "node", "attr.name": name, "attr.type": type_name})

    # Define edge attribute keys
    edge_keys = [
        ("e_kind", "kind", "string"),
        ("e_count", "count", "int"),
        ("e_text", "text", "string"),
        ("e_nofollow", "nofollow", "boolean"),
    ]
    for key_id, name, type_name in edge_keys:
        k = ET.SubElement(root, f"{{{NS}}}key", id=key_id, attrib={"for": "edge", "attr.name": name, "attr.type": type_name})

    graph_elem = ET.SubElement(root, f"{{{NS}}}graph", id="G", edgedefault="directed")

    # Nodes
    for node in data.get("nodes", []):
        node_id = str(node["id"])
        n_elem = ET.SubElement(graph_elem, f"{{{NS}}}node", id=node_id)
        for key_id, name, type_name in node_keys:
            val = node.get(name)
            if val is not None:
                d_elem = ET.SubElement(n_elem, f"{{{NS}}}data", key=key_id)
                d_elem.text = str(val)

    # Edges
    for edge in data.get("edges", []):
        source = str(edge["source"])
        target = str(edge["target"])
        e_elem = ET.SubElement(graph_elem, f"{{{NS}}}edge", source=source, target=target)
        for key_id, name, type_name in edge_keys:
            val = edge.get(name)
            if val is not None:
                d_elem = ET.SubElement(e_elem, f"{{{NS}}}data", key=key_id)
                if isinstance(val, bool):
                    d_elem.text = "true" if val else "false"
                else:
                    d_elem.text = str(val)

    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _dot_escape(s: str) -> str:
    """Escape backslashes, quotes, and newlines for DOT format strings."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def export_dot(data: dict[str, Any], path: str) -> None:
    """Export graph as Graphviz DOT format."""
    _ensure_parent_dir(path)
    lines = [
        "digraph linkatlas {",
        "  rankdir=LR;",
        '  node [fontname="Helvetica", fontsize=10];',
        '  edge [fontname="Helvetica", fontsize=9];',
    ]

    for node in data.get("nodes", []):
        node_id = _dot_escape(node["id"])
        node_type = node.get("type", "page")
        if node_type == "page":
            path_part = urlparse(node["id"]).path or "/"
            label = _dot_escape(path_part)
            lines.append(f'  "{node_id}" [label="{label}", shape=box];')
        else:
            domain = _dot_escape(node.get("domain", ""))
            lines.append(f'  "{node_id}" [label="{domain}", shape=ellipse, style=filled];')

    for edge in data.get("edges", []):
        src = _dot_escape(edge["source"])
        tgt = _dot_escape(edge["target"])
        attrs = []
        if edge.get("text"):
            attrs.append(f'label="{_dot_escape(edge["text"])}"')
        if edge.get("kind") == "redirect":
            attrs.append('style=dashed, color=blue')
        attr_str = f" [{', '.join(attrs)}]" if attrs else ""
        lines.append(f'  "{src}" -> "{tgt}"{attr_str};')

    lines.append("}\n")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def export_csv(data: dict[str, Any], path: str) -> None:
    """Export unique external links to CSV with referrer counts and earliest source page."""
    _ensure_parent_dir(path)

    # Build ordering of pages according to BFS node list
    page_order = {
        node["id"]: i
        for i, node in enumerate(data.get("nodes", []))
        if node.get("type") == "page"
    }

    # Map external URL -> list of source URLs
    ext_sources: dict[str, list[str]] = {}
    for edge in data.get("edges", []):
        tgt = edge["target"]
        src = edge["source"]
        if tgt not in ext_sources:
            ext_sources[tgt] = []
        ext_sources[tgt].append(src)

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["external_url", "domain", "linked_from_count", "first_found_on"])

        # Filter external nodes
        ext_nodes = [n for n in data.get("nodes", []) if n.get("type") == "external"]
        for ext in ext_nodes:
            url = ext["id"]
            domain = ext.get("domain", "")
            sources = ext_sources.get(url, [])
            unique_sources = sorted(list(set(sources)), key=lambda s: page_order.get(s, 999999))
            linked_count = len(unique_sources)
            first_found = unique_sources[0] if unique_sources else ""
            writer.writerow([url, domain, linked_count, first_found])
