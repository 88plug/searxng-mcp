# Contributing to searxng-mcp

Thanks for taking time to improve `searxng-mcp`.

This project is intentionally small in surface area and opinionated in behavior. Contributions are welcome when they make the server faster, safer, more reliable, or easier to operate.

## Before you start

- Open an issue first for anything non-trivial.
- Keep changes focused. One feature or one fix per pull request is the default.
- Do not mix unrelated refactors with behavior changes.
- If you are changing transport, fetch behavior, security policy, or packaging, include tests.

## What we care about

- Correctness under real MCP client usage.
- Low token output with complete hidden metadata.
- Deterministic, cached, and deduplicated fetch/search behavior.
- Safe self-hosting defaults.
- Clear install and deployment paths.

## Development workflow

1. Create a branch from `main`.
2. Make the smallest useful change.
3. Run the test suite locally.
4. Verify packaging if you touch distribution code.
5. Update docs if the user-facing behavior changes.

Suggested checks:

```bash
uv sync --all-groups
uv run pytest -q
uv run python -m compileall src
uv build
uv lock --upgrade --dry-run
uvx --from pip-audit pip-audit
```

If your change touches container behavior:

```bash
docker build -t searxng-mcp .
docker build -f Dockerfile.prod -t searxng-mcp:prod .
```

## Coding expectations

- Keep the code readable and explicit.
- Prefer small helper functions over large monoliths.
- Preserve the existing response shape unless a change is clearly justified.
- Do not remove hidden metadata unless there is a strong reason.
- Do not weaken security defaults to make demos easier.

## Tests

Add or update tests whenever behavior changes.

Good test targets:

- URL normalization and deduplication
- Search aggregation and ranking
- Fetch caching and render fallback
- Tool response structure
- Packaging and CLI startup

## Pull requests

A good pull request should include:

- A short summary of the problem
- What changed
- How you tested it
- Any operational or security implications

## Review standards

We review for:

- Functional correctness
- Security posture
- Impact on token usage
- Compatibility with MCP clients
- Maintenance cost

If a change introduces a tradeoff, state it directly in the PR description.
