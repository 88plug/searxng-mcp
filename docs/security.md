# Security

`searxng-mcp` is designed for trusted MCP clients and private or internal deployment.

It is not a public internet search proxy by default.

## Threat Model

The main risk is arbitrary URL fetching through `fetch_url` and `fetch_many`.

That means a deployment can be used to:

- probe public URLs
- probe internal URLs if you do not restrict them
- spend browser or network resources on attacker-controlled targets

If you expose `streamable-http`, treat it like a service endpoint and put it behind auth or a reverse proxy.

## SSRF Risk

The fetch tools accept user-provided URLs.

If your deployment is reachable by untrusted users, add URL policy controls before exposing it:

- block localhost
- block private IP ranges
- block link-local addresses
- block metadata service ranges
- consider an allowlist for approved domains

## Browser Rendering

Rendered fetch is useful for JavaScript-heavy pages, but it expands the attack surface.

Safe defaults to keep in mind:

- run the browser as a non-root user
- enable the Chromium sandbox when possible
- keep resource blocking enabled unless a page needs extra assets
- keep render concurrency low enough to avoid noisy failures

## TLS Verification

`SEARXNG_MCP_FETCH_VERIFY_TLS=0` is for private or self-signed backend setups only.

Do not disable TLS verification for normal internet-facing fetches unless you fully understand the risk.

## Deployment Guidance

Use this service in one of these modes:

- local `stdio` for a single user
- private LAN deployment behind access control
- reverse-proxied HTTP with authentication

Avoid:

- unauthenticated public HTTP exposure
- browser rendering on untrusted public traffic without hardening
- turning off TLS verification on general-purpose deployments

## Suggested Baseline

- use the hardened container for self-hosting
- run as non-root
- keep browser sandboxing enabled
- keep SearXNG on a trusted network
- use fallback backends only if you control all of them
