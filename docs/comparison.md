# Comparison

`searxng-mcp` is built to be an opinionated, research-oriented SearXNG MCP server.

The goal is not to be the smallest wrapper.

The goal is to combine search, fetch, caching, render fallback, and low-token output in one package.

## How It Compares

- `ihor-sokoliuk/mcp-searxng`: strong exact-match baseline with the core MCP shape
- `jae-jae/searxng-mul-mcp`: strong multi-query search throughput baseline
- `OvertliDS/mcp-searxng-enhanced`: enrichment and scraping-oriented baseline
- `tisDDM/searxng-mcp`: public-instance convenience baseline
- `SecretiveShell/MCP-searxng`: minimal wrapper baseline

## What `searxng-mcp` Adds

- `stdio` and `streamable-http`
- `search_many`
- `search_and_fetch`
- `research`
- `fetch_many`
- compact visible output with hidden raw payloads
- cache-backed repeated use
- automatic render fallback
- rendered fetch controls
- benchmark tooling
- docs-site ready structure

## Why That Matters

This shape is better when you want:

- one repo for local use and deployment
- a fast first answer and enough detail for follow-up work
- lower token consumption than raw search dumps
- a clearer path from search to source verification

## Tradeoff

The project is opinionated.

It favors one integrated workflow over a large grab bag of unrelated search features.
