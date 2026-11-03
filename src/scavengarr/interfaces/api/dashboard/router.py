"""The live dashboard: a page and the event stream it listens to."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import cast

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from scavengarr.infrastructure.telemetry.events import Event
from scavengarr.interfaces.app_state import AppState

router = APIRouter(tags=["dashboard"])

_PAGE = Path(__file__).with_name("index.html")

# The stream wakes this often to see a closed client or the shutdown, and
# sends a comment line every _PINGS_PER_COMMENT wakes to keep proxies open
_POLL_SECONDS = 1.0
_PINGS_PER_COMMENT = 15


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def page() -> HTMLResponse:
    return HTMLResponse(_PAGE.read_text(encoding="utf-8"))


@router.get("/api/v1/dashboard/recent")
async def recent(request: Request) -> JSONResponse:
    """The last events (a plain JSON read of what the stream replays)."""
    state = cast(AppState, request.app.state)
    return JSONResponse(content={"events": state.telemetry.feed.recent()})


def _frame(event: Event) -> str:
    return f"id: {event['id']}\ndata: {json.dumps(event)}\n\n"


@router.get("/api/v1/dashboard/events")
async def events(request: Request) -> StreamingResponse:
    """Server-sent events: the backlog first, then every new event.

    A reconnecting browser sends ``Last-Event-ID``; the events up to it are
    not repeated.
    """
    state = cast(AppState, request.app.state)
    feed = state.telemetry.feed
    try:
        last_id = int(request.headers.get("last-event-id", "0"))
    except ValueError:
        last_id = 0

    async def stream() -> AsyncIterator[str]:
        # Subscribed before the backlog is read, so no event falls between them
        queue = feed.subscribe()
        seen = last_id
        try:
            for event in feed.recent():
                if event["id"] > seen:
                    seen = event["id"]
                    yield _frame(event)
            idle = 0
            while not state.graceful_shutdown.is_shutting_down:
                try:
                    event = await asyncio.wait_for(queue.get(), _POLL_SECONDS)
                except TimeoutError:
                    if await request.is_disconnected():
                        return
                    idle += 1
                    if idle >= _PINGS_PER_COMMENT:
                        idle = 0
                        yield ": ping\n\n"
                    continue
                idle = 0
                if event["id"] > seen:
                    seen = event["id"]
                    yield _frame(event)
        finally:
            feed.unsubscribe(queue)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
