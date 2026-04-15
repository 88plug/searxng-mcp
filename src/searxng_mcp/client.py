from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import time

import httpx

from .settings import Settings


class BackendRequestError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        url: str | None = None,
        status_code: int | None = None,
        body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.url = url
        self.status_code = status_code
        self.body = body


@dataclass(slots=True)
class BackendResponse:
    backend_url: str
    url: str
    status_code: int
    elapsed_ms: float
    payload: dict[str, Any]


@dataclass(slots=True)
class FetchResponse:
    url: str
    status_code: int
    elapsed_ms: float
    response: httpx.Response


def _is_valid_search_payload(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False

    results = payload.get("results")
    if not isinstance(results, list):
        return False
    if any(not isinstance(item, dict) for item in results):
        return False

    for key in ("answers", "corrections", "infoboxes", "suggestions", "unresponsive_engines"):
        value = payload.get(key)
        if value is not None and not isinstance(value, list):
            return False
    return True


def _should_fallback(error: BackendRequestError) -> bool:
    message = str(error).lower()
    if "non-json" in message or "malformed" in message or "unexpected search payload" in message:
        return True
    if error.status_code is None:
        return True
    return error.status_code in {403, 404, 408, 425, 429} or error.status_code >= 500


class SearxngClient:
    def __init__(self, settings: Settings, *, transport: Any | None = None) -> None:
        limits = httpx.Limits(
            max_connections=settings.search_connections,
            max_keepalive_connections=settings.search_keepalive,
        )
        timeout = httpx.Timeout(settings.search_timeout, connect=min(settings.search_timeout, 5.0))
        headers = {
            "Accept": "application/json",
            "User-Agent": settings.mcp_user_agent,
        }
        base_urls = [settings.normalized_base_url, *settings.normalized_fallback_base_urls]
        self._backends: list[tuple[str, httpx.AsyncClient]] = []
        seen: set[str] = set()
        for base_url in base_urls:
            if base_url in seen:
                continue
            seen.add(base_url)
            self._backends.append(
                (
                    base_url,
                    httpx.AsyncClient(
                        base_url=base_url,
                        follow_redirects=True,
                        headers=headers,
                        limits=limits,
                        timeout=timeout,
                        trust_env=settings.trust_env,
                        http2=True,
                        transport=transport,
                    ),
                )
            )

    @staticmethod
    def _clean_params(params: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in params.items() if value not in (None, "", [], ())}

    async def _search_on_backend(self, backend_url: str, client: httpx.AsyncClient, params: dict[str, Any]) -> BackendResponse:
        cleaned = self._clean_params(params)
        started = time.perf_counter()
        response = await client.get("/search", params=cleaned)
        elapsed_ms = (time.perf_counter() - started) * 1000
        if response.status_code >= 400:
            raise BackendRequestError(
                f"SearXNG search failed with HTTP {response.status_code}",
                url=str(response.request.url),
                status_code=response.status_code,
                body=response.text[:1200],
            )
        try:
            payload = response.json()
        except Exception as exc:  # noqa: BLE001
            raise BackendRequestError(
                f"SearXNG returned non-JSON search response: {exc!r}",
                url=str(response.request.url),
                status_code=response.status_code,
                body=response.text[:1200],
            ) from exc
        if not _is_valid_search_payload(payload):
            raise BackendRequestError(
                "SearXNG returned a malformed search payload",
                url=str(response.request.url),
                status_code=response.status_code,
                body=response.text[:1200],
            )
        return BackendResponse(
            backend_url=backend_url,
            url=str(response.request.url),
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
            payload=payload,
        )

    async def search(self, params: dict[str, Any]) -> BackendResponse:
        errors: list[BackendRequestError] = []
        for backend_url, client in self._backends:
            try:
                return await self._search_on_backend(backend_url, client, params)
            except BackendRequestError as exc:
                errors.append(exc)
                if not _should_fallback(exc):
                    raise
        if errors:
            message = "; ".join(str(error) for error in errors)
            raise BackendRequestError(f"SearXNG search failed across backends: {message}")
        raise BackendRequestError("SearXNG search failed: no backends configured")

    async def _ping_backend(self, backend_url: str, client: httpx.AsyncClient) -> BackendResponse:
        started = time.perf_counter()
        response = await client.get("/")
        elapsed_ms = (time.perf_counter() - started) * 1000
        if response.status_code >= 400:
            raise BackendRequestError(
                f"SearXNG ping failed with HTTP {response.status_code}",
                url=str(response.request.url),
                status_code=response.status_code,
                body=response.text[:1200],
            )
        return BackendResponse(
            backend_url=backend_url,
            url=str(response.request.url),
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
            payload={},
        )

    async def ping(self) -> BackendResponse:
        errors: list[BackendRequestError] = []
        for backend_url, client in self._backends:
            try:
                return await self._ping_backend(backend_url, client)
            except BackendRequestError as exc:
                errors.append(exc)
                if not _should_fallback(exc):
                    raise
        if errors:
            message = "; ".join(str(error) for error in errors)
            raise BackendRequestError(f"SearXNG ping failed across backends: {message}")
        raise BackendRequestError("SearXNG ping failed: no backends configured")

    async def close(self) -> None:
        for _, client in self._backends:
            await client.aclose()


class FetchClient:
    def __init__(self, settings: Settings) -> None:
        limits = httpx.Limits(
            max_connections=settings.fetch_connections,
            max_keepalive_connections=settings.fetch_keepalive,
        )
        timeout = httpx.Timeout(settings.fetch_timeout, connect=min(settings.fetch_timeout, 5.0))
        self._client = httpx.AsyncClient(
            follow_redirects=True,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.5",
                "User-Agent": settings.mcp_user_agent,
            },
            limits=limits,
            timeout=timeout,
            trust_env=settings.trust_env,
            verify=settings.fetch_verify_tls,
            http2=True,
        )

    async def get(self, url: str) -> FetchResponse:
        started = time.perf_counter()
        response = await self._client.get(url)
        elapsed_ms = (time.perf_counter() - started) * 1000
        if response.status_code >= 400:
            raise BackendRequestError(
                f"Fetch failed with HTTP {response.status_code}",
                url=str(response.request.url),
                status_code=response.status_code,
                body=response.text[:1200],
            )
        return FetchResponse(
            url=str(response.request.url),
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
            response=response,
        )

    async def close(self) -> None:
        await self._client.aclose()
