# Changelog

All notable changes to `searxng-mcp` are documented in this file.

The project follows a calver release log (`YYYY.M.N`), most recent first.

## 2026.6.23

### Changed

- Plugin compliance pass for the 88plug marketplace scaffold: `version`
  (calver) added to `.claude-plugin/plugin.json`, keyword set expanded to the
  required 20 (base set + MCP triad + niche tags), CI/Pages workflows and the
  manifest validator brought up to current action versions, MkDocs config
  hardened (`md_in_html`, `site_url`/`repo_url`/`repo_name`/`edit_uri`), and a
  `tests/smoke.sh` wiring check added.

## 2026.5.26

### Changed — license

- **Relicensed from MIT to `FSL-1.1-ALv2`** (Functional Source License,
  Version 1.1, Apache-2.0 Future License). Source remains visible;
  redistribution and modification remain permitted for any Permitted Purpose.
  A Competing Use — offering searxng-mcp (or a substantially similar
  substitute) as a commercial product or service — is no longer a Permitted
  Purpose. Each released version automatically converts to the Apache License
  2.0 on the second anniversary of its release date. See [`LICENSE.md`](./LICENSE.md).
- `LICENSE` (MIT) removed in favor of `LICENSE.md` (FSL-1.1-ALv2).
- `pyproject.toml` license expression updated to `LicenseRef-FSL-1.1-ALv2`
  (PEP 639); `license-files = ["LICENSE.md"]`; `setuptools>=77`.

### Added — Claude Code plugin wrapper

- `.claude-plugin/plugin.json` declares this repo as a Claude Code plugin
  named `searxng`. Users can install via:
  ```
  /plugin marketplace add 88plug/claude-code-plugins
  /plugin install searxng@88plug
  ```
- The plugin invokes the pure MCP server via `uvx --from git+...` so no
  separate install step is needed for users with `uv` installed.
- The underlying pure MCP remains independently usable for non-Claude-Code
  clients (Cline, Cursor, Continue, Codex, etc.) via the existing
  `uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp`
  invocation.

## 2026.5.20

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

## 2026.5.1

Initial public release of `searxng-mcp`.

- FastMCP-based SearXNG MCP server
- Search, fetch, research, and health tools
- Local and container-based deployment support
- Public OSS governance files and security guidance
