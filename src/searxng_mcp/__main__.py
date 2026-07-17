from __future__ import annotations

import argparse
import asyncio
from typing import Literal, cast

from .server import create_server
from .settings import load_settings

Transport = Literal["stdio", "sse", "streamable-http"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="searxng-mcp", description="Fast token-efficient MCP server for SearXNG"
    )
    parser.add_argument(
        "--transport", choices=["stdio", "streamable-http", "sse"], default=None
    )
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument(
        "--mount-path",
        default=None,
        help="Optional path prefix for streamable-http or SSE deployments.",
    )
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--search-timeout", type=float, default=None)
    parser.add_argument("--fetch-timeout", type=float, default=None)
    parser.add_argument("--search-concurrency", type=int, default=None)
    parser.add_argument("--fetch-concurrency", type=int, default=None)
    parser.add_argument("--search-cache-ttl", type=int, default=None)
    parser.add_argument("--fetch-cache-ttl", type=int, default=None)
    return parser


def _normalize_mount_path(value: str | None) -> str | None:
    if value is None:
        return None
    mount_path = value.strip()
    if not mount_path:
        return None
    if not mount_path.startswith("/"):
        mount_path = f"/{mount_path}"
    mount_path = mount_path.rstrip("/")
    return mount_path or "/"


def _run_streamable_http_with_mount_path(bundle, settings, mount_path: str) -> None:
    from starlette.applications import Starlette
    from starlette.routing import Mount
    import uvicorn

    app = bundle.server.streamable_http_app()
    if mount_path != "/":
        app = Starlette(routes=[Mount(mount_path, app=app)])

    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    asyncio.run(server.serve())


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = load_settings()
    if args.transport:
        settings.transport = args.transport
    if args.base_url:
        settings.base_url = args.base_url
    if args.host:
        settings.host = args.host
    if args.port is not None:
        settings.port = args.port
    if args.cache_dir:
        from pathlib import Path

        settings.cache_dir = Path(args.cache_dir).expanduser()
    if args.search_timeout is not None:
        settings.search_timeout = args.search_timeout
    if args.fetch_timeout is not None:
        settings.fetch_timeout = args.fetch_timeout
    if args.search_concurrency is not None:
        settings.search_concurrency = args.search_concurrency
    if args.fetch_concurrency is not None:
        settings.fetch_concurrency = args.fetch_concurrency
    if args.search_cache_ttl is not None:
        settings.search_cache_ttl = args.search_cache_ttl
    if args.fetch_cache_ttl is not None:
        settings.fetch_cache_ttl = args.fetch_cache_ttl

    bundle = create_server(settings)
    try:
        mount_path = _normalize_mount_path(args.mount_path)
        transport = cast(Transport, settings.transport)
        if transport == "streamable-http" and mount_path:
            _run_streamable_http_with_mount_path(bundle, settings, mount_path)
        else:
            bundle.server.run(transport, mount_path=mount_path)
    finally:
        asyncio.run(bundle.service.close())


if __name__ == "__main__":
    main()
