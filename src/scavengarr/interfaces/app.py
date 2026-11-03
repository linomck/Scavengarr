"""FastAPI application factory (create_app)."""

from __future__ import annotations

import asyncio
import secrets
import time
from collections.abc import Awaitable, Callable
from urllib.parse import parse_qsl, urlencode

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.responses import Response

from scavengarr.infrastructure.config import AppConfig
from scavengarr.infrastructure.graceful_shutdown import GracefulShutdown
from scavengarr.infrastructure.network_probe import NetworkProbe
from scavengarr.infrastructure.telemetry import CONTENT_TYPE, Telemetry
from scavengarr.infrastructure.version import APP_VERSION, build_identity
from scavengarr.interfaces.api.middleware import RateLimitMiddleware
from scavengarr.interfaces.app_state import AppState
from scavengarr.interfaces.composition import lifespan

log = structlog.get_logger(__name__)

# Torznab's query parameters, the only ones whose values are logged
_TORZNAB_PATH = "/api/v1/torznab/"
_TORZNAB_KEYS = frozenset({"t", "q", "cat", "extended", "offset", "limit"})


def create_app(config: AppConfig) -> FastAPI:
    """Create FastAPI app — configuration ONLY, NO resource initialization.

    Resources (HTTP client, cache, plugins) are created in lifespan().
    """
    app = FastAPI(
        title="Scavengarr",
        description="Prowlarr-compatible Torznab/Newznab indexer",
        version=APP_VERSION,
        lifespan=lifespan,
    )

    app.state = AppState()
    app.state.config = config
    app.state.graceful_shutdown = GracefulShutdown()

    # API rate limiting (per-IP sliding window)
    if config.api_rate_limit_rpm > 0:
        app.add_middleware(
            RateLimitMiddleware, requests_per_minute=config.api_rate_limit_rpm
        )

    from scavengarr.interfaces.api.dashboard import router as dashboard_router
    from scavengarr.interfaces.api.download.router import router as download_router
    from scavengarr.interfaces.api.stats import router as stats_router
    from scavengarr.interfaces.api.stremio import router as stremio_router
    from scavengarr.interfaces.api.torznab import router as torznab_router

    app.include_router(download_router, prefix="/api/v1")
    app.include_router(torznab_router, prefix="/api/v1")
    app.include_router(stremio_router, prefix="/api/v1")
    app.include_router(stats_router, prefix="/api/v1")
    app.include_router(dashboard_router)

    @app.get("/api/v1/healthz")
    async def healthz() -> dict[str, str | int | list[str]]:
        """Liveness probe — returns 200 as long as the process is running.

        Also names the build (version, commit, build time).
        """
        state = app.state
        plugins = getattr(state, "plugins", None)
        registry = getattr(state, "hoster_resolver_registry", None)
        return {
            "status": "ok",
            **build_identity(),
            "plugins": len(plugins.list_names()) if plugins else 0,
            "hosters": registry.supported_hosters if registry else [],
        }

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        """Prometheus metrics, rendered in a worker thread (a few ms of CPU
        that would otherwise hold the event loop)."""
        telemetry: Telemetry = app.state.telemetry
        body = await asyncio.to_thread(telemetry.render)
        return Response(body, media_type=CONTENT_TYPE)

    @app.get("/api/v1/readyz")
    async def readyz() -> Response:
        """Readiness probe — 200 after startup complete, 503 before it and
        at the shutdown, and 503 while the network is lost: the cache
        backend and the DNS have failed for over 5 min (``NetworkProbe``)."""
        gs: GracefulShutdown = app.state.graceful_shutdown
        if not gs.is_ready:
            return JSONResponse({"status": "not_ready"}, status_code=503)
        probe: NetworkProbe = app.state.network_probe
        if await probe.lost():
            return JSONResponse(
                {"status": "not_ready", "reason": "network"}, status_code=503
            )
        return JSONResponse({"status": "ready"}, status_code=200)

    @app.middleware("http")
    async def log_requests(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ):
        gs: GracefulShutdown = app.state.graceful_shutdown
        gs.request_started()
        start = time.perf_counter()
        # Every log line of the request, and of the tasks it starts (a shared
        # search, background resolutions), carries its id. Generated: a
        # client's own X-Request-ID would be untrusted input in the logs
        request_id = secrets.token_hex(6)
        tokens = structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            gs.request_finished()
            duration_ms = (time.perf_counter() - start) * 1000.0
            status_code = getattr(locals().get("response", None), "status_code", 500)

            log.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                query=loggable_query(request.url.path, request.url.query),
                status_code=status_code,
                duration_ms=round(duration_ms, 2),
                client_host=(request.client.host if request.client else None),
            )
            structlog.contextvars.reset_contextvars(**tokens)

    return app


def loggable_query(path: str, query: str) -> str:
    """*query* as the access log shows it: other values masked.

    Only the Torznab API's own parameters keep their values, on its paths:
    Prowlarr sends its apikey, and proxied HLS paths carry the CDN's tokens
    and the client's address (``i=``), also under the names ``t`` and ``q``.
    """
    keep = _TORZNAB_KEYS if path.startswith(_TORZNAB_PATH) else frozenset()
    pairs = parse_qsl(query, keep_blank_values=True)
    return urlencode([(k, v if k in keep else "***") for k, v in pairs], safe="*")
