<div align="center">

# Scavengarr

**Self-hosted, German-first streams for Stremio — plus a Torznab indexer for your Arr stack.**

[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue)](LICENSE)
[![Python 3.12 – 3.14](https://img.shields.io/badge/python-3.12%20%E2%80%93%203.14-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Version](https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2FStrob0t%2FScavengarr%2Fmain%2Fpyproject.toml&query=%24.tool.poetry.version&label=version&color=green)](CHANGELOG.md)
[![Stremio addon](https://img.shields.io/badge/Stremio-addon-8A5AAB)](docs/current/stremio-addon.md)
[![Torznab](https://img.shields.io/badge/Torznab-Prowlarr%20%7C%20Sonarr%20%7C%20Radarr-orange)](docs/reference/torznab-api.md)

[Quick Start](#quick-start) ·
[Connect your apps](#connect-your-apps) ·
[Configuration](#configuration) ·
[FAQ](#faq--troubleshooting) ·
[Plugins](docs/reference/plugins.md) ·
[Docs](docs/README.md)

</div>

---

## What is Scavengarr?

Scavengarr turns streaming and direct-download websites into sources your media apps already understand. You run it on your own machine or server; it searches the sites through small Python plugins, checks what it finds, and hands the results to:

- **Stremio**, as a community addon: open a movie or an episode, and Scavengarr answers with streams that are resolved to real video URLs and checked for playback before they show up. German audio is ranked first, followed by German subtitles and English.
- **Prowlarr, Sonarr, Radarr and other Arr apps**, as a Torznab indexer: every plugin is its own indexer, results carry validated direct-download links, and multi-link releases can be bundled as JDownloader `.crawljob` files.

Scavengarr hosts nothing itself. It is a search-and-verify layer between the sites you choose and the apps you already use.

---

## Table of Contents

- [How it works](#how-it-works)
- [Features](#features)
- [Quick Start](#quick-start)
- [Connect your apps](#connect-your-apps)
- [Configuration](#configuration)
- [Supported sources](#supported-sources)
- [FAQ / Troubleshooting](#faq--troubleshooting)
- [Documentation](#documentation)
- [How Scavengarr is built](#how-scavengarr-is-built)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## How it works

```mermaid
flowchart LR
    stremio([Stremio]) -- "stream request<br/>IMDb / TMDB / Kitsu id" --> api
    arr([Prowlarr / Sonarr / Radarr]) -- "Torznab search" --> api

    subgraph scavengarr [Scavengarr]
        api[HTTP API] --> title[Title lookup<br/>per language]
        title --> search[Plugin search<br/>parallel, time-boxed]
        search --> validate[Link validation]
        validate --> resolve[Hoster resolution<br/>+ playback check]
        validate --> torznab[Torznab XML<br/>+ .crawljob]
    end

    search <--> sites[(Streaming and<br/>download sites)]
    resolve <--> hosters[(Video hosters)]
    resolve -- "ranked, playable streams" --> stremio
    torznab -- "releases" --> arr
```

1. **Title lookup.** A Stremio request carries an IMDb, TMDB or Kitsu id (an anime catalog's Kitsu id is translated to its IMDb id first). Scavengarr looks up the title and year in every language its plugins search in (TMDB, or IMDb/Wikidata without a TMDB key), and for an episode its title, air date and number, so the plugins that read a site's season pages find the episode the way the site numbers it.
2. **Plugin search.** All matching plugins search in parallel. Each plugin runs its own multi-stage scrape (search page → detail pages → links); the answer goes out at its budget with what is known, a plugin still searching then finishes in the background for the next request, and sites that keep failing are skipped for a while by a circuit breaker.
3. **Filtering and validation.** Results are matched against the title (sequels and spin-offs are filtered out), narrowed to the requested episode, and their links are checked in parallel.
4. **Stremio: resolution.** Hoster embed links are turned into direct video URLs by 63 hoster resolvers. Every resolved URL gets a playback check (does it actually return video?). One working stream per hoster and language is returned, ranked by language, quality and hoster.
5. **Torznab: packaging.** For the Arr apps, results become Torznab XML with validated links; links behind a captcha or download quota are resolved only when you grab the release.

---

## Features

### Stremio addon

- Streams for movies and series episodes, looked up by IMDb (`tt…`), TMDB (`tmdb:…`) or Kitsu (`kitsu:…`, Stremio's anime catalogs) id
- Anime episodes numbered the way the sites count them: an IMDb episode of a long-running anime carries its Kitsu number, and the anime plugins place it on the site's own season pages
- Hoster links resolved to direct video URLs (MP4 and HLS), with the playback headers Stremio needs
- HLS streams play through Scavengarr's HLS proxy (the CDN's headers on every request, three segments fetched ahead for CDNs that throttle a connection), and files that a hoster binds to the resolving address through its file proxy
- Playback check: resolved URLs that return an error page or no video are dropped before you see them
- Ranking by language (German audio first by default), quality and hoster reliability; quality and size are read from the stream itself (an HLS playlist's resolution, a file's length) where the site names none
- One working stream per hoster and language (dub and sub both stay): if a hoster's best link is dead, its next link is tried
- Autoplay of the next episode (Stremio's binge watching keeps the language of the current stream)
- Answer budget: a request answers 30 s after its start with what is known, earlier at 5 resolved streams or when everything is done, at the latest after 60 s (defaults), so Stremio always gets an answer in time; plugins still searching then finish in the background, and the next request for the title gets their streams
- Catalogs: trending titles (needs a TMDB API key) and search (TMDB, or IMDb without a key)

### Arr indexer (Torznab)

- Every plugin is a Torznab indexer (`/api/v1/torznab/<plugin>`) for Prowlarr, Sonarr, Radarr and other Arr apps
- Category filtering (movies, TV) and pagination
- Validated download links: dead links are removed before the results reach your apps
- JDownloader `.crawljob` bundles for releases with several links
- Grab-time resolution: links behind a captcha or a download quota are resolved only when a release is grabbed

### Sources and hosters

- 43 plugins for streaming, direct-download and anime sites, mostly German-language — see the [plugin list](docs/reference/plugins.md)
- 63 hoster resolvers (streaming hosters, direct-download hosters, XFS-based hosters)
- The public broadcasters' mediatheken (German, Austrian and Swiss): films, documentaries and series episodes from the broadcasters' own files, without a hoster
- Two engines: `httpx` for static pages and APIs, a real browser (Patchright/Playwright) for sites that need JavaScript
- Mirror fallback: plugins try alternative domains when the primary one is down, and follow a site's own published list of its addresses
- Multi-language search: titles are looked up in each plugin's language

### Anti-bot and captchas

- Headful browser that passes Cloudflare Turnstile; clearance cookies survive restarts
- Built-in solvers for ALTCHA proof-of-work and a simple image captcha
- Optional [Byparr](https://github.com/ThePhaseless/Byparr) / FlareSolverr sidecar for sites the built-in browser cannot pass

### Reliability and performance

- Parallel, time-boxed plugin search with a per-plugin circuit breaker (cooldown grows while a site stays down)
- Hoster resolutions (an hour for a stream, 15 minutes for a dead link) and open circuit breakers survive a restart
- Global concurrency pool with fair-share slots across simultaneous requests, auto-tuned from container CPU and memory limits
- One shared browser process for all browser-based plugins
- Adaptive per-domain rate limiting for outgoing requests, per-IP limit for the API
- Plugin scoring: background probes rank plugins by health and search quality
- Search result cache (diskcache/SQLite or Redis)

### Operations

- Single container with Docker Compose from a published `linux/amd64` and `linux/arm64` image; optional Byparr, Redis and Tempo profiles
- Health, readiness and metrics endpoints (`/api/v1/healthz`; `/api/v1/readyz`, which the image's healthcheck asks and which answers 503 once the network is lost for 5 min; Prometheus `/metrics` with a Grafana dashboard and alert rules in `docker/`, `/api/v1/stats/metrics`)
- Structured logs (JSON or console) with per-plugin context
- A record per plugin and day, kept 180 days: searches, results, timeouts, challenges and site checks (`/api/v1/stats/plugins`), the evidence for keeping or dropping a plugin whose site died
- Graceful shutdown that drains in-flight requests, bounded at 5 s so a playback still open cannot hold the stop past Docker's grace
- Configuration via YAML, environment variables or CLI flags

---

## Quick Start

### Docker Compose (recommended)

Requirements: Docker with the Compose plugin, about 2 GB of free RAM (the browser engine is part of the image).

```bash
git clone https://github.com/Strob0t/Scavengarr.git
cd Scavengarr
docker compose up -d
```

Compose pulls the published image `ghcr.io/strob0t/scavengarr:latest` (`linux/amd64` and `linux/arm64`; the plugins are part of it). Then check that it is running:

```bash
curl http://localhost:7979/api/v1/healthz
```

The answer names the version, the commit and the build time.

Image tags: `latest` (the newest release), `vX.Y.Z` (one release), `staging` (every push to the development branch, before its CI result) and `sha-<commit>` (one build). Every release has its page under the repository's Releases, with the changes from its changelog section. [Deploy Scavengarr](docs/how-to/deploy.md) has the details.

Scavengarr reads `data/config.yaml` (mounted into the container; when the file is missing, the container writes the default there on its first start, if the directory is writable for its user, uid 1000). Edit the config and run `docker compose restart` to apply changes. In Docker, the log level and format, headless mode and the cache and plugin directories come from environment variables (`Dockerfile.prod`, `docker-compose.yml`), which beat `config.yaml`: change those in `docker-compose.yml`.

The compose file joins Traefik's external `proxy` network (create it once with `docker network create proxy`; set the router's `Host(...)` rule, and `TMDB_API_KEY` in `.env` if you have a key; no port is published) and always runs [Byparr](https://github.com/ThePhaseless/Byparr), the captcha solver, wired in through `SCAVENGARR_PLAYWRIGHT_SOLVER_URL`.

**Updating:**

```bash
docker compose pull
docker compose up -d
```

An updater such as watchtower can do this on its own, since nothing is built locally. `git pull` brings changes to `docker-compose.yml` and the default `data/config.yaml`, which the image does not apply to an existing config.

**Building from source:** in `docker-compose.yml`, replace the `image:` line with the commented `build:` block and run `docker compose up -d --build` (the first build takes a few minutes: it installs the browser). The build records the checkout's commit and the build time for the health answer and the startup log; a rebuild of the same commit keeps the first build's time unless the build arguments set them:

```bash
SCAVENGARR_COMMIT=$(git rev-parse --short=12 HEAD) \
SCAVENGARR_BUILT=$(date -u +%Y-%m-%dT%H:%M:%SZ) docker compose up -d --build
```

### Without Docker (Poetry)

Requirements: Python 3.12–3.14 (the Docker image runs 3.14), [Poetry](https://python-poetry.org/).

```bash
git clone https://github.com/Strob0t/Scavengarr.git
cd Scavengarr
poetry install
poetry run python -m patchright install chromium   # browser for JS-heavy sites
poetry run start --host 0.0.0.0 --port 7979 --config data/config.yaml
```

The browser also needs system libraries: install them once with `sudo poetry run python -m patchright install-deps chromium`. Without Docker the browser runs headful and needs a display: without one it falls back to headless (`browser_headful_no_display` in the log), which fails Cloudflare Turnstile. On a server use `xvfb-run -a poetry run start …`.

---

## Connect your apps

### Stremio

1. Open Stremio → **Addons** → search field (or the addon URL box).
2. Enter the manifest URL:
   ```text
   https://<your-host>/api/v1/stremio/manifest.json
   ```
3. Click **Install**. Open any movie or episode; Scavengarr's streams appear in the stream list.

Stremio only loads addons over **HTTPS** (except on `localhost`). Put Scavengarr behind a reverse proxy with a certificate (Caddy, Traefik, nginx) when you use it from other devices; `docker-compose.yml` trusts the proxy's `X-Forwarded-Proto` from private networks (`FORWARDED_ALLOW_IPS`), so the links Scavengarr builds use `https://`. Details: [Deploying the Stremio addon](docs/how-to/stremio-deployment.md).

### Prowlarr (and through it Sonarr/Radarr)

Each plugin is added as its own indexer:

1. Prowlarr → **Settings → Indexers → Add Indexer → Generic Torznab**.
2. **URL:** `http://<your-host>:7979/api/v1/torznab/<plugin>` (plugin names: [plugin list](docs/reference/plugins.md)).
3. **API Key:** leave empty.
4. **Categories:** `2000` (Movies), `5000` (TV).
5. **Test**, then **Save**. Prowlarr syncs the indexer to Sonarr and Radarr.

Download plugins deliver direct-download links; send them to JDownloader (e.g. via the `.crawljob` bundles). Details: [Connect Prowlarr](docs/how-to/connect-prowlarr.md), [Torznab API](docs/reference/torznab-api.md).

---

## Configuration

Scavengarr works out of the box with [`data/config.yaml`](data/config.yaml). Settings are read in this order (first wins): CLI flags → `SCAVENGARR_*` environment variables (a `--dotenv` file's values included; real variables win over them) → YAML file → defaults.

The settings you are most likely to change:

| Setting (YAML) | Environment variable | Built-in default | What it does |
|---|---|---|---|
| `stremio.plugin_timeout_seconds` | `SCAVENGARR_STREMIO_PLUGIN_TIMEOUT_SECONDS` | `30` | Each plugin's search time, from the moment it holds a slot; also the answer budget unless `stremio.answer_budget_seconds` is set |
| `stremio.answer_budget_seconds` | `SCAVENGARR_STREMIO_ANSWER_BUDGET_SECONDS` | unset (the plugin timeout) | When a Stremio request stops waiting for the search, counted from the request start; the plugins still searching finish in the background |
| `stremio.stream_deadline_seconds` | `SCAVENGARR_STREMIO_STREAM_DEADLINE_SECONDS` | `60` | Latest answer of a Stremio request; it goes out earlier at `stremio.resolve_target_count` (5) streams or when everything is done |
| `stremio.verify_streams` | `SCAVENGARR_STREMIO_VERIFY_STREAMS` | `true` | Drop resolved streams that do not return video |
| `stremio.language_scores` | `SCAVENGARR_STREMIO_LANGUAGE_SCORES` (JSON) | `de` > `de-sub` > `en-sub` > `en` | Language ranking of streams |
| `stremio.max_results_per_plugin` | `SCAVENGARR_STREMIO_MAX_RESULTS_PER_PLUGIN` | `100` (`data/config.yaml`: `50`) | Results per plugin and Stremio request |
| `tmdb_api_key` | `SCAVENGARR_TMDB_API_KEY` | unset | TMDB key for catalogs and title lookup (IMDb/Wikidata fallback without it) |
| `playwright.solver_url` | `SCAVENGARR_PLAYWRIGHT_SOLVER_URL` | unset | Byparr/FlareSolverr sidecar, e.g. `http://byparr:8191` |
| `playwright.headless` | `SCAVENGARR_PLAYWRIGHT_HEADLESS` | `false` | Headful browser passes Cloudflare Turnstile; needs a display (Xvfb in the image) |
| `cache.backend` | `SCAVENGARR_CACHE_BACKEND` | `diskcache` | `diskcache` or `redis` |
| `cache.search_ttl_seconds` | `SCAVENGARR_CACHE_SEARCH_TTL_SECONDS` | `900` (`data/config.yaml`: `1800`) | How long search results are cached (`0` = off) |
| `http.rate_limit_rps` | `SCAVENGARR_RATE_LIMIT_REQUESTS_PER_SECOND` | `5.0` (`data/config.yaml`: `10.0`) | Starting request rate per site (adaptive) |
| `http.api_rate_limit_rpm` | `SCAVENGARR_API_RATE_LIMIT_RPM` | `120` | Requests per minute per client IP on the API |
| `logging.level` | `SCAVENGARR_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

Every setting can also come from the environment: a section's key as `SCAVENGARR_<SECTION>_<KEY>`, a dict-typed one as JSON (the older names in the table win over the sectioned ones). The answer does not wait for the whole search: it goes out once 5 streams resolve, or at its budget with what is known by then. The full reference is in [docs/reference/configuration.md](docs/reference/configuration.md).

---

## Supported sources

Scavengarr ships 43 plugins: streaming sites (used by the Stremio addon), direct-download sites (served via Torznab), anime sites and the public broadcasters' mediatheken, most of them German-language. Six of them use the browser engine, the rest plain HTTP.

The complete, generated list with domains, content type, engine and languages is in **[docs/reference/plugins.md](docs/reference/plugins.md)**. Sites change often. In Stremio searches, a plugin that keeps failing is skipped by the circuit breaker, and a site that does not answer by the health check, until it is back; Torznab requests still reach it.

Want a site that is missing? Plugins are single Python files — see [Contributing](#contributing).

---

## FAQ / Troubleshooting

<details>
<summary><b>Stremio shows no Scavengarr streams at all</b></summary>

- Check that the addon is reachable from the device: open `https://<your-host>/api/v1/stremio/manifest.json` in its browser.
- Stremio needs HTTPS for addons that are not on `localhost` (see [Connect your apps](#stremio)).
- Look at the logs: `docker compose logs -f scavengarr`. Each request logs `stremio_search_complete` with the number of results, matches and streams.
- If results are found but no streams come back, the hosters could not be resolved or failed the playback check (`hoster_resolve_unplayable` in the logs). That happens when every hoster of a title is down.

</details>

<details>
<summary><b>Streams take long to appear</b></summary>

An answer goes out once `stremio.resolve_target_count` streams (5) resolve, or when the search and every resolution are done, at the latest after `stream_deadline_seconds` (60 s by default). For faster answers with fewer streams, lower `resolve_target_count` (e.g. 3) or `stream_deadline_seconds`; for more streams per answer, raise `resolve_target_count`.

</details>

<details>
<summary><b>A stream is listed but does not play</b></summary>

Every stream passed a playback check when it was listed, and Scavengarr resolves the hoster link again when an old stream is played, but the hoster may have removed the file meanwhile, and stream links are kept 7 days. Pick another stream or request the title again. Some hosters bind their files to the address that resolved them: Scavengarr passes those through its own file proxy, so the device playing them needs no route of its own to the hoster.

</details>

<details>
<summary><b>A site is behind Cloudflare or a captcha</b></summary>

The built-in headful browser passes most Cloudflare challenges; in Docker it runs on a virtual display automatically. For sites it cannot pass, use the Byparr sidecar (a service of `docker-compose.yml`, wired in through `SCAVENGARR_PLAYWRIGHT_SOLVER_URL`). See [Browser and challenges](docs/current/browser-and-challenges.md).

</details>

<details>
<summary><b>A plugin returns nothing or keeps timing out</b></summary>

Sites move, go down or change their layout. In Stremio searches, the circuit breaker skips a plugin after repeated failures for a while (the pause grows up to one hour while it stays down), and the health check skips a site that does not answer, so a dead site does not slow down your requests; Torznab requests still reach it. Check `/api/v1/stats/metrics` for per-plugin errors and timeouts, and search the issues or open one with the plugin name and the log lines.

</details>

<details>
<summary><b>My whole network gets slow or connections fail while Scavengarr searches</b></summary>

Some home routers treat many new connections to different hosts in a short time like a port scan and block the machine for a minute or two. Scavengarr already limits this (at most 4 link checks per host, one link per hoster at a time during resolution). If it still happens, set `stremio.auto_tune_all` and `stremio.max_concurrent_plugins_auto` to `false` (auto-tuning overwrites the limits at startup), then lower `stremio.max_concurrent_plugins` and `stremio.probe_concurrency`, or run Scavengarr behind a router without that protection.

</details>

<details>
<summary><b>Prowlarr's test fails</b></summary>

- The URL must include the plugin name: `http://<host>:7979/api/v1/torznab/<plugin>`.
- Leave the API key empty.
- A plugin whose site is currently down fails the test; try another plugin to rule out a connection problem.

</details>

<details>
<summary><b>Where is my data stored?</b></summary>

In the `scavengarr-cache` Docker volume (search cache, browser clearance cookies and the state of the hosters the browser plays, plugin scores and their 180-day record, hoster resolutions and circuit breakers) and in `data/config.yaml`. Scavengarr stores no media.

</details>

---

## Documentation

The index [docs/README.md](docs/README.md) maps the document groups, states what the docs cover and what is open, and lists every document with its status and the rules the documents follow. By topic:

| Topic | Link |
|---|---|
| Stremio addon | [docs/current/stremio-addon.md](docs/current/stremio-addon.md) |
| Deploying the Stremio addon (HTTPS, reverse proxy) | [docs/how-to/stremio-deployment.md](docs/how-to/stremio-deployment.md) |
| Deployment | [docs/how-to/deploy.md](docs/how-to/deploy.md) |
| Torznab API | [docs/reference/torznab-api.md](docs/reference/torznab-api.md) |
| Torznab and CrawlJobs | [docs/current/torznab-and-crawljobs.md](docs/current/torznab-and-crawljobs.md) |
| Connecting Prowlarr | [docs/how-to/connect-prowlarr.md](docs/how-to/connect-prowlarr.md) |
| Configuration reference | [docs/reference/configuration.md](docs/reference/configuration.md) |
| Observability | [docs/current/observability.md](docs/current/observability.md) |
| Metrics reference | [docs/reference/metrics.md](docs/reference/metrics.md) |
| Operating production | [docs/how-to/operations.md](docs/how-to/operations.md) |
| Measuring a change | [docs/how-to/performance-measurement.md](docs/how-to/performance-measurement.md) |
| The dev container (setup, worktrees, hooks) | [docs/how-to/dev-container.md](docs/how-to/dev-container.md) |
| Known issues | [docs/current/known-issues.md](docs/current/known-issues.md) |
| Plugin list | [docs/reference/plugins.md](docs/reference/plugins.md) |
| Plugins | [docs/current/plugins.md](docs/current/plugins.md) |
| Plugin domains | [docs/current/plugin-domains.md](docs/current/plugin-domains.md) |
| Writing a plugin | [docs/how-to/new-plugin.md](docs/how-to/new-plugin.md) |
| Resolver list | [docs/reference/resolvers.md](docs/reference/resolvers.md) |
| Hoster resolvers | [docs/current/hoster-resolvers.md](docs/current/hoster-resolvers.md) |
| Writing a resolver | [docs/how-to/new-resolver.md](docs/how-to/new-resolver.md) |
| Link validation | [docs/current/link-validation.md](docs/current/link-validation.md) |
| Browser and challenges | [docs/current/browser-and-challenges.md](docs/current/browser-and-challenges.md) |
| Architecture as built | [docs/current/architecture.md](docs/current/architecture.md) |
| Architecture rules | [docs/target/architecture.md](docs/target/architecture.md) |
| Coding guidelines | [docs/target/coding-guidelines.md](docs/target/coding-guidelines.md) |
| Tech stack and the reasons for it | [docs/reference/tech-stack.md](docs/reference/tech-stack.md) |
| Glossary of the codebase's terms | [docs/reference/glossary.md](docs/reference/glossary.md) |
| Decision records | [docs/target/decisions/](docs/target/decisions/) |
| Plans in work | [docs/plans/](docs/plans/) |
| The work queue | [docs/backlog.md](docs/backlog.md) |
| How the coding assistants work | [docs/agents/orchestration.md](docs/agents/orchestration.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) |

`tests/unit/infrastructure/test_readme.py` keeps this table and the counts above current: every document under `docs/current/`, `docs/how-to/` and `docs/reference/` is linked here, and the plugin and resolver counts are those of the generated lists.

---

## How Scavengarr is built

Most of Scavengarr's code was written with AI coding assistants — it is, openly, a largely vibe-coded project. It is not an unreviewed one: every change was directed, reviewed and accepted by an experienced software developer, and the project follows rules that keep the generated code honest:

- **Test-driven development.** Tests come first; the suite has about 7,000 unit, integration and end-to-end tests, plus opt-in live tests against the real sites.
- **Clean Architecture.** Strict layers (domain, application, infrastructure, interfaces) with a dependency rule, ports as protocols and a single composition root.
- **Quality gates on every commit.** `ruff` linting and formatting, type-annotated code checked by basedpyright, pre-commit hooks and the full test suite before anything is committed.
- **Dependencies with their reasons.** Every package in `pyproject.toml` has its line in [docs/reference/tech-stack.md](docs/reference/tech-stack.md) with what it does and why it was chosen, beside the alternatives deliberately not used; a test fails when a dependency comes or goes without it.
- **Written plans and measurements.** Larger changes start with a plan in [`docs/plans/`](docs/plans), and performance changes are measured against real requests before and after.
- **Documentation ships with the code.** Behaviour, configuration and architecture changes update the docs and the changelog in the same commit.

The rules the assistants work under are public in [AGENTS.md](AGENTS.md).

---

## Contributing

Contributions are welcome — new plugins and hoster resolvers most of all. Development setup, tests, code style, commit conventions and step-by-step guides are in **[CONTRIBUTING.md](CONTRIBUTING.md)**.

---

## Disclaimer

Scavengarr does not host, store or distribute any content. It only searches websites chosen by its user and reads what those websites publish themselves. The authors are not affiliated with any of the sites or hosters the plugins or resolvers talk to and do not endorse them.

You are solely responsible for how you use Scavengarr: comply with the laws of your country and the terms of the sites you use, and only access content you are allowed to access. The software is provided "as is", without warranty of any kind (see the [license](LICENSE)).

---

## Acknowledgements

Scavengarr builds on the work of many projects:

- [Prowlarr](https://github.com/Prowlarr/Prowlarr), [Sonarr](https://github.com/Sonarr/Sonarr) and [Radarr](https://github.com/Radarr/Radarr) — the Arr ecosystem and the Torznab conventions Scavengarr speaks
- [Stremio](https://www.stremio.com/) and its [addon SDK and protocol](https://github.com/Stremio/stremio-addon-sdk)
- [JDownloader](https://jdownloader.org/) — many hoster resolvers are ports of its open-source hoster plugins
- [Byparr](https://github.com/ThePhaseless/Byparr) and [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) — captcha and challenge solving
- [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python) and [Playwright](https://playwright.dev/) — browser automation
- [FastAPI](https://fastapi.tiangolo.com/), [httpx](https://www.python-httpx.org/), [structlog](https://www.structlog.org/), [guessit](https://github.com/guessit-io/guessit), [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) and [diskcache](https://github.com/grantjenks/python-diskcache)
- [TMDB](https://www.themoviedb.org/) and [Wikidata](https://www.wikidata.org/) for title metadata (this product uses the TMDB API but is not endorsed or certified by TMDB)

---

## License

Scavengarr is licensed under the [GNU General Public License v3.0](LICENSE).
