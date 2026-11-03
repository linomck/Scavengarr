"""Stremio stream use case: a request's streams, best first.

The phases live in ``application/stremio/`` (plugin selection, the titles
per language, the shared title search, the resolve flow, the answer's
streams); the use case runs them in order and owns the tasks that outlive
a request.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Coroutine, Mapping
from contextvars import ContextVar
from functools import partial
from typing import Any, Protocol

import structlog

from scavengarr.application.stremio.answer import (
    ConvertFn,
    StreamAnswer,
    cache_and_proxy,
    rank_streams,
    with_measurements,
)
from scavengarr.application.stremio.plugin_search import (
    BrowserWarmupFn,
    CircuitBreaker,
    EpisodeFilterFn,
    PluginHealth,
    PluginSearchRunner,
)
from scavengarr.application.stremio.plugin_selection import (
    PluginSelectionConfig,
    PluginSelector,
)
from scavengarr.application.stremio.queries import first_available_title
from scavengarr.application.stremio.resolution import (
    CachedResolutionCallback,
    ResolveCallback,
    ResolveConfig,
    ResolveFlow,
)
from scavengarr.application.stremio.search_cache import SearchCache, search_cache_key
from scavengarr.application.stremio.search_progress import SearchProgress
from scavengarr.application.stremio.stream_builder import (
    deduplicate_by_hoster,
    format_stream,
)
from scavengarr.application.stremio.title_resolution import (
    TitleFilterFn,
    TitleMatchConfig,
    TitleResolver,
)
from scavengarr.application.stremio.title_search import TitleSearch, answer_budget_s
from scavengarr.domain.entities.stremio import (
    EpisodeRef,
    RankedStream,
    ResolvedStream,
    SeriesMeta,
    StremioStream,
    StremioStreamRequest,
)
from scavengarr.domain.ports.anime_ids import NO_ANIME_IDS, AnimeIdResolverPort
from scavengarr.domain.ports.cache import CachePort
from scavengarr.domain.ports.concurrency import ConcurrencyPoolPort
from scavengarr.domain.ports.plugin_history import (
    NO_PLUGIN_HISTORY,
    PluginHistoryPort,
)
from scavengarr.domain.ports.plugin_registry import PluginRegistryPort
from scavengarr.domain.ports.plugin_score_store import PluginScoreStorePort
from scavengarr.domain.ports.search_engine import SearchEnginePort
from scavengarr.domain.ports.series_meta import NO_SERIES_META, SeriesMetaPort
from scavengarr.domain.ports.stream_link_repository import StreamLinkRepository
from scavengarr.domain.ports.telemetry import (
    NO_TELEMETRY,
    Stage,
    TelemetryPort,
    bind_search,
)
from scavengarr.domain.ports.tmdb import TmdbClientPort

# ---------------------------------------------------------------------------
# Protocols — define what this use case needs from its dependencies.
# Infrastructure components satisfy these via structural subtyping.
# ---------------------------------------------------------------------------


class _StremioConfig(TitleMatchConfig, PluginSelectionConfig, ResolveConfig, Protocol):
    """Configuration values consumed by StremioStreamUseCase."""

    plugin_timeout_seconds: float
    answer_budget_seconds: float | None
    max_results_per_plugin: int


class _StreamSorter(Protocol):
    """Sorts RankedStreams by language, quality, and hoster scores."""

    def rank(self, stream: RankedStream) -> int: ...

    def sort(self, streams: list[RankedStream]) -> list[RankedStream]: ...


log = structlog.get_logger(__name__)

# The answer without a search: no title, no plugins
_NO_ANSWER = StreamAnswer([], "none", True, ())


class StremioStreamUseCase:
    """Resolve Stremio stream requests into sorted stream links.

    Flow (``_answer``):
        0. Anime: a ``kitsu:`` id (the Anime Kitsu addon's catalogs)
           becomes the IMDb request (``AnimeIdResolverPort``).
        1. Plugins: the stream plugins, all or the best scored
           (``PluginSelector``).
        2. Titles: the TMDB title in each language the plugins search in
           (``TitleResolver``).
        3. Search: all plugins in parallel (bounded concurrency), one
           search per title shared by its requests, cached (``TitleSearch``).
        4. Rank the results as they arrive and resolve each hoster's best
           link meanwhile; answer once enough hosters resolved, when
           everything is done, or at the deadline (``ResolveFlow``).
           Without a resolver: rank once the search is done or at the
           deadline.
        5. Format into StremioStream objects.
        6. Serve them through ``/play/`` or the HLS proxy, their links
           saved (``cache_and_proxy``).
    """

    def __init__(
        self,
        *,
        tmdb: TmdbClientPort,
        plugins: PluginRegistryPort,
        search_engine: SearchEnginePort,
        config: _StremioConfig,
        sorter: _StreamSorter,
        convert_fn: ConvertFn,
        filter_fn: TitleFilterFn,
        episode_filter_fn: EpisodeFilterFn,
        user_agent: str,
        max_results_var: ContextVar[int | None],
        stream_link_repo: StreamLinkRepository | None = None,
        resolve_fn: ResolveCallback | None = None,
        cached_resolution_fn: CachedResolutionCallback | None = None,
        telemetry: TelemetryPort = NO_TELEMETRY,
        score_store: PluginScoreStorePort | None = None,
        browser_warmup_fn: BrowserWarmupFn | None = None,
        pool: ConcurrencyPoolPort,
        circuit_breaker: CircuitBreaker | None = None,
        mirror_groups: Mapping[str, str] | None = None,
        plugin_health: PluginHealth | None = None,
        plugin_history: PluginHistoryPort = NO_PLUGIN_HISTORY,
        cache: CachePort | None = None,
        search_ttl_seconds: int = 0,
        anime_ids: AnimeIdResolverPort = NO_ANIME_IDS,
        series_meta: SeriesMetaPort = NO_SERIES_META,
    ) -> None:
        self._anime_ids = anime_ids
        self._titles = TitleResolver(
            tmdb=tmdb,
            plugins=plugins,
            filter_fn=filter_fn,
            config=config,
            series_meta=series_meta,
            telemetry=telemetry,
        )
        self._sorter = sorter
        self._rank = partial(rank_streams, convert_fn=convert_fn, sort=sorter.sort)
        self._user_agent = user_agent
        self._title_search = TitleSearch(
            search_runner=PluginSearchRunner(
                plugins=plugins,
                search_engine=search_engine,
                episode_filter_fn=episode_filter_fn,
                max_results_var=max_results_var,
                plugin_timeout=config.plugin_timeout_seconds,
                max_results_per_plugin=config.max_results_per_plugin,
                telemetry=telemetry,
                circuit_breaker=circuit_breaker,
                browser_warmup_fn=browser_warmup_fn,
                mirror_groups=mirror_groups,
                plugin_health=plugin_health,
                score_store=score_store,
                history=plugin_history,
            ),
            titles=self._titles,
            search_cache=SearchCache(cache, ttl_seconds=search_ttl_seconds),
            pool=pool,
            telemetry=telemetry,
            answer_budget_s=answer_budget_s(
                config.plugin_timeout_seconds, config.answer_budget_seconds
            ),
            spawn=self._spawn,
            resolve_late=self._resolve_late,
        )
        self._stream_link_repo = stream_link_repo
        self._resolve_fn = resolve_fn
        self._resolve_flow = ResolveFlow(
            rank=self._rank,
            cached_resolution_fn=cached_resolution_fn,
            telemetry=telemetry,
            config=config,
            spawn=self._spawn,
        )
        self._max_probe_count = config.max_probe_count
        self._deadline_s = config.stream_deadline_seconds
        # Every task that outlives a request (searches, background
        # resolutions), for aclose()
        self._tasks: set[asyncio.Task[Any]] = set()
        self._telemetry = telemetry
        self._selector = PluginSelector(
            plugins=plugins, score_store=score_store, config=config
        )

    async def execute(
        self,
        request: StremioStreamRequest,
        *,
        base_url: str = "",
    ) -> list[StremioStream]:
        """The streams of ``answer()``."""
        return (await self.answer(request, base_url=base_url)).streams

    async def answer(
        self,
        request: StremioStreamRequest,
        *,
        base_url: str = "",
    ) -> StreamAnswer:
        """Resolve streams for a Stremio request.

        Args:
            request: Parsed stream request with IMDb ID and optional season/episode.
            base_url: Service base URL for generating proxy play links.

        Returns:
            The streams, best first (none when the title is not found or no
            plugin matches), where their search results came from and
            whether the answer is complete (``StreamAnswer``).
        """
        with self._telemetry.stage("stremio_request", source="none") as stage:
            stage.annotate(imdb_id=request.imdb_id, content_type=request.content_type)
            answer = await self._answer(request, base_url, stage)
            self._telemetry.record("stremio_streams", len(answer.streams))
            return answer

    def _resolve_late(self, key: str, progress: SearchProgress) -> None:
        """Results arriving after the answer (a continuing search, a refresh,
        a completion) resolve in the background for the next request."""
        if self._resolve_fn is None:
            return
        plugin_languages = self._titles.default_languages(
            self._selector.stream_plugins()
        )
        self._resolve_flow.resolve_in_background(
            key, progress, plugin_languages, self._resolve_fn
        )

    async def _answer(
        self, request: StremioStreamRequest, base_url: str, stage: Stage
    ) -> StreamAnswer:
        """The answer for *request*; sets the request *stage*'s source and
        outcome."""
        started = time.monotonic()

        # 0. Anime: a kitsu: id becomes the IMDb request, its episode placed
        # as IMDb counts it; the sources log what they found. The Kitsu
        # number counts the entry's episodes through its seasons: it places
        # the episode on the anime sites (the episode reference below)
        absolute = None
        if request.imdb_id.startswith("kitsu:"):
            absolute = request.episode
            with self._telemetry.stage("stremio_phase", phase="anime_ids") as anime:
                translated = await self._anime_ids.translate(request)
                anime.outcome = "not_found" if translated is None else "found"
            if translated is None:
                stage.outcome = "no_title"
                return _NO_ANSWER
            request = translated
        category = 2000 if request.content_type == "movie" else 5000
        # The request's search names its events (the dashboard lists them)
        bind_search(
            imdb=request.imdb_id, season=request.season, episode=request.episode
        )

        # 1. Plugins: all stream plugins, or the best scored ones
        all_names = self._selector.stream_plugins()
        if not all_names:
            log.warning("stremio_no_stream_plugins")
            stage.outcome = "no_plugins"
            return _NO_ANSWER

        with self._telemetry.stage("stremio_phase", phase="metadata") as metadata:
            selected = await self._selector.select(all_names, category)

            # 2. Titles: one per language the stream plugins search in, so
            # the request's series titles are the same whichever plugins it
            # selects (code review 2026-10-12, finding 11), and the episode's
            # Kitsu number alongside
            languages = self._titles.languages(selected)
            (title_infos, meta), (absolute, position_trusted) = await asyncio.gather(
                self._titles.title_infos(request, self._titles.languages(all_names)),
                self._numbering(request, absolute),
            )
            primary_title_info = first_available_title(title_infos, languages)
            titles = (
                () if primary_title_info is None else primary_title_info.series_titles
            )
            episode_ref = self._episode_ref(
                request, meta, absolute, titles, position_trusted=position_trusted
            )
            metadata.outcome = "not_found" if primary_title_info is None else "found"
            if primary_title_info is not None:
                bind_search(
                    title=primary_title_info.title, year=primary_title_info.year
                )
        if primary_title_info is None:
            log.warning("stremio_title_not_found", imdb_id=request.imdb_id)
            stage.outcome = "no_title"
            return _NO_ANSWER

        # 3. Search: one search per title, shared by its requests, cached
        key = search_cache_key(request, episode_ref)
        progress, source = await self._title_search.progress(
            key,
            request,
            self._titles.language_groups(selected),
            title_infos,
            category,
            started=started,
            scored=len(selected) < len(all_names),
            episode_ref=episode_ref,
        )
        stage.label(source=source)

        # 4. Rank, and resolve meanwhile. Cached results can come from
        # plugins this request did not select
        plugin_languages = self._titles.default_languages(all_names)
        deadline = started + self._deadline_s
        # The wait for the search ends at its answer budget (a joined request
        # shares the first request's); the resolutions run on to the deadline
        budget_ends = progress.budget_ends
        # Scavengarr serves the streams (/play/, the HLS proxy) when it saves
        # their links and knows its own URL
        link_repo = self._stream_link_repo if base_url else None
        resolved: dict[int, ResolvedStream] = {}
        if link_repo is not None and self._resolve_fn is not None:
            ranked, resolved = await self._resolve_flow.resolve(
                progress,
                plugin_languages,
                self._resolve_fn,
                deadline=deadline,
                budget_ends=budget_ends,
                key=key,
                from_cache=source in ("cache", "stale"),
            )
            ranked, resolved = with_measurements(
                ranked, resolved, rank_score=self._sorter.rank
            )
        else:
            await progress.wait(min(deadline, budget_ends))
            ranked = await self._rank(progress.results, plugin_languages)
            if self._resolve_fn is None:
                ranked = deduplicate_by_hoster(ranked)
            else:
                ranked = ranked[: self._max_probe_count]

        if not progress.results:
            if progress.total:
                log.info(
                    "stremio_all_filtered",
                    imdb_id=request.imdb_id,
                    total=progress.total,
                    dropped=progress.dropped,
                    search_done=progress.done,
                )
            else:
                log.info(
                    "stremio_search_no_results",
                    imdb_id=request.imdb_id,
                    dropped=progress.dropped,
                    search_done=progress.done,
                )
            stage.outcome = "empty"
            return StreamAnswer(
                [], source, self._complete(key, progress), progress.missing
            )

        # 5. Format
        streams = [
            format_stream(
                s,
                reference_title=primary_title_info.title,
                year=primary_title_info.year,
                season=request.season,
                episode=request.episode,
            )
            for s in ranked
        ]
        # 6. Serve: /play/ and HLS proxy URLs, the stream links saved
        if link_repo is not None:
            streams = await cache_and_proxy(
                streams,
                ranked,
                resolved,
                base_url,
                stream_link_repo=link_repo,
                has_resolver=self._resolve_fn is not None,
                user_agent=self._user_agent,
            )

        complete = self._complete(key, progress)
        log.info(
            "stremio_search_complete",
            imdb_id=request.imdb_id,
            result_count=progress.total,
            filtered_count=len(progress.results),
            dropped=progress.dropped,
            stream_count=len(streams),
            source=source,
            complete=complete,
            missing=list(progress.missing),
        )
        stage.outcome = "streams" if streams else "empty"
        return StreamAnswer(streams, source, complete, progress.missing)

    async def _numbering(
        self, request: StremioStreamRequest, absolute: int | None
    ) -> tuple[int | None, bool]:
        """The episode's number as Kitsu counts it: a ``kitsu:`` request's
        own (*absolute*), else the one the anime ids give an IMDb anime
        episode (the anime sites count by it); and whether the catalog's
        position counts as the sites do where that number is missing or
        gives way: only for a series no Kitsu entry counts whole (code
        review of 2026-10-12, finding 1)."""
        if absolute is None:
            absolute = await self._anime_ids.kitsu_episode(request)
            if absolute is not None:
                # Its entry counts the series whole
                return absolute, False
        if request.season is None or request.episode is None:
            return absolute, False
        whole_series = await self._anime_ids.has_whole_series_entry(request.imdb_id)
        return absolute, whole_series is False

    def _episode_ref(
        self,
        request: StremioStreamRequest,
        meta: SeriesMeta | None,
        absolute: int | None,
        titles: tuple[str, ...],
        *,
        position_trusted: bool,
    ) -> EpisodeRef | None:
        """The episode's placement for the plugins that locate episodes (the
        title and air date from the Cinemeta list, the absolute number and
        its source, the request's series titles), logged when there is
        one."""
        ref = self._titles.episode_ref(
            request,
            meta,
            absolute=absolute,
            position_trusted=position_trusted,
            titles=titles,
        )
        if ref is not None:
            log.debug(
                "stremio_episode_ref",
                season=ref.season,
                episode=ref.episode,
                absolute=ref.absolute,
                source=ref.source,
                has_title=ref.title is not None,
            )
        return ref

    def _complete(self, key: str, progress: SearchProgress) -> bool:
        """Whether an answer built now is complete: nothing of any plugin is
        missing, and no search goes on for *key* that a later request would
        find more from. Decided after the request's wait: a search that
        ends within the budget is done by then (decided at the search's
        start, every fresh answer said incomplete)."""
        return not progress.missing and not self._title_search.running(key)

    def _spawn[T](self, coro: Coroutine[Any, Any, T]) -> asyncio.Task[T]:
        """Run *coro* as a task that may outlive the request (see aclose)."""
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._task_done)
        return task

    def _task_done(self, task: asyncio.Task[Any]) -> None:
        self._tasks.discard(task)
        if not task.cancelled() and (error := task.exception()) is not None:
            log.warning("stremio_background_search_failed", exc_info=error)

    async def aclose(self) -> None:
        """Cancel the searches and background resolutions still running."""
        tasks = list(self._tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
