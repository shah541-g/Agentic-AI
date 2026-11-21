"""Robots.txt caching and policy checking."""
from __future__ import annotations
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import requests

from linkatlas.urls import _DEFAULT_PORTS


def get_origin(url: str) -> str:
    """Return canonical origin (scheme://host[:port]) from a URL."""
    parsed = urlparse(url)
    scheme = (parsed.scheme or "http").lower()
    host = (parsed.hostname or "").lower()
    port = parsed.port
    default_port = _DEFAULT_PORTS.get(scheme)
    if port is not None and port != default_port:
        return f"{scheme}://{host}:{port}"
    return f"{scheme}://{host}"


def _extract_crawl_delays(lines: list[str]) -> dict[str, float]:
    """Extract crawl-delay values supporting floating point numbers."""
    delays: dict[str, float] = {}
    current_agents: list[str] = []
    state = 0
    for raw_line in lines:
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split(":", 1)
        if len(parts) == 2:
            key, val = parts[0].strip().lower(), parts[1].strip()
            if key == "user-agent":
                if state == 2:
                    current_agents = []
                current_agents.append(val.lower())
                state = 1
            elif key in ("allow", "disallow", "crawl-delay", "request-rate"):
                if state != 0:
                    state = 2
                if key == "crawl-delay":
                    try:
                        val_float = float(val)
                        for ag in current_agents:
                            delays[ag] = val_float
                    except ValueError:
                        pass
    return delays


class RobotsPolicy:
    """Policy for a single origin based on its robots.txt."""

    def __init__(
        self,
        state: str,
        rfp: RobotFileParser | None = None,
        product_token: str = "LinkAtlas",
        custom_delays: dict[str, float] | None = None,
    ) -> None:
        self.state = state  # "ok" | "missing" | "forbidden" | "unreachable"
        self._rfp = rfp
        self._product_token = product_token
        self._custom_delays = custom_delays or {}

    def allowed(self, url: str) -> bool:
        """Check whether LinkAtlas is allowed to fetch the given URL."""
        if self.state == "ok" and self._rfp is not None:
            return self._rfp.can_fetch(self._product_token, url)
        if self.state == "missing":
            return True
        # "forbidden" (401/403) and "unreachable" (5xx/timeouts) disallow all
        return False

    def crawl_delay(self) -> float | None:
        """Return Crawl-delay in seconds, or None if not specified."""
        if self.state == "ok":
            # Check custom delays first to support float values (e.g. 2.5)
            token_lower = self._product_token.lower()
            if token_lower in self._custom_delays:
                return self._custom_delays[token_lower]
            if "*" in self._custom_delays:
                return self._custom_delays["*"]

            if self._rfp is not None:
                delay = self._rfp.crawl_delay(self._product_token)
                if delay is None:
                    delay = self._rfp.crawl_delay("*")
                if delay is not None:
                    try:
                        return float(delay)
                    except (ValueError, TypeError):
                        return None
        return None


class RobotsCache:
    """Cache of robots policies per origin."""

    def __init__(
        self,
        session: requests.Session | None = None,
        user_agent: str = "LinkAtlas/0.1",
        timeout: float = 10.0,
        sleep=time.sleep,
    ) -> None:
        self.session = session or requests.Session()
        self.user_agent = user_agent
        self.timeout = timeout
        self.sleep = sleep
        self._cache: dict[str, RobotsPolicy] = {}

        # Extract product token (e.g. LinkAtlas from LinkAtlas/0.1)
        if "/" in user_agent:
            self.product_token = user_agent.split("/")[0].strip()
        else:
            self.product_token = user_agent.split()[0].strip() if user_agent else "LinkAtlas"

    def policy_for(self, url: str) -> RobotsPolicy:
        """Fetch and cache policy by origin according to Section 5.1 rules."""
        origin = get_origin(url)
        if origin in self._cache:
            return self._cache[origin]

        robots_url = f"{origin}/robots.txt"
        policy = self._fetch_policy(robots_url)
        self._cache[origin] = policy
        return policy

    def _fetch_policy(self, robots_url: str) -> RobotsPolicy:
        """Fetch robots.txt with up to 1 retry on 5xx or connection/timeout error."""
        for attempt in range(2):
            try:
                resp = self.session.get(
                    robots_url,
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout,
                    stream=True,
                )
                status = resp.status_code
                if status == 200:
                    raw_bytes = bytearray()
                    for chunk in resp.iter_content(chunk_size=8192):
                        raw_bytes.extend(chunk)
                        if len(raw_bytes) >= 500_000:
                            break
                    resp.close()
                    text = bytes(raw_bytes[:500_000]).decode("utf-8", errors="replace")
                    clean_lines = [line.strip() for line in text.splitlines()]
                    rfp = RobotFileParser()
                    rfp.parse(clean_lines)
                    custom_delays = _extract_crawl_delays(clean_lines)
                    return RobotsPolicy(
                        "ok",
                        rfp=rfp,
                        product_token=self.product_token,
                        custom_delays=custom_delays,
                    )
                elif status in (401, 403):
                    resp.close()
                    return RobotsPolicy("forbidden", product_token=self.product_token)
                elif 400 <= status < 500:
                    resp.close()
                    return RobotsPolicy("missing", product_token=self.product_token)
                else:  # 5xx or other status
                    resp.close()
                    if attempt == 0:
                        self.sleep(1.0)
                        continue
                    return RobotsPolicy("unreachable", product_token=self.product_token)
            except (requests.Timeout, requests.ConnectionError):
                if attempt == 0:
                    self.sleep(1.0)
                    continue
                return RobotsPolicy("unreachable", product_token=self.product_token)
            except requests.RequestException:
                if attempt == 0:
                    self.sleep(1.0)
                    continue
                return RobotsPolicy("unreachable", product_token=self.product_token)

        return RobotsPolicy("unreachable", product_token=self.product_token)

    def states(self) -> dict[str, str]:
        """Return map of origin -> state for meta.robots."""
        return {origin: policy.state for origin, policy in self._cache.items()}
