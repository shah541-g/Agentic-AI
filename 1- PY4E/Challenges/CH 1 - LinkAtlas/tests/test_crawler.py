"""Integration tests for Crawler on local fake site."""
import pytest
from linkatlas.crawler import Crawler
from linkatlas.fetcher import Fetcher
from linkatlas.graph import Graph
from linkatlas.models import CrawlConfig


def test_crawler_default_run(fake_site):
    # Clear recorded requests before test
    fake_site.requests.clear()

    config = CrawlConfig(
        seed=fake_site.url,
        max_depth=2,
        delay=0.0,
        timeout=0.5,
        retries=0,
    )
    graph = Graph()
    fetcher = Fetcher(config=config)
    crawler = Crawler(config=config, fetcher=fetcher, graph=graph)

    result = crawler.run()
    summary = result["summary"]
    meta = result["meta"]

    # 1. Requests made to fake_site (excluding /robots.txt)
    reqs_no_robots = [r for r in fake_site.requests if r != "/robots.txt"]
    assert len(reqs_no_robots) == 7
    expected_requested = {"/", "/a", "/slow", "/missing", "/old", "/redir-ext", "/c"}
    assert set(reqs_no_robots) == expected_requested

    # 2. Never requested URLs
    never_requested = {"/private/secret", "/file.pdf", "/nf", "/d"}
    for unrequested in never_requested:
        assert unrequested not in fake_site.requests

    # 3. Summary metrics
    assert summary["pages_requested"] == 7
    assert summary["pages_ok"] == 3
    assert summary["ignored_links"] == 2
    assert summary["external_unique_urls"] == 5
    assert summary["external_unique_domains"] == 5

    # 4. State counts
    st = summary["state_counts"]
    assert st["ok"] == 3
    assert st["http_error"] == 1
    assert st["timeout"] == 1
    assert st["redirect"] == 2
    assert st["not_crawled"] == 2
    assert st["robots_disallowed"] == 1
    assert st["skipped_extension"] == 1

    # 5. Nodes and edges count
    assert len(graph.pages) == 11
    assert len(graph.externals) == 5
    total_nodes = len(graph.pages) + len(graph.externals)
    assert total_nodes == 16
    assert len(graph.edges) == 19

    # 6. Specific edges and counts
    seed_norm = fake_site.url
    edge_slash_to_a = graph.edges.get((seed_norm, seed_norm + "a"))
    assert edge_slash_to_a is not None
    assert edge_slash_to_a["count"] == 2  # /a and /a#section

    edge_old_redirect = graph.edges.get((seed_norm + "old", seed_norm + "a"))
    assert edge_old_redirect is not None
    assert edge_old_redirect["kind"] == "redirect"

    edge_ext_redirect = graph.edges.get((seed_norm + "redir-ext", "https://external-five.test/landing"))
    assert edge_ext_redirect is not None
    assert edge_ext_redirect["kind"] == "redirect"

    # 7. Problems
    problems = summary["problems"]
    assert len(problems) == 2
    prob_urls = {p["url"] for p in problems}
    assert prob_urls == {seed_norm + "missing", seed_norm + "slow"}
    for p in problems:
        assert p["linked_from"] == [seed_norm]

    assert meta["truncated"] is False
    assert meta["interrupted"] is False


def test_crawler_depth_0(fake_site):
    fake_site.requests.clear()
    config = CrawlConfig(seed=fake_site.url, max_depth=0, delay=0.0, timeout=0.5, retries=0)
    graph = Graph()
    fetcher = Fetcher(config=config)
    crawler = Crawler(config=config, fetcher=fetcher, graph=graph)

    res = crawler.run()
    reqs_no_robots = [r for r in fake_site.requests if r != "/robots.txt"]
    assert reqs_no_robots == ["/"]
    assert res["summary"]["pages_requested"] == 1
    assert res["summary"]["pages_ok"] == 1
    # External edges still recorded
    assert res["summary"]["external_unique_urls"] == 2


def test_crawler_depth_1(fake_site):
    fake_site.requests.clear()
    config = CrawlConfig(seed=fake_site.url, max_depth=1, delay=0.0, timeout=0.5, retries=0)
    graph = Graph()
    fetcher = Fetcher(config=config)
    crawler = Crawler(config=config, fetcher=fetcher, graph=graph)

    res = crawler.run()
    reqs_no_robots = [r for r in fake_site.requests if r != "/robots.txt"]
    # At depth 1: /c is depth 2 so /c is NOT requested!
    assert "/c" not in reqs_no_robots
    assert len(reqs_no_robots) == 6


def test_crawler_max_pages_truncation(fake_site):
    fake_site.requests.clear()
    config = CrawlConfig(seed=fake_site.url, max_depth=2, max_pages=2, delay=0.0, timeout=0.5, retries=0)
    graph = Graph()
    fetcher = Fetcher(config=config)
    crawler = Crawler(config=config, fetcher=fetcher, graph=graph)

    res = crawler.run()
    assert res["meta"]["truncated"] is True
    assert res["pages_requested"] == 2


def test_crawler_interrupted_partial_graph(fake_site):
    fake_site.requests.clear()
    config = CrawlConfig(seed=fake_site.url, max_depth=2, delay=0.0, timeout=0.5, retries=0)
    graph = Graph()
    fetcher = Fetcher(config=config)

    def on_page_abort(result, depth):
        if result.url.endswith("/a"):
            raise KeyboardInterrupt()

    crawler = Crawler(config=config, fetcher=fetcher, graph=graph, on_page=on_page_abort)
    res = crawler.run()
    assert res["interrupted"] is True
    assert res["meta"]["interrupted"] is True
    assert res["pages_requested"] >= 1
