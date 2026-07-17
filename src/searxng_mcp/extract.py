from __future__ import annotations

from dataclasses import dataclass, field
from email.message import Message
from io import BytesIO
from typing import Any
from urllib.parse import urljoin, urlsplit
import re

import httpx
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text as extract_pdf_text

from .render import clean_text, ensure_http_url, normalize_url, truncate_text


def _rel_contains_canonical(value: str | None) -> bool:
    return bool(value and "canonical" in value)


_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_BLOCK_TAGS = {"p", "li", "blockquote", "pre", "td", "th"}
_BOILERPLATE_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "iframe",
    "footer",
    "header",
    "nav",
    "aside",
}
_CONTENT_SELECTORS = [
    "article",
    "main",
    "[role=main]",
    "#content",
    "#main",
    ".content",
    ".article",
    ".post",
    ".entry-content",
]
_CONTENT_TYPE_RE = re.compile(r"^[^;]+")
_RENDER_HINT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("next_data", re.compile(r"__NEXT_DATA__", re.IGNORECASE)),
    ("nuxt", re.compile(r"__NUXT__", re.IGNORECASE)),
    ("react_root", re.compile(r"data-reactroot", re.IGNORECASE)),
    ("initial_state", re.compile(r"window\.__INITIAL_STATE__", re.IGNORECASE)),
    ("hydration", re.compile(r"hydrat(?:e|ion)", re.IGNORECASE)),
    ("app_root", re.compile(r'id=["\'](?:root|app)["\']', re.IGNORECASE)),
    (
        "json_script",
        re.compile(r'<script[^>]+type=["\']application/json["\']', re.IGNORECASE),
    ),
    (
        "js_required",
        re.compile(
            r"(enable javascript|javascript required|please (?:turn on|enable) javascript)",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(slots=True)
class ExtractedDocument:
    url: str
    final_url: str
    content_type: str
    title: str | None
    description: str | None
    author: str | None
    text: str
    excerpt: str
    headings: list[str] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    word_count: int = 0
    char_count: int = 0
    truncated: bool = False
    rendered: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_summary(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "final_url": self.final_url,
            "content_type": self.content_type,
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "excerpt": self.excerpt,
            "headings": self.headings,
            "links": self.links,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "truncated": self.truncated,
            "rendered": self.rendered,
        }


def _content_type(response: httpx.Response) -> str:
    header = response.headers.get("content-type", "")
    match = _CONTENT_TYPE_RE.match(header)
    return (match.group(0) if match else header).strip().lower()


def _meta_value(soup: BeautifulSoup, *names: str) -> str | None:
    for name in names:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return clean_text(str(tag.get("content")))
        tag = soup.find("meta", attrs={"property": name})
        if tag and tag.get("content"):
            return clean_text(str(tag.get("content")))
    return None


def _candidate_container(soup: BeautifulSoup):
    candidates = []
    for selector in _CONTENT_SELECTORS:
        candidates.extend(soup.select(selector))
    if soup.body is not None:
        candidates.append(soup.body)
    if not candidates:
        return soup

    def score(node) -> int:
        try:
            return len(clean_text(node.get_text(" ", strip=True)))
        except Exception:
            return 0

    return max(candidates, key=score)


def _collect_blocks(
    container, base_url: str, max_links: int
) -> tuple[list[str], list[str], list[dict[str, str]]]:
    headings: list[str] = []
    blocks: list[str] = []
    links: list[dict[str, str]] = []
    seen_links: set[str] = set()

    for tag in container.find_all(True):
        name = (tag.name or "").lower()
        if name in _BOILERPLATE_TAGS:
            tag.decompose()

    for node in container.find_all(list(_HEADING_TAGS | _BLOCK_TAGS)):
        name = (node.name or "").lower()
        if name in _HEADING_TAGS:
            text = clean_text(node.get_text(" ", strip=True))
            if text:
                headings.append(text)
                blocks.append(f"{'#' * int(name[1])} {text}")
        elif name == "pre":
            text = node.get_text("\n", strip=True)
            text = clean_text(text)
            if text:
                blocks.append(f"```text\n{text}\n```")
        else:
            text = clean_text(node.get_text(" ", strip=True))
            if text:
                blocks.append(text)

    for anchor in container.find_all("a", href=True):
        if len(links) >= max_links:
            break
        href = clean_text(str(anchor.get("href") or ""))
        if not href:
            continue
        absolute = urljoin(base_url, href)
        parsed = urlsplit(absolute)
        if parsed.scheme not in {"http", "https"}:
            continue
        normalized = normalize_url(absolute)
        if normalized in seen_links:
            continue
        seen_links.add(normalized)
        text = clean_text(anchor.get_text(" ", strip=True)) or parsed.netloc
        links.append({"text": truncate_text(text, 80), "url": absolute})

    return headings, blocks, links


def _extract_text_blocks(
    soup: BeautifulSoup, base_url: str, max_links: int
) -> tuple[list[str], list[str], list[dict[str, str]]]:
    container = _candidate_container(soup)
    if container is None:
        return [], [], []
    return _collect_blocks(container, base_url, max_links)


def _render_profile(html: str, text: str) -> dict[str, Any]:
    hints: list[str] = []
    script_count = len(re.findall(r"<script\b", html, flags=re.IGNORECASE))
    html_char_count = len(html)
    text_char_count = len(text)
    text_density = (
        round((text_char_count / html_char_count), 4) if html_char_count else 0.0
    )

    for label, pattern in _RENDER_HINT_PATTERNS:
        if pattern.search(html):
            hints.append(label)

    if script_count >= 3 and text_char_count <= 800:
        hints.append("script_heavy")
    if html_char_count and text_density <= 0.06 and script_count >= 2:
        hints.append("low_text_density")

    seen: set[str] = set()
    deduped: list[str] = []
    for hint in hints:
        if hint in seen:
            continue
        seen.add(hint)
        deduped.append(hint)

    return {
        "html_char_count": html_char_count,
        "text_char_count": text_char_count,
        "script_count": script_count,
        "text_density": text_density,
        "hints": deduped,
    }


def _content_disposition_filename(header: str | None) -> str | None:
    if not header:
        return None
    message = Message()
    message["content-disposition"] = header
    filename = clean_text(str(message.get_filename() or ""))
    if not filename:
        return None
    filename = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    return filename or None


def _extract_from_html(
    *,
    html: str,
    url: str,
    final_url: str,
    content_type: str,
    max_excerpt_chars: int,
    max_links: int,
    rendered: bool,
) -> ExtractedDocument:
    base_url = final_url or url
    title: str | None = None
    description: str | None = None
    author: str | None = None
    headings: list[str] = []
    links: list[dict[str, str]] = []
    metadata: dict[str, Any] = {}

    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.find("title")
    if title_tag:
        title = clean_text(title_tag.get_text(" ", strip=True)) or None
    description = _meta_value(
        soup, "description", "og:description", "twitter:description"
    )
    author = _meta_value(soup, "author", "article:author", "parsely-author")
    canonical = soup.find("link", attrs={"rel": _rel_contains_canonical})
    if canonical and canonical.get("href"):
        metadata["canonical_url"] = urljoin(base_url, str(canonical.get("href")))
    headings, blocks, links = _extract_text_blocks(soup, base_url, max_links)
    text = "\n\n".join(blocks)

    if not title:
        path = urlsplit(final_url).path.rstrip("/").split("/")[-1]
        title = path or urlsplit(final_url).netloc or urlsplit(url).netloc

    full_text = clean_text(text or "")
    char_count = len(full_text)
    excerpt = truncate_text(full_text, max_excerpt_chars)
    word_count = len(re.findall(r"\S+", full_text))
    truncated = char_count > max_excerpt_chars if max_excerpt_chars > 0 else False
    metadata["render_profile"] = _render_profile(html, full_text)

    return ExtractedDocument(
        url=url,
        final_url=final_url,
        content_type=content_type or "application/octet-stream",
        title=title,
        description=description,
        author=author,
        text=full_text,
        excerpt=excerpt,
        headings=headings,
        links=links,
        word_count=word_count,
        char_count=char_count,
        truncated=truncated,
        rendered=rendered,
        metadata=metadata,
    )


def extract_from_html(
    html: str,
    *,
    url: str,
    final_url: str | None = None,
    content_type: str = "text/html; charset=utf-8",
    max_excerpt_chars: int,
    max_links: int = 8,
    rendered: bool = False,
) -> ExtractedDocument:
    return _extract_from_html(
        html=html,
        url=url,
        final_url=final_url or url,
        content_type=content_type,
        max_excerpt_chars=max_excerpt_chars,
        max_links=max_links,
        rendered=rendered,
    )


def extract_from_response(
    response: httpx.Response,
    *,
    max_excerpt_chars: int,
    max_links: int = 8,
) -> ExtractedDocument:
    url = str(response.request.url)
    final_url = str(response.url)
    content_type = _content_type(response)
    metadata: dict[str, Any] = {}

    if "pdf" in content_type or final_url.lower().endswith(".pdf"):
        try:
            text = extract_pdf_text(BytesIO(response.content))
        except Exception as exc:  # noqa: BLE001
            metadata["pdf_error"] = repr(exc)
            text = ""
        text = clean_text(text)
        title = _content_disposition_filename(
            response.headers.get("content-disposition")
        )
        full_text = text or ""
        char_count = len(full_text)
        excerpt = truncate_text(full_text, max_excerpt_chars)
        word_count = len(re.findall(r"\S+", full_text))
        truncated = char_count > max_excerpt_chars if max_excerpt_chars > 0 else False
        return ExtractedDocument(
            url=url,
            final_url=final_url,
            content_type=content_type or "application/octet-stream",
            title=title or None,
            description=None,
            author=None,
            text=full_text,
            excerpt=excerpt,
            headings=[],
            links=[],
            word_count=word_count,
            char_count=char_count,
            truncated=truncated,
            rendered=False,
            metadata=metadata,
        )
    elif (
        content_type.startswith("text/")
        or "html" in content_type
        or "xml" in content_type
        or content_type == ""
    ):
        return _extract_from_html(
            html=response.text,
            url=url,
            final_url=final_url,
            content_type=content_type or "text/html; charset=utf-8",
            max_excerpt_chars=max_excerpt_chars,
            max_links=max_links,
            rendered=False,
        )
    else:
        try:
            text = response.text
        except Exception:
            text = response.content.decode("utf-8", errors="replace")
        text = clean_text(text)
        full_text = text or ""
        char_count = len(full_text)
        excerpt = truncate_text(full_text, max_excerpt_chars)
        word_count = len(re.findall(r"\S+", full_text))
        truncated = char_count > max_excerpt_chars if max_excerpt_chars > 0 else False
        return ExtractedDocument(
            url=url,
            final_url=final_url,
            content_type=content_type or "application/octet-stream",
            title=None,
            description=None,
            author=None,
            text=full_text,
            excerpt=excerpt,
            headings=[],
            links=[],
            word_count=word_count,
            char_count=char_count,
            truncated=truncated,
            rendered=False,
            metadata=metadata,
        )


def normalize_requested_url(url: str) -> str:
    value = ensure_http_url(url)
    return value
