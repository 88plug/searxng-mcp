# Changelog

Public release history for `searxng-mcp`. Source of truth on GitHub:
[CHANGELOG.md](https://github.com/88plug/searxng-mcp/blob/main/CHANGELOG.md).

Calver-style tags (`YYYY.M.N`), most recent first.

## 2026.6.23

### Changed

- Plugin compliance pass for the 88plug marketplace scaffold: calver `version` in
  `.claude-plugin/plugin.json`, keyword set expanded, CI/Pages workflows and
  manifest validator updated, MkDocs config hardened, `tests/smoke.sh` wiring check
  added.

## 2026.5.26

### Changed — license

- Relicensed from MIT to **FSL-1.1-ALv2** (Functional Source License, Version 1.1,
  Apache-2.0 Future License). Competing Use (offering this software or a
  substantially similar substitute as a commercial product/service) is not a
  Permitted Purpose. Each released version converts to Apache License 2.0 on the
  second anniversary of its release date. See `LICENSE`.

### Added — Claude Code plugin wrapper

- `.claude-plugin/plugin.json` declares the `searxng` plugin. Install via:
  ```text
  /plugin marketplace add 88plug/claude-code-plugins
  /plugin install searxng@88plug
  ```
- Pure MCP remains usable independently via
  `uvx --from git+https://github.com/88plug/searxng-mcp searxng-mcp`.

## 2026.5.20

### Added

- MCP server for SearXNG with `stdio` and `streamable-http` transports
- Search helpers for single-query, multi-query, and search-plus-fetch workflows
- Token-efficient tool responses with full payloads in hidden metadata
- Optional rendered fetching for JS-heavy pages
- Docker and hardened Docker deployment paths
- Benchmark tooling for latency and tool-payload checks

### Changed

- Distribution via git source (`uvx --from git+…`); no PyPI publication planned
  (bare `searxng-mcp` on PyPI is unrelated)
- LM-callability hardening: multi-paragraph tool descriptions, constrained
  `Annotated` parameters, OpenAPI 3.0-intersection schemas for broad client
  compatibility
- Tool annotations on every tool; prompt `Literal` args
- Client config docs for Claude Code, Codex CLI, gemini-cli, opencode, and
  streamable-http

### Security

- Designed for trusted self-hosting
- Arbitrary URL fetching must sit behind network controls or auth when exposed
  beyond trusted users

## 2026.5.1

Initial public release.

- FastMCP-based SearXNG MCP server
- Search, fetch, research, and health tools
- Local and container-based deployment support
- Public OSS governance files and security guidance
