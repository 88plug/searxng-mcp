# Changelog

All notable changes to `searxng-mcp` are documented in this file.

The project follows a simple release log:

- `Unreleased` tracks work that has landed on `main` but has not been tagged.
- Versioned sections will record shipped releases once we start publishing tags.

## Unreleased

### Added

- MCP server for SearXNG with `stdio` and `streamable-http` transports.
- Search helpers for single-query, multi-query, and search-plus-fetch workflows.
- Token-efficient tool responses with full payloads available in hidden metadata.
- Optional rendered fetching for JS-heavy pages.
- Docker and hardened Docker deployment paths for self-hosting.
- Benchmark tooling for latency and tool-payload checks.

### Changed

- Distribution is via git source (`uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp`); no PyPI publication is planned. The bare `searxng-mcp` name on PyPI is held by an unrelated project.
- LM-callability hardening across every tool: multi-paragraph descriptions following the `purpose / Best for / Returns / sibling-routing` template, per-parameter `Annotated[T, Field(description=...)]` with constraints (`Literal` enums for `time_range` and `safesearch`, numeric ranges on `pageno`/`max_results`/`fetch_limit`/`concurrency`/`ttl`, length caps on `query`/`urls`). Schemas stay inside the OpenAPI 3.0 intersection that Codex CLI, gemini-cli, opencode, and Claude Code all accept (no `$defs`/`$ref`, no `oneOf`, no nested input models). Pydantic validation now rejects invalid input with messages naming valid values, instead of silently coercing.
- Tool annotations set on every tool (`readOnlyHint=True`, `destructiveHint=False`, `openWorldHint=True` for search/fetch; `idempotentHint=True` only on the deterministic fetch tools).
- Prompt arguments use `Literal[...]` so invalid `intent`/`scope`/`depth` values raise instead of falling back silently.
- `docs/reference/client-configs.md` rewritten with copy-paste config for Claude Code, Codex CLI, gemini-cli, sst/opencode, and streamable-http.

### Security

- The server is designed for trusted self-hosting.
- Arbitrary URL fetching is available and must be protected behind network controls or an auth layer when exposed beyond trusted users.

## 0.1.0

Initial public release of `searxng-mcp`.

- FastMCP-based SearXNG MCP server
- Search, fetch, research, and health tools
- Local and container-based deployment support
- Public OSS governance files and security guidance
