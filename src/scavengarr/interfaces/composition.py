"""Composition root: dependency injection via FastAPI lifespan."""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from functools import partial
from typing import cast
from urllib.parse import urlparse

import httpx
import structlog
from fastapi import FastAPI

from scavengarr.application.factories import CrawlJobFactory
from scavengarr.application.use_cases.stremio_catalog import StremioCatalogUseCase
from scavengarr.application.use_cases.stremio_links import StremioLinks
from scavengarr.application.use_cases.stremio_stream import StremioStreamUseCase
from scavengarr.domain.entities.crawljob import Priority
from scavengarr.domain.ports.browser_fetcher import BrowserFetcherPort
from scavengarr.domain.ports.cache import CachePort
from scavengarr.domain.ports.hoster_resolver import HosterResolverPort
from scavengarr.domain.ports.tmdb import TmdbClientPort
from scavengarr.infrastructure.anime.id_lists import AnimeIdLists
from scavengarr.infrastructure.anime.kitsu_addon import KitsuAddonClient
from scavengarr.infrastructure.anime.resolver import KitsuAnimeIdResolver
from scavengarr.infrastructure.browser.clearance_store import ClearanceStore
from scavengarr.infrastructure.browser.page_budget import PageBudget
from scavengarr.infrastructure.browser.page_gate import PageGate
from scavengarr.infrastructure.browser.shared_browser import SharedBrowserPool
from scavengarr.infrastructure.browser.solver_fetcher import (
    ChainedBrowserFetcher,
    SolverFetcher,
)
from scavengarr.infrastructure.browser.stealth_pool import StealthPool
from scavengarr.infrastructure.cache.cache_factory import create_cache
from scavengarr.infrastructure.circuit_breaker import PluginCircuitBreaker
from scavengarr.infrastructure.common.private_address_guard import (
    GuardedTransport,
    PrivateAddressGuard,
)
from scavengarr.infrastructure.common.rate_limiter import DomainRateLimiter
from scavengarr.infrastructure.common.retry_transport import RetryTransport
from scavengarr.infrastructure.concurrency import ConcurrencyPool
from scavengarr.infrastructure.config.load import changed_values
from scavengarr.infrastructure.config.schema import AppConfig
from scavengarr.infrastructure.hoster_resolvers import HosterResolverRegistry
from scavengarr.infrastructure.hoster_resolvers.ddownload import DDownloadResolver
from scavengarr.infrastructure.hoster_resolvers.doodstream import DoodStreamResolver
from scavengarr.infrastructure.hoster_resolvers.filemoon import FilemoonResolver
from scavengarr.infrastructure.hoster_resolvers.filernet import FilerNetResolver
from scavengarr.infrastructure.hoster_resolvers.firestream import FirestreamResolver
from scavengarr.infrastructure.hoster_resolvers.fsst import FsstResolver
from scavengarr.infrastructure.hoster_resolvers.generic_ddl import (
    create_all_ddl_resolvers,
)
from scavengarr.infrastructure.hoster_resolvers.gofile import GoFileResolver
from scavengarr.infrastructure.hoster_resolvers.gxplayer import GxplayerResolver
from scavengarr.infrastructure.hoster_resolvers.mediafire import MediafireResolver
from scavengarr.infrastructure.hoster_resolvers.mediathek import MediathekResolver
from scavengarr.infrastructure.hoster_resolvers.mixdrop import MixdropResolver
from scavengarr.infrastructure.hoster_resolvers.pass_keeper import PassKeeper
from scavengarr.infrastructure.hoster_resolvers.playmate import PlaymateResolver
from scavengarr.infrastructure.hoster_resolvers.rapidgator import RapidgatorResolver
from scavengarr.infrastructure.hoster_resolvers.sendvid import SendVidResolver
from scavengarr.infrastructure.hoster_resolvers.serienstream import SerienstreamResolver
from scavengarr.infrastructure.hoster_resolvers.state_store import HosterStateStore
from scavengarr.infrastructure.hoster_resolvers.stmix import StmixResolver
from scavengarr.infrastructure.hoster_resolvers.streamtape import StreamtapeResolver
from scavengarr.infrastructure.hoster_resolvers.strmup import StrmupResolver
from scavengarr.infrastructure.hoster_resolvers.supervideo import SuperVideoResolver
from scavengarr.infrastructure.hoster_resolvers.upns import UpnsResolver
from scavengarr.infrastructure.hoster_resolvers.veev import VeevResolver
from scavengarr.infrastructure.hoster_resolvers.vidguard import VidguardResolver
from scavengarr.infrastructure.hoster_resolvers.vidking import VidkingResolver
from scavengarr.infrastructure.hoster_resolvers.vidsonic import VidsonicResolver
from scavengarr.infrastructure.hoster_resolvers.vinovo import VinovoResolver
from scavengarr.infrastructure.hoster_resolvers.vixeo import VixeoResolver
from scavengarr.infrastructure.hoster_resolvers.voe import VoeResolver
from scavengarr.infrastructure.hoster_resolvers.xfs import create_all_xfs_resolvers
from scavengarr.infrastructure.network_probe import NetworkProbe
from scavengarr.infrastructure.persistence.crawljob_cache import (
    CacheCrawlJobRepository,
)
from scavengarr.infrastructure.persistence.plugin_score_cache import (
    CachePluginScoreStore,
)
from scavengarr.infrastructure.persistence.stream_link_cache import (
    CacheStreamLinkRepository,
)
from scavengarr.infrastructure.plugins import PluginRegistry
from scavengarr.infrastructure.plugins.constants import (
    DEFAULT_USER_AGENT,
    search_max_results,
)
from scavengarr.infrastructure.plugins.health_monitor import PluginHealthMonitor
from scavengarr.infrastructure.plugins.history import PluginHistory
from scavengarr.infrastructure.plugins.httpx_base import HttpxPluginBase
from scavengarr.infrastructure.plugins.playwright_base import PlaywrightPluginBase
from scavengarr.infrastructure.resource_detector import detect_resources
from scavengarr.infrastructure.scoring.health_prober import HealthProber
from scavengarr.infrastructure.scoring.query_pool import QueryPoolBuilder
from scavengarr.infrastructure.scoring.scheduler import ScoringScheduler
from scavengarr.infrastructure.scoring.search_prober import MiniSearchProber
from scavengarr.infrastructure.stremio.cinemeta import CinemetaClient
from scavengarr.infrastructure.stremio.episode_filter import filter_by_episode
from scavengarr.infrastructure.stremio.hls_proxy import SegmentReadAhead
from scavengarr.infrastructure.stremio.stream_converter import convert_search_results
from scavengarr.infrastructure.stremio.stream_sorter import StreamSorter
from scavengarr.infrastructure.stremio.title_matcher import filter_by_title_match
from scavengarr.infrastructure.telemetry import create_telemetry, monitor_loop_lag
from scavengarr.infrastructure.telemetry.collectors import (
    BreakerCollector,
    BrowserPagesCollector,
)
from scavengarr.infrastructure.telemetry.events import FeedLogHandler
from scavengarr.infrastructure.tmdb.client import HttpxTmdbClient
from scavengarr.infrastructure.tmdb.imdb_fallback import ImdbFallbackClient
from scavengarr.infrastructure.torznab.search_engine import HttpxSearchEngine
from scavengarr.infrastructure.version import build_identity
from scavengarr.interfaces.app_state import AppState

log = structlog.get_logger(__name__)

# Shared HTTP client: idle connections stay open this long (httpx: 5 s), and
# connecting to a host may take at most this long
_KEEPALIVE_S = 60.0
_CONNECT_TIMEOUT_S = 5.0
# At most this many idle connections (httpx's default). httpcore 1.0 scans
# its whole pool for every request and every finished response, quadratic
# in the idle connections: with 100 kept, the scan held the GIL 10-20% of
# the time during stream requests on the production host, 2% with httpx's defaults
_KEEPALIVE_CONNECTIONS = 20


def _log_config(config: AppConfig) -> None:
    """What the server runs with: the values away from the defaults, secrets
    masked, with the layer each came from, and the YAML keys and environment
    names that loading ignored."""
    source = config.source
    config_file = str(source.file) if source.file else None
    changed = changed_values(config)
    sources = {path: source.value_sources.get(path, "defaults") for path in changed}
    # One field per changed value, so the processors mask URL passwords in them
    log.info("config_effective", config_file=config_file, sources=sources, **changed)
    if source.unknown_keys:
        log.warning(
            "config_unknown_keys",
            config_file=config_file,
            keys=list(source.unknown_keys),
        )
    if source.unknown_env:
        log.warning("config_unknown_env", names=list(source.unknown_env))
    for used, ignored in source.env_conflicts:
        log.warning("config_env_conflict", used=used, ignored=ignored)


def _auto_tune_concurrency(config: AppConfig) -> None:
    """Auto-tune max_concurrent_plugins based on host CPU/RAM capacity.

    Legacy single-parameter tuning.  Superseded by :func:`_auto_tune` when
    ``stremio.auto_tune_all`` is enabled.
    """
    if not config.stremio.max_concurrent_plugins_auto:
        return

    cpu_count = os.cpu_count() or 2
    try:
        import psutil

        available_ram_gb = psutil.virtual_memory().available / (1024**3)
        mem_limit = int(available_ram_gb * 2)
    except ImportError:
        mem_limit = 8  # conservative default without psutil

    auto_concurrent = max(2, min(cpu_count, mem_limit, 20))
    config.stremio.max_concurrent_plugins = auto_concurrent
    log.info(
        "auto_concurrency",
        cpu=cpu_count,
        mem_limit=mem_limit,
        result=auto_concurrent,
    )


def _auto_tune(config: AppConfig) -> None:
    """Container-aware auto-tuning of ALL concurrency parameters.

    Uses cgroup v2/v1 detection to read actual container limits instead of
    host values.  Scales every concurrency parameter proportionally:

    - ``max_concurrent_plugins``:    ``min(cpu*3, mem_gb*2, 30)``
    - ``max_concurrent_playwright``: ``min(cpu, mem_gb/0.15, 10)``
    - ``probe_concurrency``:         ``min(cpu*4, 100)``
    - ``validation_max_concurrent``:  ``min(cpu*5, 120)``

    Caps for probe/validation derived from benchmark diminishing-returns
    analysis (tests/benchmark/): throughput gains < 5% beyond 64–100
    for probes and 60–120 for validation across typical URL counts.
    """
    resources = detect_resources()
    cpus = resources.cpu_cores
    mem_gb = resources.memory_bytes / (1024**3)

    s = config.stremio
    s.max_concurrent_plugins = max(2, min(cpus * 3, int(mem_gb * 2), 30))
    s.max_concurrent_playwright = max(1, min(cpus, int(mem_gb / 0.15), 10))
    s.probe_concurrency = max(4, min(cpus * 4, 100))
    config.validation_max_concurrent = max(5, min(cpus * 5, 120))

    log.info(
        "auto_tune_complete",
        cpu_cores=cpus,
        memory_mb=round(mem_gb * 1024),
        cpu_source=resources.cpu_source,
        mem_source=resources.mem_source,
        cgroup_limited=resources.cgroup_limited,
        max_concurrent_plugins=s.max_concurrent_plugins,
        max_concurrent_playwright=s.max_concurrent_playwright,
        probe_concurrency=s.probe_concurrency,
        validation_max_concurrent=config.validation_max_concurrent,
    )


def _apply_plugin_overrides(plugins: PluginRegistry, config: AppConfig) -> None:
    """Apply per-plugin YAML overrides (timeout, concurrency, enabled)."""
    for name, override in config.plugins.overrides.items():
        try:
            # Unknown names raise here, a misspelled disable included
            plugin = plugins.get(name)
            if not override.enabled:
                plugins.remove(name)
                log.info("plugin_disabled_by_config", plugin=name)
                continue
            if not isinstance(plugin, HttpxPluginBase | PlaywrightPluginBase):
                log.warning("plugin_override_unsupported", plugin=name)
                continue
            if override.timeout is not None:
                if isinstance(plugin, HttpxPluginBase):
                    plugin._timeout = override.timeout  # noqa: SLF001
                else:
                    # Playwright plugins have page timeouts, no client timeout
                    log.warning("plugin_timeout_override_unsupported", plugin=name)
            if override.max_concurrent is not None:
                plugin._max_concurrent = override.max_concurrent  # noqa: SLF001
            if override.max_results is not None:
                plugin._max_results = override.max_results  # noqa: SLF001
            log.info("plugin_override_applied", plugin=name, override=override)
        except Exception:
            log.warning("plugin_override_unknown", plugin=name, exc_info=True)


def build_browser_fetcher(
    config: AppConfig,
    stealth_pool: BrowserFetcherPort,
    http_client: httpx.AsyncClient,
) -> BrowserFetcherPort | None:
    """Fetcher for Cloudflare-challenged pages of httpx plugins.

    Own browser first (``playwright.browser_fallback``), then the optional
    Byparr/FlareSolverr sidecar (``playwright.solver_url``); ``None`` = off.
    """
    fetchers: list[BrowserFetcherPort] = []
    if config.playwright_browser_fallback:
        fetchers.append(stealth_pool)
    if config.playwright_solver_url:
        fetchers.append(
            SolverFetcher(
                http_client=http_client, base_url=config.playwright_solver_url
            )
        )
    if not fetchers:
        return None
    if len(fetchers) == 1:
        return fetchers[0]
    return ChainedBrowserFetcher(fetchers)


def configure_event_loop() -> None:
    """Start the running loop's tasks lazily, asyncio's default.

    uvicorn runs on uvloop when it is installed (``loop="auto"``). anyio,
    under Starlette's middleware and httpcore's connection locks, keeps its
    own tasks lazy only under asyncio's own eager task factory, which uvloop
    0.23 cannot use (it hands the factory ``eager_start=None``: refused on
    Python 3.13, a lazy start on 3.14). Under a factory of the app's own a
    task group's child that suspended inside a cancel scope at once lost
    that scope, and every proxied HLS variant answered 500 (production,
    2026-10-06).
    """
    loop = asyncio.get_running_loop()
    loop.set_task_factory(None)
    log.info("event_loop_configured", loop=type(loop).__module__)


def build_http_client(config: AppConfig) -> httpx.AsyncClient:
    """Shared HTTP client: per-domain rate limit, 429/503 retry, SSRF guard.

    Scraped pages decide most URLs this client requests, so every request
    and redirect hop to a non-public address is refused, except for the
    configured solver sidecar (``playwright.solver_url``).

    Idle connections stay open for a minute (up to
    ``_KEEPALIVE_CONNECTIONS``): one stream request talks to 18-42 hosts,
    and with httpx's 5 s default every pause between two requests closed
    them all (TLS handshakes were 21% of the Python CPU on the production host).
    A host that does not answer fails after ``_CONNECT_TIMEOUT_S`` instead
    of the full read timeout.
    """
    rate_limiter = DomainRateLimiter(
        default_rps=config.rate_limit_requests_per_second,
        burst=10,
        adaptive=config.rate_limit_adaptive,
        min_rate=config.rate_limit_min_rps,
        max_rate=config.rate_limit_max_rps,
    )
    limits = httpx.Limits(
        max_connections=100,
        max_keepalive_connections=_KEEPALIVE_CONNECTIONS,
        keepalive_expiry=_KEEPALIVE_S,
    )
    solver_host = (
        urlparse(config.playwright_solver_url).hostname
        if config.playwright_solver_url
        else None
    )
    guard = PrivateAddressGuard(
        allowed_hosts=frozenset({solver_host}) if solver_host else frozenset()
    )
    transport = RetryTransport(
        # Connections go to the addresses the guard checked (DNS rebinding)
        wrapped=GuardedTransport(guard, limits=limits, http2=config.http_http2),
        rate_limiter=rate_limiter,
        max_retries=config.http_retry_max_attempts,
        backoff_base=config.http_retry_backoff_base,
        max_backoff=config.http_retry_max_backoff,
    )
    timeout = config.http_timeout_seconds
    return httpx.AsyncClient(
        transport=transport,
        timeout=httpx.Timeout(timeout, connect=min(_CONNECT_TIMEOUT_S, timeout)),
        headers={"User-Agent": config.http_user_agent},
        follow_redirects=config.http_follow_redirects,
        event_hooks={"request": [guard]},
    )


def build_crawljob_store(
    config: AppConfig, cache: CachePort
) -> tuple[CacheCrawlJobRepository, CrawlJobFactory]:
    """CrawlJob repository and factory sharing ``cache.crawljob_ttl_seconds``.

    The cache entry and the job's ``expires_at`` must expire together.
    """
    ttl = config.cache.crawljob_ttl_seconds
    repo = CacheCrawlJobRepository(cache=cache, ttl_seconds=ttl)
    factory = CrawlJobFactory(
        ttl_seconds=ttl,
        auto_start=True,
        default_priority=Priority.DEFAULT,
    )
    return repo, factory


def build_hoster_resolvers(
    http_client: httpx.AsyncClient,
    stealth_pool: StealthPool | None,
    *,
    clearance_store: ClearanceStore | None = None,
) -> list[HosterResolverPort]:
    """The hoster resolvers in registration order.

    A domain two resolvers claim stays with the first one registered, so the
    specific resolvers come before the generic XFS and DDL ones.
    ``scripts/generate_resolver_list.py`` lists them in
    ``docs/reference/resolvers.md``. *clearance_store* holds the kept
    capture state, whose captcha pass tells Filemoon a cold capture.
    """
    return [
        # Streaming resolvers (extract direct video URLs)
        VoeResolver(http_client=http_client),
        StreamtapeResolver(http_client=http_client),
        SuperVideoResolver(http_client=http_client, stealth_pool=stealth_pool),
        DoodStreamResolver(http_client=http_client, stealth_pool=stealth_pool),
        FilemoonResolver(
            http_client=http_client,
            stealth_pool=stealth_pool,
            clearance_store=clearance_store,
        ),
        # DDL resolvers (custom — non-generic)
        FilerNetResolver(http_client=http_client),
        RapidgatorResolver(http_client=http_client),
        DDownloadResolver(http_client=http_client),
        SerienstreamResolver(http_client=http_client),
        StmixResolver(http_client=http_client),
        StrmupResolver(http_client=http_client),
        VidguardResolver(http_client=http_client),
        VidkingResolver(http_client=http_client),
        VidsonicResolver(http_client=http_client),
        SendVidResolver(http_client=http_client),
        VeevResolver(http_client=http_client),
        FirestreamResolver(http_client=http_client),
        PlaymateResolver(http_client=http_client),
        MixdropResolver(http_client=http_client),
        VixeoResolver(http_client=http_client, stealth_pool=stealth_pool),
        VinovoResolver(http_client=http_client),
        GxplayerResolver(http_client=http_client),
        FsstResolver(http_client=http_client),
        UpnsResolver(http_client=http_client, hoster="upns"),
        UpnsResolver(http_client=http_client, hoster="rpmplay"),
        # DDL resolvers (custom — non-XFS)
        MediafireResolver(http_client=http_client),
        GoFileResolver(http_client=http_client),
        # The public broadcasters' own files (the mediathek plugin)
        MediathekResolver(http_client=http_client),
        # DDL resolvers (consolidated, one per GenericDDLConfig)
        *create_all_ddl_resolvers(http_client=http_client),
        # XFS resolvers (consolidated, one per XFSConfig)
        *create_all_xfs_resolvers(http_client=http_client, stealth_pool=stealth_pool),
    ]


def build_tmdb_client(
    config: AppConfig, http_client: httpx.AsyncClient, cache: CachePort
) -> TmdbClientPort:
    """The title look-up: TMDB with ``tmdb_api_key``, else the IMDb suggest
    API."""
    if config.tmdb_api_key:
        log.info("tmdb_client_initialized")
        return HttpxTmdbClient(
            api_key=config.tmdb_api_key, http_client=http_client, cache=cache
        )
    log.info("tmdb_client_fallback", reason="no API key, using IMDB suggest API")
    return ImdbFallbackClient(http_client=http_client, cache=cache)


def _inject_shared_browser_pool(
    plugins: PluginRegistry,
    pool: SharedBrowserPool,
) -> None:
    """Inject the shared browser pool into all Playwright plugins."""
    for name in plugins.list_names():
        if plugins.get_mode(name) == "playwright":
            plugin = plugins.get(name)
            if isinstance(plugin, PlaywrightPluginBase):
                plugin.set_shared_pool(pool)


def _mirror_groups(plugins: PluginRegistry) -> dict[str, str]:
    """Plugin name -> ``mirror_group`` of the plugins that declare one."""
    groups: dict[str, str] = {}
    for name in plugins.list_names():
        group = getattr(plugins.get(name), "mirror_group", None)
        if isinstance(group, str) and group:
            groups[name] = group
    return groups


def _wire_scoring(state: AppState, config: AppConfig) -> asyncio.Task[None]:
    """Wire scoring components; return the scheduler's background task."""
    state.plugin_score_store = CachePluginScoreStore(
        cache=state.cache,
        ttl_days=config.scoring.score_ttl_days,
    )
    health_prober = HealthProber(
        http_client=state.http_client,
        timeout=config.scoring.health_timeout_seconds,
    )
    search_prober = MiniSearchProber(
        plugins=state.plugins,
        http_client=state.http_client,
        # A link counts as supported where the dispatch finds a resolver
        resolver_name=state.hoster_resolver_registry.resolver_name,
    )
    query_pool = QueryPoolBuilder(
        http_client=state.http_client,
        cache=state.cache,
    )
    state.scoring_scheduler = ScoringScheduler(
        health_prober=health_prober,
        search_prober=search_prober,
        query_pool=query_pool,
        score_store=state.plugin_score_store,
        plugins=state.plugins,
        config=config.scoring,
    )
    log.info("scoring_scheduler_started")
    return asyncio.create_task(state.scoring_scheduler.run_forever())


def _plugin_health(state: AppState, config: AppConfig) -> PluginHealthMonitor | None:
    """Checks of the Stremio plugins' sites; ``None`` when turned off."""
    interval = config.stremio.plugin_health_interval_seconds
    if interval <= 0:
        return None
    names = state.plugins.get_by_provides("stream")
    log.info("plugin_health_monitor_started", plugins=len(names), interval_s=interval)
    return PluginHealthMonitor(
        prober=HealthProber(http_client=state.http_client),
        plugins=state.plugins,
        names=names,
        interval_s=interval,
        history=state.plugin_history,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan Hook: Initialize and cleanup all resources (DI Composition Root).

    Order matters:
        1. Cache (required by other components)
        2. HTTP Client (required by search engine)
        3. Plugin Registry
        4. Search Engine (uses HTTP client + cache)
        5. CrawlJob Repository (uses cache)
        6. CrawlJob Factory (stateless, no dependencies)
    """
    state = cast(AppState, app.state)
    config = state.config
    _log_config(config)
    configure_event_loop()

    # 0) Telemetry (must exist before the components that record); tracing
    #    only with an OTLP endpoint
    state.telemetry = create_telemetry(config.telemetry.tracing_endpoint)
    if state.telemetry.tracing is not None:
        log.info("tracing_enabled", endpoint=config.telemetry.tracing_endpoint)
    state._loop_lag_task = asyncio.create_task(monitor_loop_lag(state.telemetry))
    # The dashboard's live errors: warnings and errors of the logs
    state._feed_log_handler = FeedLogHandler(state.telemetry.feed)
    logging.getLogger().addHandler(state._feed_log_handler)

    # 0b) Auto-tune concurrency based on detected container/host resources
    if config.stremio.auto_tune_all:
        _auto_tune(config)
    else:
        _auto_tune_concurrency(config)

    # 1) Cache (must be first - other components depend on it)
    cache = create_cache(
        backend=config.cache.backend,
        directory=str(config.cache.directory),
        redis_url=config.cache.redis_url,
        ttl_seconds=config.cache.ttl_seconds,
        max_concurrent=config.cache.max_concurrent,
    )

    await cache.__aenter__()
    state.cache = cache
    log.info("cache_initialized", backend=config.cache.backend)
    # readyz: the cache backend and the DNS, so a lost network shows
    state.network_probe = NetworkProbe(state.cache, telemetry=state.telemetry)

    if config.environment == "dev":
        await cache.clear()
        log.debug("cache_cleared", environment="dev")

    # 2) HTTP client with per-domain rate limiting + 429/503 retry
    state.http_client = build_http_client(config)
    log.info(
        "http_client_initialized",
        rate_limit_rps=config.rate_limit_requests_per_second,
        retry_max_attempts=config.http_retry_max_attempts,
    )

    # 2b) Share HTTP client and cache with httpx-based plugins
    HttpxPluginBase.set_shared_http_client(state.http_client)
    HttpxPluginBase.set_cache(state.cache)

    # 3) Plugin registry
    state.plugins = PluginRegistry(plugin_dir=config.plugin_dir)
    state.plugins.discover()
    log.info("plugins_discovered", count=state.plugins.discovered_count)

    # 3b) Apply per-plugin overrides from config
    _apply_plugin_overrides(state.plugins, config)

    # 4) Search engine
    state.search_engine = HttpxSearchEngine(
        http_client=state.http_client,
        cache=state.cache,
        validate_links=config.validate_download_links,
        validation_timeout=config.validation_timeout_seconds,
        validation_concurrency=config.validation_max_concurrent,
    )
    log.info("search_engine_initialized")

    # 5) + 6) CrawlJob repository and factory
    state.crawljob_repo, state.crawljob_factory = build_crawljob_store(
        config, state.cache
    )
    log.info(
        "crawljob_store_initialized", ttl_seconds=config.cache.crawljob_ttl_seconds
    )

    # 7) TMDB client (with IMDB fallback when no API key is configured)
    state.tmdb_client = build_tmdb_client(config, state.http_client, state.cache)

    # 8) One Chromium process for everything: the shared browser pool serves
    #    the Playwright plugins (own contexts) and the stealth pool (CF bypass
    #    context used by SuperVideoResolver and stealth probes).
    state.shared_browser_pool = SharedBrowserPool(
        headless=config.playwright_headless,
    )
    # Solved Cloudflare/DDoS-Guard challenges survive restarts
    clearance_store = ClearanceStore(state.cache)
    PlaywrightPluginBase.set_clearance_store(clearance_store)
    PlaywrightPluginBase.set_page_timeout(config.playwright_timeout_ms)
    # The stealth browser's pages: 2 at the start, then adapted to the waits
    # for a page, the CPU and the free memory, up to max_concurrent_playwright
    ceiling = config.stremio.max_concurrent_playwright
    pages = PageGate(limit=min(ceiling, 2), telemetry=state.telemetry)
    state.telemetry.registry.register(BrowserPagesCollector(pages))
    state._page_budget_task = asyncio.create_task(
        PageBudget(pages, ceiling=ceiling).run_forever()
    )
    state.stealth_pool = StealthPool(
        browser_pool=state.shared_browser_pool,
        clearance_store=clearance_store,
        timeout_ms=int(config.stremio.probe_stealth_timeout_seconds * 1000),
        pages=pages,
    )
    log.info("browser_pages_budget", start=pages.limit, ceiling=ceiling)

    # 8b) httpx plugins fall back to the stealth browser (and/or an external
    #     solver) on CF challenges
    HttpxPluginBase.set_browser_fetcher(
        build_browser_fetcher(config, state.stealth_pool, state.http_client)
    )
    log.info(
        "browser_fallback_configured",
        enabled=config.playwright_browser_fallback,
        solver=bool(config.playwright_solver_url),
    )

    # 9) Hoster resolver registry (for extracting video URLs from embed pages).
    #    Its breaker skips hosters whose resolutions keep timing out or are
    #    unplayable (browser captures that cannot pass a challenge from this IP)
    hoster_breaker = PluginCircuitBreaker(failure_threshold=5, cooldown_seconds=60.0)
    state.hoster_resolver_registry = HosterResolverRegistry(
        resolvers=build_hoster_resolvers(
            state.http_client, state.stealth_pool, clearance_store=clearance_store
        ),
        http_client=state.http_client,
        resolve_timeout=config.http_timeout_resolve_seconds,
        verify_playback=config.stremio.verify_streams,
        circuit_breaker=hoster_breaker,
        telemetry=state.telemetry,
        pages=pages,
    )
    log.info(
        "hoster_resolver_registry_initialized",
        hosters=state.hoster_resolver_registry.supported_hosters,
    )

    # 10) Stream link repository (for Stremio play endpoint)
    state.stream_link_repo = CacheStreamLinkRepository(
        cache=state.cache,
        ttl_seconds=config.stremio.stream_link_ttl_seconds,
    )
    log.info(
        "stream_link_repo_initialized",
        ttl_seconds=config.stremio.stream_link_ttl_seconds,
    )
    # /play and the HLS proxy resolve a stale or refused link again
    state.stremio_links = StremioLinks(
        repo=state.stream_link_repo, resolver=state.hoster_resolver_registry
    )
    # The HLS proxy fetches the next segments ahead of the player
    state.hls_read_ahead = SegmentReadAhead(telemetry=state.telemetry)

    # 11) Plugin scoring (optional — background health + search probes)
    state.plugin_score_store = None
    state.scoring_scheduler = None
    state._scoring_task = (
        _wire_scoring(state, config) if config.scoring.enabled else None
    )

    # 12) Playwright plugins share the browser created in step 8
    _inject_shared_browser_pool(state.plugins, state.shared_browser_pool)
    log.info("shared_browser_pool_configured")

    # 13) Global concurrency pool (fair-share httpx + PW slots across requests)
    state.concurrency_pool = ConcurrencyPool(
        httpx_slots=config.stremio.max_concurrent_plugins,
        pw_slots=config.stremio.max_concurrent_playwright,
    )
    log.info(
        "concurrency_pool_initialized",
        httpx_slots=config.stremio.max_concurrent_plugins,
        pw_slots=config.stremio.max_concurrent_playwright,
    )

    # 14) Circuit breaker (skip plugins after consecutive failures)
    state.circuit_breaker = PluginCircuitBreaker(
        failure_threshold=5,
        cooldown_seconds=60.0,
    )
    log.info("circuit_breaker_initialized")
    breakers = {"plugin": state.circuit_breaker, "hoster": hoster_breaker}
    state.telemetry.registry.register(BreakerCollector(breakers))

    # 14a) Resolutions, redirects and open breakers outlive a restart: a
    #      snapshot in the cache, written every 30 s when it changed and at
    #      shutdown, restored before the first request
    state.hoster_state_store = HosterStateStore(
        state.cache, state.hoster_resolver_registry, breakers
    )
    await state.hoster_state_store.restore()
    state.hoster_state_store.start()

    # 14b) The plugins' long-term record (searches, results, timeouts, checks
    #      and unreachable marks per day, 180 days): in the cache, written
    #      every minute when it changed and at shutdown, restored at the start
    state.plugin_history = PluginHistory(state.cache)
    await state.plugin_history.restore()
    state.plugin_history.start()

    # 14c) Plugin health: Stremio searches skip sites that do not answer
    state.plugin_health = _plugin_health(state, config)
    state._plugin_health_task = (
        asyncio.create_task(state.plugin_health.run_forever())
        if state.plugin_health is not None
        else None
    )

    # 15) Anime: the Kitsu addon's ids become IMDb requests (the addon's
    # meta, the public id list as the fallback), both cached in the backend
    anime_id_lists = AnimeIdLists(http_client=state.http_client, cache=state.cache)
    state.anime_ids = KitsuAnimeIdResolver(
        addon=KitsuAddonClient(http_client=state.http_client, cache=state.cache),
        lists=anime_id_lists,
    )
    # 15b) The catalog's record of a title (kind, episodes), cached 7 days
    state.series_meta = CinemetaClient(http_client=state.http_client, cache=state.cache)

    # 16) Stremio use cases (always initialized — fallback handles missing key)
    state.stremio_stream_uc = StremioStreamUseCase(
        tmdb=state.tmdb_client,
        anime_ids=state.anime_ids,
        series_meta=state.series_meta,
        plugins=state.plugins,
        search_engine=state.search_engine,
        config=config.stremio,
        sorter=StreamSorter(config.stremio),
        # Hoster names are resolver names: mirror domains share one name
        convert_fn=partial(
            convert_search_results,
            canonical_hoster=state.hoster_resolver_registry.canonical_hoster,
        ),
        filter_fn=filter_by_title_match,
        episode_filter_fn=filter_by_episode,
        user_agent=DEFAULT_USER_AGENT,
        max_results_var=search_max_results,
        stream_link_repo=state.stream_link_repo,
        resolve_fn=state.hoster_resolver_registry.resolve,
        # A cached search answers at once with the cached resolutions
        cached_resolution_fn=state.hoster_resolver_registry.cached,
        telemetry=state.telemetry,
        score_store=state.plugin_score_store,
        browser_warmup_fn=state.shared_browser_pool.warmup,
        pool=state.concurrency_pool,
        circuit_breaker=state.circuit_breaker,
        # hdfilme, streamcloud, streamkiste: one database, one asked per request
        mirror_groups=_mirror_groups(state.plugins),
        plugin_health=state.plugin_health,
        plugin_history=state.plugin_history,
        # Search results per title, shared with Torznab's TTL (0 = off)
        cache=state.cache,
        search_ttl_seconds=config.cache.search_ttl_seconds,
    )
    # The IMDB fallback (no TMDB key) has no trending lists, only search
    state.stremio_catalog_uc = StremioCatalogUseCase(
        tmdb=state.tmdb_client, has_trending=bool(config.tmdb_api_key)
    )

    # Mark the application as ready for traffic
    state.graceful_shutdown.mark_ready()
    log.info("app_startup_complete", **build_identity())
    # The browser and the stealth context with the kept state, so the first
    # capture (a breaker trial after a restart) does not pay for the launch
    state._browser_warmup_task = asyncio.create_task(state.stealth_pool.warmup())
    # Filemoon's captcha pass: one capture once it has gone, so a request
    # after a quiet half hour finds one (row 106)
    state._pass_keeper_task = asyncio.create_task(
        PassKeeper(
            state.hoster_resolver_registry,
            clearance_store,
            pages,
            telemetry=state.telemetry,
        ).run_forever()
    )
    # The anime id list, so an IMDb anime request right after the start has
    # its episode's Kitsu number (the shutdown ends a load still running)
    anime_id_lists.load_in_background()

    try:
        yield
    finally:
        # Drain in-flight requests before tearing down resources
        await state.graceful_shutdown.wait_for_drain(timeout=10.0)

        # Background searches and resolutions, links resolved again and
        # half-open hoster probes use the browser, HTTP client and cache
        # closed below
        await state.stremio_stream_uc.aclose()
        # The anime id list's background load
        await state.anime_ids.aclose()
        await state.stremio_links.aclose()
        await state.hls_read_ahead.aclose()
        # The pass keeper's capture, before the registry ends its completions
        state._pass_keeper_task.cancel()
        with suppress(asyncio.CancelledError):
            await state._pass_keeper_task
        await state.hoster_resolver_registry.aclose()
        # The last resolutions and breaker changes, before the cache closes
        await state.hoster_state_store.aclose()
        # The plugin record's last counts (the health task is cancelled
        # below: a check it still runs is not worth a write)
        await state.plugin_history.aclose()

        if state._scoring_task is not None:
            state._scoring_task.cancel()
            with suppress(asyncio.CancelledError):
                await state._scoring_task
            log.info("scoring_scheduler_stopped")

        if state._plugin_health_task is not None:
            state._plugin_health_task.cancel()
            with suppress(asyncio.CancelledError):
                await state._plugin_health_task

        state._loop_lag_task.cancel()
        with suppress(asyncio.CancelledError):
            await state._loop_lag_task

        state._page_budget_task.cancel()
        with suppress(asyncio.CancelledError):
            await state._page_budget_task

        state._browser_warmup_task.cancel()
        with suppress(asyncio.CancelledError):
            await state._browser_warmup_task

        # Stealth context first: it lives on the shared browser.
        if state.stealth_pool is not None:
            await state.stealth_pool.cleanup()
            log.info("stealth_pool_cleaned_up")

        if state.shared_browser_pool is not None:
            await state.shared_browser_pool.cleanup()
            log.info("shared_browser_pool_cleaned_up")

        await state.hoster_resolver_registry.cleanup()
        log.info("hoster_resolvers_cleaned_up")

        await state.http_client.aclose()
        log.info("http_client_closed")

        await state.cache.aclose()
        log.info("cache_closed")

        # Spans of everything closed above still go out (blocks up to 3 s)
        await asyncio.to_thread(state.telemetry.close)
        logging.getLogger().removeHandler(state._feed_log_handler)

        log.info("app_shutdown_complete")
