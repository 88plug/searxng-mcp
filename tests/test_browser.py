from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

from searxng_mcp.browser import RenderedFetchClient
from searxng_mcp.settings import Settings


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        base_url="http://searx.local",
        fallback_base_urls=(),
        transport="stdio",
        host="127.0.0.1",
        port=8811,
        search_timeout=5.0,
        fetch_timeout=5.0,
        search_concurrency=4,
        fetch_concurrency=2,
        search_cache_ttl=60,
        fetch_cache_ttl=60,
        cache_dir=tmp_path / "cache",
        cache_size_limit=32 * 1024 * 1024,
        default_language="en",
        default_categories="general",
        default_safesearch=0,
        default_max_results=5,
        default_excerpt_chars=300,
        search_connections=8,
        search_keepalive=4,
        fetch_connections=4,
        fetch_keepalive=2,
        fetch_verify_tls=True,
        render_timeout=10.0,
        render_wait_ms=1000,
        render_concurrency=2,
        render_headless=True,
        render_browser_path="",
        render_sandbox=False,
        render_block_resources=True,
        render_auto_fallback=True,
        render_auto_min_words=60,
        render_auto_min_chars=800,
        trust_env=False,
        user_agent="searxng-mcp-test",
    )


class FakeContext:
    def __init__(self) -> None:
        self.timeout_ms: int | None = None
        self.routes: list[str] = []

    async def route(self, pattern: str, _handler) -> None:
        self.routes.append(pattern)

    def set_default_timeout(self, timeout_ms: int) -> None:
        self.timeout_ms = timeout_ms

    async def close(self) -> None:
        return None


class FakeBrowser:
    def __init__(self) -> None:
        self.contexts: list[FakeContext] = []

    async def new_context(self, **_kwargs) -> FakeContext:
        context = FakeContext()
        self.contexts.append(context)
        return context

    async def close(self) -> None:
        return None


class FakeChromium:
    def __init__(self) -> None:
        self.launch_calls = 0

    async def launch(self, **_kwargs) -> FakeBrowser:
        self.launch_calls += 1
        if self.launch_calls == 1:
            raise RuntimeError(
                "BrowserType.launch: Executable doesn't exist at /tmp/ms-playwright/chromium\n"
                "Please run the following command to download new browsers: playwright install"
            )
        return FakeBrowser()


class FakePlaywrightRuntime:
    def __init__(self) -> None:
        self.chromium = FakeChromium()

    async def stop(self) -> None:
        return None


class FakePlaywrightStarter:
    def __init__(self, runtime: FakePlaywrightRuntime) -> None:
        self.runtime = runtime

    async def start(self) -> FakePlaywrightRuntime:
        return self.runtime


def test_render_client_auto_installs_playwright_browser(
    tmp_path: Path, monkeypatch
) -> None:
    from searxng_mcp import browser as browser_module

    runtime = FakePlaywrightRuntime()
    install_calls: list[list[str]] = []

    def fake_async_playwright() -> FakePlaywrightStarter:
        return FakePlaywrightStarter(runtime)

    def fake_run(
        command: list[str], *, check: bool, capture_output: bool, text: bool
    ) -> subprocess.CompletedProcess[str]:
        assert check is True
        assert capture_output is True
        assert text is True
        install_calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(browser_module, "async_playwright", fake_async_playwright)
    monkeypatch.setattr(browser_module, "which", lambda _name: None)
    monkeypatch.setattr(browser_module.subprocess, "run", fake_run)

    client = RenderedFetchClient(make_settings(tmp_path))
    context = asyncio.run(client._ensure_context())

    assert context.timeout_ms == 10000
    assert context.routes == ["**/*"]
    assert runtime.chromium.launch_calls == 2
    assert install_calls == [
        [sys.executable, "-m", "playwright", "install", "chromium"]
    ]

    asyncio.run(client.close())
