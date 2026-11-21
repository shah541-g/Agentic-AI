"""Data models for LinkAtlas."""
from dataclasses import dataclass, field

DEFAULT_UA = "LinkAtlas/0.1 (+https://github.com/your-username/linkatlas)"

@dataclass
class CrawlConfig:
    seed: str
    max_depth: int = 2
    max_pages: int = 200
    delay: float = 1.0
    timeout: float = 10.0
    retries: int = 1
    max_bytes: int = 2_000_000
    include_subdomains: bool = False
    user_agent: str = DEFAULT_UA

    def __post_init__(self):
        if self.max_depth not in (0, 1, 2):
            raise ValueError(f"max_depth must be 0, 1 or 2 (got {self.max_depth})")
        if self.max_pages < 1:
            raise ValueError("max_pages must be at least 1")
        if self.delay < 0:
            raise ValueError("delay must be >= 0")
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")
        if not (0 <= self.retries <= 3):
            raise ValueError("retries must be 0–3")


@dataclass
class FetchResult:
    url: str
    state: str
    status: int | None = None
    content: bytes | None = None
    redirect_to: str | None = None
    nofollow_header: bool = False
    error: str | None = None
    elapsed_ms: int = 0


@dataclass
class RawLink:
    url: str
    text: str
    nofollow: bool


@dataclass
class ExtractResult:
    title: str | None
    links: list[RawLink] = field(default_factory=list)
    page_nofollow: bool = False
    ignored_links: int = 0
