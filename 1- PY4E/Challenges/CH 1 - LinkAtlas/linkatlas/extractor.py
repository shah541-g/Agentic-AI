"""Link and metadata extraction from HTML content."""
from __future__ import annotations
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from linkatlas.models import ExtractResult, RawLink
from linkatlas.urls import normalize_url

_NON_HTTP_SCHEMES = frozenset({"mailto", "tel", "javascript", "data", "ftp", "file", "sms"})
_WHITESPACE_RE = re.compile(r"\s+")


def extract_links(content: bytes, page_url: str) -> ExtractResult:
    """Extract page title, links, and robots meta tags from HTML bytes.
    Never raises an exception on broken HTML or invalid encodings."""
    if not content:
        return ExtractResult(title=None, links=[], page_nofollow=False, ignored_links=0)

    try:
        soup = BeautifulSoup(content, "html.parser")
    except Exception:
        return ExtractResult(title=None, links=[], page_nofollow=False, ignored_links=0)

    # 1. Base URL
    base_url = page_url
    base_tag = soup.find("base", href=True)
    if base_tag and base_tag.get("href"):
        raw_base = str(base_tag["href"]).strip()
        base_url = urljoin(page_url, raw_base)

    # 2. Page title
    title = None
    title_tag = soup.find("title")
    if title_tag:
        raw_title = title_tag.get_text(" ", strip=True)
        if raw_title:
            title = _WHITESPACE_RE.sub(" ", raw_title).strip()[:120].strip()

    # 3. Meta robots nofollow
    page_nofollow = False
    meta_tags = soup.find_all("meta")
    for meta in meta_tags:
        name = meta.get("name")
        if name and name.strip().lower() == "robots":
            content_val = meta.get("content", "")
            if isinstance(content_val, str):
                tokens = {t.strip().lower() for t in content_val.split(",")}
                if "nofollow" in tokens or "none" in tokens:
                    page_nofollow = True
                    break

    # 4. Extract links from <a href="...">
    links: list[RawLink] = []
    ignored_links = 0

    for a in soup.find_all("a", href=True):
        href_raw = a.get("href")
        if not href_raw:
            continue
        href = str(href_raw).strip()

        # Skip empty hrefs and pure fragment identifiers (#...) silently
        if not href or href.startswith("#"):
            continue

        # Check for non-http(s) schemes directly
        parsed_href = urlparse(href)
        if parsed_href.scheme and parsed_href.scheme.lower() in _NON_HTTP_SCHEMES:
            ignored_links += 1
            continue

        # Resolve against base_url
        full_url = urljoin(base_url, href)
        parsed_full = urlparse(full_url)
        if parsed_full.scheme.lower() not in ("http", "https"):
            ignored_links += 1
            continue

        normalized = normalize_url(full_url)
        if not normalized:
            # e.g., exceeds 2000 chars or normalization failed
            continue

        # Anchor text: collapse whitespace, max 80 chars
        raw_text = a.get_text(" ", strip=True)
        text = _WHITESPACE_RE.sub(" ", raw_text).strip()[:80].strip() if raw_text else ""

        # nofollow attribute
        rel_attr = a.get("rel", [])
        if isinstance(rel_attr, str):
            rel_tokens = rel_attr.split()
        elif isinstance(rel_attr, (list, tuple)):
            rel_tokens = rel_attr
        else:
            rel_tokens = []
        nofollow = any(str(r).strip().lower() == "nofollow" for r in rel_tokens)

        links.append(RawLink(url=normalized, text=text, nofollow=nofollow))

    return ExtractResult(
        title=title,
        links=links,
        page_nofollow=page_nofollow,
        ignored_links=ignored_links,
    )
