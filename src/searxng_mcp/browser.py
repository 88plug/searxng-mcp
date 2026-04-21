from __future__ import annotations

from dataclasses import dataclass
import asyncio
from http import HTTPStatus
from shutil import which
import subprocess
import sys
import time
from typing import Any

try:  # pragma: no cover - imported defensively for incomplete installs
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    from playwright.async_api import async_playwright
except Exception:  # pragma: no cover
    async_playwright = None
    PlaywrightTimeoutError = TimeoutError

from .extract import extract_from_html
from .settings import Settings


class RenderedFetchError(RuntimeError):
    pass


@dataclass(slots=True)
class RenderedResponse:
    url: str
    final_url: str
    status_code: int
    elapsed_ms: float
    html: str
    content_type: str
    title: str | None = None


class RenderedFetchClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._startup_lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max(1, settings.render_concurrency))
        self._playwright = None
        self._browser = None
        self._context = None
        self._browser_install_attempted = False

    def _browser_executable(self) -> str | None:
        if self.settings.render_browser_path:
            return self.settings.render_browser_path
        for candidate in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
            path = which(candidate)
            if path:
                return path
        return None

    def status(self) -> dict[str, Any]:
        return {
            "playwright_installed": async_playwright is not None,
            "browser_path_configured": bool(self.settings.render_browser_path),
            "browser_executable": self._browser_executable(),
            "headless": self.settings.render_headless,
            "sandbox": self.settings.render_sandbox,
            "block_resources": self.settings.render_block_resources,
            "concurrency": self.settings.render_concurrency,
            "timeout_s": self.settings.render_timeout,
            "wait_ms": self.settings.render_wait_ms,
        }

    def _should_auto_install_browser(self, exc: Exception, *, executable_path: str | None) -> bool:
        if executable_path is not None or self._browser_install_attempted:
            return False
        message = str(exc).lower()
        return any(
            hint in message
            for hint in (
                "executable doesn't exist",
                "download new browsers",
                "playwright install",
            )
        )

    async def _install_playwright_browser(self) -> None:
        self._browser_install_attempted = True
        command = [sys.executable, "-m", "playwright", "install", "chromium"]
        try:
            # Keep browser payload in Playwright's user cache so one uvx install stays usable.
            await asyncio.to_thread(
                subprocess.run,
                command,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            output = (exc.stderr or exc.stdout or "").strip().splitlines()
            detail = f": {output[-1]}" if output else ""
            raise RenderedFetchError(f"Failed to install Chromium for rendered fetch{detail}") from exc
        except Exception as exc:  # noqa: BLE001
            raise RenderedFetchError(f"Failed to install Chromium for rendered fetch: {exc}") from exc

    async def _route_handler(self, route) -> Any:  # pragma: no cover - Playwright callback
        resource_type = route.request.resource_type
        if self.settings.render_block_resources and resource_type in {"image", "media", "font", "stylesheet"}:
            await route.abort()
            return None
        await route.continue_()
        return None

    async def _ensure_context(self):
        if self._context is not None:
            return self._context
        async with self._startup_lock:
            if self._context is not None:
                return self._context
            if async_playwright is None:
                raise RenderedFetchError(
                    "Playwright is unavailable in this install. Reinstall searxng-mcp to restore rendered fetch support."
                )
            try:
                self._playwright = await async_playwright().start()
            except Exception as exc:  # noqa: BLE001
                raise RenderedFetchError(f"Playwright is unavailable: {exc}") from exc

            browser_args = ["--disable-dev-shm-usage", "--disable-gpu"]
            if not self.settings.render_sandbox:
                browser_args.append("--no-sandbox")
            launch_kwargs: dict[str, Any] = {
                "headless": self.settings.render_headless,
                "args": browser_args,
            }
            executable_path = self._browser_executable()
            if executable_path:
                launch_kwargs["executable_path"] = executable_path

            try:
                self._browser = await self._playwright.chromium.launch(**launch_kwargs)
            except Exception as exc:  # noqa: BLE001
                if self._should_auto_install_browser(exc, executable_path=executable_path):
                    await self._install_playwright_browser()
                    try:
                        self._browser = await self._playwright.chromium.launch(**launch_kwargs)
                    except Exception as retry_exc:  # noqa: BLE001
                        await self.close()
                        raise RenderedFetchError(f"Failed to start Chromium: {retry_exc}") from retry_exc
                else:
                    await self.close()
                    raise RenderedFetchError(f"Failed to start Chromium: {exc}") from exc

            try:
                self._context = await self._browser.new_context(
                    user_agent=self.settings.mcp_user_agent,
                    viewport={"width": 1280, "height": 800},
                    java_script_enabled=True,
                    ignore_https_errors=not self.settings.fetch_verify_tls,
                )
                if self.settings.render_block_resources:
                    await self._context.route("**/*", self._route_handler)
                self._context.set_default_timeout(int(self.settings.render_timeout * 1000))
            except Exception as exc:  # noqa: BLE001
                await self.close()
                raise RenderedFetchError(f"Failed to start Chromium: {exc}") from exc

            return self._context

    async def get(self, url: str, *, wait_ms: int | None = None) -> RenderedResponse:
        limit_ms = max(0, wait_ms if wait_ms is not None else self.settings.render_wait_ms)
        async with self._semaphore:
            context = await self._ensure_context()
            page = await context.new_page()
            started = time.perf_counter()
            try:
                response = await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=int(self.settings.render_timeout * 1000),
                )
                if response is None:
                    raise RenderedFetchError(f"Rendered fetch returned no response for {url}")
                if response.status < HTTPStatus.OK or response.status >= HTTPStatus.MULTIPLE_CHOICES:
                    raise RenderedFetchError(
                        f"Rendered fetch returned HTTP {response.status} for {url}"
                    )
                if limit_ms > 0:
                    try:
                        await page.wait_for_load_state("networkidle", timeout=limit_ms)
                    except PlaywrightTimeoutError:
                        pass
                html = await page.content()
                try:
                    title = await page.title()
                except Exception:  # noqa: BLE001
                    title = None
                content_type = "text/html; charset=utf-8"
                if response is not None:
                    content_type = response.headers.get("content-type", content_type)
                extracted = extract_from_html(
                    html,
                    url=url,
                    final_url=page.url,
                    content_type=content_type,
                    max_excerpt_chars=1,
                    max_links=0,
                    rendered=True,
                )
                return RenderedResponse(
                    url=url,
                    final_url=page.url,
                    status_code=response.status,
                    elapsed_ms=(time.perf_counter() - started) * 1000,
                    html=html,
                    content_type=content_type,
                    title=title or extracted.title,
                )
            except Exception as exc:  # noqa: BLE001
                raise RenderedFetchError(f"Rendered fetch failed for {url}: {exc}") from exc
            finally:
                await page.close()

    async def close(self) -> None:
        if self._context is not None:
            try:
                await self._context.close()
            finally:
                self._context = None
        if self._browser is not None:
            try:
                await self._browser.close()
            finally:
                self._browser = None
        if self._playwright is not None:
            try:
                await self._playwright.stop()
            finally:
                self._playwright = None
