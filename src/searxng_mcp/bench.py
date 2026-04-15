from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
import argparse
import asyncio
from dataclasses import dataclass
from pathlib import Path
import statistics
import tempfile
import time
from typing import Any

from .render import approximate_tokens
from .service import SearxngMCPService
from .settings import Settings, load_settings
from .server import create_server

DEFAULT_QUERIES = [
    "python asyncio gather",
    "python taskgroup",
    "postgres jsonb indexing",
    "linux epoll explained",
    "docker compose restart service",
    "valkey redis differences",
]

DEFAULT_FETCH_URLS = [
    "https://docs.python.org/3/library/asyncio-task.html",
    "https://example.com",
    "https://www.iana.org/domains/reserved",
]


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    index = (len(values) - 1) * pct
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    weight = index - lower
    return values[lower] * (1 - weight) + values[upper] * weight


def _summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    successes = [sample for sample in samples if not sample.get("error")]
    latencies = [float(sample["elapsed_ms"]) for sample in successes if "elapsed_ms" in sample]
    tokens = [int(sample.get("visible_tokens", 0)) for sample in successes]
    return {
        "count": len(samples),
        "success_count": len(successes),
        "error_count": len(samples) - len(successes),
        "latency_ms": {
            "min": round(min(latencies), 2) if latencies else 0.0,
            "p50": round(_percentile(latencies, 0.5), 2) if latencies else 0.0,
            "p95": round(_percentile(latencies, 0.95), 2) if latencies else 0.0,
            "max": round(max(latencies), 2) if latencies else 0.0,
            "mean": round(statistics.fmean(latencies), 2) if latencies else 0.0,
        },
        "visible_tokens": {
            "min": min(tokens) if tokens else 0,
            "p50": int(_percentile(tokens, 0.5)) if tokens else 0,
            "p95": int(_percentile(tokens, 0.95)) if tokens else 0,
            "max": max(tokens) if tokens else 0,
            "mean": round(statistics.fmean(tokens), 2) if tokens else 0.0,
        },
    }


def _tool_result_text(result: Any) -> str:
    if hasattr(result, "content"):
        content = getattr(result, "content", None)
        if isinstance(content, Sequence) and not isinstance(content, (str, bytes, bytearray)):
            parts: list[str] = []
            for block in content:
                text = getattr(block, "text", None)
                if text is not None:
                    parts.append(str(text))
                elif isinstance(block, dict):
                    value = block.get("text")
                    if value is not None:
                        parts.append(str(value))
                else:
                    parts.append(str(block))
            return "\n".join(part for part in parts if part)
        if content is not None:
            return str(content)
    if isinstance(result, Sequence) and not isinstance(result, (str, bytes, bytearray)):
        parts: list[str] = []
        for block in result:
            text = getattr(block, "text", None)
            if text is not None:
                parts.append(str(text))
            elif isinstance(block, dict):
                value = block.get("text")
                if value is not None:
                    parts.append(str(value))
            else:
                parts.append(str(block))
        return "\n".join(part for part in parts if part)
    if isinstance(result, dict):
        if isinstance(result.get("content"), str):
            return str(result["content"])
        if isinstance(result.get("text"), str):
            return str(result["text"])
    return ""


def _tool_result_structured(result: Any) -> dict[str, Any]:
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    if isinstance(result, dict):
        structured = result.get("structuredContent")
        if isinstance(structured, dict):
            return structured
    return {}


async def _call_tool(server: Any, name: str, arguments: dict[str, Any]) -> Any:
    tool_manager = getattr(server, "_tool_manager", None)
    if tool_manager is not None:
        return await tool_manager.call_tool(name, arguments, context=None, convert_result=True)
    return await server.call_tool(name, arguments)


async def _measure_round(
    runner: Callable[[], Any],
    *,
    extra: Callable[[Any, dict[str, Any], str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = await runner()
        elapsed_ms = (time.perf_counter() - started) * 1000
        text = _tool_result_text(result)
        structured = _tool_result_structured(result)
        sample: dict[str, Any] = {
            "elapsed_ms": round(elapsed_ms, 2),
            "visible_tokens": approximate_tokens(text),
        }
        is_error = bool(getattr(result, "isError", False))
        if not is_error and isinstance(result, dict):
            is_error = bool(result.get("isError"))
        if is_error:
            sample["error"] = str(structured.get("error") or text or "tool returned an error result")
        if extra is not None:
            sample.update(extra(result, structured, text))
        return sample
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - started) * 1000
        return {
            "elapsed_ms": round(elapsed_ms, 2),
            "error": str(exc),
            "visible_tokens": 0,
        }


async def _run_search_backend_round(
    service: SearxngMCPService,
    query: str,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        backend = await service.search_client.search(  # noqa: SLF001
            {
                "q": query,
                "format": "json",
                "categories": service.settings.default_categories,
                "language": service.settings.default_language,
                "pageno": 1,
                "safesearch": service.settings.default_safesearch,
            }
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        return {
            "query": query,
            "elapsed_ms": round(elapsed_ms, 2),
            "backend_elapsed_ms": round(backend.elapsed_ms, 2),
            "result_count": len(backend.payload.get("results", [])),
            "visible_tokens": 0,
        }
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - started) * 1000
        return {
            "query": query,
            "elapsed_ms": round(elapsed_ms, 2),
            "error": str(exc),
            "visible_tokens": 0,
        }


async def _run_search_round(
    runner: Callable[[], Any],
    query: str,
    max_results: int,
) -> dict[str, Any]:
    return await _measure_round(
        runner,
        extra=lambda _result, structured, _text: {
            "query": query,
            "result_count": structured.get("result_count", len(structured.get("top_results") or [])),
            "cache_hit": structured.get("cache_hit", False),
            "top_results": len(structured.get("top_results") or []),
            "max_results": max_results,
        },
    )


async def _run_search_many_round(
    runner: Callable[[], Any],
    queries: list[str],
    max_results: int,
) -> dict[str, Any]:
    return await _measure_round(
        runner,
        extra=lambda _result, structured, _text: {
            "queries": queries,
            "unique_results": structured.get("unique_results", 0),
            "cache_hits": structured.get("cache_hits", 0),
            "top_results": len(structured.get("merged_results") or []),
        },
    )


async def _run_fetch_round(
    runner: Callable[[], Any],
    url: str,
    *,
    rendered: bool = False,
    render_wait_ms: int | None = None,
) -> dict[str, Any]:
    return await _measure_round(
        runner,
        extra=lambda _result, structured, _text: {
            "url": url,
            "rendered": rendered,
            "cache_hit": structured.get("cache_hit", False),
            "render_mode": structured.get("render_mode"),
            "render_wait_ms": render_wait_ms,
        },
    )


async def _run_fetch_many_round(
    runner: Callable[[], Any],
    urls: list[str],
    *,
    rendered: bool = False,
    render_wait_ms: int | None = None,
) -> dict[str, Any]:
    return await _measure_round(
        runner,
        extra=lambda _result, structured, _text: {
            "urls": urls,
            "rendered": rendered,
            "successful_urls": structured.get("successful_urls", 0),
            "cache_hits": structured.get("cache_hits", 0),
            "render_mode": structured.get("render_mode"),
            "render_wait_ms": render_wait_ms,
        },
    )


async def _run_research_round(
    runner: Callable[[], Any],
    queries: list[str],
    max_results: int,
) -> dict[str, Any]:
    return await _measure_round(
        runner,
        extra=lambda _result, structured, _text: {
            "queries": queries,
            "unique_results": structured.get("unique_results", 0),
            "fetched_pages": len(structured.get("fetched_pages") or []),
            "fetch_cache_hits": structured.get("fetch_cache_hits", 0),
            "render_mode": structured.get("render_mode"),
        },
    )


async def run_benchmark(
    *,
    settings: Settings,
    queries: list[str],
    rounds: int,
    max_results: int,
    fetch_url: str,
) -> dict[str, Any]:
    bundle = create_server(settings)
    service = bundle.service
    try:
        backend_samples: list[dict[str, Any]] = []
        service_search_cold: list[dict[str, Any]] = []
        service_search_warm: list[dict[str, Any]] = []
        service_many_cold: list[dict[str, Any]] = []
        service_many_warm: list[dict[str, Any]] = []
        service_research_cold: list[dict[str, Any]] = []
        service_research_warm: list[dict[str, Any]] = []
        service_fetch_cold: list[dict[str, Any]] = []
        service_fetch_warm: list[dict[str, Any]] = []
        service_fetch_many_cold: list[dict[str, Any]] = []
        service_fetch_many_warm: list[dict[str, Any]] = []
        tool_search_cold: list[dict[str, Any]] = []
        tool_search_warm: list[dict[str, Any]] = []
        tool_many_cold: list[dict[str, Any]] = []
        tool_many_warm: list[dict[str, Any]] = []
        tool_research_cold: list[dict[str, Any]] = []
        tool_research_warm: list[dict[str, Any]] = []
        tool_fetch_cold: list[dict[str, Any]] = []
        tool_fetch_warm: list[dict[str, Any]] = []
        tool_fetch_many_cold: list[dict[str, Any]] = []
        tool_fetch_many_warm: list[dict[str, Any]] = []

        for _ in range(rounds):
            for query in queries:
                backend_samples.append(await _run_search_backend_round(service, query))

            service.cache.clear()
            for query in queries:
                service_search_cold.append(await _run_search_round(lambda: service.search(query=query, max_results=max_results), query, max_results))
                service_search_warm.append(await _run_search_round(lambda: service.search(query=query, max_results=max_results), query, max_results))

            service.cache.clear()
            service_many_cold.append(
                await _run_search_many_round(
                    lambda: service.search_many(queries=queries, max_results=max_results),
                    queries,
                    max_results,
                )
            )
            service_many_warm.append(
                await _run_search_many_round(
                    lambda: service.search_many(queries=queries, max_results=max_results),
                    queries,
                    max_results,
                )
            )

            service.cache.clear()
            service_research_cold.append(
                await _run_research_round(
                    lambda: service.research(queries=queries, max_results=max_results, fetch_limit=min(3, max_results)),
                    queries,
                    max_results,
                )
            )
            service_research_warm.append(
                await _run_research_round(
                    lambda: service.research(queries=queries, max_results=max_results, fetch_limit=min(3, max_results)),
                    queries,
                    max_results,
                )
            )

            service.cache.clear()
            service_fetch_cold.append(
                await _run_fetch_round(
                    lambda: service.fetch_url(url=fetch_url),
                    fetch_url,
                )
            )
            service_fetch_warm.append(
                await _run_fetch_round(
                    lambda: service.fetch_url(url=fetch_url),
                    fetch_url,
                )
            )

            service.cache.clear()
            service_fetch_many_cold.append(
                await _run_fetch_many_round(
                    lambda: service.fetch_many(urls=DEFAULT_FETCH_URLS, rendered=False),
                    DEFAULT_FETCH_URLS,
                )
            )
            service_fetch_many_warm.append(
                await _run_fetch_many_round(
                    lambda: service.fetch_many(urls=DEFAULT_FETCH_URLS, rendered=False),
                    DEFAULT_FETCH_URLS,
                )
            )

            service.cache.clear()
            for query in queries:
                tool_search_cold.append(
                    await _run_search_round(
                        lambda: _call_tool(bundle.server, "search", {"query": query, "max_results": max_results}),
                        query,
                        max_results,
                    )
                )
                tool_search_warm.append(
                    await _run_search_round(
                        lambda: _call_tool(bundle.server, "search", {"query": query, "max_results": max_results}),
                        query,
                        max_results,
                    )
                )

            service.cache.clear()
            tool_many_cold.append(
                await _run_search_many_round(
                    lambda: _call_tool(bundle.server, "search_many", {"queries": queries, "max_results": max_results}),
                    queries,
                    max_results,
                )
            )
            tool_many_warm.append(
                await _run_search_many_round(
                    lambda: _call_tool(bundle.server, "search_many", {"queries": queries, "max_results": max_results}),
                    queries,
                    max_results,
                )
            )

            service.cache.clear()
            tool_research_cold.append(
                await _run_research_round(
                    lambda: _call_tool(
                        bundle.server,
                        "research",
                        {"queries": queries, "max_results": max_results, "fetch_limit": min(3, max_results)},
                    ),
                    queries,
                    max_results,
                )
            )
            tool_research_warm.append(
                await _run_research_round(
                    lambda: _call_tool(
                        bundle.server,
                        "research",
                        {"queries": queries, "max_results": max_results, "fetch_limit": min(3, max_results)},
                    ),
                    queries,
                    max_results,
                )
            )

            service.cache.clear()
            tool_fetch_cold.append(
                await _run_fetch_round(
                    lambda: _call_tool(bundle.server, "fetch_url", {"url": fetch_url}),
                    fetch_url,
                )
            )
            tool_fetch_warm.append(
                await _run_fetch_round(
                    lambda: _call_tool(bundle.server, "fetch_url", {"url": fetch_url}),
                    fetch_url,
                )
            )

            service.cache.clear()
            tool_fetch_many_cold.append(
                await _run_fetch_many_round(
                    lambda: _call_tool(bundle.server, "fetch_many", {"urls": DEFAULT_FETCH_URLS}),
                    DEFAULT_FETCH_URLS,
                )
            )
            tool_fetch_many_warm.append(
                await _run_fetch_many_round(
                    lambda: _call_tool(bundle.server, "fetch_many", {"urls": DEFAULT_FETCH_URLS}),
                    DEFAULT_FETCH_URLS,
                )
            )

        service_only = {
            "search": {
                "cold": _summary(service_search_cold),
                "warm": _summary(service_search_warm),
            },
            "search_many": {
                "cold": _summary(service_many_cold),
                "warm": _summary(service_many_warm),
            },
            "research": {
                "cold": _summary(service_research_cold),
                "warm": _summary(service_research_warm),
            },
            "fetch_url": {
                "cold": _summary(service_fetch_cold),
                "warm": _summary(service_fetch_warm),
            },
            "fetch_many": {
                "cold": _summary(service_fetch_many_cold),
                "warm": _summary(service_fetch_many_warm),
            },
        }
        tool_layer = {
            "search": {
                "cold": _summary(tool_search_cold),
                "warm": _summary(tool_search_warm),
            },
            "search_many": {
                "cold": _summary(tool_many_cold),
                "warm": _summary(tool_many_warm),
            },
            "research": {
                "cold": _summary(tool_research_cold),
                "warm": _summary(tool_research_warm),
            },
            "fetch_url": {
                "cold": _summary(tool_fetch_cold),
                "warm": _summary(tool_fetch_warm),
            },
            "fetch_many": {
                "cold": _summary(tool_fetch_many_cold),
                "warm": _summary(tool_fetch_many_warm),
            },
        }

        return {
            "base_url": settings.normalized_base_url,
            "rounds": rounds,
            "queries": queries,
            "search_backend": _summary(backend_samples),
            "service_only": service_only,
            "tool_layer": tool_layer,
        }
    finally:
        await service.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark searxng-mcp against a local SearXNG instance")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--fetch-url", default="https://docs.python.org/3/library/asyncio-task.html")
    parser.add_argument("--queries", nargs="*", default=DEFAULT_QUERIES)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--fetch-verify-tls", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = load_settings()
    if args.base_url:
        settings.base_url = args.base_url
    if args.cache_dir:
        settings.cache_dir = Path(args.cache_dir).expanduser()
    if args.fetch_verify_tls is not None:
        settings.fetch_verify_tls = str(args.fetch_verify_tls).strip().lower() in {"1", "true", "yes", "on"}

    report = asyncio.run(
        run_benchmark(
            settings=settings,
            queries=[query for query in args.queries if query],
            rounds=max(1, args.rounds),
            max_results=max(1, args.max_results),
            fetch_url=args.fetch_url,
        )
    )
    import orjson

    print(orjson.dumps(report, option=orjson.OPT_INDENT_2).decode())


if __name__ == "__main__":
    main()
