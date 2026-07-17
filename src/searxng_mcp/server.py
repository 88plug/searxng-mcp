from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Literal

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from . import __version__
from .service import SearxngMCPService
from .settings import Settings


@dataclass(slots=True)
class MCPBundle:
    server: FastMCP
    service: SearxngMCPService


SERVER_INSTRUCTIONS = (
    "Token-efficient MCP access to SearXNG. The model should choose tools autonomously. "
    "Pick `search` for one query and a compact answer; `search_many` to fan out across query "
    "variants and merge results; `search_and_fetch` when one query needs source extraction; "
    "`research` for multi-query investigations that need merged sources and citations; "
    "`fetch_url` and `fetch_many` to read pages you already have URLs for; `health` to check "
    "the backend. Rendered fetch is automatic for JS-heavy pages; pass `rendered=true` to force it. "
    "All visible output is intentionally compact; full raw payloads are returned in hidden `_meta`. "
    "Resources `searxng://config` and `searxng://guide` describe the runtime and intended workflow."
)

CategoriesParam = Annotated[
    str | None,
    Field(
        default=None,
        description=(
            "Comma-separated SearXNG categories to search (e.g. 'general', 'news', 'images', "
            "'videos', 'science', 'files'). Default is the server's configured category set, "
            "typically 'general'."
        ),
    ),
]

EnginesParam = Annotated[
    str | None,
    Field(
        default=None,
        description=(
            "Comma-separated SearXNG engine names to use for this query. Forwarded to SearXNG's "
            "'engines' parameter. Leave unset to use the backend's default engine selection."
        ),
    ),
]

EnabledEnginesParam = Annotated[
    str | None,
    Field(
        default=None,
        description=(
            "Comma-separated engine names to enable in addition to the backend defaults. "
            "Forwarded as SearXNG's 'enabled_engines' parameter."
        ),
    ),
]

DisabledEnginesParam = Annotated[
    str | None,
    Field(
        default=None,
        description=(
            "Comma-separated engine names to exclude from this query. Forwarded as SearXNG's "
            "'disabled_engines' parameter."
        ),
    ),
]

LanguageParam = Annotated[
    str | None,
    Field(
        default=None,
        description=(
            "BCP-47 language hint for SearXNG (e.g. 'en', 'en-US', 'de', 'all'). Default is the "
            "server's configured language."
        ),
    ),
]

PageNoParam = Annotated[
    int,
    Field(
        default=1,
        ge=1,
        le=20,
        description="Result page number (1–20, default 1). Use to paginate beyond the first page.",
    ),
]

TimeRangeParam = Annotated[
    Literal["day", "week", "month", "year"] | None,
    Field(
        default=None,
        description=(
            "Restrict results to recent content. Valid values: 'day', 'week', 'month', 'year'. "
            "Omit for no time filter."
        ),
    ),
]

SafesearchParam = Annotated[
    Literal[0, 1, 2] | None,
    Field(
        default=None,
        description=(
            "Safe search level: 0=off, 1=moderate, 2=strict. Omit to use the server default."
        ),
    ),
]

MaxResultsParam = Annotated[
    int | None,
    Field(
        default=None,
        ge=1,
        le=50,
        description=(
            "Maximum visible results to include in the compact summary (1–50). Default comes "
            "from server settings (typically 5). The hidden `_meta.raw_payload.results` always "
            "contains the full SearXNG response regardless of this cap."
        ),
    ),
]

TtlParam = Annotated[
    int | None,
    Field(
        default=None,
        ge=0,
        le=86400,
        description=(
            "Cache TTL override in seconds (0–86400). 0 disables caching for this call. Omit "
            "to use the server's default TTL."
        ),
    ),
]

ConcurrencyParam = Annotated[
    int | None,
    Field(
        default=None,
        ge=1,
        le=16,
        description=(
            "Maximum concurrent backend requests for this fan-out (1–16). Higher is faster but "
            "puts more load on the SearXNG instance and remote pages. Omit for the server default."
        ),
    ),
]

FetchLimitParam = Annotated[
    int,
    Field(
        default=3,
        ge=1,
        le=20,
        description=(
            "Maximum number of search results to fetch and extract (1–20, default 3). Lower is "
            "faster; higher gives more sources at the cost of latency."
        ),
    ),
]

FetchExcerptCharsParam = Annotated[
    int | None,
    Field(
        default=None,
        ge=200,
        le=20000,
        description=(
            "Per-source excerpt character cap (200–20000). Default comes from server settings. "
            "Smaller values keep the visible output tight; the full text is always available "
            "in hidden `_meta` for each source."
        ),
    ),
]

RenderedParam = Annotated[
    bool,
    Field(
        default=False,
        description=(
            "Force browser-based rendering for fetches. Default false: the server auto-renders "
            "only when a page is JS-heavy or returns near-empty text. Set true when a previous "
            "fetch came back nearly empty or to read a known SPA. Forced rendering is several "
            "times slower than HTTP fetch."
        ),
    ),
]

RenderWaitMsParam = Annotated[
    int | None,
    Field(
        default=None,
        ge=0,
        le=15000,
        description=(
            "Extra milliseconds to wait after DOM content load before extracting (0–15000). "
            "Use a higher value (e.g. 1500–4000) for SPAs that hydrate slowly."
        ),
    ),
]

MaxExcerptCharsParam = Annotated[
    int | None,
    Field(
        default=None,
        ge=200,
        le=50000,
        description=(
            "Excerpt character cap for the visible output (200–50000). Default comes from server "
            "settings. The full extracted text is always returned in hidden `_meta.full_text`."
        ),
    ),
]

MaxLinksParam = Annotated[
    int,
    Field(
        default=8,
        ge=0,
        le=64,
        description=(
            "Maximum outbound links to surface in the visible output (0–64, default 8). The "
            "complete link list is always included in hidden `_meta`."
        ),
    ),
]

QueryParam = Annotated[
    str,
    Field(
        min_length=1,
        max_length=400,
        description=(
            "Search query (1–400 chars). Plain text or SearXNG syntax. SearXNG bangs like "
            "'!wikipedia foo' or '!images cats' are supported and route to specific engines."
        ),
    ),
]

QueriesParam = Annotated[
    list[str],
    Field(
        min_length=1,
        max_length=10,
        description=(
            "List of 1–10 search queries to run in parallel. Use distinct phrasings or angles "
            "(synonyms, related entities, opposing framings) for the best merged coverage."
        ),
    ),
]

UrlParam = Annotated[
    str,
    Field(
        min_length=4,
        max_length=4000,
        description=(
            "Absolute http:// or https:// URL to fetch. Bare domains like 'example.com' are "
            "auto-prefixed with https://. Other schemes are rejected."
        ),
    ),
]

UrlsParam = Annotated[
    list[str],
    Field(
        min_length=1,
        max_length=20,
        description=(
            "List of 1–20 absolute http(s) URLs to fetch in parallel. Duplicates are dedupe-d "
            "after canonicalisation."
        ),
    ),
]


# Tool display titles go on @server.tool(title=...), not ToolAnnotations.
# Inspector / MCP 2025-11-25 emit top-level tool "title"; annotations.title is not enough.
READ_ONLY_SEARCH = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=True,
)

READ_ONLY_FETCH = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)

# health() network-pings the SearXNG backend — openWorld must be True (same class as search/fetch).
READ_ONLY_HEALTH = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)


def create_server(settings: Settings) -> MCPBundle:
    service = SearxngMCPService(settings)
    server = FastMCP(
        name="searxng",
        instructions=SERVER_INSTRUCTIONS,
        host=settings.host,
        port=settings.port,
        json_response=True,
        stateless_http=True,
        log_level="INFO",
    )
    # Surface the package version in the MCP initialize handshake's serverInfo
    # (FastMCP has no version= param; the low-level server defaults to the mcp
    # SDK version when this is unset).
    server._mcp_server.version = __version__

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
            "tools": [
                "search",
                "search_many",
                "search_and_fetch",
                "research",
                "fetch_url",
                "fetch_many",
                "health",
            ],
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
    def quick_lookup(
        topic: Annotated[
            str, Field(min_length=1, description="The topic or question to look up.")
        ],
        intent: Annotated[
            Literal["facts", "links", "citations", "summary"],
            Field(
                default="facts",
                description="Output emphasis: 'facts', 'links', 'citations', or 'summary'.",
            ),
        ] = "facts",
    ) -> str:
        return (
            f"Quick lookup topic: {topic}\n"
            f"Intent: {intent}\n"
            "Use search_and_fetch first unless a specific URL is already known.\n"
            "Keep the result set small, prefer compact excerpts, and answer directly.\n"
            "Rendered fetch is automatic for JS-heavy pages; only force rendered=True if the page is incomplete."
        )

    @server.prompt(
        name="deep_research",
        title="Deep research",
        description="Seed the broader multi-query research workflow.",
    )
    def deep_research(
        topic: Annotated[
            str, Field(min_length=1, description="The topic or question to research.")
        ],
        scope: Annotated[
            Literal["focused", "broad", "wide"],
            Field(
                default="broad",
                description="Breadth: 'focused' (few queries), 'broad' (default), or 'wide' (many queries).",
            ),
        ] = "broad",
    ) -> str:
        if scope == "focused":
            workflow = "search_many -> research"
            extra = "Use a few query variants to widen coverage before fetching the strongest sources."
        elif scope == "wide":
            workflow = "search_many -> research -> fetch_many"
            extra = (
                "Use more query variants and compare multiple sources before deciding."
            )
        else:
            workflow = "research"
            extra = "Use merged multi-query search, then fetch the top sources with citations."
        return (
            f"Deep research topic: {topic}\n"
            f"Scope: {scope}\n"
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
    def research_workflow(
        topic: Annotated[
            str,
            Field(min_length=1, description="The topic or question to investigate."),
        ],
        depth: Annotated[
            Literal["quick", "broad", "deep"],
            Field(
                default="deep",
                description="Depth router: 'quick' for a fact lookup, 'broad' or 'deep' for multi-source research.",
            ),
        ] = "deep",
    ) -> str:
        if depth == "quick":
            return (
                f"Use quick_lookup for topic: {topic}.\n"
                "This is the best fit for direct questions, short fact finding, and small result sets."
            )
        if depth == "broad":
            return (
                f"Use deep_research for topic: {topic}.\n"
                "This is the best fit for broader investigations that need multiple sources."
            )
        return (
            f"Use deep_research for topic: {topic}.\n"
            "This is the best fit for broader investigations that need source verification and citations."
        )

    @server.tool(
        name="search",
        title="Search",
        description=(
            "Search the open web via SearXNG for a single query and return a compact, "
            "token-efficient summary of the top results.\n"
            "Best for: quick fact-finding, current events, locating likely sources, single-question lookups.\n"
            "Returns: ranked list of {title, url, domain, snippet, engine, score} plus answers, infoboxes, "
            "suggestions and corrections when SearXNG provides them. The full SearXNG payload is also "
            "available in hidden `_meta.raw_payload`.\n"
            "Use `search_many` instead when running multiple parallel queries; `search_and_fetch` when "
            "you also need extracted page content; `research` for multi-query investigations with merged "
            "sources and fetched excerpts."
        ),
        annotations=READ_ONLY_SEARCH,
    )
    async def search_tool(
        query: QueryParam,
        categories: CategoriesParam = None,
        engines: EnginesParam = None,
        enabled_engines: EnabledEnginesParam = None,
        disabled_engines: DisabledEnginesParam = None,
        language: LanguageParam = None,
        pageno: PageNoParam = 1,
        time_range: TimeRangeParam = None,
        safesearch: SafesearchParam = None,
        max_results: MaxResultsParam = None,
        ttl: TtlParam = None,
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

    @server.tool(
        name="search_many",
        title="Search Many",
        description=(
            "Run several SearXNG searches in parallel, then dedupe and merge their result sets into "
            "a single ranked list.\n"
            "Best for: broadening coverage on one topic with synonym/angle variants, comparing how "
            "different phrasings rank, building a high-recall source pool before fetching.\n"
            "Returns: merged hits with per-hit `queries` (which inputs surfaced it), `engines`, "
            "`hit_count`, and a `merged_score`. Per-query raw payloads are in hidden `_meta`.\n"
            "Use `search` for a single query; `research` when you also need the top sources fetched "
            "and excerpted in the same call."
        ),
        annotations=READ_ONLY_SEARCH,
    )
    async def search_many_tool(
        queries: QueriesParam,
        categories: CategoriesParam = None,
        engines: EnginesParam = None,
        enabled_engines: EnabledEnginesParam = None,
        disabled_engines: DisabledEnginesParam = None,
        language: LanguageParam = None,
        pageno: PageNoParam = 1,
        time_range: TimeRangeParam = None,
        safesearch: SafesearchParam = None,
        max_results: MaxResultsParam = None,
        concurrency: ConcurrencyParam = None,
        ttl: TtlParam = None,
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

    @server.tool(
        name="search_and_fetch",
        title="Search and Fetch",
        description=(
            "Search SearXNG for one query and fetch+extract the top results in a single call. "
            "Combines `search` and `fetch_many` for one-query research workflows.\n"
            "Use when answering one question that needs evidence from full pages, building a "
            "citation-backed answer to a single prompt, or getting both ranked results and readable "
            "excerpts in one round-trip.\n"
            "Returns: search summary plus per-source `{title, url, excerpt, citations, render_mode}`. "
            "The full SearXNG payload and per-page full text are in hidden `_meta`.\n"
            "Rendered fetch is automatic for JS-heavy pages; pass `rendered=true` to force browser "
            "mode (slower).\n"
            "Use `search` if extraction is not needed; `research` for multi-query investigations."
        ),
        annotations=READ_ONLY_SEARCH,
    )
    async def search_and_fetch_tool(
        query: QueryParam,
        categories: CategoriesParam = None,
        engines: EnginesParam = None,
        enabled_engines: EnabledEnginesParam = None,
        disabled_engines: DisabledEnginesParam = None,
        language: LanguageParam = None,
        pageno: PageNoParam = 1,
        time_range: TimeRangeParam = None,
        safesearch: SafesearchParam = None,
        max_results: MaxResultsParam = None,
        fetch_limit: FetchLimitParam = 3,
        fetch_excerpt_chars: FetchExcerptCharsParam = None,
        rendered: RenderedParam = False,
        render_wait_ms: RenderWaitMsParam = None,
        ttl: TtlParam = None,
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

    @server.tool(
        name="research",
        title="Research",
        description=(
            "Run multi-query research: search several queries in parallel, merge and dedupe results, "
            "then fetch and extract the strongest sources with citations.\n"
            "Best for: open-ended investigations, building a multi-source briefing, answering a "
            "complex question that needs cross-checking across providers.\n"
            "Returns: merged ranking, per-source extracted excerpts and citations, plus a query map "
            "showing which queries surfaced each source. Full payloads in hidden `_meta`.\n"
            "Rendered fetch is automatic for JS-heavy pages; pass `rendered=true` to force browser mode.\n"
            "Use `search_many` when extraction is not needed; `search_and_fetch` for a single query."
        ),
        annotations=READ_ONLY_SEARCH,
    )
    async def research_tool(
        queries: QueriesParam,
        categories: CategoriesParam = None,
        engines: EnginesParam = None,
        enabled_engines: EnabledEnginesParam = None,
        disabled_engines: DisabledEnginesParam = None,
        language: LanguageParam = None,
        pageno: PageNoParam = 1,
        time_range: TimeRangeParam = None,
        safesearch: SafesearchParam = None,
        max_results: MaxResultsParam = None,
        fetch_limit: FetchLimitParam = 3,
        fetch_excerpt_chars: FetchExcerptCharsParam = None,
        rendered: RenderedParam = False,
        render_wait_ms: RenderWaitMsParam = None,
        concurrency: ConcurrencyParam = None,
        ttl: TtlParam = None,
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

    @server.tool(
        name="fetch_url",
        title="Fetch URL",
        description=(
            "Fetch one URL, extract readable content (Readability-style), and return a compact "
            "excerpt plus link list. The full extracted text is preserved in hidden `_meta.full_text`.\n"
            "Best for: reading a known page after `search`/`search_many`, extracting clean prose "
            "from an article, getting an outbound-link list from a hub page.\n"
            "Returns: `{title, url, excerpt, citations, links, content_type, render_mode}` plus "
            "domain and word/char counts.\n"
            "Rendered fetch is automatic for JS-heavy pages; pass `rendered=true` to force browser "
            "mode when a previous fetch came back nearly empty.\n"
            "Use `fetch_many` for multiple URLs in one call; `search_and_fetch` if you do not yet "
            "have URLs."
        ),
        annotations=READ_ONLY_FETCH,
    )
    async def fetch_url_tool(
        url: UrlParam,
        max_excerpt_chars: MaxExcerptCharsParam = None,
        max_links: MaxLinksParam = 8,
        rendered: RenderedParam = False,
        render_wait_ms: RenderWaitMsParam = None,
        ttl: TtlParam = None,
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

    @server.tool(
        name="fetch_many",
        title="Fetch Many",
        description=(
            "Fetch and extract several URLs in parallel. URLs are deduplicated after canonicalisation. "
            "Each per-source full text is preserved in hidden `_meta.pages[].full_text`.\n"
            "Use when reading a batch of search results, comparing several known sources, or building "
            "a multi-source citation set.\n"
            "Returns: per-source `{title, url, excerpt, citations, render_mode}` and aggregate "
            "stats (success_count, error_count, elapsed_ms).\n"
            "Rendered fetch is automatic for JS-heavy pages; pass `rendered=true` to force browser "
            "mode for every URL (slower).\n"
            "Use `fetch_url` for a single URL; `research` for an end-to-end multi-query workflow."
        ),
        annotations=READ_ONLY_FETCH,
    )
    async def fetch_many_tool(
        urls: UrlsParam,
        max_excerpt_chars: MaxExcerptCharsParam = None,
        max_links: MaxLinksParam = 8,
        rendered: RenderedParam = False,
        render_wait_ms: RenderWaitMsParam = None,
        concurrency: ConcurrencyParam = None,
        ttl: TtlParam = None,
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

    @server.tool(
        name="health",
        title="Health",
        description=(
            "Report backend, cache, and render-engine readiness. Takes no arguments.\n"
            "Use for a one-shot check before a session, debugging a 'search failed' result, "
            "or verifying that the SearXNG backend is reachable and that rendered fetch is available.\n"
            "Returns: `{backend, cache, render}` with status, latency, and any active fallback URLs."
        ),
        annotations=READ_ONLY_HEALTH,
    )
    async def health_tool(ctx: Context = None):  # type: ignore[assignment]
        return await service.health(ctx=ctx)

    return MCPBundle(server=server, service=service)
