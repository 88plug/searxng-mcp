from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from . import __version__

TRUE_VALUES = {"1", "true", "yes", "on", "y", "t"}


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return default if value is None or value == "" else value


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in TRUE_VALUES


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _env_csv(name: str) -> tuple[str, ...]:
    value = os.getenv(name)
    if value is None or value == "":
        return ()
    items: list[str] = []
    seen: set[str] = set()
    for part in value.split(","):
        item = part.strip().rstrip("/")
        if not item or item in seen:
            continue
        seen.add(item)
        items.append(item)
    return tuple(items)


@dataclass(slots=True)
class Settings:
    base_url: str
    fallback_base_urls: tuple[str, ...]
    transport: str
    host: str
    port: int
    search_timeout: float
    fetch_timeout: float
    search_concurrency: int
    fetch_concurrency: int
    search_cache_ttl: int
    fetch_cache_ttl: int
    cache_dir: Path
    cache_size_limit: int
    default_language: str
    default_categories: str
    default_safesearch: int
    default_max_results: int
    default_excerpt_chars: int
    search_connections: int
    search_keepalive: int
    fetch_connections: int
    fetch_keepalive: int
    fetch_verify_tls: bool
    render_timeout: float
    render_wait_ms: int
    render_concurrency: int
    render_headless: bool
    render_browser_path: str
    render_sandbox: bool
    render_block_resources: bool
    render_auto_fallback: bool
    render_auto_min_words: int
    render_auto_min_chars: int
    trust_env: bool
    user_agent: str

    @property
    def normalized_base_url(self) -> str:
        return self.base_url.rstrip("/")

    @property
    def normalized_fallback_base_urls(self) -> tuple[str, ...]:
        urls: list[str] = []
        seen = {self.normalized_base_url}
        for value in self.fallback_base_urls:
            normalized = value.rstrip("/")
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            urls.append(normalized)
        return tuple(urls)

    @property
    def mcp_user_agent(self) -> str:
        return self.user_agent or f"searxng-mcp/{__version__}"


def load_settings() -> Settings:
    base_url = _env(
        "SEARXNG_MCP_BASE_URL", _env("SEARXNG_BASE_URL", "http://127.0.0.1:8890")
    )
    fallback_base_urls = _env_csv("SEARXNG_MCP_FALLBACK_BASE_URLS")
    transport = _env("SEARXNG_MCP_TRANSPORT", "stdio").strip().lower()
    host = _env("SEARXNG_MCP_HOST", "127.0.0.1")
    port = _env_int("SEARXNG_MCP_PORT", 8811)
    search_timeout = _env_float("SEARXNG_MCP_SEARCH_TIMEOUT", 6.0)
    fetch_timeout = _env_float("SEARXNG_MCP_FETCH_TIMEOUT", 15.0)
    search_concurrency = _env_int("SEARXNG_MCP_SEARCH_CONCURRENCY", 6)
    fetch_concurrency = _env_int("SEARXNG_MCP_FETCH_CONCURRENCY", 3)
    search_cache_ttl = _env_int("SEARXNG_MCP_SEARCH_CACHE_TTL", 30)
    fetch_cache_ttl = _env_int("SEARXNG_MCP_FETCH_CACHE_TTL", 3600)
    cache_dir = Path(_env("SEARXNG_MCP_CACHE_DIR", "~/.cache/searxng-mcp")).expanduser()
    cache_size_limit = _env_int("SEARXNG_MCP_CACHE_SIZE_LIMIT", 256 * 1024 * 1024)
    default_language = _env("SEARXNG_MCP_DEFAULT_LANGUAGE", "en")
    default_categories = _env("SEARXNG_MCP_DEFAULT_CATEGORIES", "general")
    default_safesearch = _env_int("SEARXNG_MCP_DEFAULT_SAFESEARCH", 0)
    default_max_results = _env_int("SEARXNG_MCP_DEFAULT_MAX_RESULTS", 5)
    default_excerpt_chars = _env_int("SEARXNG_MCP_DEFAULT_EXCERPT_CHARS", 1800)
    search_connections = _env_int("SEARXNG_MCP_SEARCH_CONNECTIONS", 32)
    search_keepalive = _env_int("SEARXNG_MCP_SEARCH_KEEPALIVE", 16)
    fetch_connections = _env_int("SEARXNG_MCP_FETCH_CONNECTIONS", 16)
    fetch_keepalive = _env_int("SEARXNG_MCP_FETCH_KEEPALIVE", 8)
    fetch_verify_tls = _env_bool("SEARXNG_MCP_FETCH_VERIFY_TLS", True)
    render_timeout = _env_float("SEARXNG_MCP_RENDER_TIMEOUT", 18.0)
    render_wait_ms = _env_int("SEARXNG_MCP_RENDER_WAIT_MS", 1200)
    render_concurrency = _env_int("SEARXNG_MCP_RENDER_CONCURRENCY", 2)
    render_headless = _env_bool("SEARXNG_MCP_RENDER_HEADLESS", True)
    render_browser_path = _env("SEARXNG_MCP_RENDER_BROWSER_PATH", "")
    render_sandbox = _env_bool("SEARXNG_MCP_RENDER_SANDBOX", False)
    render_block_resources = _env_bool("SEARXNG_MCP_RENDER_BLOCK_RESOURCES", True)
    render_auto_fallback = _env_bool("SEARXNG_MCP_RENDER_AUTO_FALLBACK", True)
    render_auto_min_words = _env_int("SEARXNG_MCP_RENDER_AUTO_MIN_WORDS", 60)
    render_auto_min_chars = _env_int("SEARXNG_MCP_RENDER_AUTO_MIN_CHARS", 800)
    trust_env = _env_bool("SEARXNG_MCP_TRUST_ENV", False)
    user_agent = _env("SEARXNG_MCP_USER_AGENT", f"searxng-mcp/{__version__}")

    return Settings(
        base_url=base_url,
        fallback_base_urls=fallback_base_urls,
        transport=transport,
        host=host,
        port=port,
        search_timeout=search_timeout,
        fetch_timeout=fetch_timeout,
        search_concurrency=search_concurrency,
        fetch_concurrency=fetch_concurrency,
        search_cache_ttl=search_cache_ttl,
        fetch_cache_ttl=fetch_cache_ttl,
        cache_dir=cache_dir,
        cache_size_limit=cache_size_limit,
        default_language=default_language,
        default_categories=default_categories,
        default_safesearch=default_safesearch,
        default_max_results=default_max_results,
        default_excerpt_chars=default_excerpt_chars,
        search_connections=search_connections,
        search_keepalive=search_keepalive,
        fetch_connections=fetch_connections,
        fetch_keepalive=fetch_keepalive,
        fetch_verify_tls=fetch_verify_tls,
        render_timeout=render_timeout,
        render_wait_ms=render_wait_ms,
        render_concurrency=render_concurrency,
        render_headless=render_headless,
        render_browser_path=render_browser_path,
        render_sandbox=render_sandbox,
        render_block_resources=render_block_resources,
        render_auto_fallback=render_auto_fallback,
        render_auto_min_words=render_auto_min_words,
        render_auto_min_chars=render_auto_min_chars,
        trust_env=trust_env,
        user_agent=user_agent,
    )
