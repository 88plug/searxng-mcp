from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

from searxng_mcp.bench import run_benchmark
from searxng_mcp.client import BackendResponse
from searxng_mcp.render import make_result

from test_service import FakeSearchClient, make_settings, payload_for


class FakeCache:
    def __init__(self, owner: "FakeBenchmarkService") -> None:
        self.owner = owner
        self.clear_count = 0

    def clear(self) -> None:
        self.clear_count += 1
        self.owner.reset_cache_state()


class FakeBenchmarkService:
    def __init__(self, settings, search_client: FakeSearchClient) -> None:
        self.settings = settings
        self.search_client = search_client
        self.cache = FakeCache(self)
        self.search_calls: list[dict] = []
        self.search_many_calls: list[list[str]] = []
        self.research_calls: list[list[str]] = []
        self.fetch_url_calls: list[str] = []
        self.fetch_many_calls: list[list[str]] = []
        self._seen_ops: set[tuple[str, str]] = set()

    def reset_cache_state(self) -> None:
        self._seen_ops.clear()

    def _cache_hit(self, op: str, key: str) -> bool:
        cache_key = (op, key)
        hit = cache_key in self._seen_ops
        self._seen_ops.add(cache_key)
        return hit

    async def search(self, *, query: str, max_results: int | None = None, **_: object):
        self.search_calls.append({"query": query, "max_results": max_results})
        cache_hit = self._cache_hit("search", query)
        top_results = [{"title": f"{query} result", "url": f"https://example.org/{query.replace(' ', '-')}" }]
        return make_result(
            f"search service {query}",
            structured={"cache_hit": cache_hit, "result_count": len(top_results), "top_results": top_results},
            meta={"cache_hit": cache_hit, "result_count": len(top_results), "top_results": top_results},
        )

    async def search_many(self, *, queries: list[str], max_results: int | None = None, **_: object):
        self.search_many_calls.append(list(queries))
        key = "\u0000".join(queries)
        cache_hit = self._cache_hit("search_many", key)
        merged_results = [{"query": query, "title": query} for query in queries]
        return make_result(
            "search_many service",
            structured={
                "cache_hit": cache_hit,
                "unique_results": len(queries),
                "cache_hits": int(cache_hit),
                "merged_results": merged_results,
            },
            meta={
                "cache_hit": cache_hit,
                "unique_results": len(queries),
                "cache_hits": int(cache_hit),
                "merged_results": merged_results,
            },
        )

    async def research(self, *, queries: list[str], max_results: int | None = None, fetch_limit: int | None = None, **_: object):
        self.research_calls.append(list(queries))
        key = "\u0000".join(queries)
        cache_hit = self._cache_hit("research", key)
        fetched_pages = [{"url": f"https://example.org/{index}", "render_mode": "off"} for index, _query in enumerate(queries[:2], start=1)]
        return make_result(
            "research service",
            structured={
                "cache_hit": cache_hit,
                "unique_results": len(queries),
                "fetched_pages": fetched_pages,
                "fetch_cache_hits": int(cache_hit),
                "render_mode": "off",
            },
            meta={
                "cache_hit": cache_hit,
                "unique_results": len(queries),
                "fetched_pages": fetched_pages,
                "fetch_cache_hits": int(cache_hit),
                "render_mode": "off",
            },
        )

    async def fetch_url(self, *, url: str, **_: object):
        self.fetch_url_calls.append(url)
        cache_hit = self._cache_hit("fetch_url", url)
        document = {
            "url": url,
            "final_url": url,
            "content_type": "text/html",
            "title": "Example",
            "description": None,
            "author": None,
            "excerpt": "Example excerpt",
            "headings": [],
            "links": [],
            "word_count": 2,
            "char_count": 10,
            "truncated": False,
            "rendered": False,
        }
        return make_result(
            "fetch service",
            structured={"cache_hit": cache_hit, "rendered": False, "render_mode": "off", "document": document},
            meta={"cache_hit": cache_hit, "rendered": False, "render_mode": "off", "document": document},
        )

    async def fetch_many(self, *, urls: list[str], **_: object):
        self.fetch_many_calls.append(list(urls))
        key = "\u0000".join(urls)
        cache_hit = self._cache_hit("fetch_many", key)
        documents = [
            {
                "requested_url": url,
                "cache_hit": cache_hit,
                "elapsed_ms": 5.0,
                "render_mode": "off",
                "document": {
                    "url": url,
                    "final_url": url,
                    "content_type": "text/html",
                    "title": url.rsplit("/", 1)[-1],
                    "description": None,
                    "author": None,
                    "excerpt": "Example excerpt",
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
        return make_result(
            "fetch_many service",
            structured={
                "cache_hit": cache_hit,
                "successful_urls": len(urls),
                "cache_hits": int(cache_hit),
                "documents": documents,
                "rendered": False,
                "render_mode": "off",
            },
            meta={
                "cache_hit": cache_hit,
                "successful_urls": len(urls),
                "cache_hits": int(cache_hit),
                "documents": documents,
                "rendered": False,
                "render_mode": "off",
            },
        )

    async def close(self) -> None:
        return None


class FakeBenchmarkServer:
    def __init__(self, service: FakeBenchmarkService) -> None:
        self.service = service
        self.tool_calls: list[tuple[str, dict]] = []

    async def call_tool(self, name: str, arguments: dict[str, object]):
        self.tool_calls.append((name, dict(arguments)))
        method = getattr(self.service, name)
        return await method(**arguments)


def test_run_benchmark_separates_service_and_tool_layers(monkeypatch, tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    queries = ["python asyncio gather", "python taskgroup", "postgres jsonb indexing"]
    search_client = FakeSearchClient(
        {
            query: payload_for(
                {
                    "url": f"https://example.org/{index}",
                    "title": query,
                    "content": "snippet",
                    "engine": "mock",
                    "score": float(index + 1),
                }
            )
            for index, query in enumerate(queries)
        }
    )
    service = FakeBenchmarkService(settings, search_client)
    bundle = SimpleNamespace(service=service, server=FakeBenchmarkServer(service))

    monkeypatch.setattr("searxng_mcp.bench.create_server", lambda _settings: bundle)

    async def run() -> dict:
        return await run_benchmark(
            settings=settings,
            queries=queries,
            rounds=1,
            max_results=3,
            fetch_url="https://example.org/article",
        )

    import asyncio

    report = asyncio.run(run())

    assert report["queries"] == queries
    assert report["search_backend"]["count"] == len(queries)
    assert report["service_only"]["search"]["cold"]["count"] == len(queries)
    assert report["service_only"]["search"]["warm"]["count"] == len(queries)
    assert report["service_only"]["search_many"]["cold"]["count"] == 1
    assert report["service_only"]["research"]["cold"]["count"] == 1
    assert report["tool_layer"]["search"]["cold"]["count"] == len(queries)
    assert report["tool_layer"]["search"]["cold"]["success_count"] == len(queries)
    assert report["tool_layer"]["search_many"]["cold"]["count"] == 1
    assert report["tool_layer"]["search_many"]["cold"]["success_count"] == 1
    assert report["tool_layer"]["research"]["cold"]["success_count"] == 1
    assert report["tool_layer"]["fetch_url"]["cold"]["success_count"] == 1
    assert report["tool_layer"]["fetch_many"]["cold"]["count"] == 1
    assert report["tool_layer"]["fetch_many"]["cold"]["success_count"] == 1
    assert service.search_many_calls[0] == queries
    assert service.research_calls[0] == queries
    assert any(name == "search_many" for name, _args in bundle.server.tool_calls)
    assert any(name == "research" for name, _args in bundle.server.tool_calls)
    assert any(name == "fetch_many" for name, _args in bundle.server.tool_calls)
    assert service.cache.clear_count >= 10
