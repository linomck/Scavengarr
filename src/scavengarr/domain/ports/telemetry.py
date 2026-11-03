"""Telemetry port: timed steps (stages) and values, for metrics and traces.

A stage is one step of a request (a plugin search, a hoster resolution, a
phase of a Stremio request). It is recorded when it ends: its duration and
its outcome, and with tracing on it is a span. Label values come from small
fixed sets only (plugin and resolver names, outcomes), never titles, ids,
URLs or domains.
"""

from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext
from contextvars import ContextVar
from typing import Any, Literal, Protocol, runtime_checkable

StageName = Literal[
    "stremio_request",
    "stremio_phase",
    "plugin_search",
    "hoster_resolve",
    "hoster_challenge_completion",
    "hoster_pass_keep",
    "hls_proxy",
    "hls_readahead",
    "browser_page_wait",
    "browser_page",
]

ValueName = Literal[
    "stremio_streams",
    "plugin_results",
    "hls_proxy_bytes",
    "network_ok",
]

AttributeValue = str | int | float | bool

_SEARCH: ContextVar[dict[str, Any]] = ContextVar("scavengarr_search")


def bind_search(**fields: Any) -> None:
    """Name the search of the running request (imdb, title, year, season,
    episode) for the dashboard's live feed. Tasks the request starts later
    inherit it; it reaches no metric, trace or log line."""
    _SEARCH.set({**_SEARCH.get({}), **fields})


def current_search() -> dict[str, Any]:
    """The search bound for the running request, empty without one."""
    return _SEARCH.get({})


class Stage(Protocol):
    """A running stage; its outcome and labels are recorded when it ends.

    Without an outcome set, the stage ends as ``ok``, ``cut`` (cancelled),
    ``timeout`` (``TimeoutError``) or ``error`` (any other exception).
    """

    outcome: str | None

    def label(self, **labels: str) -> None:
        """Set labels known only while the stage runs."""
        ...

    def annotate(self, **attributes: AttributeValue) -> None:
        """Add details to the stage's span (traces only, not metrics)."""
        ...


@runtime_checkable
class TelemetryPort(Protocol):
    """Records stages, outcomes without a run, and values."""

    def stage(self, name: StageName, /, **labels: str) -> AbstractContextManager[Stage]:
        """Time the ``with`` block as stage *name*; exceptions propagate."""
        ...

    def count(self, name: StageName, outcome: str, /, **labels: str) -> None:
        """Count an outcome of stage *name* that did not run (no duration)."""
        ...

    def record(self, name: ValueName, value: float, /, **labels: str) -> None:
        """Record a value that is not a duration (a count, bytes, a state)."""
        ...


class _NoStage:
    def __init__(self) -> None:
        self.outcome: str | None = None

    def label(self, **labels: str) -> None:
        pass

    def annotate(self, **attributes: AttributeValue) -> None:
        pass


class _NoTelemetry:
    """Records nothing: the default where no telemetry is wired in."""

    def stage(self, name: StageName, /, **labels: str) -> AbstractContextManager[Stage]:
        return nullcontext(_NoStage())

    def count(self, name: StageName, outcome: str, /, **labels: str) -> None:
        pass

    def record(self, name: ValueName, value: float, /, **labels: str) -> None:
        pass


NO_TELEMETRY: TelemetryPort = _NoTelemetry()
