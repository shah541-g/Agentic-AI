"""URL utilities: normalization, internal detection, extension checks."""
from __future__ import annotations
from urllib.parse import urlparse, urlunparse, urljoin, urlencode, parse_qsl

# Tracking query param names to remove (exact match)
_EXACT_TRACKING = frozenset({"fbclid", "gclid", "msclkid", "mc_cid", "mc_eid"})

# Default ports that should be stripped
_DEFAULT_PORTS = {"http": 80, "https": 443}

# File extensions that mean the URL should be skipped (never fetched)
_SKIP_EXTS = frozenset({
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".bmp",
    ".zip", ".gz", ".tar", ".rar", ".7z", ".mp3", ".mp4", ".avi", ".mov",
    ".wmv", ".css", ".js", ".json", ".xml", ".woff", ".woff2", ".ttf",
    ".exe", ".dmg", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
})


def normalize_url(url: str, base: str | None = None) -> str | None:
    """Normalize a URL according to LinkAtlas rules (section 4.4).
    Returns None if the URL is not crawlable (bad scheme, too long, etc.)."""
    if base:
        url = urljoin(base, url)
    if len(url) > 2000:
        return None
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        return None
    host = parsed.hostname or ""
    host = host.lower()
    # Drop userinfo; drop default port
    port = parsed.port
    if port and port == _DEFAULT_PORTS.get(scheme):
        port = None
    netloc = host if port is None else f"{host}:{port}"
    # Remove fragment; normalise empty path
    path = parsed.path or "/"
    # Clean tracking query params
    params = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
              if not k.startswith("utm_") and k not in _EXACT_TRACKING]
    query = urlencode(params)
    return urlunparse((scheme, netloc, path, "", query, ""))


def site_key(host: str) -> str:
    """Return lowercase hostname with leading 'www.' stripped."""
    h = host.lower()
    if h.startswith("www."):
        h = h[4:]
    return h


def is_internal(url: str, seed_url: str, include_subdomains: bool = False) -> bool:
    """Return True if url belongs to the same site as seed_url."""
    parsed = urlparse(url)
    seed_parsed = urlparse(seed_url)
    url_key = site_key(parsed.hostname or "")
    seed_key = site_key(seed_parsed.hostname or "")
    if url_key == seed_key:
        return True
    if include_subdomains and url_key.endswith("." + seed_key):
        return True
    return False


def has_skippable_extension(url: str) -> bool:
    """Return True if the URL path ends with a skippable extension (case-insensitive)."""
    path = urlparse(url).path
    dot = path.rfind(".")
    if dot == -1:
        return False
    ext = path[dot:].lower()
    return ext in _SKIP_EXTS


def domain_of(url: str) -> str:
    """Return the site_key of the URL's hostname."""
    return site_key(urlparse(url).hostname or "")
