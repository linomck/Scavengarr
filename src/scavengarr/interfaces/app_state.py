"""Application state container for FastAPI dependency injection."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from starlette.datastructures import State

from scavengarr.application.factories import CrawlJobFactory
from scavengarr.infrastructure.circuit_breaker import PluginCircuitBreaker
from scavengarr.infrastructure.config import AppConfig
from scavengarr.infrastructure.graceful_shutdown import GracefulShutdown

if TYPE_CHECKING:
    import asyncio
    import logging

    from scavengarr.application.use_cases.stremio_catalog import StremioCatalogUseCase
    from scavengarr.application.use_cases.stremio_links import StremioLinks
    from scavengarr.application.use_cases.stremio_stream import StremioStreamUseCase
    from scavengarr.domain.ports import (
        CachePort,
        CrawlJobRepository,
        PluginRegistryPort,
        PluginScoreStorePort,
        SearchEnginePort,
        StreamLinkRepository,
    )
    from scavengarr.domain.ports.anime_ids import AnimeIdResolverPort
    from scavengarr.domain.ports.series_meta import SeriesMetaPort
    from scavengarr.domain.ports.tmdb import TmdbClientPort
    from scavengarr.infrastructure.browser.shared_browser import SharedBrowserPool
    from scavengarr.infrastructure.browser.stealth_pool import StealthPool
    from scavengarr.infrastructure.concurrency import ConcurrencyPool
    from scavengarr.infrastructure.hoster_resolvers import HosterResolverRegistry
    from scavengarr.infrastructure.hoster_resolvers.state_store import (
        HosterStateStore,
    )
    from scavengarr.infrastructure.network_probe import NetworkProbe
    from scavengarr.infrastructure.plugins.health_monitor import PluginHealthMonitor
    from scavengarr.infrastructure.plugins.history import PluginHistory
    from scavengarr.infrastructure.scoring.scheduler import ScoringScheduler
    from scavengarr.infrastructure.stremio.hls_proxy import SegmentReadAhead
    from scavengarr.infrastructure.telemetry import Telemetry


class AppState(State):
    """FastAPI application state with all DI resources.

    Lifecycle managed by composition.py::lifespan().
    """

    # Configuration
    config: AppConfig

    # Infrastructure
    cache: CachePort
    http_client: httpx.AsyncClient

    # Domain Ports
    plugins: PluginRegistryPort
    search_engine: SearchEnginePort
    crawljob_repo: CrawlJobRepository
    stream_link_repo: StreamLinkRepository

    # Application Services
    crawljob_factory: CrawlJobFactory

    # Hoster resolution
    hoster_resolver_registry: HosterResolverRegistry
    # Its resolutions and the open circuit breakers across restarts
    hoster_state_store: HosterStateStore

    # Playwright shared browser pool (single Chromium for all PW plugins)
    shared_browser_pool: SharedBrowserPool | None

    # Playwright Stealth pool (optional — for CF bypass probing)
    stealth_pool: StealthPool | None

    # Metrics of the core's stages (/metrics, /api/v1/stats/metrics)
    telemetry: Telemetry

    # Stremio (optional — requires TMDB API key)
    tmdb_client: TmdbClientPort | None
    # The Anime Kitsu addon's ids translated into IMDb requests
    anime_ids: AnimeIdResolverPort
    # The catalog's record of a title (Cinemeta): its kind and episodes
    series_meta: SeriesMetaPort
    stremio_stream_uc: StremioStreamUseCase | None
    stremio_catalog_uc: StremioCatalogUseCase | None
    # The stored links behind /play and the HLS proxy
    stremio_links: StremioLinks
    # The HLS proxy's segments fetched ahead of the player
    hls_read_ahead: SegmentReadAhead

    # Global concurrency pool (fair-share httpx + PW slots)
    concurrency_pool: ConcurrencyPool | None

    # Circuit breaker (skip plugins after consecutive failures)
    circuit_breaker: PluginCircuitBreaker

    # Graceful shutdown (request tracking + drain)
    graceful_shutdown: GracefulShutdown

    # Readiness beyond the startup: the cache backend and the DNS (readyz)
    network_probe: NetworkProbe

    # Plugin scoring (optional — requires scoring.enabled=True)
    plugin_score_store: PluginScoreStorePort | None
    scoring_scheduler: ScoringScheduler | None
    _scoring_task: asyncio.Task[None] | None

    # Checks of the Stremio plugins' sites (optional: off when the
    # stremio.plugin_health_interval_seconds is 0)
    plugin_health: PluginHealthMonitor | None
    _plugin_health_task: asyncio.Task[None] | None
    # The plugins' long-term record (searches, results, timeouts, checks,
    # unreachable marks per day), in the cache across restarts
    plugin_history: PluginHistory

    # Event-loop lag monitor (feeds telemetry)
    _loop_lag_task: asyncio.Task[None]
    _feed_log_handler: logging.Handler

    # Adapts the stealth browser's page limit (PageBudget)
    _page_budget_task: asyncio.Task[None]

    # Launches the stealth browser after the app reported ready
    _browser_warmup_task: asyncio.Task[None]

    # Captures a Filemoon link once the kept captcha pass has gone (PassKeeper)
    _pass_keeper_task: asyncio.Task[None]
