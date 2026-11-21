"""
Unit tests for the asynchronous fetcher using respx mocking.
"""

import asyncio
import time
import httpx
import pytest
import respx

from feedfuse.fetcher import fetch_all, fetch_source
from feedfuse.models import Source


@pytest.mark.asyncio
@respx.mock
async def test_fetch_source_success():
    """Successful fetch returns state='ok' and mapped data."""
    respx.get("https://api.test.com/weather").mock(
        return_value=httpx.Response(200, json={"temperature": 22.5, "city": "Lahore"})
    )
    src = Source(
        name="weather",
        url="https://api.test.com/weather",
        map={"temp": "temperature", "location": "city"},
    )

    async with httpx.AsyncClient() as client:
        res = await fetch_source(client, src)

    assert res.state == "ok"
    assert res.name == "weather"
    assert res.data == {"temp": 22.5, "location": "Lahore"}
    assert res.error is None


@pytest.mark.asyncio
@respx.mock
async def test_fetch_concurrent_timing():
    """Two sources run concurrently; total time is close to slowest, not the sum."""
    async def delayed_1(request):
        await asyncio.sleep(0.1)
        return httpx.Response(200, json={"s1": 1})

    async def delayed_2(request):
        await asyncio.sleep(0.1)
        return httpx.Response(200, json={"s2": 2})

    respx.get("https://api.test.com/s1").mock(side_effect=delayed_1)
    respx.get("https://api.test.com/s2").mock(side_effect=delayed_2)

    sources = [
        Source(name="s1", url="https://api.test.com/s1"),
        Source(name="s2", url="https://api.test.com/s2"),
    ]

    t0 = time.perf_counter()
    results = await fetch_all(sources)
    total_elapsed = time.perf_counter() - t0

    assert len(results) == 2
    assert results[0].state == "ok"
    assert results[1].state == "ok"
    # Total elapsed should be around ~0.1s - 0.18s, well below serial sum ~0.2s + overhead
    assert total_elapsed < 0.25


@pytest.mark.asyncio
@respx.mock
async def test_retry_on_500_then_succeed():
    """HTTP 500 is retried and succeeds on second attempt."""
    route = respx.get("https://api.test.com/flaky").mock(
        side_effect=[
            httpx.Response(500, json={"error": "server error"}),
            httpx.Response(200, json={"status": "recovered"}),
        ]
    )
    src = Source(
        name="flaky",
        url="https://api.test.com/flaky",
        retries=2,
    )

    async with httpx.AsyncClient() as client:
        res = await fetch_source(client, src)

    assert res.state == "ok"
    assert res.data == {"status": "recovered"}
    assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_no_retry_on_404():
    """HTTP 404 is not retried and fails immediately."""
    route = respx.get("https://api.test.com/not_found").mock(
        return_value=httpx.Response(404, text="Not Found")
    )
    src = Source(
        name="not_found",
        url="https://api.test.com/not_found",
        retries=3,
    )

    async with httpx.AsyncClient() as client:
        res = await fetch_source(client, src)

    assert res.state == "failed"
    assert res.error == "HTTP 404"
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_timeout_isolation():
    """Timeout produces state='timeout', while other sources succeed."""
    respx.get("https://api.test.com/slow").mock(
        side_effect=httpx.TimeoutException("Read timed out")
    )
    respx.get("https://api.test.com/fast").mock(
        return_value=httpx.Response(200, json={"msg": "fast ok"})
    )

    sources = [
        Source(name="slow", url="https://api.test.com/slow", timeout=1.0, retries=0),
        Source(name="fast", url="https://api.test.com/fast", timeout=1.0, retries=0),
    ]

    results = await fetch_all(sources)
    assert len(results) == 2
    assert results[0].state == "timeout"
    assert "Timed out after 1s" in results[0].error
    assert results[1].state == "ok"
    assert results[1].data == {"msg": "fast ok"}


@pytest.mark.asyncio
@respx.mock
async def test_non_json_response_fails():
    """Non-JSON response body produces state='failed'."""
    respx.get("https://api.test.com/html").mock(
        return_value=httpx.Response(200, text="<html>Not JSON</html>")
    )
    src = Source(name="html_src", url="https://api.test.com/html")

    async with httpx.AsyncClient() as client:
        res = await fetch_source(client, src)

    assert res.state == "failed"
    assert res.error == "Response is not valid JSON"


@pytest.mark.asyncio
async def test_missing_env_fails_only_that_source():
    """Missing environment variable fails only the source requiring it."""
    sources = [
        Source(
            name="needs_secret",
            url="https://api.test.com/secret",
            headers={"Authorization": "Bearer ${UNDEFINED_API_KEY}"},
        ),
        Source(
            name="public_source",
            url="https://api.test.com/public",
        ),
    ]

    with respx.mock:
        respx.get("https://api.test.com/public").mock(
            return_value=httpx.Response(200, json={"data": "public"})
        )
        results = await fetch_all(sources)

    assert len(results) == 2
    assert results[0].state == "failed"
    assert "Missing environment variable UNDEFINED_API_KEY" in results[0].error
    assert results[1].state == "ok"
    assert results[1].data == {"data": "public"}
