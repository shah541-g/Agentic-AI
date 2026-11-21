"""Polite HTTP fetcher with robots checking, delays, retries, and error isolation."""
from __future__ import annotations
import time
from urllib.parse import urlparse
import requests
from requests.exceptions import Timeout, SSLError, ConnectionError, RequestException

from linkatlas.models import CrawlConfig, FetchResult
from linkatlas.robots import RobotsCache
from linkatlas.urls import normalize_url

_HTML_TYPES = ("text/html", "application/xhtml+xml")
_RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


class Fetcher:
    """Synchronous, polite fetcher for LinkAtlas."""

    def __init__(
        self,
        config: CrawlConfig,
        session: requests.Session | None = None,
        robots: RobotsCache | None = None,
        sleep=time.sleep,
        clock=time.monotonic,
    ) -> None:
        self.config = config
        self.session = session or requests.Session()
        self.sleep = sleep
        self.clock = clock
        self.robots = robots or RobotsCache(
            session=self.session,
            user_agent=config.user_agent,
            timeout=config.timeout,
            sleep=sleep,
        )
        self._last_request_time: dict[str, float] = {}

    def fetch(self, url: str) -> FetchResult:
        """Fetch a URL according to politeness rules. Never raises."""
        try:
            return self._fetch_internal(url)
        except Exception as e:
            return FetchResult(url=url, state="connection_error", error=str(e))

    def _fetch_internal(self, url: str) -> FetchResult:
        # 1. Robots.txt check
        policy = self.robots.policy_for(url)
        if not policy.allowed(url):
            return FetchResult(
                url=url,
                state="robots_disallowed",
                error="Blocked by robots.txt",
            )

        # 2. Determine effective crawl delay for this host
        crawl_delay = policy.crawl_delay()
        effective_delay = min(10.0, max(self.config.delay, crawl_delay or 0.0))

        host = (urlparse(url).hostname or "").lower()
        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
        }

        max_retries = self.config.retries

        for attempt in range(max_retries + 1):
            # Enforce politeness delay between requests to the same host
            if host in self._last_request_time:
                elapsed = self.clock() - self._last_request_time[host]
                if elapsed < effective_delay:
                    self.sleep(effective_delay - elapsed)

            self._last_request_time[host] = self.clock()
            start_req = self.clock()

            resp = None
            try:
                resp = self.session.get(
                    url,
                    headers=headers,
                    stream=True,
                    allow_redirects=False,
                    timeout=(self.config.timeout, self.config.timeout),
                )
                status = resp.status_code

                # Handle 3xx Redirects
                if status in (301, 302, 303, 307, 308):
                    loc = resp.headers.get("Location")
                    resp.close()
                    if loc:
                        target = normalize_url(loc, base=url)
                        if target:
                            return FetchResult(
                                url=url,
                                state="redirect",
                                status=status,
                                redirect_to=target,
                            )
                    return FetchResult(
                        url=url,
                        state="http_error",
                        status=status,
                        error="Redirect missing or invalid Location",
                    )

                # Handle Retryable Server Errors & Rate Limits (429, 500, 502, 503, 504)
                if status in _RETRYABLE_STATUSES:
                    # Check Retry-After on 429/503
                    if status in (429, 503) and "Retry-After" in resp.headers:
                        retry_after_str = resp.headers.get("Retry-After", "")
                        retry_after = self._parse_retry_after(retry_after_str)
                        resp.close()
                        if retry_after is not None:
                            if retry_after <= 10.0:
                                if attempt < max_retries:
                                    self.sleep(retry_after)
                                    continue
                                return FetchResult(url=url, state="http_error", status=status)
                            else:
                                # Over 10s: give up on that page immediately
                                return FetchResult(
                                    url=url,
                                    state="http_error",
                                    status=status,
                                    error="Retry-After exceeds 10s",
                                )
                    resp.close()
                    if attempt < max_retries:
                        backoff = 1.0 * (2**attempt)
                        self.sleep(backoff)
                        continue
                    return FetchResult(url=url, state="http_error", status=status)

                # Handle other non-2xx status codes
                if not (200 <= status < 300):
                    resp.close()
                    return FetchResult(url=url, state="http_error", status=status)

                # Handle 2xx: Validate Content-Type
                ct = resp.headers.get("Content-Type", "").lower()
                if not any(html_type in ct for html_type in _HTML_TYPES):
                    resp.close()
                    return FetchResult(
                        url=url,
                        state="non_html",
                        status=status,
                        error=f"Non-HTML Content-Type: {ct}",
                    )

                # Read body with size & duration safety limits
                raw_bytes = bytearray()
                too_large = False
                timed_out = False
                max_time = 3 * self.config.timeout

                for chunk in resp.iter_content(chunk_size=8192):
                    if (self.clock() - start_req) > max_time:
                        timed_out = True
                        break
                    raw_bytes.extend(chunk)
                    if len(raw_bytes) > self.config.max_bytes:
                        too_large = True
                        break

                resp.close()

                if too_large:
                    return FetchResult(
                        url=url,
                        state="too_large",
                        status=status,
                        error=f"Body exceeded limit of {self.config.max_bytes} bytes",
                    )
                if timed_out:
                    return FetchResult(
                        url=url,
                        state="timeout",
                        status=status,
                        error="Download exceeded 3x timeout",
                    )

                # Inspect X-Robots-Tag header
                x_robots = resp.headers.get("X-Robots-Tag", "").lower()
                x_tokens = {t.strip() for t in x_robots.split(",")}
                nofollow_header = ("nofollow" in x_tokens or "none" in x_tokens)
                elapsed_ms = int((self.clock() - start_req) * 1000)

                return FetchResult(
                    url=url,
                    state="ok",
                    status=status,
                    content=bytes(raw_bytes),
                    nofollow_header=nofollow_header,
                    elapsed_ms=elapsed_ms,
                )

            except SSLError as e:
                if resp:
                    resp.close()
                return FetchResult(url=url, state="ssl_error", error=str(e))

            except Timeout as e:
                if resp:
                    resp.close()
                if attempt < max_retries:
                    backoff = 1.0 * (2**attempt)
                    self.sleep(backoff)
                    continue
                return FetchResult(url=url, state="timeout", error=str(e))

            except ConnectionError as e:
                if resp:
                    resp.close()
                if attempt < max_retries:
                    backoff = 1.0 * (2**attempt)
                    self.sleep(backoff)
                    continue
                return FetchResult(url=url, state="connection_error", error=str(e))

            except RequestException as e:
                if resp:
                    resp.close()
                return FetchResult(url=url, state="connection_error", error=str(e))

        return FetchResult(url=url, state="connection_error", error="Max retries exhausted")

    def _parse_retry_after(self, val: str) -> float | None:
        """Parse Retry-After header as seconds or HTTP-date."""
        if not val:
            return None
        val = val.strip()
        try:
            return float(val)
        except ValueError:
            try:
                from email.utils import parsedate_to_datetime
                from datetime import datetime, timezone
                dt = parsedate_to_datetime(val)
                now = datetime.now(timezone.utc)
                diff = (dt - now).total_seconds()
                return max(0.0, diff)
            except Exception:
                return None
