"""Tests for robots.txt caching and policy checking."""
import responses
import pytest
import requests
from linkatlas.robots import RobotsCache, get_origin


@responses.activate
def test_robots_200_with_rules():
    robots_txt = """
    User-agent: *
    Disallow: /admin/
    Disallow: /private/
    Crawl-delay: 2.5
    """
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        body=robots_txt,
        status=200,
    )

    session = requests.Session()
    cache = RobotsCache(session=session, user_agent="LinkAtlas/0.1")
    policy = cache.policy_for("https://example.com/page")

    assert policy.state == "ok"
    assert policy.allowed("https://example.com/page") is True
    assert policy.allowed("https://example.com/admin/settings") is False
    assert policy.allowed("https://example.com/private/data") is False
    assert policy.crawl_delay() == 2.5
    assert cache.states() == {"https://example.com": "ok"}


@responses.activate
def test_robots_product_token_beats_wildcard():
    robots_txt = """
    User-agent: *
    Disallow: /

    User-agent: LinkAtlas
    Disallow: /secret/
    Allow: /
    Crawl-delay: 1.0
    """
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        body=robots_txt,
        status=200,
    )

    session = requests.Session()
    cache = RobotsCache(session=session, user_agent="LinkAtlas/0.1 (+https://...)")
    policy = cache.policy_for("https://example.com/blog")

    assert policy.state == "ok"
    assert policy.allowed("https://example.com/blog") is True
    assert policy.allowed("https://example.com/secret/key") is False
    assert policy.crawl_delay() == 1.0


@responses.activate
def test_robots_404_allows_all():
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=404,
    )

    session = requests.Session()
    cache = RobotsCache(session=session)
    policy = cache.policy_for("https://example.com/anything")

    assert policy.state == "missing"
    assert policy.allowed("https://example.com/anything") is True
    assert policy.crawl_delay() is None
    assert cache.states() == {"https://example.com": "missing"}


@responses.activate
def test_robots_403_disallows_all():
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=403,
    )

    session = requests.Session()
    cache = RobotsCache(session=session)
    policy = cache.policy_for("https://example.com/public")

    assert policy.state == "forbidden"
    assert policy.allowed("https://example.com/public") is False
    assert policy.crawl_delay() is None
    assert cache.states() == {"https://example.com": "forbidden"}


@responses.activate
def test_robots_401_disallows_all():
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=401,
    )

    session = requests.Session()
    cache = RobotsCache(session=session)
    policy = cache.policy_for("https://example.com/public")

    assert policy.state == "forbidden"
    assert policy.allowed("https://example.com/public") is False


@responses.activate
def test_robots_503_retried_and_unreachable():
    sleep_calls = []

    def mock_sleep(seconds):
        sleep_calls.append(seconds)

    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=503,
    )
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=503,
    )

    session = requests.Session()
    cache = RobotsCache(session=session, sleep=mock_sleep)
    policy = cache.policy_for("https://example.com/page")

    assert policy.state == "unreachable"
    assert policy.allowed("https://example.com/page") is False
    assert len(sleep_calls) == 1
    assert len(responses.calls) == 2


@responses.activate
def test_robots_retry_recovers():
    sleep_calls = []

    def mock_sleep(seconds):
        sleep_calls.append(seconds)

    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        status=500,
    )
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        body="User-agent: *\nDisallow: /admin/",
        status=200,
    )

    session = requests.Session()
    cache = RobotsCache(session=session, sleep=mock_sleep)
    policy = cache.policy_for("https://example.com/page")

    assert policy.state == "ok"
    assert policy.allowed("https://example.com/page") is True
    assert policy.allowed("https://example.com/admin/x") is False
    assert len(sleep_calls) == 1
    assert len(responses.calls) == 2


@responses.activate
def test_robots_caching_per_origin():
    responses.add(
        responses.GET,
        "https://example.com/robots.txt",
        body="User-agent: *\nDisallow: /secret/",
        status=200,
    )

    session = requests.Session()
    cache = RobotsCache(session=session)

    pol1 = cache.policy_for("https://example.com/page1")
    pol2 = cache.policy_for("https://example.com/page2")

    assert pol1 is pol2
    assert len(responses.calls) == 1
