# Benchmarks

`searxng-mcp` includes a benchmark harness so you can measure backend latency, tool-layer latency, cache effects, and visible token counts.

## What It Measures

- direct SearXNG backend search time
- `search`
- `search_many`
- `research`
- `fetch_url`
- `fetch_many`
- cold cache and warm cache runs
- visible token count in the model-facing text

## Run It

```bash
searxng-mcp-bench --rounds 3 --max-results 5
```

If your fetch target should be different:

```bash
searxng-mcp-bench \
  --rounds 3 \
  --max-results 5 \
  --fetch-url https://docs.python.org/3/library/asyncio-task.html
```

## How To Read The Output

Look for:

- low backend search latency
- low visible token counts for common requests
- large cold-to-warm improvement when cache hits are working
- stable `fetch_many` and `research` timings under concurrency

## Practical Interpretation

- high backend latency usually means the SearXNG instance or its upstream engines are slow
- high tool-layer latency usually means fetch or render work is dominating
- high visible token counts mean your prompt shaping needs tightening

## Why This Matters

The benchmark helps answer a practical question:

can the server stay fast while still returning enough detail for a model to act on?
