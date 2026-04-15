from __future__ import annotations

from dataclasses import dataclass

from mcp.server.fastmcp import Context, FastMCP

from . import __version__
from .service import SearxngMCPService
from .settings import Settings


@dataclass(slots=True)
class MCPBundle:
    server: FastMCP
    service: SearxngMCPService


def create_server(settings: Settings) -> MCPBundle:
    service = SearxngMCPService(settings)
    server = FastMCP(
        name="searxng-mcp",
        instructions=(
            "Fast, token-efficient MCP access to SearXNG. "
            "The AI client should choose tools autonomously. "
            "Use search for one query, search_many for parallel fan-out, "
            "search_and_fetch for one-query research, research for multi-query workflows, "
            "fetch_url and fetch_many for source reading, "
            "rendered fetch is automatic for JS-heavy pages and rendered=True forces browser mode, "
            "read searxng://guide for the built-in workflow guide, "
            "prompts are optional compatibility surfaces rather than the primary interface, "
            "and health for backend status."
        ),
        host=settings.host,
        port=settings.port,
        json_response=True,
        stateless_http=True,
        log_level="INFO",
    )

    @server.resource(
        "searxng://config",
        mime_type="application/json",
        title="searxng-mcp configuration",
        description="Machine-readable server configuration and capability summary.",
    )
    def config_resource() -> dict[str, object]:
        return {
            "name": "searxng-mcp",
            "version": __version__,
            "base_url": settings.normalized_base_url,
            "fallback_base_urls": list(settings.normalized_fallback_base_urls),
            "transport": settings.transport,
            "resources": ["searxng://config", "searxng://guide"],
            "prompts": ["quick_lookup", "deep_research", "research_workflow"],
            "agent_driven": True,
            "prompts_optional": True,
            "default_language": settings.default_language,
            "default_categories": settings.default_categories,
            "default_safesearch": settings.default_safesearch,
            "default_max_results": settings.default_max_results,
            "default_excerpt_chars": settings.default_excerpt_chars,
            "render_timeout": settings.render_timeout,
            "render_wait_ms": settings.render_wait_ms,
            "render_concurrency": settings.render_concurrency,
            "render_headless": settings.render_headless,
            "render_block_resources": settings.render_block_resources,
            "render_browser_path": settings.render_browser_path,
            "render_sandbox": settings.render_sandbox,
            "render_auto_fallback": settings.render_auto_fallback,
            "render_auto_min_words": settings.render_auto_min_words,
            "render_auto_min_chars": settings.render_auto_min_chars,
            "render_support": service.render_client.status(),
            "tools": ["search", "search_many", "search_and_fetch", "research", "fetch_url", "fetch_many", "health"],
        }

    @server.resource(
        "searxng://guide",
        mime_type="application/json",
        title="searxng-mcp workflow guide",
        description="Machine-readable workflow guidance for agent-driven clients.",
    )
    def guide_resource() -> dict[str, object]:
        return {
            "name": "searxng-mcp workflow guide",
            "operating_mode": {
                "orchestration": "agent-driven",
                "primary_interface": "tools",
                "prompts": "optional compatibility only",
            },
            "transport_recommendation": {
                "local": "stdio",
                "shared_or_deployed": "streamable-http",
            },
            "tool_selection": {
                "search": "Single query lookup with compact visible output.",
                "search_many": "Parallel fan-out across query variants before merging and deduping.",
                "search_and_fetch": "One-query research that needs search plus source reading.",
                "research": "Broad or multi-part research that should merge multiple queries and fetch the best sources.",
                "fetch_url": "Read one URL.",
                "fetch_many": "Read a batch of URLs in parallel.",
                "health": "Check backend, cache, and render readiness.",
            },
            "prompt_compatibility": {
                "quick_lookup": "Optional helper prompt for direct questions when a client supports prompts.",
                "deep_research": "Optional helper prompt for broader investigations when a client supports prompts.",
                "research_workflow": "Optional compatibility router prompt.",
            },
            "default_behavior": {
                "visible_output": "compact",
                "raw_payload": "hidden in _meta",
                "render": "automatic for JS-heavy pages",
                "render_forcing": "rendered=True",
                "cache": "enabled for search and fetch flows",
                "default_interface": "tools",
            },
            "recommended_flow": [
                "Use search or search_many to locate likely sources.",
                "Use search_and_fetch when one query is enough.",
                "Use research for broader questions or when the answer needs multiple sources.",
                "Use fetch_many when you already have URLs.",
                "Leave render mode automatic unless a page is JS-heavy or incomplete.",
            ],
            "performance_tips": [
                "Keep max_results small unless breadth is required.",
                "Use ttl to reuse search and fetch work when iterating.",
                "Bound concurrency for large batches to keep render and fetch latency stable.",
            ],
        }

    @server.prompt(
        name="quick_lookup",
        title="Quick lookup",
        description="Seed the fastest single-question workflow.",
    )
    def quick_lookup(topic: str, intent: str = "facts") -> str:
        intent_key = (intent or "").strip().lower()
        if intent_key not in {"facts", "links", "citations", "summary"}:
            intent_key = "facts"
        return (
            f"Quick lookup topic: {topic}\n"
            f"Intent: {intent_key}\n"
            "Use search_and_fetch first unless a specific URL is already known.\n"
            "Keep the result set small, prefer compact excerpts, and answer directly.\n"
            "Rendered fetch is automatic for JS-heavy pages; only force rendered=True if the page is incomplete."
        )

    @server.prompt(
        name="deep_research",
        title="Deep research",
        description="Seed the broader multi-query research workflow.",
    )
    def deep_research(topic: str, scope: str = "broad") -> str:
        scope_key = (scope or "").strip().lower()
        if scope_key not in {"focused", "broad", "wide"}:
            scope_key = "broad"
        if scope_key == "focused":
            workflow = "search_many -> research"
            extra = "Use a few query variants to widen coverage before fetching the strongest sources."
        elif scope_key == "wide":
            workflow = "search_many -> research -> fetch_many"
            extra = "Use more query variants and compare multiple sources before deciding."
        else:
            workflow = "research"
            extra = "Use merged multi-query search, then fetch the top sources with citations."
        return (
            f"Deep research topic: {topic}\n"
            f"Scope: {scope_key}\n"
            f"Preferred workflow: {workflow}\n"
            "Start broad, merge and dedupe, then read the best sources.\n"
            "Use rendered fetch automatically for JS-heavy pages and rendered=True only when the first pass is incomplete.\n"
            f"{extra}"
        )

    @server.prompt(
        name="research_workflow",
        title="Research workflow",
        description="Compatibility router that chooses quick_lookup or deep_research.",
    )
    def research_workflow(topic: str, depth: str = "deep") -> str:
        depth_key = (depth or "").strip().lower()
        if depth_key not in {"quick", "broad", "deep"}:
            depth_key = "deep"
        if depth_key == "quick":
            return (
                f"Use quick_lookup for topic: {topic}.\n"
                "This is the best fit for direct questions, short fact finding, and small result sets."
            )
        elif depth_key == "broad":
            return (
                f"Use deep_research for topic: {topic}.\n"
                "This is the best fit for broader investigations that need multiple sources."
            )
        return (
            f"Use deep_research for topic: {topic}.\n"
            "This is the best fit for broader investigations that need source verification and citations."
        )

    @server.tool(name="search", description="Search SearXNG for a single query and return a compact summary plus hidden raw payload.")
    async def search_tool(
        query: str,
        categories: str | None = None,
        engines: str | None = None,
        enabled_engines: str | None = None,
        disabled_engines: str | None = None,
        language: str | None = None,
        pageno: int = 1,
        time_range: str | None = None,
        safesearch: int | None = None,
        max_results: int | None = None,
        ttl: int | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ):
        return await service.search(
            query=query,
            categories=categories,
            engines=engines,
            enabled_engines=enabled_engines,
            disabled_engines=disabled_engines,
            language=language,
            pageno=pageno,
            time_range=time_range,
            safesearch=safesearch,
            max_results=max_results,
            ttl=ttl,
            ctx=ctx,
        )

    @server.tool(name="search_many", description="Search multiple queries in parallel, dedupe the results, and return a merged ranking.")
    async def search_many_tool(
        queries: list[str],
        categories: str | None = None,
        engines: str | None = None,
        enabled_engines: str | None = None,
        disabled_engines: str | None = None,
        language: str | None = None,
        pageno: int = 1,
        time_range: str | None = None,
        safesearch: int | None = None,
        max_results: int | None = None,
        concurrency: int | None = None,
        ttl: int | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ):
        return await service.search_many(
            queries=queries,
            categories=categories,
            engines=engines,
            enabled_engines=enabled_engines,
            disabled_engines=disabled_engines,
            language=language,
            pageno=pageno,
            time_range=time_range,
            safesearch=safesearch,
            max_results=max_results,
            concurrency=concurrency,
            ttl=ttl,
            ctx=ctx,
        )

    @server.tool(name="search_and_fetch", description="Search SearXNG and fetch the top results with content extraction and citation metadata. Rendered fetch is automatic for JS-heavy pages; set rendered=True to force browser mode.")
    async def search_and_fetch_tool(
        query: str,
        categories: str | None = None,
        engines: str | None = None,
        enabled_engines: str | None = None,
        disabled_engines: str | None = None,
        language: str | None = None,
        pageno: int = 1,
        time_range: str | None = None,
        safesearch: int | None = None,
        max_results: int | None = None,
        fetch_limit: int = 3,
        fetch_excerpt_chars: int | None = None,
        rendered: bool = False,
        render_wait_ms: int | None = None,
        ttl: int | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ):
        return await service.search_and_fetch(
            query=query,
            categories=categories,
            engines=engines,
            enabled_engines=enabled_engines,
            disabled_engines=disabled_engines,
            language=language,
            pageno=pageno,
            time_range=time_range,
            safesearch=safesearch,
            max_results=max_results,
            fetch_limit=fetch_limit,
            fetch_excerpt_chars=fetch_excerpt_chars,
            rendered=rendered,
            render_wait_ms=render_wait_ms,
            ttl=ttl,
            ctx=ctx,
        )

    @server.tool(name="research", description="Search multiple queries, merge and dedupe results, then fetch the top sources with citations. Rendered fetch is automatic for JS-heavy pages; set rendered=True to force browser mode.")
    async def research_tool(
        queries: list[str],
        categories: str | None = None,
        engines: str | None = None,
        enabled_engines: str | None = None,
        disabled_engines: str | None = None,
        language: str | None = None,
        pageno: int = 1,
        time_range: str | None = None,
        safesearch: int | None = None,
        max_results: int | None = None,
        fetch_limit: int = 3,
        fetch_excerpt_chars: int | None = None,
        rendered: bool = False,
        render_wait_ms: int | None = None,
        concurrency: int | None = None,
        ttl: int | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ):
        return await service.research(
            queries=queries,
            categories=categories,
            engines=engines,
            enabled_engines=enabled_engines,
            disabled_engines=disabled_engines,
            language=language,
            pageno=pageno,
            time_range=time_range,
            safesearch=safesearch,
            max_results=max_results,
            fetch_limit=fetch_limit,
            fetch_excerpt_chars=fetch_excerpt_chars,
            rendered=rendered,
            render_wait_ms=render_wait_ms,
            concurrency=concurrency,
            ttl=ttl,
            ctx=ctx,
        )

    @server.tool(name="fetch_url", description="Fetch a URL, extract readable content, and return a compact excerpt with hidden full text metadata. Rendered fetch is automatic for JS-heavy pages; set rendered=True to force browser mode.")
    async def fetch_url_tool(
        url: str,
        max_excerpt_chars: int | None = None,
        max_links: int = 8,
        rendered: bool = False,
        render_wait_ms: int | None = None,
        ttl: int | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ):
        return await service.fetch_url(
            url=url,
            max_excerpt_chars=max_excerpt_chars,
            max_links=max_links,
            rendered=rendered,
            render_wait_ms=render_wait_ms,
            ttl=ttl,
            ctx=ctx,
        )

    @server.tool(name="fetch_many", description="Fetch multiple URLs in parallel, extract content, and return compact citations. Rendered fetch is automatic for JS-heavy pages; set rendered=True to force browser mode.")
    async def fetch_many_tool(
        urls: list[str],
        max_excerpt_chars: int | None = None,
        max_links: int = 8,
        rendered: bool = False,
        render_wait_ms: int | None = None,
        concurrency: int | None = None,
        ttl: int | None = None,
        ctx: Context = None,  # type: ignore[assignment]
    ):
        return await service.fetch_many(
            urls=urls,
            max_excerpt_chars=max_excerpt_chars,
            max_links=max_links,
            rendered=rendered,
            render_wait_ms=render_wait_ms,
            concurrency=concurrency,
            ttl=ttl,
            ctx=ctx,
        )

    @server.tool(name="health", description="Check that SearXNG and the local cache are healthy.")
    async def health_tool(ctx: Context = None):  # type: ignore[assignment]
        return await service.health(ctx=ctx)

    return MCPBundle(server=server, service=service)
