"""Tests for the polite HTTP fetcher."""
import responses
import pytest
import requests
from requests.exceptions import Timeout, SSLError, ConnectionError

from linkatlas.fetcher import Fetcher
from linkatlas.models import CrawlConfig
from linkatlas.robots import RobotsCache


class MockClock:
    def __init__(self, start: float = 1000.0):
        self.time = start

    def __call__(self) -> float:
        return self.time

    def advance(self, seconds: float):
        self.time += seconds


@responses.activate
def test_fetcher_200_html_ok():
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=404,
    )
    responses.add(
        responses.GET,
        "https://example.com/page",
        body="<html><body>Hello</body></html>",
        status=200,
        headers={"Content-Type": "text/html; charset=utf-8", "X-Robots-Tag": "noindex, nofollow"},
    )

    config = CrawlConfig(seed="https://example.com", delay=0.0)
    fetcher = Fetcher(config=config)
    res = fetcher.fetch("https://example.com/page")

    assert res.state == "ok"
    assert res.status == 200
    assert res.content == b"<html><body>Hello</body></html>"
    assert res.nofollow_header is True
    assert res.redirect_to is None


@responses.activate
def test_fetcher_404_gives_http_error():
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=404,
    )
    responses.add(
        responses.GET,
        "https://example.com/missing",
        status=404,
    )

    config = CrawlConfig(seed="https://example.com", delay=0.0)
    fetcher = Fetcher(config=config)
    res = fetcher.fetch("https://example.com/missing")

    assert res.state == "http_error"
    assert res.status == 404
    assert res.content is None


@responses.activate
def test_fetcher_500_then_200_succeeds_with_retries():
    sleep_calls = []
    clock = MockClock()

    def mock_sleep(s):
        sleep_calls.append(s)
        clock.advance(s)

    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=404,
    )
    responses.add(
        responses.GET,
        "https://example.com/flaky",
        status=500,
    )
    responses.add(
        responses.GET,
        "https://example.com/flaky",
        body="<html><body>Recovered</body></html>",
        status=200,
        headers={"Content-Type": "text/html"},
    )

    config = CrawlConfig(seed="https://example.com", delay=0.0, retries=1)
    fetcher = Fetcher(config=config, sleep=mock_sleep, clock=clock)
    res = fetcher.fetch("https://example.com/flaky")

    assert res.state == "ok"
    assert res.status == 200
    assert len(sleep_calls) >= 1  # retry backoff slept
    assert sleep_calls[0] == 1.0


@responses.activate
def test_fetcher_timeout_retried():
    sleep_calls = []
    clock = MockClock()

    def mock_sleep(s):
        sleep_calls.append(s)
        clock.advance(s)

    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=404,
    )
    responses.add(
        responses.GET,
        "https://example.com/slow",
        body=Timeout("Connection timed out"),
    )
    responses.add(
        responses.GET,
        "https://example.com/slow",
        body=Timeout("Read timed out"),
    )

    config = CrawlConfig(seed="https://example.com", delay=0.0, retries=1)
    fetcher = Fetcher(config=config, sleep=mock_sleep, clock=clock)
    res = fetcher.fetch("https://example.com/slow")

    assert res.state == "timeout"
    assert len(sleep_calls) == 1
    assert sleep_calls[0] == 1.0


@responses.activate
def test_fetcher_ssl_error_not_retried():
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=404,
    )
    responses.add(
        responses.GET,
        "https://example.com/bad-ssl",
        body=SSLError("Certificate verify failed"),
    )

    config = CrawlConfig(seed="https://example.com", delay=0.0, retries=2)
    fetcher = Fetcher(config=config)
    res = fetcher.fetch("https://example.com/bad-ssl")

    assert res.state == "ssl_error"
    # Verify it made only 1 request to /bad-ssl (not retried)
    bad_ssl_calls = [c for c in responses.calls if "bad-ssl" in c.request.url]
    assert len(bad_ssl_calls) == 1


@responses.activate
def test_fetcher_non_html():
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=404,
    )
    responses.add(
        responses.GET,
        "https://example.com/doc.pdf",
        body=b"%PDF-1.4...",
        status=200,
        headers={"Content-Type": "application/pdf"},
    )

    config = CrawlConfig(seed="https://example.com", delay=0.0)
    fetcher = Fetcher(config=config)
    res = fetcher.fetch("https://example.com/doc.pdf")

    assert res.state == "non_html"
    assert res.status == 200
    assert res.content is None


@responses.activate
def test_fetcher_too_large():
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=404,
    )
    # Exceeds max_bytes of 100 bytes
    large_body = b"x" * 200
    responses.add(
        responses.GET,
        "https://example.com/large",
        body=large_body,
        status=200,
        headers={"Content-Type": "text/html"},
    )

    config = CrawlConfig(seed="https://example.com", delay=0.0, max_bytes=100)
    fetcher = Fetcher(config=config)
    res = fetcher.fetch("https://example.com/large")

    assert res.state == "too_large"
    assert res.content is None


@responses.activate
def test_fetcher_301_redirect():
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=404,
    )
    responses.add(
        responses.GET,
        "https://example.com/old",
        status=301,
        headers={"Location": "/new"},
    )

    config = CrawlConfig(seed="https://example.com", delay=0.0)
    fetcher = Fetcher(config=config)
    res = fetcher.fetch("https://example.com/old")

    assert res.state == "redirect"
    assert res.status == 301
    assert res.redirect_to == "https://example.com/new"


@responses.activate
def test_fetcher_429_retry_after():
    sleep_calls = []
    clock = MockClock()

    def mock_sleep(s):
        sleep_calls.append(s)
        clock.advance(s)

    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=404,
    )
    # First: 429 with Retry-After: 2
    responses.add(
        responses.GET,
        "https://example.com/rate-limited",
        status=429,
        headers={"Retry-After": "2"},
    )
    responses.add(
        responses.GET,
        "https://example.com/rate-limited",
        body="<html><body>OK</body></html>",
        status=200,
        headers={"Content-Type": "text/html"},
    )

    config = CrawlConfig(seed="https://example.com", delay=0.0, retries=1)
    fetcher = Fetcher(config=config, sleep=mock_sleep, clock=clock)
    res = fetcher.fetch("https://example.com/rate-limited")

    assert res.state == "ok"
    assert 2.0 in sleep_calls

    # Now test Retry-After > 10s: gives up immediately
    responses.add(
        responses.GET,
        "https://example.com/blocked",
        status=429,
        headers={"Retry-After": "60"},
    )
    res_blocked = fetcher.fetch("https://example.com/blocked")
    assert res_blocked.state == "http_error"
    assert res_blocked.status == 429
    assert "Retry-After exceeds 10s" in (res_blocked.error or "")


@responses.activate
def test_fetcher_robots_disallow_makes_no_http_request():
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        body="User-agent: *\nDisallow: /secret/",
        status=200,
    )

    config = CrawlConfig(seed="https://example.com", delay=0.0)
    fetcher = Fetcher(config=config)
    res = fetcher.fetch("https://example.com/secret/key")

    assert res.state == "robots_disallowed"
    # Verify no GET was made to /secret/key
    secret_calls = [c for c in responses.calls if "secret/key" in c.request.url]
    assert len(secret_calls) == 0


@responses.activate
def test_fetcher_delay_between_requests_to_same_host():
    sleep_calls = []
    clock = MockClock()

    def mock_sleep(s):
        sleep_calls.append(s)
        clock.advance(s)

    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=404,
    )
    responses.add(
        responses.GET,
        "https://example.com/p1",
        body="<html></html>",
        status=200,
        headers={"Content-Type": "text/html"},
    )
    responses.add(
        responses.GET,
        "https://example.com/p2",
        body="<html></html>",
        status=200,
        headers={"Content-Type": "text/html"},
    )

    config = CrawlConfig(seed="https://example.com", delay=1.5)
    fetcher = Fetcher(config=config, sleep=mock_sleep, clock=clock)

    fetcher.fetch("https://example.com/p1")
    # Advance clock by 0.5s (less than delay of 1.5s)
    clock.advance(0.5)
    fetcher.fetch("https://example.com/p2")

    # Should sleep for remaining 1.0s
    assert len(sleep_calls) == 1
    assert sleep_calls[0] == pytest.approx(1.0)
