"""
Unit tests for disk cache and key hashing.
"""

import time
import httpx
import pytest
import respx

from feedfuse.cache import Cache, make_key
from feedfuse.fetcher import fetch_source
from feedfuse.models import Source


def test_make_key_changes_with_url_and_params():
    """Cache key varies with url, params, and headers."""
    k1 = make_key("https://api.com", {"a": "1"}, {})
    k2 = make_key("https://api.com", {"a": "2"}, {})
    k3 = make_key("https://other.com", {"a": "1"}, {})
    assert k1 != k2
    assert k1 != k3


def test_make_key_secrets_not_in_plain_text(tmp_path):
    """File contents and keys never contain plain-text secret tokens."""
    token = "super_secret_github_token_xyz"
    key = make_key("https://api.com", {}, {"Authorization": f"Bearer {token}"})
    assert token not in key

    cache = Cache(ttl_seconds=60, directory=tmp_path)
    cache.set(key, {"data": "test"})

    cache_file = tmp_path / f"{key}.json"
    assert cache_file.exists()
    content = cache_file.read_text(encoding="utf-8")
    assert token not in content


@pytest.mark.asyncio
@respx.mock
async def test_cache_hit_makes_no_http_request(tmp_path):
    """Second call within TTL returns state='cached' without HTTP request."""
    route = respx.get("https://api.com/cached").mock(
        return_value=httpx.Response(200, json={"value": 42})
    )
    cache = Cache(ttl_seconds=60, directory=tmp_path)
    src = Source(name="s1", url="https://api.com/cached")

    async with httpx.AsyncClient() as client:
        # First call -> fetches and caches
        res1 = await fetch_source(client, src, cache=cache)
        assert res1.state == "ok"
        assert res1.data == {"value": 42}
        assert route.call_count == 1

        # Second call -> cache hit
        res2 = await fetch_source(client, src, cache=cache)
        assert res2.state == "cached"
        assert res2.data == {"value": 42}
        assert route.call_count == 1  # No additional request made


@pytest.mark.asyncio
@respx.mock
async def test_expired_entry_triggers_new_request(tmp_path):
    """Expired cache entry triggers a new HTTP request."""
    route = respx.get("https://api.com/expire").mock(
        return_value=httpx.Response(200, json={"time": 1})
    )
    # TTL of 1 second
    cache = Cache(ttl_seconds=1, directory=tmp_path)
    src = Source(name="s1", url="https://api.com/expire")

    async with httpx.AsyncClient() as client:
        res1 = await fetch_source(client, src, cache=cache)
        assert res1.state == "ok"
        assert route.call_count == 1

        # Wait for TTL to expire
        time.sleep(1.1)

        res2 = await fetch_source(client, src, cache=cache)
        assert res2.state == "ok"
        assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_corrupted_cache_file_ignored(tmp_path):
    """Corrupted cache file is ignored and a fresh request is made."""
    route = respx.get("https://api.com/corrupt").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    cache = Cache(ttl_seconds=60, directory=tmp_path)
    key = make_key("https://api.com/corrupt", {}, {})

    # Write corrupted JSON
    bad_file = tmp_path / f"{key}.json"
    bad_file.write_text("CORRUPTED NOT JSON", encoding="utf-8")

    src = Source(name="s1", url="https://api.com/corrupt")
    async with httpx.AsyncClient() as client:
        res = await fetch_source(client, src, cache=cache)
        assert res.state == "ok"
        assert route.call_count == 1
