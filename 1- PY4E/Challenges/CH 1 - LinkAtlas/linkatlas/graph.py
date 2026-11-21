"""Graph data structures and summary computation."""
from __future__ import annotations
from collections import defaultdict
from typing import Any

from linkatlas.urls import domain_of


class Graph:
    """Directed link graph storing pages, external URLs, and directed edges."""

    def __init__(self) -> None:
        self.pages: dict[str, dict[str, Any]] = {}
        self.externals: dict[str, dict[str, Any]] = {}
        # key: (source, target) -> edge dict
        self.edges: dict[tuple[str, str], dict[str, Any]] = {}
        # Track first found order for external URLs
        self.external_first_found: dict[str, str] = {}

    def add_page(self, url: str, depth: int, state: str = "not_crawled", **attrs) -> bool:
        """Add a page node if not already present. Returns True if newly added."""
        if url in self.pages:
            return False
        node = {
            "id": url,
            "type": "page",
            "depth": depth,
            "state": state,
            "status": attrs.get("status", None),
            "title": attrs.get("title", None),
            "redirect_to": attrs.get("redirect_to", None),
        }
        node.update(attrs)
        self.pages[url] = node
        return True

    def update_page(self, url: str, **attrs) -> None:
        """Update existing page node attributes."""
        if url in self.pages:
            self.pages[url].update(attrs)
        else:
            depth = attrs.pop("depth", 0)
            state = attrs.pop("state", "ok")
            self.add_page(url, depth=depth, state=state, **attrs)

    def add_external(self, url: str) -> bool:
        """Add an external URL node if not already present. Returns True if newly added."""
        if url in self.externals:
            return False
        self.externals[url] = {
            "id": url,
            "type": "external",
            "domain": domain_of(url),
        }
        return True

    def add_edge(
        self,
        source: str,
        target: str,
        kind: str,
        text: str = "",
        nofollow: bool = False,
    ) -> None:
        """Add a directed edge or update an existing edge.
        Keeps first non-empty text. nofollow is AND of all occurrences."""
        key = (source, target)
        if key in self.edges:
            edge = self.edges[key]
            edge["count"] += 1
            if not edge["text"] and text:
                edge["text"] = text
            edge["nofollow"] = edge["nofollow"] and nofollow
        else:
            self.edges[key] = {
                "source": source,
                "target": target,
                "kind": kind,
                "count": 1,
                "text": text,
                "nofollow": nofollow,
            }

        # Track first found referrer for external URLs
        if kind == "external" and target not in self.external_first_found:
            self.external_first_found[target] = source

    def summary(self, ignored_links: int, pages_requested: int) -> dict[str, Any]:
        """Compute crawl summary statistics as specified in Section 6.3."""
        pages_ok = sum(1 for p in self.pages.values() if p.get("state") == "ok")

        state_counts: dict[str, int] = defaultdict(int)
        for p in self.pages.values():
            state_counts[p.get("state", "not_crawled")] += 1

        ext_unique_urls = len(self.externals)
        ext_domains = {node["domain"] for node in self.externals.values()}
        ext_unique_domains = len(ext_domains)

        # Domain stats: unique URLs and linking pages per external domain
        domain_urls: dict[str, set[str]] = defaultdict(set)
        domain_referrers: dict[str, set[str]] = defaultdict(set)

        for (src, tgt), edge in self.edges.items():
            if edge["kind"] == "external" and tgt in self.externals:
                dom = self.externals[tgt]["domain"]
                domain_urls[dom].add(tgt)
                domain_referrers[dom].add(src)

        top_domains_list = []
        for dom, urls_set in domain_urls.items():
            top_domains_list.append({
                "domain": dom,
                "urls": len(urls_set),
                "linked_from_pages": len(domain_referrers[dom]),
            })

        # Sort top domains: by unique URLs desc, then linked_from_pages desc, then domain asc
        top_domains_list.sort(key=lambda d: (-d["urls"], -d["linked_from_pages"], d["domain"]))
        top_external_domains = top_domains_list[:10]

        # Problem pages
        problem_states = frozenset({"http_error", "timeout", "connection_error", "ssl_error"})
        # Map target page -> set of source pages
        page_referrers: dict[str, set[str]] = defaultdict(set)
        for (src, tgt), edge in self.edges.items():
            if edge["kind"] in ("internal", "redirect"):
                page_referrers[tgt].add(src)

        problems = []
        for url, page in self.pages.items():
            st = page.get("state")
            if st in problem_states:
                problems.append({
                    "url": url,
                    "state": st,
                    "status": page.get("status"),
                    "linked_from": sorted(list(page_referrers[url])),
                })
        problems.sort(key=lambda p: p["url"])

        return {
            "pages_requested": pages_requested,
            "pages_ok": pages_ok,
            "state_counts": dict(state_counts),
            "external_unique_urls": ext_unique_urls,
            "external_unique_domains": ext_unique_domains,
            "top_external_domains": top_external_domains,
            "problems": problems,
            "ignored_links": ignored_links,
        }

    def to_dict(self, meta: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
        """Convert graph to deterministic JSON-serializable node-link dictionary."""
        # Pages sorted by depth then id
        sorted_pages = sorted(self.pages.values(), key=lambda p: (p.get("depth", 0), p["id"]))
        # Externals sorted by id
        sorted_externals = sorted(self.externals.values(), key=lambda e: e["id"])
        nodes = sorted_pages + sorted_externals

        # Edges sorted by (source, target)
        sorted_edges = sorted(self.edges.values(), key=lambda e: (e["source"], e["target"]))

        return {
            "directed": True,
            "multigraph": False,
            "meta": meta,
            "nodes": nodes,
            "edges": sorted_edges,
            "summary": summary,
        }
