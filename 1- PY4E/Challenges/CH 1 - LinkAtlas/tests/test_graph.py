"""Tests for Graph building and summary calculation."""
import pytest
from linkatlas.graph import Graph


def test_graph_add_page_and_update():
    g = Graph()
    assert g.add_page("https://example.com/", depth=0, state="not_crawled") is True
    assert g.add_page("https://example.com/", depth=0) is False  # duplicate
    g.update_page("https://example.com/", state="ok", status=200, title="Homepage")

    assert g.pages["https://example.com/"]["state"] == "ok"
    assert g.pages["https://example.com/"]["status"] == 200
    assert g.pages["https://example.com/"]["title"] == "Homepage"


def test_graph_add_external():
    g = Graph()
    assert g.add_external("https://external.org/path") is True
    assert g.add_external("https://external.org/path") is False
    assert g.externals["https://external.org/path"]["domain"] == "external.org"


def test_graph_edge_count_and_nofollow_and_text():
    g = Graph()
    # First occurrence has nofollow=True and text="First"
    g.add_edge("https://a.com/", "https://b.com/", kind="internal", text="First", nofollow=True)
    assert g.edges[("https://a.com/", "https://b.com/")]["count"] == 1
    assert g.edges[("https://a.com/", "https://b.com/")]["nofollow"] is True
    assert g.edges[("https://a.com/", "https://b.com/")]["text"] == "First"

    # Second occurrence has nofollow=False and empty text
    g.add_edge("https://a.com/", "https://b.com/", kind="internal", text="", nofollow=False)
    # nofollow is AND of occurrences -> True and False == False
    assert g.edges[("https://a.com/", "https://b.com/")]["count"] == 2
    assert g.edges[("https://a.com/", "https://b.com/")]["nofollow"] is False
    # Keeps first non-empty text
    assert g.edges[("https://a.com/", "https://b.com/")]["text"] == "First"

    # Third occurrence with nofollow=True
    g.add_edge("https://a.com/", "https://b.com/", kind="internal", text="Other", nofollow=True)
    assert g.edges[("https://a.com/", "https://b.com/")]["count"] == 3
    assert g.edges[("https://a.com/", "https://b.com/")]["nofollow"] is False
    assert g.edges[("https://a.com/", "https://b.com/")]["text"] == "First"


def test_graph_deterministic_ordering():
    g = Graph()
    g.add_page("https://example.com/z", depth=1)
    g.add_page("https://example.com/a", depth=1)
    g.add_page("https://example.com/", depth=0)

    g.add_external("https://zebra.com/")
    g.add_external("https://apple.com/")

    g.add_edge("https://example.com/z", "https://zebra.com/", kind="external")
    g.add_edge("https://example.com/", "https://example.com/a", kind="internal")

    d = g.to_dict(meta={"test": 1}, summary={})

    # Nodes: pages by (depth, id), then externals by id
    node_ids = [n["id"] for n in d["nodes"]]
    expected_ids = [
        "https://example.com/",
        "https://example.com/a",
        "https://example.com/z",
        "https://apple.com/",
        "https://zebra.com/",
    ]
    assert node_ids == expected_ids

    # Edges: sorted by (source, target)
    edge_pairs = [(e["source"], e["target"]) for e in d["edges"]]
    assert edge_pairs == sorted(edge_pairs)


def test_graph_summary_stats():
    g = Graph()
    g.add_page("https://example.com/", depth=0, state="ok", status=200)
    g.add_page("https://example.com/broken", depth=1, state="http_error", status=404)
    g.add_page("https://example.com/slow", depth=1, state="timeout")

    g.add_external("https://ext1.com/a")
    g.add_external("https://ext1.com/b")
    g.add_external("https://ext2.com/c")

    g.add_edge("https://example.com/", "https://example.com/broken", kind="internal")
    g.add_edge("https://example.com/", "https://example.com/slow", kind="internal")
    g.add_edge("https://example.com/", "https://ext1.com/a", kind="external")
    g.add_edge("https://example.com/", "https://ext1.com/b", kind="external")
    g.add_edge("https://example.com/", "https://ext2.com/c", kind="external")

    summary = g.summary(ignored_links=3, pages_requested=3)

    assert summary["pages_requested"] == 3
    assert summary["pages_ok"] == 1
    assert summary["ignored_links"] == 3
    assert summary["external_unique_urls"] == 3
    assert summary["external_unique_domains"] == 2
    assert summary["state_counts"] == {"ok": 1, "http_error": 1, "timeout": 1}

    # Top external domains: ext1.com has 2 urls, ext2.com has 1
    assert summary["top_external_domains"][0]["domain"] == "ext1.com"
    assert summary["top_external_domains"][0]["urls"] == 2
    assert summary["top_external_domains"][1]["domain"] == "ext2.com"

    # Problems
    assert len(summary["problems"]) == 2
    assert summary["problems"][0]["url"] == "https://example.com/broken"
    assert summary["problems"][0]["linked_from"] == ["https://example.com/"]
    assert summary["problems"][1]["url"] == "https://example.com/slow"
