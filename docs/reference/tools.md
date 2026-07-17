# Tool Reference

Seven MCP tools. All search/fetch tools return **compact visible output**; richer
payloads sit in hidden `_meta` when the client supports it.

Server instructions tell the model to pick tools autonomously. Use this page for
parameter names, defaults, and constraints.

## Routing cheat sheet

| Need | Tool |
| --- | --- |
| One query, ranked hits | `search` |
| Several phrasings, merged ranking | `search_many` |
| One query + page excerpts | `search_and_fetch` |
| Multi-query + fetch + citations | `research` |
| One known URL | `fetch_url` |
| Many known URLs | `fetch_many` |
| Backend / cache / render check | `health` |

Rendered fetch is **automatic** for weak/JS-heavy HTML. Pass `rendered=true` only
to force browser mode (slower).

---

## `search`

Single-query SearXNG search. Compact ranked hits; full SearXNG payload in
`_meta.raw_payload`.

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `query` | string | required | 1–400 chars; SearXNG bangs (`!wikipedia foo`) work |
| `categories` | string | server default | Comma-separated (e.g. `general`, `news`, `science`) |
| `engines` | string | backend default | Comma-separated engine names |
| `enabled_engines` | string | — | Extra engines to enable |
| `disabled_engines` | string | — | Engines to exclude |
| `language` | string | server default | BCP-47 (`en`, `de`, `all`, …) |
| `pageno` | int | `1` | 1–20 |
| `time_range` | string | — | `day` \| `week` \| `month` \| `year` |
| `safesearch` | int | server default | `0` off, `1` moderate, `2` strict |
| `max_results` | int | server default (5) | 1–50 visible hits |
| `ttl` | int | server default | Cache TTL seconds; `0` disables; max 86400 |

**Returns:** ranked `{title, url, domain, snippet, engine, score}` plus answers,
infoboxes, suggestions when SearXNG provides them.

---

## `search_many`

Parallel search across query variants; merge + dedupe into one ranked list.

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `queries` | string[] | required | 1–10 distinct phrasings/angles |
| `concurrency` | int | server default | 1–16 parallel backend requests |
| `ttl` | int | server default | Cache TTL override |
| *(filters)* | | | Same SearXNG filters as `search` |

**Returns:** merged hits with per-hit `queries`, `engines`, `hit_count`,
`merged_score`. Per-query raw payloads in `_meta`.

---

## `search_and_fetch`

Search one query, then fetch+extract the top hits in one call.

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `query` | string | required | Same rules as `search` |
| `fetch_limit` | int | `3` | 1–20 pages to extract |
| `fetch_excerpt_chars` | int | server default | 200–20000 per-source excerpt |
| `rendered` | bool | `false` | Force browser render |
| `render_wait_ms` | int | server default | Extra wait after DOM load (0–15000) |
| `ttl` | int | server default | Cache TTL override |
| *(filters)* | | | Same SearXNG filters as `search` |

**Returns:** search summary plus per-source
`{title, url, excerpt, citations, render_mode}`. Full text in `_meta`.

---

## `research`

Multi-query search → merge/dedupe → fetch strongest sources with citations.

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `queries` | string[] | required | 1–10 queries |
| `fetch_limit` | int | `3` | 1–20 pages to extract |
| `fetch_excerpt_chars` | int | server default | 200–20000 |
| `rendered` | bool | `false` | Force browser render |
| `render_wait_ms` | int | server default | 0–15000 |
| `concurrency` | int | server default | 1–16 |
| `ttl` | int | server default | Cache TTL override |
| *(filters)* | | | Same SearXNG filters as `search` |

**Returns:** merged ranking, per-source excerpts/citations, query map. Full
payloads in `_meta`.

---

## `fetch_url`

Fetch one URL; Readability-style extract; compact excerpt + links.

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `url` | string | required | Absolute `http(s)`; bare domains get `https://` |
| `max_excerpt_chars` | int | server default | 200–50000 visible excerpt |
| `max_links` | int | `8` | 0–64 outbound links in visible output |
| `rendered` | bool | `false` | Force browser render |
| `render_wait_ms` | int | server default | 0–15000 |
| `ttl` | int | server default | Cache TTL; `0` disables |

**Returns:** `{title, url, excerpt, citations, links, content_type, render_mode}`
plus domain and word/char counts. Full text in `_meta.full_text`.

---

## `fetch_many`

Fetch several URLs in parallel. URLs are deduped after canonicalisation.

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `urls` | string[] | required | 1–20 absolute `http(s)` URLs |
| `max_excerpt_chars` | int | server default | 200–50000 |
| `max_links` | int | `8` | 0–64 |
| `rendered` | bool | `false` | Force render for every URL (slower) |
| `render_wait_ms` | int | server default | 0–15000 |
| `concurrency` | int | server default | 1–16 |
| `ttl` | int | server default | Cache TTL override |

**Returns:** per-source excerpts plus aggregate
`success_count` / `error_count` / `elapsed_ms`. Full texts in `_meta.pages[]`.

---

## `health`

No arguments. Backend, cache, and render-engine readiness.

**Returns:** `{backend, cache, render}` with status, latency, and active fallback
URLs when configured.

Use before a session, after deploy, or when search fails unexpectedly.

---

## Resources

| URI | Content |
| --- | --- |
| `searxng://config` | Machine-readable settings, transport, render capability |
| `searxng://guide` | Built-in workflow guide for tool selection |

## Prompts

Compatibility helpers for clients that surface MCP prompts. Primary interface is
still tools.

| Prompt | Role |
| --- | --- |
| `quick_lookup` | Direct fact / short lookup framing |
| `deep_research` | Multi-source research framing |
| `research_workflow` | Router: `quick` vs `broad`/`deep` |

## Annotations

| Family | Hints |
| --- | --- |
| Search tools | `readOnlyHint`, `openWorldHint`; not idempotent |
| Fetch tools | `readOnlyHint`, `openWorldHint`, `idempotentHint` |
| `health` | `readOnlyHint` |

All tools set `destructiveHint=false`.
