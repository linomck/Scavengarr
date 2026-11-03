"""Live feed of what the core does, for the dashboard.

``Telemetry`` publishes every ended stage (a plugin search, a hoster
resolution, a Stremio request ...) and ``FeedLogHandler`` every warning and
error of the logs. The feed keeps the last events in memory and hands new
ones to the dashboard's subscribers; it holds no URLs (the metrics' label
rule, plus a hoster's second-level domain).

The one exception is the search a Stremio request carries: its title, year,
episode and IMDb id (bound by the use case, `bind_search()`) tag every
event of the request, so the dashboard can list the searches. The feed lives
in memory only and is shown by the dashboard alone; it reaches no metric,
trace or log.
"""

from __future__ import annotations

import asyncio
import logging
import re
import threading
import time
from collections import deque
from typing import Any

from urllib.parse import urlparse

import structlog

from scavengarr.domain.ports.telemetry import current_search

Event = dict[str, Any]

# Events kept for a dashboard that opens later
BACKLOG = 3000
# Events a slow subscriber may lag behind before it loses the oldest ones
SUBSCRIBER_QUEUE = 1000

# Log fields the dashboard shows; anything else (titles, URLs) stays in the logs
_LOG_FIELDS = ("plugin", "resolver", "hoster", "stage", "status_code", "reason")
_URL_RE = re.compile(r"\bhttps?://[^\s'\"]+")
_MAX_TEXT = 200


class EventFeed:
    """A ring buffer of events and the queues of the live subscribers.

    ``publish`` may be called from any thread (log records come from workers).
    """

    def __init__(self, size: int = BACKLOG) -> None:
        self._events: deque[Event] = deque(maxlen=size)
        self._lock = threading.Lock()
        self._seq = 0
        self._subscribers: dict[asyncio.Queue[Event], asyncio.AbstractEventLoop] = {}

    def publish(self, type_: str, /, **fields: Any) -> None:
        context = dict(current_search())
        request_id = structlog.contextvars.get_contextvars().get("request_id")
        if request_id is not None:
            context["request_id"] = request_id
        with self._lock:
            self._seq += 1
            event: Event = {
                "id": self._seq,
                "ts": time.time(),
                "type": type_,
                **context,
                **fields,
            }
            self._events.append(event)
            subscribers = list(self._subscribers.items())
        for queue, loop in subscribers:
            try:
                loop.call_soon_threadsafe(_offer, queue, event)
            except RuntimeError:
                # The subscriber's loop is closed
                self.unsubscribe(queue)

    def recent(self) -> list[Event]:
        with self._lock:
            return list(self._events)

    def subscribe(self) -> asyncio.Queue[Event]:
        """A queue of the events published from now on (call on the loop)."""
        queue: asyncio.Queue[Event] = asyncio.Queue(SUBSCRIBER_QUEUE)
        with self._lock:
            self._subscribers[queue] = asyncio.get_running_loop()
        return queue

    def unsubscribe(self, queue: asyncio.Queue[Event]) -> None:
        with self._lock:
            self._subscribers.pop(queue, None)


def _offer(queue: asyncio.Queue[Event], event: Event) -> None:
    if queue.full():
        queue.get_nowait()
    queue.put_nowait(event)


def extract_domain(url: str) -> str:
    """The second-level domain of *url* (``voe`` of ``https://voe.sx/e/a``)."""
    try:
        parts = (urlparse(url).hostname or "").split(".")
    except ValueError:
        return ""
    return parts[-2] if len(parts) >= 2 else ""


def _clean(text: str) -> str:
    """*text* without URLs (their paths and queries carry tokens), shortened."""
    text = _URL_RE.sub(lambda m: extract_domain(m.group()) or "url", text)
    return text if len(text) <= _MAX_TEXT else text[: _MAX_TEXT - 1] + "…"


class FeedLogHandler(logging.Handler):
    """Publishes the warnings and errors of the logs to an ``EventFeed``."""

    def __init__(self, feed: EventFeed) -> None:
        super().__init__(level=logging.WARNING)
        self._feed = feed

    def emit(self, record: logging.LogRecord) -> None:
        try:
            fields: dict[str, Any] = {}
            message = record.msg
            if isinstance(message, dict):
                event = str(message.get("event", ""))
                for key in _LOG_FIELDS:
                    value = message.get(key)
                    if isinstance(value, str | int | float):
                        fields[key] = value
                url = message.get("url")
                if isinstance(url, str) and url:
                    fields["domain"] = extract_domain(url)
                error = message.get("error")
                if error is not None:
                    fields["error"] = _clean(str(error))
            else:
                event = record.getMessage()
            self._feed.publish(
                "log",
                level=record.levelname.lower(),
                event=_clean(event),
                logger=record.name,
                **fields,
            )
        except Exception:  # noqa: BLE001
            # A broken feed must never break the code that logs
            self.handleError(record)
