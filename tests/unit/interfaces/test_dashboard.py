"""The dashboard's event feed: stages, log lines and the stream."""

from __future__ import annotations

import asyncio
import json
import logging

import httpx
import pytest
from fastapi import FastAPI

from scavengarr.infrastructure.graceful_shutdown import GracefulShutdown
from scavengarr.infrastructure.telemetry import Telemetry
from scavengarr.infrastructure.telemetry.events import EventFeed, FeedLogHandler
from scavengarr.interfaces.api.dashboard import router
from scavengarr.interfaces.app_state import AppState


def test_stage_publishes_outcome_and_labels() -> None:
    telemetry = Telemetry()
    with telemetry.stage("hoster_resolve", resolver="voe") as stage:
        stage.outcome = "stream"
    telemetry.count("hoster_resolve", "cached", resolver="doodstream")

    first, second = telemetry.feed.recent()
    assert first["type"] == "stage"
    assert (first["stage"], first["resolver"], first["outcome"]) == (
        "hoster_resolve",
        "voe",
        "stream",
    )
    assert first["duration_ms"] >= 0
    assert second["outcome"] == "cached"
    assert "duration_ms" not in second


def test_stage_with_a_kind_label_does_not_clash_with_the_envelope() -> None:
    telemetry = Telemetry()
    with telemetry.stage("browser_page", kind="capture"):
        pass

    (event,) = telemetry.feed.recent()
    assert event["type"] == "stage"
    assert event["kind"] == "capture"


def test_a_failing_stage_is_published_as_error() -> None:
    telemetry = Telemetry()
    with pytest.raises(RuntimeError), telemetry.stage("plugin_search", plugin="x"):
        raise RuntimeError("boom")

    (event,) = telemetry.feed.recent()
    assert event["outcome"] == "error"


def test_hls_segments_stay_out_of_the_feed() -> None:
    telemetry = Telemetry()
    with telemetry.stage("hls_proxy", kind="segment"):
        pass
    with telemetry.stage("hls_readahead"):
        pass

    assert telemetry.feed.recent() == []


def test_plugin_results_are_published_as_values() -> None:
    telemetry = Telemetry()
    telemetry.record("plugin_results", 3, plugin="kinoger")

    (event,) = telemetry.feed.recent()
    assert (event["type"], event["plugin"], event["value"]) == ("value", "kinoger", 3)


def test_backlog_is_bounded() -> None:
    feed = EventFeed(size=3)
    for i in range(5):
        feed.publish("stage", n=i)

    assert [e["n"] for e in feed.recent()] == [2, 3, 4]


def test_log_handler_keeps_warnings_with_a_domain_and_no_url() -> None:
    feed = EventFeed()
    handler = FeedLogHandler(feed)
    logger = logging.getLogger("test_dashboard_feed")
    logger.propagate = False
    logger.addHandler(handler)
    try:
        logger.info({"event": "ignored"})
        logger.warning(
            {
                "event": "hoster_resolve_failed",
                "hoster": "voe",
                "url": "https://voe.sx/e/secret?token=abc",
                "error": "GET https://cdn.example.net/a/b?i=1.2.3.4 failed",
                "title": "Some Movie",
            }
        )
    finally:
        logger.removeHandler(handler)

    (event,) = feed.recent()
    assert event["level"] == "warning"
    assert event["event"] == "hoster_resolve_failed"
    assert event["hoster"] == "voe"
    assert event["domain"] == "voe"
    assert "secret" not in json.dumps(event)
    assert "1.2.3.4" not in json.dumps(event)
    assert "Some Movie" not in json.dumps(event)


def test_log_handler_takes_plain_stdlib_records() -> None:
    feed = EventFeed()
    handler = FeedLogHandler(feed)
    logger = logging.getLogger("test_dashboard_feed_plain")
    logger.propagate = False
    logger.addHandler(handler)
    try:
        logger.error("failed for %s", "https://host.example/path?x=1")
    finally:
        logger.removeHandler(handler)

    (event,) = feed.recent()
    assert event["level"] == "error"
    assert event["event"] == "failed for host"


async def test_subscriber_receives_events_from_another_thread() -> None:
    feed = EventFeed()
    queue = feed.subscribe()
    await asyncio.to_thread(feed.publish, "log", event="from a worker")

    event = await asyncio.wait_for(queue.get(), 1)
    assert event["event"] == "from a worker"
    feed.unsubscribe(queue)


def _app() -> tuple[FastAPI, Telemetry]:
    app = FastAPI()
    app.state = AppState()
    app.state.telemetry = telemetry = Telemetry()
    app.state.graceful_shutdown = GracefulShutdown()
    app.include_router(router)
    return app, telemetry


async def test_page_is_served() -> None:
    app, _ = _app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://t"
    ) as client:
        response = await client.get("/dashboard")

    assert response.status_code == 200
    assert "EventSource" in response.text


async def test_recent_returns_the_backlog() -> None:
    app, telemetry = _app()
    telemetry.count("plugin_search", "hits", plugin="kinoger")
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://t"
    ) as client:
        response = await client.get("/api/v1/dashboard/recent")

    (event,) = response.json()["events"]
    assert event["plugin"] == "kinoger"


async def test_stream_replays_backlog_then_live_events_and_skips_seen() -> None:
    app, telemetry = _app()
    telemetry.count("plugin_search", "hits", plugin="old")
    telemetry.count("plugin_search", "hits", plugin="seen")
    shutdown: GracefulShutdown = app.state.graceful_shutdown

    seen_plugins: list[str] = []
    async with (
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://t"
        ) as client,
        client.stream(
            "GET", "/api/v1/dashboard/events", headers={"Last-Event-ID": "1"}
        ) as response,
    ):
        assert response.headers["content-type"].startswith("text/event-stream")
        telemetry.count("plugin_search", "timeout", plugin="live")
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                seen_plugins.append(json.loads(line[6:])["plugin"])
            if "live" in seen_plugins:
                shutdown._shutting_down = True

    assert seen_plugins == ["seen", "live"]


def test_events_carry_the_search_of_the_running_request() -> None:
    import contextvars

    from scavengarr.domain.ports.telemetry import bind_search

    telemetry = Telemetry()

    def run() -> None:
        bind_search(imdb="tt1", season=1, episode=2)
        bind_search(title="Some Movie", year=1999)
        telemetry.count("hoster_resolve", "stream", resolver="voe")

    contextvars.copy_context().run(run)
    telemetry.count("hoster_resolve", "stream", resolver="voe")

    tagged, untagged = telemetry.feed.recent()
    assert (tagged["title"], tagged["year"], tagged["imdb"]) == (
        "Some Movie",
        1999,
        "tt1",
    )
    assert (tagged["season"], tagged["episode"]) == (1, 2)
    assert "title" not in untagged
