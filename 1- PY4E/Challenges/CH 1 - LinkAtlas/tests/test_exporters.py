"""Tests for link graph exporters (JSON, GraphML, DOT, CSV)."""
import csv
import json
import xml.etree.ElementTree as ET
import pytest

from linkatlas.exporters import export_json, export_graphml, export_dot, export_csv


@pytest.fixture
def sample_graph_data():
    return {
        "directed": True,
        "multigraph": False,
        "meta": {"seed": "https://example.com/"},
        "nodes": [
            {
                "id": "https://example.com/",
                "type": "page",
                "depth": 0,
                "state": "ok",
                "status": 200,
                "title": "Home \"Sweet\" Home",
                "redirect_to": None,
            },
            {
                "id": "https://example.com/about",
                "type": "page",
                "depth": 1,
                "state": "ok",
                "status": 200,
                "title": "About",
                "redirect_to": None,
            },
            {
                "id": "https://external.org/landing",
                "type": "external",
                "domain": "external.org",
            },
        ],
        "edges": [
            {
                "source": "https://example.com/",
                "target": "https://example.com/about",
                "kind": "internal",
                "count": 1,
                "text": "About Us",
                "nofollow": False,
            },
            {
                "source": "https://example.com/",
                "target": "https://external.org/landing",
                "kind": "external",
                "count": 2,
                "text": "Partner \"Site\"",
                "nofollow": True,
            },
            {
                "source": "https://example.com/about",
                "target": "https://external.org/landing",
                "kind": "external",
                "count": 1,
                "text": "Landing",
                "nofollow": True,
            },
        ],
        "summary": {},
    }


def test_export_json(tmp_path, sample_graph_data):
    out = tmp_path / "graph.json"
    export_json(sample_graph_data, str(out))
    assert out.exists()

    with open(out, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["directed"] is True
    assert len(loaded["nodes"]) == 3
    assert len(loaded["edges"]) == 3


def test_export_graphml_valid_xml(tmp_path, sample_graph_data):
    out = tmp_path / "graph.graphml"
    export_graphml(sample_graph_data, str(out))
    assert out.exists()

    # Verify it parses cleanly with ElementTree
    tree = ET.parse(str(out))
    root = tree.getroot()
    # Check graph element
    graph = root.find("{http://graphml.graphdrawing.org/xmlns}graph")
    assert graph is not None
    assert graph.attrib.get("edgedefault") == "directed"

    nodes = graph.findall("{http://graphml.graphdrawing.org/xmlns}node")
    assert len(nodes) == 3

    edges = graph.findall("{http://graphml.graphdrawing.org/xmlns}edge")
    assert len(edges) == 3


def test_export_dot_escaping(tmp_path, sample_graph_data):
    out = tmp_path / "graph.dot"
    export_dot(sample_graph_data, str(out))
    assert out.exists()

    with open(out, "r", encoding="utf-8") as f:
        content = f.read()

    assert "digraph linkatlas {" in content
    # Quotes should be escaped in labels
    assert r'Partner \"Site\"' in content
    assert '"https://external.org/landing"' in content
    assert 'shape=ellipse' in content
    assert 'shape=box' in content


def test_export_csv_rows(tmp_path, sample_graph_data):
    out = tmp_path / "links.csv"
    export_csv(sample_graph_data, str(out))
    assert out.exists()

    with open(out, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    assert reader[0] == ["external_url", "domain", "linked_from_count", "first_found_on"]
    assert len(reader) == 2  # header + 1 external URL
    row = reader[1]
    assert row[0] == "https://external.org/landing"
    assert row[1] == "external.org"
    assert row[2] == "2"  # linked from both / and /about
    assert row[3] == "https://example.com/"  # earliest in BFS order
