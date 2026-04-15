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

### Security

- The server is designed for trusted self-hosting.
- Arbitrary URL fetching is available and must be protected behind network controls or an auth layer when exposed beyond trusted users.

## 0.1.0

Initial public release of `searxng-mcp`.

- FastMCP-based SearXNG MCP server
- Search, fetch, research, and health tools
- Local and container-based deployment support
- Public OSS governance files and security guidance
