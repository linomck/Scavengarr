"""Prometheus metrics of the core's stages (``TelemetryPort``).

Every stage has a duration histogram ``scavengarr_<stage>_seconds`` by its
labels and an outcome counter ``scavengarr_<stage>_total`` by its labels and
outcome: a histogram per outcome would multiply the series. The buckets
follow the deadlines (``docs/reference/metrics.md``). With tracing on,
a stage is also a span (``tracing.py``).
"""

from __future__ import annotations

import asyncio
import time
from collections import Counter as Tally
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    GCCollector,
    Histogram,
    Info,
    PlatformCollector,
    ProcessCollector,
    disable_created_metrics,
    generate_latest,
)
from prometheus_client.exposition import CONTENT_TYPE_PLAIN_0_0_4

from scavengarr.domain.ports.telemetry import AttributeValue, StageName, ValueName
from scavengarr.infrastructure.telemetry.collectors import ContainerCollector
from scavengarr.infrastructure.telemetry.events import EventFeed
from scavengarr.infrastructure.version import build_identity

if TYPE_CHECKING:
    from scavengarr.infrastructure.telemetry.tracing import TracedStage, Tracing

# The creation time of every counter and histogram would double the series
disable_created_metrics()

# Classic text format: Prometheus 2 and 3 read it
CONTENT_TYPE = CONTENT_TYPE_PLAIN_0_0_4

# Event-loop lag samples kept for the JSON statistics: 5 min of 0.5 s timers
LAG_WINDOW = 600


@dataclass(frozen=True, slots=True)
class _StageSpec:
    labels: tuple[str, ...]
    buckets: tuple[float, ...]
    doc: str
    # The label whose value names the span (``plugin_search kinoger``)
    span_label: str | None = None
    traced: bool = True


# The answer goes out at the latest 60 s after the request
_REQUEST_BUCKETS = (0.5, 1.0, 2.0, 4.0, 7.0, 10.0, 15.0, 30.0, 60.0)

_STAGES: dict[StageName, _StageSpec] = {
    "stremio_request": _StageSpec(
        ("source",), _REQUEST_BUCKETS, "Stremio stream requests by search state"
    ),
    "stremio_phase": _StageSpec(
        ("phase",),
        _REQUEST_BUCKETS,
        "Phases of Stremio stream requests",
        span_label="phase",
    ),
    # The search ends 30 s after the request
    "plugin_search": _StageSpec(
        ("plugin",),
        (1.0, 2.0, 4.0, 7.0, 10.0, 15.0, 30.0),
        "Plugin searches of Stremio requests",
        span_label="plugin",
    ),
    # A resolution gets 15 s
    "hoster_resolve": _StageSpec(
        ("resolver",),
        (0.5, 1.0, 2.0, 4.0, 7.0, 15.0),
        "Hoster resolutions",
        span_label="resolver",
    ),
    # A capture the bound cut after a challenge runs on for at most 20 s
    "hoster_challenge_completion": _StageSpec(
        ("resolver",),
        (1.0, 2.0, 4.0, 7.0, 10.0, 15.0, 20.0),
        "Background completions of challenged hoster captures",
        span_label="resolver",
    ),
    # Filemoon's pass keeper resolves a link once its captcha pass has gone:
    # the resolve bound, and the wait for a page before it
    "hoster_pass_keep": _StageSpec(
        (),
        (1.0, 2.0, 4.0, 7.0, 10.0, 15.0, 20.0, 30.0),
        "Captures of Filemoon's captcha pass keeper",
    ),
    # A span per segment would bury the requests in the traces
    "hls_proxy": _StageSpec(
        ("kind",),
        (0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0),
        "HLS proxy requests until the answer starts",
        traced=False,
    ),
    # A segment fetched ahead of the player (4 s of video, mostly 1 to 4 MB)
    "hls_readahead": _StageSpec(
        (),
        (0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 7.0, 15.0),
        "HLS segments fetched ahead of the player",
        traced=False,
    ),
    # The stealth browser's pages: the wait for one and the work on it, by
    # what the page is for (play, plugin, capture, background)
    "browser_page_wait": _StageSpec(
        ("kind",),
        (0.1, 0.5, 1.0, 2.0, 4.0, 7.0, 10.0, 15.0, 30.0, 60.0),
        "Waits for a stealth browser page",
        span_label="kind",
    ),
    "browser_page": _StageSpec(
        ("kind",),
        (0.5, 1.0, 2.0, 4.0, 7.0, 10.0, 15.0, 30.0, 60.0),
        "Work on a stealth browser page",
        span_label="kind",
    ),
}

# One event per segment would bury the dashboard's feed
_UNFED: frozenset[StageName] = frozenset({"hls_proxy", "hls_readahead"})

_FED_VALUES: frozenset[ValueName] = frozenset({"plugin_results", "stremio_streams"})

_SUCCESSES = ("hits", "empty")
_FAILURES = ("error", "cut", "timeout")


def _outcome_of(error: type[BaseException] | None) -> str:
    """The outcome of a stage the code left without one."""
    if error is None:
        return "ok"
    if issubclass(error, asyncio.CancelledError):
        return "cut"
    if issubclass(error, TimeoutError):
        return "timeout"
    return "error"


class _Stage:
    """One running stage; records itself on exit (exceptions propagate)."""

    __slots__ = ("_labels", "_name", "_owner", "_span", "_started", "outcome")

    def __init__(
        self, owner: Telemetry, name: StageName, labels: dict[str, str]
    ) -> None:
        self.outcome: str | None = None
        self._owner = owner
        self._name: StageName = name
        self._labels = labels
        self._started = 0.0
        self._span: TracedStage | None = None

    def label(self, **labels: str) -> None:
        self._labels.update(labels)
        if self._span is not None:
            self._span.set_attributes(labels)

    def annotate(self, **attributes: AttributeValue) -> None:
        if self._span is not None:
            self._span.set_attributes(attributes)

    def __enter__(self) -> _Stage:
        self._span = self._owner.start_span(self._name, self._labels)
        self._started = time.perf_counter()
        return self

    def __exit__(
        self,
        error: type[BaseException] | None,
        exc: BaseException | None,
        _tb: TracebackType | None,
    ) -> None:
        seconds = time.perf_counter() - self._started
        outcome = self.outcome or _outcome_of(error)
        self._owner.finish(self._name, self._labels, outcome, seconds)
        if self._span is not None:
            self._span.end(outcome, exc)


class Telemetry:
    """The ``TelemetryPort`` on prometheus-client, with its own registry.

    With *tracing*, every stage but the HLS proxy is also a span. Also keeps
    the event-loop lag samples and the plugin statistics of
    ``/api/v1/stats/metrics``.
    """

    def __init__(self, *, tracing: Tracing | None = None) -> None:
        self.tracing = tracing
        self.feed = EventFeed()
        self.registry = CollectorRegistry()
        self._started = time.monotonic()
        self._durations = {
            name: Histogram(
                f"scavengarr_{name}_seconds",
                f"{spec.doc}: duration",
                spec.labels,
                buckets=spec.buckets,
                registry=self.registry,
            )
            for name, spec in _STAGES.items()
        }
        self._outcomes = {
            name: Counter(
                f"scavengarr_{name}",
                f"{spec.doc} by outcome",
                (*spec.labels, "outcome"),
                registry=self.registry,
            )
            for name, spec in _STAGES.items()
        }
        self._values: dict[ValueName, Counter | Gauge | Histogram] = {
            "stremio_streams": Histogram(
                "scavengarr_stremio_streams",
                "Streams per Stremio answer",
                buckets=(0, 1, 2, 3, 5, 8, 13, 21, 34),
                registry=self.registry,
            ),
            "plugin_results": Counter(
                "scavengarr_plugin_results",
                "Validated results of plugin searches",
                ("plugin",),
                registry=self.registry,
            ),
            "hls_proxy_bytes": Counter(
                "scavengarr_hls_proxy_bytes",
                "Bytes the HLS proxy sent",
                ("kind",),
                registry=self.registry,
            ),
            # The readiness probe's checks at its last run (NetworkProbe)
            "network_ok": Gauge(
                "scavengarr_network_ok",
                "1 when the readiness probe's check answered at its last run, else 0",
                ("check",),
                registry=self.registry,
            ),
        }
        self._loop_lag = Histogram(
            "scavengarr_event_loop_lag_seconds",
            "How late a 0.5 s event-loop timer fired",
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
            registry=self.registry,
        )
        self._loop_lag_ms: deque[float] = deque(maxlen=LAG_WINDOW)
        # One series by construction: its labels name the build, not a set
        Info(
            "scavengarr_build", "Scavengarr version and build", registry=self.registry
        ).info(build_identity())
        ProcessCollector(registry=self.registry)
        self.registry.register(ContainerCollector())
        PlatformCollector(registry=self.registry)
        GCCollector(registry=self.registry)

    # ------------------------------------------------------------------
    # TelemetryPort
    # ------------------------------------------------------------------

    def stage(self, name: StageName, /, **labels: str) -> _Stage:
        return _Stage(self, name, labels)

    def count(self, name: StageName, outcome: str, /, **labels: str) -> None:
        self._outcomes[name].labels(**labels, outcome=outcome).inc()
        if name not in _UNFED:
            self.feed.publish("stage", stage=name, outcome=outcome, **labels)

    def record(self, name: ValueName, value: float, /, **labels: str) -> None:
        if name in _FED_VALUES:
            self.feed.publish("value", name=name, value=value, **labels)
        metric = self._values[name]
        child = metric.labels(**labels) if labels else metric
        if isinstance(child, Histogram):
            child.observe(value)
        elif isinstance(child, Gauge):
            child.set(value)
        else:
            child.inc(value)

    def finish(
        self, name: StageName, labels: dict[str, str], outcome: str, seconds: float
    ) -> None:
        """Record an ended stage (called by the stage)."""
        duration = self._durations[name]
        # A stage without labels of its own has a plain histogram
        (duration.labels(**labels) if labels else duration).observe(seconds)
        self._outcomes[name].labels(**labels, outcome=outcome).inc()
        if name not in _UNFED:
            self.feed.publish(
                "stage",
                stage=name,
                outcome=outcome,
                duration_ms=round(seconds * 1000, 1),
                **labels,
            )

    def start_span(self, name: StageName, labels: dict[str, str]) -> TracedStage | None:
        """The span of a starting stage, with tracing on (called by the stage)."""
        spec = _STAGES[name]
        if self.tracing is None or not spec.traced:
            return None
        span_name = f"{name} {labels[spec.span_label]}" if spec.span_label else name
        return self.tracing.start(span_name, labels)

    def close(self) -> None:
        """Send the spans still queued (at shutdown; blocks briefly)."""
        if self.tracing is not None:
            self.tracing.close()

    # ------------------------------------------------------------------
    # Event loop, exposition, JSON statistics
    # ------------------------------------------------------------------

    def record_loop_lag(self, lag_ms: float) -> None:
        """Record how late one event-loop timer fired (``monitor_loop_lag``)."""
        self._loop_lag_ms.append(lag_ms)
        self._loop_lag.observe(lag_ms / 1000)

    def render(self) -> bytes:
        """The metrics in the Prometheus text format (``CONTENT_TYPE``)."""
        return generate_latest(self.registry)

    def snapshot(self) -> dict[str, object]:
        """The JSON statistics of ``/api/v1/stats/metrics``."""
        return {
            "uptime_seconds": round(time.monotonic() - self._started, 1),
            "plugins": self._plugin_snapshot(),
            "event_loop": self._loop_lag_snapshot(),
        }

    def _plugin_snapshot(self) -> dict[str, dict[str, object]]:
        """Searches per plugin: ``hits``/``empty`` succeeded, the rest failed.

        Outcomes without a run (open breaker, no slot, unreachable) are no
        searches.
        """
        outcomes: dict[str, Tally[str]] = {}
        for labels, value in _samples(self._outcomes["plugin_search"], "_total"):
            outcomes.setdefault(labels["plugin"], Tally())[labels["outcome"]] += int(
                value
            )
        durations = self._durations["plugin_search"]
        seconds = {labels["plugin"]: v for labels, v in _samples(durations, "_sum")}
        timed = {labels["plugin"]: v for labels, v in _samples(durations, "_count")}
        results = {
            labels["plugin"]: v
            for labels, v in _samples(self._values["plugin_results"], "_total")
        }
        plugins: dict[str, dict[str, object]] = {}
        for plugin, tally in sorted(outcomes.items()):
            successes = sum(tally[o] for o in _SUCCESSES)
            failures = sum(tally[o] for o in _FAILURES)
            if not successes + failures:
                continue
            plugins[plugin] = {
                "searches": successes + failures,
                "successes": successes,
                "failures": failures,
                "total_results": int(results.get(plugin, 0)),
                "avg_duration_ms": round(
                    seconds.get(plugin, 0.0) / timed.get(plugin, 1) * 1000, 1
                ),
            }
        return plugins

    def _loop_lag_snapshot(self) -> dict[str, object]:
        """Percentiles of the event-loop lag over the last ``LAG_WINDOW`` samples."""
        samples = sorted(self._loop_lag_ms)
        if not samples:
            return {"samples": 0}

        def _pct(share: float) -> float:
            return round(samples[min(len(samples) - 1, int(share * len(samples)))], 1)

        return {
            "samples": len(samples),
            "lag_ms_p50": _pct(0.5),
            "lag_ms_p99": _pct(0.99),
            "lag_ms_max": round(samples[-1], 1),
        }


def _samples(
    metric: Counter | Gauge | Histogram, suffix: str
) -> Iterator[tuple[dict[str, str], float]]:
    """The labels and values of *metric*'s samples named ``…<suffix>``."""
    for family in metric.collect():
        for sample in family.samples:
            if sample.name.endswith(suffix):
                yield sample.labels, sample.value
