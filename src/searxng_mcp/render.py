from __future__ import annotations

from collections.abc import Iterable, Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import math
import re
from typing import Any

from mcp.types import CallToolResult, TextContent

_WHITESPACE_RE = re.compile(r"\s+")
_TRACKING_PREFIXES = ("utm_",)
_TRACKING_KEYS = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "mkt_tok",
    "ref",
    "ref_src",
}


def clean_text(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text or "").strip()


def truncate_text(text: str, limit: int, suffix: str = "…") -> str:
    text = text or ""
    if limit <= 0 or len(text) <= limit:
        return text
    cut = max(0, limit - len(suffix))
    return text[:cut].rstrip() + suffix


def _scheme_and_netloc(url: str) -> tuple[str, str, str, str, str]:
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    if scheme in {"http", "https"}:
        if scheme == "http" and netloc.endswith(":80"):
            netloc = netloc[:-3]
        elif scheme == "https" and netloc.endswith(":443"):
            netloc = netloc[:-4]
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith(_TRACKING_PREFIXES) and key.lower() not in _TRACKING_KEYS
    ]
    query = urlencode(query_items, doseq=True)
    return scheme, netloc, path, query, ""


def normalize_url(url: str) -> str:
    try:
        return urlunsplit(_scheme_and_netloc(url))
    except Exception:
        return clean_text(url)


def ensure_http_url(url: str) -> str:
    value = clean_text(url)
    if not value:
        raise ValueError("url is required")
    parsed = urlsplit(value)
    if not parsed.scheme:
        value = f"https://{value.lstrip('/')}"
        parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("only http and https URLs are supported")
    return value


def domain_from_url(url: str) -> str:
    try:
        return urlsplit(url).netloc.lower()
    except Exception:
        return ""


def approximate_tokens(text: str) -> int:
    text = text or ""
    try:
        import tiktoken

        encoding = tiktoken.get_encoding("o200k_base")
        return len(encoding.encode(text))
    except Exception:
        return max(1, math.ceil(len(text) / 4)) if text else 0


def result_summary(item: dict[str, Any], rank: int | None = None) -> dict[str, Any]:
    url = clean_text(str(item.get("url") or ""))
    title = clean_text(str(item.get("title") or url or ""))
    snippet = clean_text(str(item.get("content") or ""))
    return {
        "rank": rank,
        "title": title,
        "url": url,
        "domain": domain_from_url(url),
        "snippet": truncate_text(snippet, 220),
        "engine": item.get("engine"),
        "category": item.get("category"),
        "score": item.get("score"),
        "published_date": item.get("publishedDate") or item.get("pubdate"),
    }


def result_summary_line(item: dict[str, Any], rank: int) -> str:
    title = item.get("title") or item.get("url") or ""
    url = item.get("url") or ""
    engine = item.get("engine")
    domain = domain_from_url(url)
    score = item.get("score")
    prefix = f"{rank}. " if rank else ""
    lines = [f"{prefix}[{title}]({url})"]
    details = []
    if domain:
        details.append(domain)
    if engine:
        details.append(str(engine))
    if score is not None:
        details.append(f"score={score}")
    if details:
        lines.append(f"   {' | '.join(details)}")
    snippet = clean_text(str(item.get("content") or ""))
    if snippet:
        lines.append(f"   {truncate_text(snippet, 240)}")
    return "\n".join(lines)


def result_bullets(results: Sequence[dict[str, Any]], start_rank: int = 1) -> str:
    return "\n".join(
        result_summary_line(item, start_rank + index)
        for index, item in enumerate(results)
    )


def list_as_text(values: Iterable[Any], limit: int = 8) -> str:
    cleaned = [clean_text(str(value)) for value in values if clean_text(str(value))]
    if not cleaned:
        return ""
    clipped = cleaned[:limit]
    return ", ".join(clipped) + (" …" if len(cleaned) > limit else "")


def text_content(text: str) -> list[TextContent]:
    return [TextContent(type="text", text=text)]


def make_result(
    text: str,
    *,
    structured: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
    is_error: bool = False,
) -> CallToolResult:
    return CallToolResult(
        content=text_content(text),
        structuredContent=structured,
        _meta=meta,
        isError=is_error,
    )

