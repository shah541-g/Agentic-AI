import json
import logging
import os
import re
import threading
import time
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from logger import clip, get_logger

log = get_logger("llm")

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)

load_dotenv()
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY is missing. Add it to your .env file.")

MODEL_NAME = "gemini-3.5-flash-lite"
client = genai.Client(api_key=API_KEY)

MAX_SEARCH_CHARS = 4000


LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))   # seconds to wait per attempt
LLM_RETRIES = int(os.getenv("LLM_RETRIES", "3"))    # attempts before giving up
_search_blocked_until = 0.0  # while in the future, skip Gemini search (quota exhausted)


def _call_with_timeout(fn, timeout: int):
    """Run fn in a daemon thread so a hung network call can never block us forever."""
    box: dict[str, Any] = {}

    def runner() -> None:
        try:
            box["value"] = fn()
        except BaseException as exc:  # noqa: BLE001 - re-raised in the caller
            box["error"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutError(f"no response within {timeout}s")
    if "error" in box:
        raise box["error"]
    return box["value"]


def _with_retries(fn, label: str, no_retry_on: tuple = (), on_error=None):
    """Call fn with timeout + retries + backoff. Returns (result, seconds_of_last_attempt)."""
    last_exc: Exception = RuntimeError("unreachable")
    for attempt in range(1, LLM_RETRIES + 1):
        start = time.perf_counter()
        log.info("%s: request sent (attempt %d/%d, timeout %ds)...",
                 label, attempt, LLM_RETRIES, LLM_TIMEOUT)
        try:
            result = _call_with_timeout(fn, LLM_TIMEOUT)
            return result, time.perf_counter() - start
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            log.debug("%s failure detail", label, exc_info=True)
            if on_error:
                on_error(exc)
            if any(token in str(exc) for token in no_retry_on):
                log.error("%s: failed, not retrying: %s", label, clip(exc, 160))
                raise
            log.warning("%s: attempt %d/%d failed after %.1fs: %s",
                        label, attempt, LLM_RETRIES, time.perf_counter() - start, clip(exc, 160))
            if attempt < LLM_RETRIES:
                time.sleep(min(2 ** attempt, 8))
    log.error("%s: giving up after %d attempts. Last error: %s", label, LLM_RETRIES, last_exc)
    raise last_exc


def call_llm(system_instructions: str, prompt: str) -> str:
    """Single place for all plain LLM calls."""
    full_input = "<<SYSTEM INSTRUCTIONS>> \n" + system_instructions + "\n\n" + prompt
    log.debug("LLM request:\n%s", full_input)

    retry_hint = {"text": ""}

    def _do() -> str:
        interaction = client.interactions.create(model=MODEL_NAME, input=full_input + retry_hint["text"])
        return interaction.output_text or ""

    def _on_error(exc: Exception) -> None:
        # An identical retry of a 'malformed_tool_call' fails the same way, so change the input.
        if "malformed_tool_call" in str(exc) or "invalid JSON" in str(exc):
            retry_hint["text"] = (
                "\n\n[NOTE] Your previous reply was rejected by the API for invalid JSON syntax. "
                "If you call a tool, output ONE short, valid JSON object and put any file text in a "
                "<file_content> block instead of inside the JSON. Otherwise reply in plain text "
                "with no <tool_call>."
            )
            log.info("Retrying with a JSON-syntax hint added to the prompt")

    text, elapsed = _with_retries(_do, f"LLM ({len(full_input)} chars)", on_error=_on_error)
    if not text.strip():
        log.warning("LLM returned an EMPTY response (%.1fs)", elapsed)
    log.info("LLM call ok: %d chars in -> %d chars out (%.1fs) | %s",
             len(full_input), len(text), elapsed, clip(text, 200))
    log.debug("LLM response:\n%s", text)
    return text


def _ddg_search(query: str) -> str:
    """Fallback search (no API key, no Gemini quota). Needs: pip install ddgs"""
    try:
        from ddgs import DDGS
    except ImportError:
        msg = "Web search unavailable: Gemini quota exhausted and fallback not installed (pip install ddgs)."
        log.error(msg)
        return msg
    try:
        results = DDGS().text(query, max_results=5)
    except Exception as exc:  # noqa: BLE001
        if "No results" in str(exc):
            log.info("DuckDuckGo: no results for this query")
            return "No results found. Try a shorter or differently worded query."
        msg = f"Web search unavailable: {clip(exc, 150)}"
        log.error(msg)
        return msg
    if not results:
        return "No results."
    log.info("DuckDuckGo fallback ok: %d result(s)", len(results))
    text = "\n\n".join(f"{r.get('title', '')}\n{r.get('href', '')}\n{r.get('body', '')}" for r in results)
    return text[:MAX_SEARCH_CHARS]


def web_search(query: str) -> str:
    """Web search: Gemini Google-Search grounding first, DuckDuckGo as fallback."""
    global _search_blocked_until
    query = query.strip()
    if not query:
        return 'Web search error: empty query. Use {"tool": "web_search", "args": {"query": "..."}}.'
    log.info("Web search: %s", clip(query, 120))
    if time.time() < _search_blocked_until:
        return _ddg_search(query)

    def _do() -> str:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            ),
        )
        return response.text or "No results."

    try:
        text, elapsed = _with_retries(
            _do, "Web search (Gemini)", no_retry_on=("RESOURCE_EXHAUSTED", "PERMISSION_DENIED")
        )
    except Exception as exc:  # noqa: BLE001
        if "RESOURCE_EXHAUSTED" in str(exc):
            _search_blocked_until = time.time() + 600
            log.warning("Gemini search quota exhausted. Using DuckDuckGo for the next 10 minutes.")
        else:
            log.warning("Gemini search unavailable (%s). Trying DuckDuckGo fallback...", clip(exc, 100))
        return _ddg_search(query)
    log.info("Web search ok: %d chars (%.1fs)", len(text), elapsed)
    log.debug("Web search result:\n%s", text)
    return text[:MAX_SEARCH_CHARS]


def extract_json(text: str) -> Any:
    """Parse JSON from an LLM reply, tolerating ```json fences and extra prose."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for open_ch, close_ch in (("[", "]"), ("{", "}")):
        start, end = text.find(open_ch), text.rfind(close_ch)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"Could not parse JSON from LLM output:\n{text}")