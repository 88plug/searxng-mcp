# FAQ

## Do I need SearXNG running locally?

Yes. `searxng-mcp` is an MCP layer over a SearXNG backend.

## Can I run it without Docker?

Yes. Use `stdio` locally or install the Python package directly.

## Does it support rendered pages?

Yes. Rendered fetch is automatic for weak HTML pages and can be forced with `rendered=True`.

## Is rendered fetch always enabled?

Yes for installs, conditional at runtime. `searxng-mcp` includes Playwright by default and uses local Chromium or Chrome when present. If not, the first rendered fetch downloads Playwright Chromium into the user cache.

## Can this be exposed publicly?

Not by default.

It should be treated as a trusted-service deployment with auth or a reverse proxy if you expose `streamable-http`.

## Why are there prompts if the AI client drives MCP?

The prompts are compatibility helpers for clients that can surface them.

The primary interface is still tools.

## Why use `search_many` instead of just `search`?

`search_many` widens coverage before deduping results.

It is the right choice when one query is too narrow or ambiguous.

## Why use `research` instead of `search_many`?

Use `research` when you want merged search results plus fetched sources and citations in one workflow.

## Why does the server keep raw payloads hidden?

So the model sees a compact answer while the full data remains available to capable clients.

## What is the default transport?

`stdio`.

That is the best local default and the safest onboarding path.
