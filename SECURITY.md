# Security Policy

`searxng-mcp` is designed for trusted self-hosting first.

It is not a public, unauthenticated fetch proxy.

## Threat model

The server can:

- Query a SearXNG backend.
- Fetch arbitrary `http` and `https` URLs when a client asks it to.
- Render pages in a browser for extraction when render support is enabled.
- Accept requests over `stdio` or over `streamable-http` when deployed that way.

That means the main risks are:

- SSRF through arbitrary URL fetches.
- Exposure of internal services if the server can reach them.
- Content-based abuse through hostile HTML, PDFs, or JS-heavy pages.
- Resource exhaustion from large batch searches or fetches.
- Misuse of browser rendering against untrusted remote content.

## Safe deployment scope

Recommended:

- Local developer use.
- Private team use behind trusted network boundaries.
- Self-hosted internal deployments with reverse-proxy auth or equivalent access control.

Not recommended without additional controls:

- Public internet exposure.
- Open, unauthenticated `streamable-http` access.
- Deployment on a network that can reach sensitive internal services unless URL policy is restricted.

## Self-hosting caveats

- `fetch_url` and `fetch_many` can retrieve arbitrary external content. If you expose the service, add an allowlist, block private IP ranges, or place the server behind a trusted gateway.
- Rendered fetch uses a browser. Treat rendered content as untrusted input.
- If you disable TLS verification for local/self-signed backends, only do that for private infrastructure that you control.
- Keep request limits in place if the server is shared by more than one trusted user.
- Do not run the public HTTP mode without some form of authentication or network restriction.

## Browser rendering

Rendered extraction is useful, but it expands the attack surface.

Recommended controls:

- Use the hardened container image for shared deployments.
- Run the browser as a non-root user when possible.
- Keep sandboxing enabled in environments that support it.
- Disable render support if you do not need it.

## Reporting a vulnerability

If you believe you found a security issue:

- Do not open a public issue.
- Contact the maintainers privately.
- Include the affected version, the request path, and a minimal reproduction if possible.

If you are reporting an SSRF, auth bypass, or remote code execution concern, say so explicitly in the subject line.

## Security fixes

Security fixes may be released without advance notice.
The changelog will note material security changes when they are public-safe to describe.
