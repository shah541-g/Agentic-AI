"""Breadth-first search crawler for LinkAtlas."""
from __future__ import annotations
from collections import deque
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urlparse

from linkatlas import __version__
from linkatlas.extractor import extract_links
from linkatlas.fetcher import Fetcher
from linkatlas.graph import Graph
from linkatlas.models import CrawlConfig, FetchResult
from linkatlas.urls import (
    domain_of,
    has_skippable_extension,
    is_internal,
    normalize_url,
)


class Crawler:
    """Polite, depth-limited BFS web crawler."""

    def __init__(
        self,
        config: CrawlConfig,
        fetcher: Fetcher,
        graph: Graph,
        on_page: Callable[[FetchResult, int], None] | None = None,
    ) -> None:
        self.config = config
        self.fetcher = fetcher
        self.graph = graph
        self.on_page = on_page

    def run(self) -> dict:
        """Execute the BFS crawl according to Section 4.3 rules.
        Catches KeyboardInterrupt to safely yield partial results."""
        started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        interrupted = False
        truncated = False
        pages_requested = 0
        ignored_links = 0

        # Normalise seed URL
        seed = self.config.seed
        if not urlparse(seed).scheme:
            seed = "https://" + seed
        norm_seed = normalize_url(seed)
        if not norm_seed:
            norm_seed = seed

        # BFS queue holds (url, depth)
        queue: deque[tuple[str, int]] = deque([(norm_seed, 0)])
        seen: set[str] = {norm_seed}
        self.graph.add_page(norm_seed, depth=0, state="not_crawled")

        try:
            while queue and pages_requested < self.config.max_pages:
                url, depth = queue.popleft()

                # Fetch page (robots checking, politeness delay, retries handled inside)
                result = self.fetcher.fetch(url)

                # pages_requested increments for actual network requests (not when blocked by robots)
                if result.state != "robots_disallowed":
                    pages_requested += 1

                # Update page node in graph
                update_attrs = {
                    "depth": depth,
                    "state": result.state,
                    "status": result.status,
                    "redirect_to": result.redirect_to,
                }
                self.graph.update_page(url, **update_attrs)

                if self.on_page:
                    self.on_page(result, depth)

                # Handle Redirect
                if result.state == "redirect" and result.redirect_to:
                    target = result.redirect_to
                    target_internal = is_internal(
                        target,
                        norm_seed,
                        self.config.include_subdomains,
                    )

                    if target_internal:
                        self.graph.add_page(target, depth=depth, state="not_crawled")
                        self.graph.add_edge(url, target, kind="redirect")
                        if target not in seen:
                            seen.add(target)
                            queue.append((target, depth))
                    else:
                        self.graph.add_external(target)
                        self.graph.add_edge(url, target, kind="redirect")
                    continue

                if result.state != "ok" or not result.content:
                    continue

                # Parse page HTML
                extracted = extract_links(result.content, url)
                ignored_links += extracted.ignored_links

                if extracted.title:
                    self.graph.update_page(url, title=extracted.title)

                effective_page_nofollow = extracted.page_nofollow or result.nofollow_header

                # Process extracted links
                for link in extracted.links:
                    if link.url == url:
                        # Skip self-links
                        continue

                    link_internal = is_internal(
                        link.url,
                        norm_seed,
                        self.config.include_subdomains,
                    )

                    if link_internal:
                        is_new = (link.url not in seen)
                        if is_new:
                            seen.add(link.url)
                            state = "not_crawled"
                            if has_skippable_extension(link.url):
                                state = "skipped_extension"

                            self.graph.add_page(link.url, depth=depth + 1, state=state)

                            if (
                                state != "skipped_extension"
                                and depth < self.config.max_depth
                                and not link.nofollow
                                and not effective_page_nofollow
                            ):
                                queue.append((link.url, depth + 1))

                        self.graph.add_edge(
                            source=url,
                            target=link.url,
                            kind="internal",
                            text=link.text,
                            nofollow=link.nofollow,
                        )
                    else:
                        self.graph.add_external(link.url)
                        self.graph.add_edge(
                            source=url,
                            target=link.url,
                            kind="external",
                            text=link.text,
                            nofollow=link.nofollow,
                        )

            # Check if terminated due to max_pages
            if queue and pages_requested >= self.config.max_pages:
                truncated = True

        except KeyboardInterrupt:
            interrupted = True

        finished_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Build meta
        meta = {
            "tool": "linkatlas",
            "version": __version__,
            "seed": norm_seed,
            "started_at": started_at,
            "finished_at": finished_at,
            "options": {
                "max_depth": self.config.max_depth,
                "max_pages": self.config.max_pages,
                "delay": self.config.delay,
                "timeout": self.config.timeout,
                "retries": self.config.retries,
                "include_subdomains": self.config.include_subdomains,
                "user_agent": self.config.user_agent,
            },
            "robots": self.fetcher.robots.states(),
            "truncated": truncated,
            "interrupted": interrupted,
        }

        summary = self.graph.summary(
            ignored_links=ignored_links,
            pages_requested=pages_requested,
        )

        return {
            "meta": meta,
            "summary": summary,
            "pages_requested": pages_requested,
            "ignored_links": ignored_links,
            "truncated": truncated,
            "interrupted": interrupted,
        }
