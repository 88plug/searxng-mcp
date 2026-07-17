from __future__ import annotations

import asyncio
from pathlib import Path

import httpx

from searxng_mcp.client import SearxngClient
from searxng_mcp.settings import Settings


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        base_url="http://primary.local",
        fallback_base_urls=("http://fallback.local",),
        transport="stdio",
        host="127.0.0.1",
        port=8811,
        search_timeout=5.0,
        fetch_timeout=5.0,
        search_concurrency=4,
        fetch_concurrency=2,
        search_cache_ttl=60,
        fetch_cache_ttl=60,
        cache_dir=tmp_path / "cache",
        cache_size_limit=32 * 1024 * 1024,
        default_language="en",
        default_categories="general",
        default_safesearch=0,
        default_max_results=5,
        default_excerpt_chars=300,
        search_connections=8,
        search_keepalive=4,
        fetch_connections=4,
        fetch_keepalive=2,
        fetch_verify_tls=True,
        render_timeout=10.0,
        render_wait_ms=1000,
        render_concurrency=2,
        render_headless=True,
        render_browser_path="",
        render_sandbox=False,
        render_block_resources=True,
        render_auto_fallback=True,
        render_auto_min_words=60,
        render_auto_min_chars=800,
        trust_env=False,
        user_agent="searxng-mcp-test",
    )


def test_search_falls_back_to_secondary_backend(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "primary.local":
            return httpx.Response(503, request=request, text="primary down")
        if request.url.host == "fallback.local" and request.url.path == "/search":
            return httpx.Response(
                200,
                request=request,
                json={
                    "query": "test",
                    "number_of_results": 1,
                    "results": [
                        {
                            "url": "https://example.com",
                            "title": "Fallback result",
                            "content": "from fallback",
                            "engine": "mock",
                            "score": 1.0,
                        }
                    ],
                    "answers": [],
                    "corrections": [],
                    "infoboxes": [],
                    "suggestions": [],
                    "unresponsive_engines": [],
                },
            )
        if request.url.host == "fallback.local" and request.url.path == "/":
            return httpx.Response(200, request=request, text="ok")
        return httpx.Response(404, request=request, text="not found")

    client = SearxngClient(
        make_settings(tmp_path), transport=httpx.MockTransport(handler)
    )

    async def run() -> None:
        result = await client.search(
            {
                "q": "test",
                "format": "json",
                "categories": "general",
                "language": "en",
                "pageno": 1,
                "safesearch": 0,
            }
        )
        ping = await client.ping()
        assert result.backend_url == "http://fallback.local"
        assert result.payload["results"][0]["title"] == "Fallback result"
        assert ping.backend_url == "http://fallback.local"

    try:
        asyncio.run(run())
    finally:
        asyncio.run(client.close())


def test_search_falls_back_when_primary_unreachable(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "primary.local":
            raise httpx.ConnectError("All connection attempts failed", request=request)
        if request.url.host == "fallback.local" and request.url.path == "/search":
            return httpx.Response(
                200,
                request=request,
                json={
                    "query": "test",
                    "number_of_results": 1,
                    "results": [
                        {
                            "url": "https://example.com",
                            "title": "Fallback result",
                            "content": "from fallback",
                            "engine": "mock",
                            "score": 1.0,
                        }
                    ],
                    "answers": [],
                    "corrections": [],
                    "infoboxes": [],
                    "suggestions": [],
                    "unresponsive_engines": [],
                },
            )
        if request.url.host == "fallback.local" and request.url.path == "/":
            return httpx.Response(200, request=request, text="ok")
        return httpx.Response(404, request=request, text="not found")

    client = SearxngClient(
        make_settings(tmp_path), transport=httpx.MockTransport(handler)
    )

    async def run() -> None:
        result = await client.search(
            {
                "q": "test",
                "format": "json",
                "categories": "general",
                "language": "en",
                "pageno": 1,
                "safesearch": 0,
            }
        )
        ping = await client.ping()
        assert result.backend_url == "http://fallback.local"
        assert ping.backend_url == "http://fallback.local"

    try:
        asyncio.run(run())
    finally:
        asyncio.run(client.close())
