from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pytest
from mcp.types import CallToolResult

from searxng_mcp.browser import RenderedResponse
from searxng_mcp.client import BackendResponse, FetchResponse
from searxng_mcp.render import content_text, make_result
from searxng_mcp.service import SearxngMCPService
from searxng_mcp.settings import Settings


def sc(result: CallToolResult) -> dict[str, Any]:
    data = result.structuredContent
    assert data is not None
    return data


def meta_of(result: CallToolResult) -> dict[str, Any]:
    data = result.meta
    assert data is not None
    return data


def text_of(result: CallToolResult) -> str:
    return content_text(result)


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        base_url="http://searx.local",
        fallback_base_urls=(),
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


def make_http_response(
    url: str, body: str, content_type: str = "text/html; charset=utf-8"
) -> httpx.Response:
    return httpx.Response(
        200,
        content=body.encode("utf-8"),
        headers={"content-type": content_type},
        request=httpx.Request("GET", url),
    )


@dataclass
class FakeSearchClient:
    payloads: dict[str, dict]
    calls: list[dict]

    def __init__(self, payloads: dict[str, dict]) -> None:
        self.payloads = payloads
        self.calls = []

    async def search(self, params: dict) -> BackendResponse:
        self.calls.append(params)
        payload = self.payloads[params["q"]]
        return BackendResponse(
            backend_url="http://searx.local",
            url=f"http://searx.local/search?q={params['q']}",
            status_code=200,
            elapsed_ms=12.5,
            payload=payload,
        )

    async def ping(self) -> BackendResponse:
        return BackendResponse(
            backend_url="http://searx.local",
            url="http://searx.local/",
            status_code=200,
            elapsed_ms=1.0,
            payload={},
        )

    async def close(self) -> None:
        return None


@dataclass
class FakeFetchClient:
    responses: dict[str, httpx.Response]
    calls: list[str]

    def __init__(self, responses: dict[str, httpx.Response]) -> None:
        self.responses = responses
        self.calls = []

    async def get(self, url: str) -> FetchResponse:
        self.calls.append(url)
        response = self.responses[url]
        return FetchResponse(
            url=url, status_code=response.status_code, elapsed_ms=5.0, response=response
        )

    async def close(self) -> None:
        return None


@dataclass
class FakeRenderClient:
    responses: dict[str, tuple[str, str]]
    calls: list[tuple[str, int | None]]

    def __init__(self, responses: dict[str, tuple[str, str]]) -> None:
        self.responses = responses
        self.calls = []

    def status(self) -> dict[str, object]:
        return {
            "playwright_installed": True,
            "browser_path_configured": True,
            "browser_executable": "/usr/bin/chromium",
            "headless": True,
            "block_resources": True,
            "concurrency": 2,
            "timeout_s": 10.0,
            "wait_ms": 1000,
        }

    async def get(self, url: str, *, wait_ms: int | None = None) -> RenderedResponse:
        self.calls.append((url, wait_ms))
        html, final_url = self.responses[url]
        return RenderedResponse(
            url=url,
            final_url=final_url,
            status_code=200,
            elapsed_ms=7.5,
            html=html,
            content_type="text/html; charset=utf-8",
            title="Rendered Example",
        )

    async def close(self) -> None:
        return None


@dataclass
class AsyncStubContext:
    info_calls: list[tuple[str, dict]]
    progress_calls: list[tuple[float, float | None, str | None]]

    def __init__(self) -> None:
        self.info_calls = []
        self.progress_calls = []

    async def info(self, message: str, **extra: object) -> None:
        await asyncio.sleep(0)
        self.info_calls.append((message, dict(extra)))

    async def report_progress(
        self, progress: float, total: float | None = None, message: str | None = None
    ) -> None:
        await asyncio.sleep(0)
        self.progress_calls.append((progress, total, message))


@dataclass
class FastMCPLikeContext:
    log_calls: list[tuple[str, str]]
    progress_calls: list[tuple[float, float | None, str | None]]

    def __init__(self) -> None:
        self.log_calls = []
        self.progress_calls = []

    async def log(
        self, level: str, message: str, *, logger_name: str | None = None
    ) -> None:
        await asyncio.sleep(0)
        self.log_calls.append((level, message))

    async def info(self, message: str, **extra: object) -> None:
        logger_name = extra.get("logger_name")
        await self.log(
            "info",
            message,
            logger_name=str(logger_name) if logger_name is not None else None,
        )

    async def report_progress(
        self, progress: float, total: float | None = None, message: str | None = None
    ) -> None:
        await asyncio.sleep(0)
        self.progress_calls.append((progress, total, message))


@dataclass
class FailingFetchClient:
    error: Exception

    async def get(self, url: str) -> FetchResponse:
        raise self.error

    async def close(self) -> None:
        return None


def payload_for(*results: dict) -> dict:
    return {
        "query": "placeholder",
        "number_of_results": len(results),
        "results": list(results),
        "answers": [],
        "corrections": [],
        "infoboxes": [],
        "suggestions": [],
        "unresponsive_engines": [],
    }


def test_search_caches_and_returns_compact_summary(tmp_path: Path) -> None:
    search_client = FakeSearchClient(
        {
            "python asyncio gather": payload_for(
                {
                    "url": "https://docs.python.org/3/library/asyncio-task.html",
                    "title": "Coroutines and tasks",
                    "content": "TaskGroup provides stronger safety guarantees than gather.",
                    "engine": "brave",
                    "score": 4.0,
                },
                {
                    "url": "https://stackoverflow.com/questions/42231161/asyncio-gather-vs-asyncio-wait-vs-asyncio-taskgroup",
                    "title": "asyncio gather vs asyncio wait",
                    "content": "Many cases compare gather and wait.",
                    "engine": "bing",
                    "score": 3.0,
                },
            )
        }
    )
    service = SearxngMCPService(
        make_settings(tmp_path),
        search_client=search_client,
        fetch_client=FakeFetchClient({}),
    )

    async def run() -> None:
        first = await service.search(query="python asyncio gather", max_results=1)
        second = await service.search(query="python asyncio gather", max_results=1)

        assert not first.isError
        assert sc(first)["cache_hit"] is False
        assert sc(first)["backend_url"] == "http://searx.local"
        assert sc(second)["cache_hit"] is True
        assert "Results: 2 total, 1 shown" in text_of(first)
        assert sc(first)["top_results"][0]["title"] == "Coroutines and tasks"
        assert len(search_client.calls) == 1

    import asyncio

    asyncio.run(run())


def test_search_tolerates_fastmcp_context_log_signature_bug(tmp_path: Path) -> None:
    search_client = FakeSearchClient(
        {
            "python asyncio gather": payload_for(
                {
                    "url": "https://docs.python.org/3/library/asyncio-task.html",
                    "title": "Coroutines and tasks",
                    "content": "TaskGroup provides stronger safety guarantees than gather.",
                    "engine": "brave",
                    "score": 4.0,
                }
            )
        }
    )
    service = SearxngMCPService(
        make_settings(tmp_path),
        search_client=search_client,
        fetch_client=FakeFetchClient({}),
    )
    ctx = FastMCPLikeContext()

    async def run() -> None:
        result = await service.search(
            query="python asyncio gather", max_results=1, ctx=ctx
        )
        assert not result.isError
        assert ctx.log_calls == [("info", "search completed")]

    asyncio.run(run())


def test_search_many_dedupes_and_merges(tmp_path: Path) -> None:
    search_client = FakeSearchClient(
        {
            "python asyncio gather": payload_for(
                {
                    "url": "https://docs.python.org/3/library/asyncio-task.html",
                    "title": "Coroutines and tasks",
                    "content": "TaskGroup provides stronger safety guarantees than gather.",
                    "engine": "brave",
                    "score": 4.0,
                },
                {
                    "url": "https://example.com/a",
                    "title": "A",
                    "content": "First",
                    "engine": "bing",
                    "score": 1.0,
                },
            ),
            "python taskgroup": payload_for(
                {
                    "url": "https://docs.python.org/3/library/asyncio-task.html?utm_source=test",
                    "title": "Coroutines and tasks",
                    "content": "TaskGroup provides stronger safety guarantees than gather.",
                    "engine": "google",
                    "score": 5.0,
                },
                {
                    "url": "https://example.com/b",
                    "title": "B",
                    "content": "Second",
                    "engine": "bing",
                    "score": 2.0,
                },
            ),
        }
    )
    service = SearxngMCPService(
        make_settings(tmp_path),
        search_client=search_client,
        fetch_client=FakeFetchClient({}),
    )

    async def run() -> None:
        result = await service.search_many(
            queries=["python asyncio gather", "python taskgroup"], max_results=10
        )
        assert not result.isError
        assert "Queries: 2" in text_of(result)
        assert sc(result)["unique_results"] == 3
        assert (
            sc(result)["merged_results"][0]["canonical_url"]
            == "https://docs.python.org/3/library/asyncio-task.html"
        )

    import asyncio

    asyncio.run(run())


def test_async_context_callbacks_are_awaited(tmp_path: Path) -> None:
    search_client = FakeSearchClient(
        {
            "python asyncio gather": payload_for(
                {
                    "url": "https://example.org/a",
                    "title": "A",
                    "content": "First",
                    "engine": "brave",
                    "score": 4.0,
                }
            ),
            "python taskgroup": payload_for(
                {
                    "url": "https://example.org/b",
                    "title": "B",
                    "content": "Second",
                    "engine": "bing",
                    "score": 3.0,
                }
            ),
        }
    )
    service = SearxngMCPService(
        make_settings(tmp_path),
        search_client=search_client,
        fetch_client=FakeFetchClient({}),
    )
    ctx = AsyncStubContext()

    async def run() -> None:
        result = await service.search_many(
            queries=["python asyncio gather", "python taskgroup"],
            max_results=5,
            ctx=ctx,
        )
        assert not result.isError
        assert len(ctx.progress_calls) == 2
        assert len(ctx.info_calls) == 1
        assert ctx.info_calls[0][0] == "search_many completed"
        assert ctx.progress_calls[0][2] == "searching python asyncio gather"
        assert ctx.progress_calls[1][2] == "searching python taskgroup"

    asyncio.run(run())


def test_research_merges_search_and_batch_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    search_client = FakeSearchClient(
        {
            "python asyncio gather": payload_for(
                {
                    "url": "https://docs.python.org/3/library/asyncio-task.html",
                    "title": "Coroutines and tasks",
                    "content": "TaskGroup provides stronger safety guarantees than gather.",
                    "engine": "brave",
                    "score": 4.0,
                },
                {
                    "url": "https://example.com/a",
                    "title": "A",
                    "content": "First",
                    "engine": "bing",
                    "score": 1.0,
                },
            ),
            "python taskgroup": payload_for(
                {
                    "url": "https://docs.python.org/3/library/asyncio-task.html?utm_source=test",
                    "title": "Coroutines and tasks",
                    "content": "TaskGroup provides stronger safety guarantees than gather.",
                    "engine": "google",
                    "score": 5.0,
                },
                {
                    "url": "https://example.com/b",
                    "title": "B",
                    "content": "Second",
                    "engine": "bing",
                    "score": 2.0,
                },
            ),
        }
    )
    fetch_client = FakeFetchClient(
        {
            "https://docs.python.org/3/library/asyncio-task.html": make_http_response(
                "https://docs.python.org/3/library/asyncio-task.html",
                """
                <html>
                  <head><title>Coroutines and tasks</title></head>
                  <body><main><p>TaskGroup body.</p></main></body>
                </html>
                """,
            ),
            "https://example.com/b": make_http_response(
                "https://example.com/b",
                """
                <html>
                  <head><title>B</title></head>
                  <body><main><p>Second body.</p></main></body>
                </html>
                """,
            ),
        }
    )
    service = SearxngMCPService(
        make_settings(tmp_path), search_client=search_client, fetch_client=fetch_client
    )
    fetch_many_calls: list[list[str]] = []

    async def fake_fetch_many(*, urls: list[str], **_: object):
        fetch_many_calls.append(list(urls))
        documents = [
            {
                "requested_url": url,
                "cache_hit": False,
                "elapsed_ms": 1.0,
                "render_mode": "off",
                "document": {
                    "url": url,
                    "final_url": url,
                    "content_type": "text/html",
                    "title": url.rsplit("/", 1)[-1],
                    "description": None,
                    "author": None,
                    "excerpt": "Stub excerpt",
                    "headings": [],
                    "links": [],
                    "word_count": 2,
                    "char_count": 10,
                    "truncated": False,
                    "rendered": False,
                },
            }
            for url in urls
        ]
        structured = {
            "urls": urls,
            "successful_urls": len(urls),
            "url_errors": [],
            "elapsed_ms": 1.0,
            "cache_hits": 0,
            "documents": documents,
            "rendered": False,
            "render_mode": "off",
            "render_wait_ms": None,
        }
        return make_result("fetch_many stub", structured=structured, meta=structured)

    monkeypatch.setattr(service, "fetch_many", fake_fetch_many)

    async def run() -> None:
        result = await service.research(
            queries=["python asyncio gather", "python taskgroup"],
            max_results=5,
            fetch_limit=2,
        )
        assert not result.isError
        assert "Merged results:" in text_of(result)
        assert "Fetched sources:" in text_of(result)
        assert sc(result)["unique_results"] == 3
        assert len(sc(result)["fetched_pages"]) == 2
        assert len(search_client.calls) == 2
        assert fetch_many_calls == [
            [
                "https://docs.python.org/3/library/asyncio-task.html?utm_source=test",
                "https://example.com/b",
            ]
        ]

    import asyncio

    asyncio.run(run())


def test_fetch_url_extracts_and_caches(tmp_path: Path) -> None:
    html = """
    <html>
      <head>
        <title>Example Article</title>
        <meta name="description" content="Short description.">
      </head>
      <body>
        <main>
          <h1>Heading One</h1>
          <p>First paragraph.</p>
          <a href="/docs">Docs link</a>
          <a href="/guide">Guide link</a>
        </main>
      </body>
    </html>
    """
    fetch_client = FakeFetchClient(
        {
            "https://example.org/article": make_http_response(
                "https://example.org/article", html
            ),
        }
    )
    service = SearxngMCPService(
        make_settings(tmp_path),
        search_client=FakeSearchClient({}),
        fetch_client=fetch_client,
    )

    async def run() -> None:
        first = await service.fetch_url(
            url="https://example.org/article", max_excerpt_chars=20, max_links=1
        )
        second = await service.fetch_url(
            url="https://example.org/article", max_excerpt_chars=120, max_links=2
        )
        assert not first.isError
        assert sc(first)["cache_hit"] is False
        assert sc(second)["cache_hit"] is True
        assert sc(first)["title"] == "Example Article"
        assert "Heading One" in text_of(first)
        assert len(sc(second)["excerpt"]) > len(sc(first)["excerpt"])
        assert len(sc(first)["links"]) == 1
        assert len(sc(second)["links"]) == 2
        assert len(fetch_client.calls) == 1

    import asyncio

    asyncio.run(run())


def test_fetch_url_rendered_extracts_and_caches(tmp_path: Path) -> None:
    render_client = FakeRenderClient(
        {
            "https://example.org/rendered": (
                """
                <html>
                  <head>
                    <title>Rendered Example</title>
                    <meta name="description" content="Rendered description.">
                  </head>
                      <body>
                        <main>
                          <h1>Rendered Heading</h1>
                          <p>Rendered body text with more detail about JavaScript hydration, dynamic rendering, and extracted content.</p>
                          <a href="/docs">Docs</a>
                          <a href="/guide">Guide</a>
                        </main>
                      </body>
                </html>
                """,
                "https://example.org/rendered",
            )
        }
    )
    service = SearxngMCPService(
        make_settings(tmp_path),
        search_client=FakeSearchClient({}),
        fetch_client=FakeFetchClient({}),
        render_client=render_client,
    )

    async def run() -> None:
        first = await service.fetch_url(
            url="https://example.org/rendered",
            rendered=True,
            render_wait_ms=250,
            max_excerpt_chars=40,
            max_links=1,
        )
        second = await service.fetch_url(
            url="https://example.org/rendered",
            rendered=True,
            render_wait_ms=250,
            max_excerpt_chars=120,
            max_links=2,
        )
        assert not first.isError
        assert sc(first)["rendered"] is True
        assert sc(first)["render_mode"] == "forced"
        assert sc(first)["cache_hit"] is False
        assert sc(second)["cache_hit"] is True
        assert sc(first)["title"] == "Rendered Example"
        assert "Rendered Heading" in text_of(first)
        assert "Rendered: forced" in text_of(first)
        assert len(sc(second)["excerpt"]) > len(sc(first)["excerpt"])
        assert len(sc(first)["links"]) == 1
        assert len(sc(second)["links"]) == 2
        assert render_client.calls == [("https://example.org/rendered", 250)]

    asyncio.run(run())


def test_fetch_url_plain_fetch_failure_falls_back_to_render(tmp_path: Path) -> None:
    render_client = FakeRenderClient(
        {
            "https://example.org/fallback": (
                """
                <html>
                  <head><title>Fallback Example</title></head>
                  <body><main><p>Rendered fallback content.</p></main></body>
                </html>
                """,
                "https://example.org/fallback",
            )
        }
    )
    service = SearxngMCPService(
        make_settings(tmp_path),
        search_client=FakeSearchClient({}),
        fetch_client=FailingFetchClient(
            httpx.ConnectError(
                "boom", request=httpx.Request("GET", "https://example.org/fallback")
            )
        ),
        render_client=render_client,
    )

    async def run() -> None:
        result = await service.fetch_url(url="https://example.org/fallback")
        assert not result.isError
        assert sc(result)["rendered"] is True
        assert sc(result)["render_mode"] == "auto"
        assert meta_of(result)["render_mode"] == "auto"
        assert meta_of(result)["document"]["rendered"] is True
        assert "Rendered: auto" in text_of(result)
        assert (
            render_client.calls
            and render_client.calls[0][0] == "https://example.org/fallback"
        )

    asyncio.run(run())


def test_fetch_many_dedupes_and_reuses_cache(tmp_path: Path) -> None:
    html_a = """
    <html>
      <head><title>Alpha</title></head>
      <body><main><p>Alpha body.</p></main></body>
    </html>
    """
    html_b = """
    <html>
      <head><title>Beta</title></head>
      <body><main><p>Beta body.</p></main></body>
    </html>
    """
    fetch_client = FakeFetchClient(
        {
            "https://example.org/a": make_http_response(
                "https://example.org/a", html_a
            ),
            "https://example.org/b": make_http_response(
                "https://example.org/b", html_b
            ),
        }
    )
    service = SearxngMCPService(
        make_settings(tmp_path),
        search_client=FakeSearchClient({}),
        fetch_client=fetch_client,
    )

    async def run() -> None:
        first = await service.fetch_many(
            urls=[
                "https://example.org/a",
                "https://example.org/a",
                "https://example.org/b",
            ],
            max_excerpt_chars=40,
        )
        second = await service.fetch_many(
            urls=["https://example.org/a", "https://example.org/b"],
            max_excerpt_chars=80,
        )
        assert not first.isError
        assert sc(first)["successful_urls"] == 2
        assert sc(first)["cache_hits"] == 0
        assert sc(second)["cache_hits"] == 2
        assert len(fetch_client.calls) == 2
        assert "URLs: 2" in text_of(first)
        assert "Fetched pages:" in text_of(first)

    asyncio.run(run())


def test_fetch_many_auto_render_keeps_render_state_in_sync(tmp_path: Path) -> None:
    search_client = FakeSearchClient({})
    fetch_client = FakeFetchClient(
        {
            "https://example.org/app": make_http_response(
                "https://example.org/app",
                """
                <html>
                  <head>
                    <title>Rendered App</title>
                    <script id="__NEXT_DATA__" type="application/json">{}</script>
                  </head>
                  <body>
                    <main>
                      <div id="root"></div>
                      <p>Loading application shell.</p>
                    </main>
                  </body>
                </html>
                """,
            )
        }
    )
    render_client = FakeRenderClient(
        {
            "https://example.org/app": (
                """
                <html>
                  <head><title>Rendered App</title></head>
                  <body><main><p>Rendered application body.</p></main></body>
                </html>
                """,
                "https://example.org/app",
            )
        }
    )
    service = SearxngMCPService(
        make_settings(tmp_path),
        search_client=search_client,
        fetch_client=fetch_client,
        render_client=render_client,
    )

    async def run() -> None:
        result = await service.fetch_many(
            urls=["https://example.org/app"], max_excerpt_chars=80, max_links=1
        )
        assert not result.isError
        assert sc(result)["rendered"] is True
        assert sc(result)["render_mode"] == "auto"
        assert meta_of(result)["rendered"] is True
        assert meta_of(result)["render_mode"] == "auto"
        assert sc(result)["documents"][0]["document"]["rendered"] is True
        assert sc(result)["documents"][0]["document"]["render_mode"] == "auto"
        assert meta_of(result)["documents"][0]["render_mode"] == "auto"
        assert (
            render_client.calls
            and render_client.calls[0][0] == "https://example.org/app"
        )

    asyncio.run(run())


def test_search_and_fetch_rendered_marks_rendered_pages(tmp_path: Path) -> None:
    search_client = FakeSearchClient(
        {
            "python asyncio gather": payload_for(
                {
                    "url": "https://example.org/rendered",
                    "title": "Rendered Example",
                    "content": "Rendered search snippet.",
                    "engine": "brave",
                    "score": 4.0,
                }
            )
        }
    )
    fetch_client = FakeFetchClient(
        {
            "https://example.org/rendered": make_http_response(
                "https://example.org/rendered",
                """
                <html>
                  <head>
                    <title>Rendered Example</title>
                    <script id="__NEXT_DATA__" type="application/json">{}</script>
                  </head>
                  <body>
                    <main>
                      <p>Loading application shell.</p>
                      <div id="root"></div>
                    </main>
                  </body>
                </html>
                """,
            )
        }
    )
    render_client = FakeRenderClient(
        {
            "https://example.org/rendered": (
                """
                <html>
                  <head><title>Rendered Example</title></head>
                  <body><main><p>Rendered body text with the real content available after hydration.</p></main></body>
                </html>
                """,
                "https://example.org/rendered",
            )
        }
    )
    service = SearxngMCPService(
        make_settings(tmp_path),
        search_client=search_client,
        fetch_client=fetch_client,
        render_client=render_client,
    )

    async def run() -> None:
        result = await service.search_and_fetch(
            query="python asyncio gather", fetch_limit=1
        )
        assert not result.isError
        assert "Rendered fetch: auto" in text_of(result)
        assert "Rendered: auto" in text_of(result)
        assert sc(result)["rendered"] is True
        assert sc(result)["render_mode"] == "auto"
        assert sc(result)["fetched_pages"][0]["document"]["rendered"] is True
        assert sc(result)["fetched_pages"][0]["document"]["render_mode"] == "auto"
        assert (
            render_client.calls
            and render_client.calls[0][0] == "https://example.org/rendered"
        )

    asyncio.run(run())


def test_search_and_fetch_combines_search_and_extraction(tmp_path: Path) -> None:
    search_client = FakeSearchClient(
        {
            "python asyncio gather": payload_for(
                {
                    "url": "https://example.org/article",
                    "title": "Example Article",
                    "content": "TaskGroup is usually better than gather.",
                    "engine": "brave",
                    "score": 4.0,
                }
            )
        }
    )
    fetch_client = FakeFetchClient(
        {
            "https://example.org/article": make_http_response(
                "https://example.org/article",
                """
                <html>
                  <head><title>Example Article</title></head>
                  <body><main><p>Body text.</p></main></body>
                </html>
                """,
            )
        }
    )
    service = SearxngMCPService(
        make_settings(tmp_path), search_client=search_client, fetch_client=fetch_client
    )

    async def run() -> None:
        result = await service.search_and_fetch(
            query="python asyncio gather", fetch_limit=1
        )
        assert not result.isError
        assert "Fetched pages: 1" in text_of(result)
        assert "Body text." in text_of(result)
        assert sc(result)["fetched_pages"][0]["document"]["title"] == "Example Article"
        repeat = await service.search_and_fetch(
            query="python asyncio gather", fetch_limit=1
        )
        assert sc(repeat)["fetched_pages"][0]["cache_hit"] is True
        assert len(fetch_client.calls) == 1

    import asyncio

    asyncio.run(run())


def test_health_reports_backend_cache_and_render_support(tmp_path: Path) -> None:
    service = SearxngMCPService(
        make_settings(tmp_path),
        search_client=FakeSearchClient({}),
        fetch_client=FakeFetchClient({}),
        render_client=FakeRenderClient({}),
    )

    async def run() -> None:
        result = await service.health()
        assert not result.isError
        assert sc(result)["ok"] is True
        assert sc(result)["configured_backends"] == 1
        assert sc(result)["render_support"]["playwright_installed"] is True
        assert "render dependency: installed" in text_of(result)
        assert "render auto fallback: enabled" in text_of(result)

    import asyncio

    asyncio.run(run())
