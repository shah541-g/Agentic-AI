"""
Asynchronous HTTP fetching engine with retries, backoff, and fault isolation.
"""

import asyncio
import time
from typing import Any, List, Optional

import httpx

from feedfuse import __version__
from feedfuse.cache import Cache, make_key
from feedfuse.config import MissingEnvError, interpolate_dict
from feedfuse.mapper import apply_map, extract_records
from feedfuse.models import Source, SourceResult


def _process_response_data(source: Source, raw_json: Any, state: str, ms: int) -> SourceResult:
    """Apply map and records extraction to raw JSON response."""
    if source.records is not None:
        records_list, rec_warnings = extract_records(raw_json, source.records)
        if source.map:
            mapped_records = []
            map_warnings = []
            for rec in records_list:
                m_row, w = apply_map(rec, source.map)
                mapped_records.append(m_row)
                map_warnings.extend(w)
            # De-duplicate warnings preserving order
            all_warnings = rec_warnings + list(dict.fromkeys(map_warnings))
            return SourceResult(
                name=source.name,
                state=state,
                data=mapped_records,
                ms=ms,
                warnings=all_warnings,
            )
        else:
            return SourceResult(
                name=source.name,
                state=state,
                data=records_list,
                ms=ms,
                warnings=rec_warnings,
            )
    else:
        mapped_data, warnings = apply_map(raw_json, source.map)
        return SourceResult(
            name=source.name,
            state=state,
            data=mapped_data,
            ms=ms,
            warnings=warnings,
        )


async def fetch_source(
    client: httpx.AsyncClient,
    source: Source,
    cache: Optional[Cache] = None,
    verbose: bool = False,
) -> SourceResult:
    """
    Fetch a single source with retries, timeout, and disk caching.

    Never raises an exception; all errors are captured inside SourceResult.

    Args:
        client: Shared httpx.AsyncClient instance.
        source: Source definition.
        cache: Optional disk cache.
        verbose: If True, prints retry attempts and timings.

    Returns:
        SourceResult with state ("ok", "cached", "failed", "timeout").
    """
    # 1. Interpolate environment variables
    try:
        headers = interpolate_dict(source.headers)
        params = interpolate_dict(source.params)
    except MissingEnvError as err:
        return SourceResult(
            name=source.name,
            state="failed",
            error=str(err),
            ms=0,
        )

    # 2. Check disk cache
    cache_key: Optional[str] = None
    if cache is not None:
        cache_key = make_key(source.url, params, headers)
        cached_payload = cache.get(cache_key)
        if cached_payload is not None:
            return _process_response_data(source, cached_payload, state="cached", ms=0)

    # 3. HTTP fetch with retries
    start_time = time.perf_counter()
    attempts = 1 + source.retries

    for attempt in range(attempts):
        is_last_attempt = (attempt == attempts - 1)
        try:
            response = await client.get(
                source.url,
                params=params,
                headers=headers,
                timeout=source.timeout,
            )

            # Check status code
            if response.status_code == 200:
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                try:
                    raw_json = response.json()
                except Exception:
                    return SourceResult(
                        name=source.name,
                        state="failed",
                        error="Response is not valid JSON",
                        ms=elapsed_ms,
                    )

                if cache is not None and cache_key is not None:
                    cache.set(cache_key, raw_json)

                return _process_response_data(source, raw_json, state="ok", ms=elapsed_ms)

            elif response.status_code == 429 or response.status_code >= 500:
                # Retryable HTTP status
                if not is_last_attempt:
                    delay = 0.5 * (2 ** attempt)
                    retry_after = response.headers.get("Retry-After")
                    if response.status_code == 429 and retry_after:
                        try:
                            ra = float(retry_after)
                            if 0 <= ra <= 10.0:
                                delay = ra
                        except ValueError:
                            pass
                    if verbose:
                        print(f"[{source.name}] HTTP {response.status_code}, retrying in {delay:.2f}s (attempt {attempt + 1}/{attempts})...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                    return SourceResult(
                        name=source.name,
                        state="failed",
                        error=f"HTTP {response.status_code}",
                        ms=elapsed_ms,
                    )
            else:
                # Other 4xx status codes (400, 401, 403, 404, etc.) -> do not retry
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                return SourceResult(
                    name=source.name,
                    state="failed",
                    error=f"HTTP {response.status_code}",
                    ms=elapsed_ms,
                )

        except httpx.TimeoutException:
            if not is_last_attempt:
                delay = 0.5 * (2 ** attempt)
                if verbose:
                    print(f"[{source.name}] Timed out, retrying in {delay:.2f}s (attempt {attempt + 1}/{attempts})...")
                await asyncio.sleep(delay)
                continue
            else:
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                retries_str = f" ({source.retries} retries)" if source.retries > 0 else ""
                return SourceResult(
                    name=source.name,
                    state="timeout",
                    error=f"Timed out after {source.timeout:g}s{retries_str}",
                    ms=elapsed_ms,
                )

        except (httpx.ConnectError, httpx.NetworkError, httpx.TransportError) as exc:
            if not is_last_attempt:
                delay = 0.5 * (2 ** attempt)
                if verbose:
                    print(f"[{source.name}] Connection error, retrying in {delay:.2f}s (attempt {attempt + 1}/{attempts})...")
                await asyncio.sleep(delay)
                continue
            else:
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                return SourceResult(
                    name=source.name,
                    state="failed",
                    error=f"Connection error: {exc}",
                    ms=elapsed_ms,
                )

        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return SourceResult(
                name=source.name,
                state="failed",
                error=str(exc),
                ms=elapsed_ms,
            )

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
    return SourceResult(name=source.name, state="failed", error="Unknown fetch failure", ms=elapsed_ms)


async def fetch_all(
    sources: List[Source],
    cache: Optional[Cache] = None,
    verbose: bool = False,
) -> List[SourceResult]:
    """
    Fetch all sources concurrently using asyncio.gather.

    Preserves the order of sources from the configuration.
    """
    headers = {"User-Agent": f"feedfuse/{__version__}"}
    async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
        tasks = [fetch_source(client, src, cache=cache, verbose=verbose) for src in sources]
        results = await asyncio.gather(*tasks)
    return list(results)
