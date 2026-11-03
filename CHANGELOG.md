# Changelog

All notable changes to Scavengarr are documented in this file. Format: version, date, grouped changes. Newest entries first.

---

## Unreleased

Live dashboard.

### Added: Live Dashboard at `/dashboard`

- `GET /dashboard` is a single page (no external assets) that listens to `GET /api/v1/dashboard/events`, a server-sent event stream: the last 500 events first, then every new one (a reconnecting browser's `Last-Event-ID` skips what it has seen). `GET /api/v1/dashboard/recent` returns the same backlog as JSON.
- The page shows per hoster and per plugin the runs, successes, failures and the last outcome, a live feed with filters (plugins, hosters, requests, errors), an errors panel and the open breakers and unresolved hosters (polled from `/api/v1/stats/metrics`).
- Events come from `Telemetry` (every ended stage and every counted outcome, so the labels are the metrics' fixed sets; HLS segments stay out) and from a log handler that forwards warnings and errors with a fixed set of fields, a hoster URL reduced to its second-level domain and URLs in texts reduced the same way. No titles, ids or URL paths.
- The dashboard and its stream are exempt from the API rate limit; the stream ends at shutdown. The page has no login: like `/metrics` it belongs on a trusted network.

---

### Changed: Compose File for Traefik

- `docker-compose.yml` joins the external `proxy` network with Traefik labels (no published port), uses the named volumes `aio_scavengarr-data` (config) and `aio_scavengarr-cache`, takes the TMDB key from `TMDB_API_KEY`, and always runs Byparr, wired in through `SCAVENGARR_PLAYWRIGHT_SOLVER_URL`. The Redis and Tempo services and their profiles are gone from the file.

---

## v0.5.1 - 2026-10-20

Security: certifi's CA bundle drops the root whose intermediate CAs lost their keys (GHSA-6q48-6c7w-9gw2); every httpx client of the app verifies TLS against it, so the image carries the fix with its rebuild. Repository upkeep: CI ends in the one check `main`'s ruleset requires and runs weekly on `main`; Dependabot takes a version a week after its release, updates pre-commit's hooks too, and its green minor and patch updates merge into `staging` by themselves; pre-commit runs the venv's ruff, pinned in `pyproject.toml` only; every release tag gets its page; and the tests check a URL's host exactly.

### Security: certifi's CA Bundle Drops the Compromised emSign Root

- certifi before 2026.10.18 carries the root `emSign ECC Root CA - G3`, below which eight intermediate CAs have compromised keys: whoever holds one and sits on the path can pass a certificate for any host (GHSA-6q48-6c7w-9gw2, Dependabot's critical alert). certifi comes in only through httpx and httpcore, and every httpx client of the app verifies TLS against its bundle.
- `poetry.lock` moves certifi from 2026.7.22 to 2026.10.19 (2026.10.18 removed every emSign root, 2026.10.19 restored the unaffected ones); its bundle names `emSign ECC Root CA - G3` 0 times, against 3 before. No code changes. The production image installs `poetry.lock`, so it carries the fix with its next rebuild.

### Added: A Release Page per Tag

- `.github/workflows/release.yml` runs on every pushed `v*` tag with write access to contents only: it prints the notes with `scripts/release_notes.py <tag>` and creates the release with `gh release create --notes-file --verify-tag`, beside the image that `image.yml` publishes for the tag.
- `scripts/release_notes.py` (standard library only) prints the summary paragraph of the tag's `CHANGELOG.md` section, its entries' titles grouped by kind (Added, Changed, Fixed, Removed, then any other kind as written; a heading without a kind under Other), the image `ghcr.io/strob0t/scavengarr:<tag>` and a link to the full section at the tag, and exits non-zero when the tag has no section, so no page goes out without notes. For v0.5.0 it lists the 87 entries under the four kinds.
- `tests/unit/infrastructure/test_release_notes_script.py` covers a sample changelog, a missing version and the real file's v0.5.0; `test_repository_files.py` checks the workflow's trigger, permissions and commands. AGENTS.md (§1, the release's step 5), `docs/how-to/deploy.md` (the page beside the image tags; `staging` takes a merged Dependabot update too), `docs/reference/tech-stack.md` (`gh` and jq), `openspec/project.md` and the README say so.

### Changed: pre-commit Runs the Venv's ruff

- pre-commit's ruff hooks are `local` hooks that run the venv's ruff through `scripts/venv_tool.sh`, with the entries and file types of `ruff-pre-commit`'s own hooks (`--force-exclude`, `types_or`, `require_serial`), the three in their order. `pyproject.toml`'s pin is the only one: Dependabot's Poetry group updates it, and the rule to bump the `ruff-pre-commit` rev with it is gone.
- `scripts/venv_tool.sh <tool>` is `scripts/basedpyright.sh` generalised to any tool of the venv (the active one, the project's `.venv`, in a worktree the main checkout's), and the basedpyright hook runs through it too. `tests/unit/infrastructure/test_repository_files.py` keeps it executable; AGENTS.md (§9), `docs/how-to/dev-container.md`, `docs/reference/tech-stack.md` and `openspec/project.md` say so.

### Added: Dependabot's Green Minor and Patch Updates Merge Themselves

- `.github/workflows/dependabot-merge.yml` runs after every CI run of a `dependabot/` branch. For a green `pull_request` run of `dependabot[bot]` from this repository it takes the open Dependabot pull request against `staging` whose head commit the run tested, and merges it at that commit (`gh pr merge --merge --match-head-commit`) when every `update-type:` line of the commit message names a minor or patch update, at least one. Then it starts CI and the image on `staging`, as a merge with `GITHUB_TOKEN` starts no push workflow.
- A major update, an update without a type, a base image (its next Python is a runtime change no CI leg builds) and an action wait for the maintainer: `GITHUB_TOKEN` may not change a workflow file, a merge included.
- GitHub runs the workflow from `main` with write access to contents, pull requests and actions, so it checks out nothing, uses no action and reads the event's values through `env:` only. `tests/unit/infrastructure/test_repository_files.py` runs its script with a fake `gh` (a merge; a major update, no type, a base image, an action and a newer head stay open) and checks its trigger and permissions; AGENTS.md (§4) and `openspec/project.md` say so. It takes effect with the next release.

### Changed: Dependabot Waits a Week and Updates pre-commit's Hooks

- Every entry of `.github/dependabot.yml` has `cooldown: default-days: 7`: an update comes 7 days after its release, so a release pulled again within days never reaches `staging`. A security alert shows at once; its fix comes with the weekly update after the cooldown, or by hand.
- A `pre-commit` entry updates the hook revs of `.pre-commit-config.yaml` against `staging`, like the other three.
- `tests/unit/infrastructure/test_repository_files.py` checks both, and AGENTS.md (§4) says so. Dependabot reads its file from `main`, so this takes effect with the next release.

### Added: CI Ends in One Required Check and Runs Weekly

- `.github/workflows/ci.yml` ends in the job `CI passed`, which needs both Python legs and fails unless both passed. It runs after a failed or cancelled leg too (`if: always()`), as a required check that is skipped counts as passed. `main`'s ruleset requires this one name, so the matrix can change without the ruleset.
- A weekly run on `main` (`schedule`; GitHub runs a schedule on the default branch only) shows a break that comes without a push: a new runner image, Python patch or Poetry release.
- `tests/unit/infrastructure/test_repository_files.py` checks the gate job, and that no workflow step puts an expression into its `run:` script: the values come through `env:`, so a branch name or commit message cannot run as code. AGENTS.md (the CI sentence; the release merge waits for `CI passed`), `CONTRIBUTING.md` and `openspec/project.md` say so.

### Changed: Tests Check a URL's Host Exactly

- 37 test lines checked a URL by substring (`"host" in url`), which CodeQL's default setup reports as `py/incomplete-url-substring-sanitization`: none was a gap in the code, but a lookalike host (`d0000d.com.evil.test`) passed them, and they buried a real finding. Each is now an exact check: the parsed host (`urlparse(url).hostname == ...`), `request.url.host == ...` in the fake transports' handlers, a prefix ending in the host's slash, and for a domain list, a hoster list or the Cloudflare block map the exact members or keys instead of `in`.
- In 13 files of `tests/unit/infrastructure/` (ddlspot, boerse, mygully, serienjunkies, warezomen, scnsrc, crawli, sto, megakino_to, the IMDb fallback, the doodstream resolver and both plugin bases); no code changes. A lookalike host now fails the checks it slipped through before (tried in the ddlspot parser, the doodstream pass URL, sto's search results and the IMDb fallback's Wikidata route).

## v0.5.0 - 2026-10-20

Challenges and captchas: a capture that meets a challenge is an outcome of its own, with a cooldown instead of the circuit breaker, and finishes in the background, so the next request finds its stream; a capture hoster's browser state outlives restarts, the browser starts with the app, Filemoon's captcha pass is kept alive while it is in demand, and a capture that met the hoster's captcha waits for it. Playback: the HLS proxy resumes a segment the CDN cuts or stalls and keeps its read-ahead across a pause. Content: the public broadcasters' mediatheken, an original version with its own language, a sub-series no longer gets its parent series' episodes (aniworld, sto), and a Torznab search over several kinds answers every kind. Operations: readiness notices a lost network and the image's healthcheck asks it, the graceful shutdown is bounded at 5 s, and the post-deploy check shows where an answer's time goes. Also the documentation rebuilt around one index, a document contract and decision records, a test of the dependency rule, a live smoke entry for every plugin, and Dependabot's pull requests against `staging`.

### Fixed: The Search Probe Counts a Claimed Host as Supported

- The search probe counted a link as supported by its second-level name against the registry's resolver names and aliases, so a link to a host a resolver claims by its full name (`supported_hosts`) counted as unsupported: the mediathek resolver's 45 broadcaster hosts and strmup's `kinoger.pw`, while filemoon's `moflix-stream.link` counted only through VidHide's alias `moflix-stream`. So the share of supported hosters, a quarter of a plugin's search score, dropped for the plugins that link there. With scored plugin selection off, as in production, it moved only the choice within a mirror group and the reported scores.
- `MiniSearchProber` takes the registry's dispatch lookup instead: `HosterResolverRegistry.resolver_name(url)` names the resolver the dispatch takes for a URL (a claimed host, then the second-level name or an alias), and the composition root passes it in place of the registry's `supported_domains`, which nothing else read and which is gone.
- `tests/unit/infrastructure/test_search_prober.py` covers a claimed host (supported and HEAD-checked), a second-level name and an alias (supported), and another host of a claimed zone and an unknown host (not supported); `test_hoster_registry.py` covers `resolver_name()` the way the dispatch looks up. `docs/current/plugins.md` (the search probe) and `docs/current/hoster-resolvers.md` say so.

### Added: The Public Broadcasters' Mediatheken

- `plugins/mediathek.py` searches the mediatheken of ARD with its regional broadcasters, ZDF, arte, 3sat, KiKA, phoenix, ORF, SRF and more through MediathekViewWeb's API: one GET `/api/query`, newest first, up to 3 pages of 1000 entries of at least 299 s, the first page in the raising mode. Each result links the broadcaster's own file (the HD file, else the normal one) under the hoster `mediathek`. Films and documentaries are 2000, series episodes 5000, and the plugin locates episodes: by the numbers an entry states, else by the reference's episode title, else by its air date against the broadcast day, never by the request's numbers alone.
- It drops the versions for accessibility, the subtitled twins of German versions and arte's channels in other languages; an original version, OmU and an English version are results of their own language. The release name names the channel, the broadcast day (`dd.mm.yy`, which guessit does not read as a year) and the quality the file name tells (a height marker, ZDF's and arte's version codes); `BR` is written "Bayerischer Rundfunk", since guessit reads "BR" as Brazilian Portuguese.
- `hoster_resolvers/mediathek.py` checks a file with `verify_video_url()` and returns it without headers: KiKA's files come as `application/octet-stream`, and a geo-blocked file answers 403. It claims the ARD CDN (`ard-mcdn`) and 45 broadcaster hosts by their full names, since `akamaihd.net` and `akamaized.net` serve other hosters too; playlists go to the content-type probe.
- Live proof on the dev server, Stremio's stream route with only this plugin: a documentary gave 1 stream (3sat, 1080p, German) in 6.59 s, 0.01 s from the cache; a series episode 2 streams (German and English, ZDF, 1080p) in 1.11 s; an episode of a series without numbers, placed by its air date, 1 stream in 2.08 s. Every stream played (206, an MP4 `ftyp`), and SRF's and ORF's playlists resolved through the probe in 0.04 to 0.14 s, their segments `video/MP2T`.
- 120 plugin tests over 5 real API answers and 20 resolver tests. `docs/reference/plugins.md` (43 plugins, 20 with streams) and `docs/reference/resolvers.md` (63 resolvers) are regenerated; README.md, AGENTS.md, CONTRIBUTING.md, `docs/current/plugins.md` (the plugin, its episode rule, its limits) and `docs/current/hoster-resolvers.md` (the resolver) describe them, and the live smoke searches the plugin.

### Added: An Original Version Keeps Its Own Language

- `parse_language()` reads "Original", "Originalversion" and "OV" as `ov` (label "Original", not dubbed): the original audio, whichever language it is. Before, such a label fell back to the plugin's default language, so the mediatheken's "(Originalversion)" would have been listed as German. `ov` ranks with the score of an unknown language (`default_language_score`) unless the language scores name it.
- `tests/unit/infrastructure/test_release_parser.py` covers the three labels; `docs/current/stremio-addon.md` names them.

### Fixed: The Content-Type Probe Takes Every HLS Playlist Type

- The probe for a URL without a resolver, and for every `.m3u8` or `.mpd` playlist, took `video/*` and `application/vnd.apple.mpegurl` only, so a playlist sent as `application/x-mpegURL` (SRF's and funk's CDNs send that type) or as RFC 8216's `audio/mpegurl` did not resolve. `_HLS_CONTENT_TYPES` adds `application/x-mpegurl`, `audio/mpegurl` and `audio/x-mpegurl`, compared lower-cased.
- `tests/unit/infrastructure/test_hoster_registry.py` probes each of the 4 types; `docs/current/hoster-resolvers.md` (Dispatch, step 7) lists them.

### Fixed: A Plugin With a Dataclass Loads

- `load_python_plugin()` ran a plugin file as a module `sys.modules` did not know, so a plugin with a dataclass and string annotations (`from __future__ import annotations`) failed to load with `AttributeError: 'NoneType' object has no attribute '__dict__'`: `dataclasses` looks the module up by its name for them. The loader enters the module (`scavengarr_dynamic_plugin_<file stem>`) before it runs the file and takes it out again when the file fails, so a broken plugin leaves no half-built module behind.
- `tests/unit/infrastructure/test_plugin_registry.py` loads a plugin with a frozen dataclass and checks that a failing file leaves no module; `docs/current/plugins.md` says so, and the new-plugin guide's tests enter their module the same way, while its triage script loads the plugin through `load_python_plugin()`.

### Fixed: A Capture Keeps a Stream That Arrives with the End of Its Wait

- `_stream_within()` asked the clock before it looked at the stream: when a late event loop ran the wait's timeout and the stream's request in one batch, the capture saw its end passed and gave `None` with the stream in hand, so it clicked again or, after its last click, missed the stream. It now returns the stream it holds once its wait ends.
- A deterministic test covers a stream already in hand at the end of the wait, and the captcha test's verify comes later (0.6 s, the captcha's wait 0.8 s, the stream at 1.0 s), so a stall of the loop up to 0.6 s still passes; its tighter timings failed once on a loaded CI runner.

### Fixed: Every httpx Plugin's Search Page Raises on a Failure of the Site

- The 36 httpx plugins fetch the first page of their search in the raising mode, so the plugin record counts a slow or unreachable site as a timeout or an unreachable search, not as a search without results; before, only jjs and kinox did. Later result pages, detail pages and listings without a query stay lenient.
- `_fetch_search_page()` takes a POST too (`method="POST"` with `data=` or `json_body=`, and `headers=`), with the GET's outcomes and its one failover to the domain the domain check finds: aniworld, megakino, nima4k and the XenForo forums' search post through it, and the XenForo login page raises like a search page.
- `_safe_fetch(raising=True)` is the raising mode for a response: a read timeout raises `TimeoutError`, a transport error, a connect timeout or a 5xx without a challenge `PluginUnreachableError`, a challenge or a 4xx answers `None`. Sites with one domain whose answer the plugin reads as a response (cine, cineby, einschalten, haschcon, hdworld, movieblog) use it on their first page; its exceptions go through the same `_request_failed()` as `_fetch_text()`'s.
- Each changed plugin's tests have a search page that times out (`TimeoutError`), and the tests that expected `[]` after a refused or failing search expect `PluginUnreachableError`; `docs/current/plugins.md`, the new-plugin guide and the glossary name the POST and the response helper.

### Removed: The Docs Archive; History Is Read from Git

- `docs/archive/` is gone (the 25 closed plans, the 3 refactor records, the old backlog and its index). `docs/README.md` has a History section instead: `git log --oneline -- <path>` for a document's commits, `git log --diff-filter=D --name-only --oneline -- docs` for the deleted ones, and `git show <commit>^:<path>` for a deleted document's text.
- Every citation of an archived file names its successor document or is dropped: the code comments of the browser, the captcha detector, the page budget, the resolvers and the measurement scripts point at the current docs and decision records, and the current docs lose their history lines. Decisions 0002, 0004, 0005 and 0011 carry the measurements they rest on (the anime ids' 10 of 10 titles, the episode placement over 6708 episodes, the read-ahead's throughput per connection, the captures' popups and the 6.9 s playlist), and the decision template says a record carries its numbers.
- `tests/unit/infrastructure/test_docs_style.py` covers every document under `docs/`, and `tests/unit/infrastructure/test_docs_paths.py` fails when a file names a document under the removed folder.

### Fixed: A Search Page's Failure Stays a Failure in the Plugin Record

- A timeout, a transport error or a 5xx of a plugin's search page became `None` in the httpx base and `[]` in the plugin, so the plugin record counted a slow or unreachable site as a search without results, and a raised `httpx.TimeoutException` landed in the search's error branch without a counter.
- The httpx base's new `_fetch_search_page()` fetches the first search page in the raising mode of `_fetch_text()` (`raising=True`). A timeout after the connection raises `TimeoutError`. A domain that does not answer (a 5xx without a challenge, a transport error, a connect timeout) sends the page to the domain the domain check then finds, and `PluginUnreachableError` follows when none answers or the page fails there too. A challenge and a 4xx keep `_fetch_text()`'s answer.
- jjs (its first result page) and kinox use it; the other httpx plugins keep the lenient answer for now. Detail pages and later result pages stay lenient, so a missing one is a partial result. A kinox mirror that stops answering no longer keeps the searches on it until a restart.
- The Stremio search counts a raised timeout under `timeouts`, with the stage outcome `timeout` and the line `stremio_plugin_page_timeout`, and a raised `PluginUnreachableError` under `unreachable_searches` as before; both leave the plugin's results missing, so a completion search asks again. The Torznab search answers both with its error answer (`TorznabExternalError`), as it answers any failure of a plugin.
- The metrics reference names the `timeout` outcome and that `cut` is also the plugin timeout's outcome; the coding guidelines and the new-plugin guide name the search page's exception.

### Added: Every Decision Record Names Its Alternatives

- The 15 decision records in `docs/target/decisions/` and their template have `## Alternatives` between Consequences and Status: the options the maintainer did not take, one line each with the reason on record, taken from the archived backlog's decisions and the plans they cite before the archive goes. Where no option or no reason is on record, the record says so instead of inventing one.
- `tests/unit/infrastructure/test_docs_style.py` requires the template's sections in their order in every record, and the contract in `docs/README.md` names the section.

### Changed: AGENTS.md Holds the Rules, the Dev Container Its Own How-To

- `AGENTS.md` is under 3,000 words (from 3,697): §9 keeps one rule line per item and links `docs/how-to/dev-container.md`, which holds the details (git access, what the setup script installs, the dev server for the LAN, checks in a worktree, line endings and executable bits, the editor and the formatter, the Claude Code hooks, code intelligence, the production diagnostics, a Verify list and a troubleshooting table).
- The rule that docs ship with the code is a table of change → documents to update (behaviour, configuration, architecture decision, dependency, plugin or resolver, plan), and §1's paragraph on the checks keeps its rules (the image tags are in `docs/how-to/deploy.md`).
- `tests/unit/infrastructure/test_repository_files.py` fails once `AGENTS.md` reaches 3,000 words. `docs/README.md` and the root `README.md` list the new how-to, and `CONTRIBUTING.md` links it for the dev container's details.

### Added: A Glossary of the Codebase's Terms

- `docs/reference/glossary.md` says in one sentence each what a term means here (plugin, mirror group, episode reference and placement, CrawlJob, grab-time link, the search cache entry's states, answer budget, read-ahead, address-bound and client-bound streams, hoster, resolver, breaker, half-open probe, cooldown, pass, keeper, capture, challenge, mark, page gate, stealth context, clearance and more) and links the section that holds it.
- `docs/README.md` lists it, its map names it, and its state paragraph no longer counts the glossary and the purpose lines as open; the root `README.md`'s documentation table links it.

### Fixed: A Capture That Met the Hoster's Captcha Waits for It

- A Byse capture (Filemoon) on the production host used up the player's clicks before its stream: of four cold captures, two ran out after 29 and 32 s, the pass keeper's own among them, so the keeping ended after one pass. The player solves a proof of work between its `captcha` and `captcha/verify` requests and requests the stream after the verify. With Chromium's CPU throttled sixfold in the dev container, the verify came 0.5 to 9.9 s after the captcha in 11 cold captures. On the production host the stream came 8.1 s after the verify, after the third click.
- A page that requested the hoster's own captcha (`challenge_requests`) now gets 16 s after the captcha's latest request before its next click and before the capture ends (`_CAPTCHA_WAIT_S`, `_CaptchaClock` in `infrastructure/browser/stealth_pool.py`). The clicks before the captcha and a provider's widget (Turnstile) keep their cadence. In the throttled dev container 8 of 8 cold captures then streamed after one click, 0.7 to 1.1 s after the verify.
- The pass keeper's capture is bounded at 45 s instead of 30 s (`_BOUND_S`), since the production host's cold Byse streams came 22.7 to 43.7 s after the resolution's start. The capture now ends inside its bound, so no cut steps the challenge cooldown up, and `hoster_pass_keep stream=` says whether the pass came.
- The capture state's read after the stream has 2 s instead of 0.5 s (`_KEEP_BOUND_S`), and a frame's read 1.5 s instead of 0.4 s (`_FRAME_READ_S`). On the production host reads took 274 and 385 ms, and two ran into the 0.5 s bound and lost the captcha's new pass. The read runs after the stream's hand-over, so the bound holds the page and the browser's lease, not the stream.
- `capture_timing --diagnose` names when each request went out and how long its answer took.
- The playback check's unplayable verdicts on two filemoon.to streams were checked in the dev container, and the check is unchanged. There it passed all four Filemoon streams, and their CDNs answered a playlist with and without the Referer, the browser's User-Agent or cookies (20 of 20 requests). The stream URLs carry an `asn` parameter and no address, so they are bound to the requesting network, which the check shares with the capture.

### Added: Every Document Says What It Is For

- Every document under `docs/` outside the archive opens its status block with `> **Purpose:** <one sentence>`, so `> **Status:**` moves to line 4 and `> **As of:**` to line 5. A current document lifts the first sentence of its Purpose section, a decision record says what it records, and the other documents take their line of the index in `docs/README.md`.
- A generated reference names its generator in its purpose line: `scripts/generate_plugin_list.py` and `scripts/generate_resolver_list.py` write it in place of their former "Generated by" line, and the configuration and metrics references name their table generators there.
- `tests/unit/infrastructure/test_docs_style.py` requires the line, and the contract in `docs/README.md` names it.

### Added: The Docs Index Shows the Map and the State

- `docs/README.md` starts with a Mermaid map of the document groups (`AGENTS.md`, target, current, how-to, reference, agents, plans and the backlog) and how they change one another.
- A status paragraph below it says what the current docs cover and what is open, by area (the docs, the hoster resolvers and the browser, the plugins); the row that opens or closes an area's work updates it in the same commit. The root `README.md`'s sentence about the index names both.

### Changed: The Production Machine Is "the Production Host" Everywhere

- The production machine's device name gave way to "the production host" in 34 files: 13 code comments and docstrings in `src/` and `plugins/` (among them the HLS transcoding setting's description, so `docs/reference/configuration.md` is regenerated), 7 tests, 14 CHANGELOG lines, `README.md` (the image's platforms without an example device), `data/config.yaml`, `.github/workflows/image.yml`, 3 OpenSpec files (`add-container-image` and the archived `add-observability`), `docs/plans/docs-overhaul.md`, the backlog and 5 files of the archive (their text only; the archive goes as a whole later). A benchmark on another device of that kind reads "an arm64 board", and the arm64 platform stays where it is the point.
- `tests/unit/infrastructure/test_docs_privacy.py` fails on the device name in every doc, so it cannot return; decision 0015 names it in its rule. The stealth pool's comment and its test's docstring followed, and the guard checks the code for the device name too.

### Changed: The Skill Set Drops `code-review`, graphify Stays User-Wide

- `code-review` (mattpocock/skills) leaves `SKILL_SOURCES` in `.devcontainer/setup.sh`; Claude Code's built-in `/code-review` stays. The new `RETIRED_SKILLS` list removes an installed copy on the next attach (`skills remove -g -a claude-code`), so its description stops costing context.
- graphify stays user-wide: its installer's project option (`graphify install --project`, read in its `install.py`: `_project_install()` calls `claude_install(project=True)`) writes a `CLAUDE.md` into the repository root, where `AGENTS.md` is the one instruction file, and a PreToolUse hook into the project's Claude Code settings.
- `docs/agents/skills.md` records both, a table of removed skills and the rule that a skill nobody invoked for two weeks is removed (the advisor keeps the usage list; the coders name their skills in every push report).

### Added: The Tech Stack With the Reasons for It

- `docs/reference/tech-stack.md` lists every runtime and development dependency of `pyproject.toml` with what it does here and why it is the one (the measurements behind selectolax, uvloop, Patchright, guessit's cache and the HTTP/2 setting included), the tools beside the Python packages (Poetry, Chromium, Xvfb, curl, the Compose services, Node in the dev container) and the alternatives deliberately not used with their reasons: playwright-stealth, Camoufox, nodriver, Selenium, a required solver service, Scrapy, BeautifulSoup and lxml, other HTTP clients, curl_cffi, paid solver services, difflib, Typer, Pydantic in the domain, mypy and Pylance, black, isort and flake8, OpenTelemetry metrics and its auto-instrumentation.
- The rule: a commit that adds, removes or replaces a dependency updates the file in the same commit. `tests/unit/infrastructure/test_tech_stack_doc.py` fails when a dependency has no line, a line names no dependency, or a package listed as not used is a dependency.
- `CONTRIBUTING.md`'s tech-stack table becomes the link, `AGENTS.md` §4 names the rule, and the README (its documentation table and "How Scavengarr is built"), `docs/README.md` and `openspec/project.md` link the file; `openspec/project.md` loses its drifted copy (a Python range, the image's Python, a resolver count, "Prometheus format: future" and the old development list).

### Removed: Two Development Dependencies Nothing Used

- `requests` and `pytest-mock` leave the dev group of `pyproject.toml`: no file imports `requests`, and no test takes pytest-mock's `mocker` fixture (the tests use `unittest.mock`). Both came with the first commits, with no recorded reason.
- `poetry.lock` drops them and `charset-normalizer`, which only `requests` needed; `urllib3` stays as a runtime package (the OTLP exporter sends over it), and no version moved.
- `redis` loses `extras = ["redis"]`: redis-py has no extra of that name, so the extra installed nothing.
- The image never had either package, since both were in the dev group only; the OTLP exporter sends over urllib3 and imports `requests` only for a credential-provider session, which the app does not set up.

### Added: The Post-Deploy Check Shows Where an Answer's Time Goes

- Each stream row of `prodctl.py check` ends with the client's time to the response headers and to the body's end (`stream_answers()` reads each answer through `httpx.Client.stream()`, the headers' time when the context opens) beside the server's `duration_ms` of the request's `http_request` record, which the check reads already. A client more than 5 s slower than the server turns a passed row into a warning that names the gap; a failed row stays failed. `Answer.headers_seconds` and `_timing()` in `scripts/deploy_check.py`.
- Why: two answers reached the check 27 s and 12 s after the server had logged them (idea N33), and the check could not tell the search's time from the way's.
- Proof: `tests/unit/infrastructure/test_deploy_check.py` (no gap passes with both times, a gap warns and names both, 5 s still passes, a failed row stays failed) and `tests/unit/infrastructure/test_prodctl_script.py` (respx: the times to the headers and to the end, an error keeps its time without headers; the check's table with the times). `docs/how-to/operations.md` → the post-deploy check names the times.

### Fixed: `prodctl` Masks Its HTTP Errors

- An HTTP error from Portainer ended `scripts/prodctl.py` in a traceback whose last line named the whole request URL, Portainer's address and port included, against the rule that everything it prints passes `portainer.mask()`. `main()` now catches `httpx.HTTPError` and prints `<command> failed: <message>` masked on stderr, exit code 1. `tests/unit/infrastructure/test_prodctl_script.py` checks a 403 on the logs call (the host masked, no path, nothing on stdout); against production, `logs` for an unknown container printed `logs failed: Server error '500 Internal Server Error' for url 'http://<ip>:9000/…'` with exit code 1. `docs/how-to/operations.md` names it.

### Changed: The Live Smoke Skips a Slow Site Instead of Failing Its Parser

- A plugin run that answers nothing after a fetch the base logged as failed (`<plugin>_timeout`, `_fetch_error` or `_http_error`: `_fetch_text()` and `_safe_fetch()` answer those with `None`, and 32 httpx plugins then answer `[]`) skips with the line, its context and status in the reason, instead of failing as a broken parser; a run without such a line keeps the old assertion. The decision is `failed_fetch()` in `tests/live/smoke_outcome.py`, tested by `tests/unit/infrastructure/test_plugin_smoke_outcome.py`; `tests/live/test_plugin_smoke.py` captures each search's log lines.
- Why: row 135's runs failed jjs on a search-page timeout and kinox on a mirror's 503, both sites merely slow. That the plugin record counts such a search as one without results is backlog row 139.

### Changed: Readiness Notices a Lost Network, and the Image's Healthcheck Asks It

- `/api/v1/readyz` answers 503 with `{"status": "not_ready", "reason": "network"}` once the cache backend's ping (`CachePort.ping()`: Redis `PING`, diskcache whether it is open) and the DNS resolution of the fully qualified `example.com.` (no search domain answers for it) have both failed for longer than 5 min (`NetworkProbe`, `src/scavengarr/infrastructure/network_probe.py`, wired in `src/scavengarr/interfaces/composition.py`). It probes at most once every 30 s, each check within 3 s, and a request in between gets the last verdict; a single miss or one check failing alone (a Redis restart, a DNS hiccup) keeps the 200. `network_lost` (error) and `network_recovered` log the loss and its end once each.
- The image's `HEALTHCHECK` (`Dockerfile.prod`) asks `/api/v1/readyz` instead of `/api/v1/healthz`, which stays the liveness check; Docker marks a container without its network unhealthy and restarts nothing by itself. With the diskcache backend the cache check needs no network, so only a deployment with Redis reports a lost network.
- New gauge `scavengarr_network_ok{check="cache"|"dns"}`: 1 when the check answered at the probe's last run, else 0 (`TelemetryPort.record("network_ok", …)`; no alert rule). `prodctl.py check` reads it from `/metrics` (`network_check()` in `scripts/deploy_check.py`: a check at 0 fails, no sample yet warns).
- Why: production's container lost its network namespace for 33 h (the VPN container it shares was recreated without it) and reported healthy all the while, since `/api/v1/healthz` answers over loopback (ledger D3, option A; row 125).
- Proof: unit tests of the three states (fresh, failing under 5 min, failing over 5 min), one check failing alone, the 30 s cache, a hanging check and the logs (`tests/unit/infrastructure/test_network_probe.py`), the readiness route (`tests/unit/interfaces/test_health_routes.py`), both cache adapters' ping, the gauge, the deploy check and the image's healthcheck. Live in the dev container, the app on a Redis stand-in with the probe's name unresolvable: after the stand-in stopped, `readyz` answered 200 at every 30 s ask up to 329 s and 503 with `reason: network` from 362 s on (`network_lost seconds=329 probes=11`, counted from the first failed probe 33 s in), `healthz` answered 200 throughout and the image's `curl -sf` exited 22 on each 503; the first probe after the stand-in was back (33 s later) saw the cache and `readyz` answered 200 (`network_recovered seconds=392 probes=12`).
- `docs/reference/torznab-api.md` → Application health, `docs/current/observability.md` → Readiness, `docs/how-to/deploy.md` (Verify, Troubleshooting) and `docs/how-to/operations.md` → 5. Check a deploy describe it; `docs/reference/metrics.md` is regenerated.

### Changed: A Stop Reads Clean in the Log

- `HosterStateStore` and `PluginHistory` log each snapshot write with its counts (`hoster_state_saved` with the resolutions, redirects and breakers, `plugin_history_saved` with the plugins and days); an unchanged state writes and logs nothing.
- A playback the 5 s shutdown bound cancels is no error any more: `_ShutdownBoundFilter` (`infrastructure/logging/setup.py`, on the `uvicorn.error` logger) makes Uvicorn's `Cancel 1 running task(s), timeout graceful shutdown exceeded` a warning and drops the cancelled task's `Exception in ASGI application`; any other cancel or exception stays an error.
- The stop's last log lines are no longer lost. Uvicorn raises SIGTERM again after its shutdown; the default handler killed the process before the log listener thread wrote its queue, so `app_shutdown_complete` was missing from every stop and once everything after `http_client_closed`. The CLI's handler (`_stop_on_sigterm`) now stops the listener once it wrote every queued line (`stop_async_logging()`), then ends the process from the signal as before; a normal exit would wait in uvloop's close for open DNS lookups, up to 5 s, which took 6 of 13 stops to 10.3 to 10.7 s, past Docker's grace.
- Proof: unit tests in `tests/unit/infrastructure/test_hoster_state_store.py`, `test_plugin_history.py`, `test_logging_setup.py` and `tests/unit/interfaces/test_cli.py`. On the dev server a stop with an open proxied playback ended after 5.23 to 5.28 s with the cancel a warning, no error line and every line through `Finished server process`; a stop with fresh resolutions logged `hoster_state_saved` (16 resolutions, 1 redirect) and `plugin_history_saved` (16 plugins). `docs/current/architecture.md` → Shutdown, `docs/current/observability.md` and `docs/current/hoster-resolvers.md` name the lines.

### Changed: A Filemoon Capture Without a Kept Pass Counts as Challenged From Its Start

- The Filemoon resolver reads the kept capture state before a Byse capture (`ClearanceStore.creation_state()` and `pass_expiry()`; `FilemoonResolver(clearance_store=)`, wired by `build_hoster_resolvers()` in `src/scavengarr/interfaces/composition.py`). Without a captcha pass with 30 s left it marks the resolution's challenge (`hoster_captcha`, `mark_resolution_challenge()`) before the capture starts, so the registry's challenge paths apply: a cut ends as `challenge` instead of a breaker failure, the challenge cooldown starts, and the capture runs on in the background for up to 20 s and caches its stream and keeps the new pass, from which the pass keeper goes on. A video the details API reports gone starts no capture, and a page past its captcha keeps its verdict (an offline notice is a dead link).
- The pass keeper's capture starts after the pass has gone, so it is marked too: its cut runs on as the completion and no longer counts toward the breaker. `hoster_resolve_success` names `hoster_captcha` for every Filemoon stream found without a kept pass.
- Why: the Byse player asks a context without a pass for its captcha first. In 54 h of one build's logs on the production host, cold captures found their stream 17.4 to 31.5 s in, past the 10 s resolve bound, and 12 of 17 were cut without a challenge mark; after the rebuild with the pass keeper the first lookup's timeout opened the breaker and the keeper idled (idea I20, the maintainer's decision D7).
- Proof: unit tests of both paths in `tests/unit/infrastructure/test_filemoon_resolver.py` (a kept pass leaves the capture unmarked; none, an expired one or one with less than 30 s left marks it; with the registry, a cut without a pass ends as `challenge` with no breaker failure and the completion caches the stream, a cut with one stays a `timeout`, an offline page stays dead) and the wiring in `tests/unit/interfaces/test_resolver_wiring.py`. The production proof follows the deploy (backlog row 121); the OpenSpec change `react-to-challenges` has the requirement and its tasks group 4.

### Added: Every Plugin Has a Live Smoke Entry

- `tests/live/test_plugin_smoke.py` lists cineby, crawli, hdsource, jjs, movieblog and serienjunkies (filmpalast_to's plugin is `filmpalast`, listed before), so all 42 plugins are searched in a live run; `tests/unit/infrastructure/test_plugin_smoke_coverage.py` fails when a registered plugin has no entry or one twice.
- A plugin whose domain check finds no domain (`PluginUnreachableError`) skips as a site that is down, as a network error does; before, a dead site's entry failed.
- `docs/how-to/new-plugin.md` → the live check names the file, the lists and the guard.

### Fixed: A Torznab Search over Several Kinds Answers Every Kind

- `cat=` with ids of several kinds (`cat=2000,5000,…`, which Prowlarr's own searches and its RSS sync send with the indexer's whole category list) answered the first kind only, so the TV results never reached Prowlarr. The router now reads every id and groups them by kind (the thousands): ids of one kind give the first id as before (Sonarr's `5030,5040` through `served_category()`); ids of several kinds make the plugin search unfiltered and the use case keep the results whose label one of the kinds covers, before they are cached under a key that carries the sorted kinds. A non-numeric id anywhere in `cat` answers 400 (before: only the first was checked). On the dev server a filmpalast search with `cat=2000,5000` answered 10 movies and 27 TV results, the sum of `cat=2000` and `cat=5000`; the code before answered the 10 movies only.
- `category_matches()` and the new `category_kind()` live in `domain/entities/torznab.py`; `infrastructure/plugins/categories.py` imports the rule from there, so the plugins' imports stay. `docs/current/torznab-and-crawljobs.md` → The category filter and `docs/reference/torznab-api.md` (the `cat` parameter) describe it.

### Changed: The Graceful Shutdown Is Bounded at 5 s

- Uvicorn runs with `timeout_graceful_shutdown=5` (`src/scavengarr/interfaces/cli/__main__.py`): a connection still answering 5 s after the stop signal, such as a proxied playback, is cancelled, so the app's cleanup (the drain, the last snapshots of the resolver state and the plugin record, the closes) runs inside Docker's 10 s stop grace instead of being cut off by its kill. Uvicorn waited without a limit before. On the dev server a stop with a proxied file playback held open by a slow reader took 5.2 to 5.3 s until the process was gone (before: still waiting after 20 s), a stop without an open connection 0.25 s. `docs/current/architecture.md` → Shutdown, the README and the index state the bound; `tests/unit/interfaces/test_cli.py` checks the argument.

### Changed: Dependabot Opens Its Pull Requests Against `staging`

- `.github/dependabot.yml` sets `target-branch: "staging"` for Poetry, GitHub Actions and the Docker base images, so an update reaches `main` only through `staging`; AGENTS.md §4 says the PRs are merged into `staging` after a green CI run, and `tests/unit/infrastructure/test_repository_files.py` fails when an ecosystem names another branch or none.

### Changed: The README Stays Current

- The README's documentation table links every document under `docs/current/`, `docs/how-to/` and `docs/reference/` and the rules, decisions, plans, the work queue and the assistants' working rules; its test count reads about 7,000.
- `tests/unit/infrastructure/test_readme.py` keeps it so: a document under those three folders that the table does not link, or a plugin, browser-plugin or resolver count that differs from the generated lists, fails the suite.
- The rule in AGENTS.md §1 and `docs/agents/orchestration.md`: a change of a feature, a setting, the setup, the deployment, a count the README names or the document layout updates `README.md` in the same commit, and the review of every row checks it.

### Changed: AGENTS.md Keeps the Rules, the Feature Handbook Becomes the Index's Feature List

- AGENTS.md §3, §7 and §9 keep the rules and link the current docs for the mechanics: §3 keeps the layer table and the invariants that are rules and links `docs/current/` (link validation, the Stremio addon, the architecture, the hoster resolvers, observability, Torznab and CrawlJobs) and `docs/reference/configuration.md`; §7 keeps the plugin MUST rules, the XFS and DDL rule and the resolvers' declaration flags and links `docs/current/plugins.md`, `docs/current/plugin-domains.md`, `docs/current/hoster-resolvers.md` and `docs/current/browser-and-challenges.md`; §9's production diagnostics link `docs/how-to/operations.md`. §1's docs line names `docs/current/`, `docs/target/`, `docs/how-to/` and `docs/reference/`, and §10 no longer names `docs/features/`.
- CONTRIBUTING.md is the one owner of the project layout and the tech stack; the index and AGENTS.md §10 say so instead of repeating them, and its docs line names the folders of the new layout.
- `docs/features/FEATURES.md` is gone, and with it `docs/features/`: its feature list is the section "What Scavengarr does" of `docs/README.md`, one line per feature with the current doc that describes it. The index's "As of" names this change's parent, and its sentence about documents still waiting to move is gone.
- `tests/unit/infrastructure/test_docs_style.py` covers every document under `docs/` outside the archive, which stays exempt: every document outside the archive carries the header; plans keep their ids and history by the contract. `docs/plans/challenge-reactions.md` and `docs/plans/stremio-latency.md` open with their title and a status block instead of a back-link, and `docs/plans/docs-overhaul.md`'s "As of" is a bare hash.
- `tests/unit/infrastructure/test_docs_paths.py` no longer globs the removed `docs/features/` and `docs/architecture/`.

### Added: The Specs of the Configuration and the Plugin System

- `openspec/specs/configuration/spec.md` holds the configuration's requirements as the code has them: the four layers and their precedence, the config file and the dotenv file, the YAML layer, the environment's names (sectioned, flat, JSON values; no variable without the `SCAVENGARR_` prefix), the startup's reports of ignored keys and variables and of a flat and a sectioned name that disagree, the validation, the log format by environment, the `config_effective` line with its masking, the bind address and the guards that every setting is read and documented.
- `openspec/specs/plugin-system/spec.md` holds the plugin system's: the discovery, the one load of every plugin file, the plugin contract and the skipped broken files, unique names, the metadata and the registry's answers, unknown names in the registry and the Torznab API, the declared episode location, the grab-time links, the startup wiring, the per-plugin overrides and their problems, and the result limit.
- Their changes `add-config-system` and `add-plugin-loader` were archived without specs; `openspec/project.md` names the specs, and its prefix for the cache settings (`CACHE_*`, which the configuration does not read), its missing redaction and its lazy loading per request are corrected.

### Changed: The Resolver Docs Follow the Document Contract, and the Resolver List Is Generated

- `docs/reference/resolvers.md` lists every registered resolver, generated by `scripts/generate_resolver_list.py` from the registrations: the individual resolvers with their module, what each does, whether it captures in the browser, what its CDN binds a stream to and whether the registry checks its streams; the generic DDL and XFS hosters; every resolver's domains. Today 62 resolvers: 27 individual ones, 10 generic DDL hosters and 25 XFS hosters. `test_resolver_list_doc.py` fails while the list is outdated.
- The composition registers the resolvers through `build_hoster_resolvers()` (`src/scavengarr/interfaces/composition.py`), in the order as before, which the generator reads; `test_resolver_wiring.py` checks that every XFS and DDL config is registered, that the specific resolvers come before the generic ones, that no two share a name and that every resolver that captures gets the stealth pool. Thirteen resolver modules' docstrings now start with the sentence the list quotes.
- `docs/current/hoster-resolvers.md` describes how a link becomes a stream: the dispatch as a flowchart, the playback headers, the bound CDNs, the CDN checks, the browser captures, a link's outcomes as a state diagram with the challenge cooldown and the background completion, the circuit breaker as a state diagram, the caches and the state across restarts, and Filemoon's pass keeper.
- `docs/how-to/new-resolver.md` holds the steps from the unresolved hosters to the regenerated list, the live check and a troubleshooting table.
- `docs/features/hoster-resolvers.md` is gone; every citation of it outside the CHANGELOG, the archived backlog and the archived OpenSpec changes names its successor, the `new-resolver` skill follows the how-to, and AGENTS.md names the generator.

### Changed: The Backlog Is Cut and the Sessions' Rules Have Their Own Document

- `docs/backlog.md` holds the open rows of the work queue, the ideas not yet taken up and the items carried over from the archived plans, one line each; a coder's hashes and the acceptance go on the row's line.
- The archived backlog is the backlog as it grew from the first production review to the docs overhaul (findings, ideas, decisions, the working rules, the order of the rows with their hashes), kept with its text; every citation of the old path names the archive, the queue or the rules.
- `docs/agents/orchestration.md` holds the three sessions' roles, the working rules (the privacy rule among them, which `test_docs_privacy.py` now names there), the worktree and push rules, production access and the maintainer's standing decisions.
- `test_docs_paths.py` leaves the backlog unchecked like the plans: its rows name the files they will create.

### Added: A Test Guards the Dependency Rule
- `tests/unit/test_dependency_rule.py` parses every module under `src/scavengarr` with `ast` and checks each import of the package, the ones under `if TYPE_CHECKING:` and the relative ones included, against the rule table of `docs/target/architecture.md` (`domain` imports only `domain`, `application` also `domain`, `infrastructure` `domain` and itself, `interfaces` everything); a breach fails with the importing module and the import named. Today all 542 imports of the 188 modules follow it.

### Changed: The Stremio and Browser Docs Follow the Document Contract
- `docs/current/stremio-addon.md` describes the addon: the endpoints, the `kitsu:` translation as a flowchart, the titles and the episode reference, the search cache's key (`v3`) and its entry states as a state diagram with the `X-Cache` and `X-Search-Complete` headers, the answer budget against the plugin timeout as a sequence, the plugin breaker (every timeout a failure; the old half-budget rule is gone), the episode filter, title matching, resolution, ranking, the streams, `/play` and both proxies.
- `docs/how-to/stremio-deployment.md` holds the deployment steps: a streaming server of its own, Scavengarr and the streaming server behind a VPN container, and the AIOStreams settings.
- `docs/current/browser-and-challenges.md` describes the shared browser, the stealth pool and its captures, the page gate as a flowchart with its adaptive budget, the clearance store and the capture state's life cycle as a state diagram, a challenge's outcome and cooldown, and the browser fallback of httpx plugins with its session adoption.
- `docs/features/stremio-addon.md` is gone; every citation of it outside the CHANGELOG and the archived OpenSpec changes, and the captcha links of README.md and `docs/features/FEATURES.md`, name the successors.

### Changed: Two OpenSpec Changes Are Archived and Two Spec Gaps Closed

- `add-stream-media-quality` and `place-episodes-by-number-first` are archived (`openspec/changes/archive/`), their requirements merged into `openspec/specs/stremio-stream-quality/`, `stremio-anime-episodes/` and `stremio-series-identity/`; `openspec/project.md` lists them as archived.
- The `stremio-anime-episodes` spec states the search cache key as the code writes it (`v3` with the reference's placement) and the rule that an unchecked position's row needs the site's title to confirm it; task 6.3 of the archived series-identity change (fireani's episode location) is backlog idea I19.

### Changed: The Observability, Operations and Guideline Docs Follow the Document Contract
- `docs/current/observability.md` (from `docs/features/observability.md`) describes what the core records and where: the `TelemetryPort` stages and their outcomes, the request id and the log masking, the plugin record, Prometheus, Grafana, the alert rules, tracing on demand and the cost, with a flowchart from `stage()` to Grafana and Tempo; the plugin timeout links the search timing of `docs/current/architecture.md`.
- `docs/reference/metrics.md` lists every metric with its type, labels, buckets and help text, the label values, the JSON statistics and the plugin record's counters; its metric table is generated from the app's registry by the new `scripts/generate_metrics_doc.py` (the families of `Telemetry` and of the scrape-time collectors, prometheus-client's own left out), and `tests/unit/infrastructure/test_metrics_doc.py` fails when it is outdated.
- `docs/how-to/operations.md` describes reading production with `scripts/prodctl.py` (`ps`, `stats`, `logs`, `metrics`, `state`, `probe`, `digest`, `check`), the post-deploy check, the digest's sections and every probe of `scripts/probes/` with where it runs.
- `docs/how-to/performance-measurement.md` describes `scripts/stremio_profile.py`, `playback_under_load.py`, `stremio_round.py` (with the local ids file `.cache/live/round-titles.txt`), `stremio_playcheck.py` and `stremio_measure.py`.
- `docs/current/known-issues.md` lists the open defects, one line each, with where each is tracked; the CHANGELOG's known-issues section links it.
- `docs/target/coding-guidelines.md` replaces `docs/PYTHON-BEST-PRACTICES.md`: the rules this codebase follows for the event loop, shared resources, concurrency, scraping, browser pages, caching, retries and logging, without the generic textbook parts.
- Every citation of the two removed docs points at its successor: `AGENTS.md`, `README.md`, `docs/README.md`, the docstrings of `infrastructure/config/schema.py` and `infrastructure/telemetry/metrics.py`, the Docker files, the observability spec, the open change, the open and archived plans and the other docs.

### Changed: The Configuration, Torznab and Deployment Docs Follow the Document Contract
- `docs/reference/configuration.md` (moved from `docs/features/configuration.md`) holds the precedence as a flowchart, the CLI, environment, YAML and `.env` rules and the generated settings tables; the hand-kept tables beside them are gone, their extra facts kept as one note per setting, and no setting is called YAML-only, since every one has its environment variable.
- `scripts/generate_config_doc.py` writes the tables under H3 headings and adds the flat names the loader maps (`_FLAT_KEYS`), formerly a hand-kept table; `tests/unit/infrastructure/test_config_doc.py` checks them.
- `docs/how-to/deploy.md` is the one description of the deployment: image tags, `docker run`, the Compose profiles, the image's environment (with `SCAVENGARR_PLAYWRIGHT_HEADLESS`), Redis, the VPN container, the reverse proxy, the build identity with the current base image, and the resolver caveat for German ISPs.
- `docs/reference/torznab-api.md` (moved) lists every endpoint, `/api/v1/stats/plugins` included, owns the download endpoints and shows the caps with `<version>` and the search as a sequence diagram; `docs/current/torznab-and-crawljobs.md` replaces `crawljob-system.md`, `docs/current/link-validation.md` (moved) is rewritten, and `docs/how-to/connect-prowlarr.md` replaces `prowlarr-integration.md`.
- `SCAVENGARR_CACHE_TTL_SECONDS` is recommended nowhere: no cache writer uses it (`data/config.yaml` says so).
- Every citation of the old paths outside the CHANGELOG and the archived OpenSpec changes names the successor.

### Changed: The Architecture Has Its Rules, Its Current State and Its Decisions Apart
- `docs/target/architecture.md` states the rules: the dependency rule as a table and as a Mermaid layer graph with the allowed edges only (`infrastructure/` never imports `application/`, which the old ring diagram left open), the layer contracts and the invariants of AGENTS.md §3.
- `docs/current/architecture.md` holds the module map of every layer, with the modules the old docs missed (`SeriesMetaPort` and `CinemetaClient`, `release_guess.py`, the episode index, the domain list, `PassKeeper`, `ChallengeFlag`, `infrastructure/anime/`); the Torznab search and the Stremio stream request as sequence diagrams; the Stremio search timing as `plugin_search.py` has it (a plugin's timeout runs from its slot, the answer budget cuts no plugin, every timeout is a breaker failure); and the composition order and the shutdown sequence (Uvicorn's wait, then the app's 10 s drain and cleanup) as flowcharts.
- `docs/target/decisions/` holds one record per decision in force, from the dependency rule to the privacy rule, each with its context, the decision, its consequences and the archived plan or OpenSpec change with the evidence.
- `docs/architecture/clean-architecture.md` and `docs/architecture/codeplan.md` are gone; AGENTS.md, CONTRIBUTING.md, README.md and the docs index point to the new docs.

### Changed: The Plugin Docs Follow the Document Contract
- `docs/current/plugins.md` describes how plugins are discovered, loaded and called (the contract, the results, the base classes, the search stages, categories, episodes, the sto gate, the plugin selection of a Stremio request, scores and probes); `docs/current/plugin-domains.md` the domain check, site moves, official domain lists, boerse's own fallback and the mirror groups; `docs/how-to/new-plugin.md` the steps of a new plugin.
- They replace `docs/features/plugin-system.md`, `python-plugins.md`, `multi-stage-scraping.md`, `plugin-scoring-and-probing.md` and `mirror-url-fallback.md`; the per-plugin overrides have one description, in `docs/current/plugins.md`, and the settings stay in the configuration reference.
- The generated plugin list moved to `docs/reference/plugins.md`; `scripts/generate_plugin_list.py` writes the generator's name on its line 3.
- Every citation of the old paths outside the CHANGELOG and the archived OpenSpec changes names the successor.

### Changed: The Closed Plans Are Archived
- The 25 closed plans and measurement logs moved unchanged under their names from `docs/plans/` to the archive's plans folder, each with an archived status block that names its successor document (or the row that will write it) and with one row in the archive's index (what it was, outcome, successor). `docs/plans/` keeps the open plans only: the backlog, the challenge decision, the Stremio latency plan and the docs overhaul.
- Every citation of a moved plan in the code, the scripts, the tests, the specs, the open OpenSpec changes and the docs names its new path; the CHANGELOG and the archived OpenSpec changes keep theirs as history. The open items of the archived plans are listed under "Carried over" in the backlog's Ideas section.

### Changed: The Docs Have One Index, a Document Contract and an Archive
- `docs/README.md` replaces `docs/features/README.md` as the one index: one line per document with its status (current, target, how-to, reference, plan, archived), a "start here" for agents, and the document contract of `docs/plans/docs-overhaul.md` word for word as its "Documentation rules". It carries no hand-kept counts; the back-links of the docs, the README and AGENTS.md point to it.
- `docs/archive/` holds the history with its own index (file, what it was, outcome, successor); the three refactor records moved there from `docs/refactor/COMPLETED/` with an archived status block. `docs/target/decisions/_template.md` is the template of the decision records, and the two docs under `docs/agents/` carry their status block.
- `tests/unit/infrastructure/test_docs_paths.py` also checks the folders of the target layout (`docs/target/`, `docs/current/`, `docs/how-to/`, `docs/reference/`, `docs/agents/`) and `docs/backlog.md`. The new `tests/unit/infrastructure/test_docs_style.py` holds the index and those folders to the contract: the status block on line 3 (a generated reference file names its generator there), no heading that names a round, trial, measurement, proof or finding, and no backlog id outside the backlog.

### Fixed: `prodctl.py stats` Shows an Idle App's CPU Load
- `scripts/prodctl.py stats` prints the cores in use with three decimals (an idle production app read "CPU 0.00", now "CPU 0.004 of 4 cores") and "CPU ? of N cores" for a sample without a previous one to measure against, which `scripts/playback_under_load.py` leaves out of its CPU figures instead of counting it as idle.

### Changed: The Docs Carry No Private Traces
- Network, device and hosting details are generic (`*.example.lan`, "the production host", "a residential network"), the usage guard reads its status repository and time zone from `USAGE_STATUS_REPO` and `USAGE_GUARD_TZ`, third-party addresses in the kinoger and kinox fixtures are `user@example.org`
- Clock times of playbacks and observations became durations or offsets from a timeline's first entry, dates of playbacks went, request ids read "a request", and the titles and IMDb/Kitsu ids of the maintainer's requests are placeholders ("Anime A", `<Anime A>`); test data and fixtures keep their titles
- `tests/unit/infrastructure/test_docs_privacy.py` guards the docs and the code against clock times with seconds or UTC, request ids, LAN hostnames, network numbers and time zones (documented examples stay allowed); AGENTS.md § 1 carries the rule
- The rounds' title list is a local file (`.cache/live/round-titles.txt`, read by `scripts/stremio_round.py`, `scripts/probes/series_episodes.py` and `scripts/probes/resolver_urls.py`); the tracked copy under `docs/plans/` is gone

### Added: Serena As The Dev Container's Code-Intelligence MCP Server
- `.mcp.json` starts Serena (oraios/serena 2.0.0; `--context claude-code --project-from-cwd`, no browser for its dashboard, no usage reporting): the language server's symbol search, references and symbol-level edits through its REPL tool, basedpyright as the server. `.devcontainer/setup.sh` installs `uv` through pipx, `serena-agent` pinned through `uv tool install -p 3.13`, and basedpyright's server ahead of the first session. `.serena/project.yml` is versioned, the rest of `.serena/` stays local. `docs/agents/mcp-servers.md` lists the repository's MCP servers with their flags; `AGENTS.md` § 9 points at it

### Added: Filemoon's Captcha Pass Is Kept Alive
- The Byse player (Filemoon) keeps its captcha pass in the localStorage item `byse:captcha-clearance:embed` on its player host: a token and an expiry 30 min (1785 s) after the captcha. A capture with the pass does not renew it, and the first capture after the expiry meets the captcha again. Dev container, one Byse link in one browser: warm captures 20 and 29 min after the captcha left the item unchanged, with 586 and 47 s left; 31 min after it the captcha came back (4.2 s into the capture, the stream at 6.1 s) with a new item 1785 s ahead. In production (54.2 h of logs on e749a0c) every Byse resolution whose pass was 30 min old or more, or that had none, came without a stream within the 10 s bound: 12 timeouts without a challenge mark and 5 challenges. The new passes came only from background completions past the bound, their streams 17.4 to 31.5 s after the resolution's start (row 106 of the archived backlog, `docs/plans/challenge-reactions.md` → R5).
- `PassKeeper` (`infrastructure/hoster_resolvers/pass_keeper.py`) reads the pass's expiry from the kept capture state (`pass_expiry()` in `hoster_resolvers/filemoon.py`). 30 s after the expiry it resolves the link of the newest cached Filemoon stream again (`HosterResolverRegistry.last_stream()`, then `resolve(link, refresh=True, bound=30)`), so the captcha falls to it and its new pass is kept for the next request. Its capture has a bound of its own, 30 s (`_BOUND_S`, as much as a challenged capture gets in production in all, the 10 s bound and the 20 s completion; `HosterResolverRegistry.resolve(bound=)` replaces the resolve bound for one lookup): the captcha comes with the player's first click, 3 s after the page has loaded, and in two dev proofs the 10 s bound cut the keeper's capture before it (a cold page load took up to 8.6 s), so no completion ran and no pass came. Requests keep the 10 s; a keeper timeout counts toward the breaker. The capture's page claim is `background`, and it starts only while one of the stealth browser's pages stays free beside its own. One capture per pass, and none without a cached Filemoon stream. It keeps the pass only while there is demand: a request looked up a Filemoon link within 48 h (`_DEMAND_S`). The registry records each resolver's last lookup (`HosterResolverRegistry.demand_age()`): `resolve()` with its cache hits and `cached()`, so a stream the keeper's capture cached counts when a request takes it; the keeper's own lookups pass `demand=False`. Past 48 h the keeper idles, and the next request's lookup starts it again. Production's quiet stretches lasted up to about 23 h, and the bound leaves at most 96 captures after the last request. The record outlives a restart in the hoster state snapshot (`demand`: seconds since each resolver's last lookup, older by the downtime; a snapshot without it restores none). The lifespan starts the keeper after the browser's warm-up and cancels it at shutdown before the registry ends its completions. Metrics `scavengarr_hoster_pass_keep_seconds` and `scavengarr_hoster_pass_keep_total{outcome}` (`stream`, `none`; counted without a run: `busy`, `no_link`, `idle`); logs `hoster_pass_keep`, `hoster_pass_keep_skipped` (`reason`: `no_link`, `idle`), `hoster_pass_keep_error`.
- A capture whose page met a challenge on its way to the stream now keeps its hosts' state at once, also within 10 minutes of the host's last keep. Before, a captcha met within that interval left the old pass in the store: a restart restored a pass that had gone, and the keeper would read its expiry. A capture without a challenge keeps the interval.
- `scripts/probes/capture_state.py` shows the epoch times among a kept localStorage value's top-level JSON fields from now, beside its length: Byse's pass as `expiresAt in 23 min`. No other field, never a value.
- Proof: unit tests (the keeper's waits, captures, bound, pages, demand and loop; the registry's newest stream, demand record and per-lookup bound; the pass's expiry). Dev proof (the app's lifespan, one Byse link): with the bound, the keeper's capture 30 s past the expiry met the captcha, found the stream in 5.7 s and brought a new pass; two runs without it ended in the 10 s bound without a mark. Lookups after a capture with the captcha streamed without a challenge (1.6 and 6.3 s). The production proof follows the next deploy: the first Filemoon request after a quiet stretch streams without the captcha.

### Fixed: An Outage Without a Network or a Cache Is Logged Once
- Production's container lost its network for 33 h (the VPN container whose namespace it shares was recreated by an image update) and wrote 670 000 log records in 24 h while it reported healthy: every Redis call logged `redis_get_error` or `redis_set_error` at error level (325 000), and every scheduler tick found all 108 scoring cells due, each rebuilding its query pool with 10 IMDb requests logged with a traceback (`query_pool_imdb_error`, 287 000). The Redis adapter now logs an outage once (`redis_unavailable`, error, the first failure's text) and its end once (`redis_recovered`, info, the calls that failed and the outage's seconds); the failures in between log at debug, other Redis errors as before. A query pool build stops at the first request that cannot reach IMDb (`httpx.ConnectError`: the name does not resolve, the connection is refused; or `httpx.ConnectTimeout`, as a resolver that does not answer gives after 10 s), logs `query_pool_unavailable` once at warning without a traceback, and `get_queries` gives no queries, without fetching, for 10 minutes after it (`_UNAVAILABLE_COOLDOWN_S`, in memory). The repository's `docker-compose.yml` rotates the app's json-file log (`max-size` 20 MB, `max-file` 3), and `docs/features/configuration.md` → Behind a VPN Container says why: the healthcheck is a liveness probe over loopback and stays green while every outbound call fails.
- Dev proof: the dev server with the Redis backend, its Redis stopped once the app was up, 6 minutes each: before 1586 records (264 per minute, 1321 of them `redis_get_error`/`redis_set_error` at error level), after 226 (38 per minute, one `redis_unavailable`, and one `redis_recovered` with 1277 failed calls when Redis came back). One scheduler tick's 108 pool requests with IMDb unreachable (the real `QueryPoolBuilder`): with a refused connection before 1080 requests and 1188 records (1080 with a traceback), after 1 request and 1 record; with a resolver that does not answer, each request waits 10.1 s, so before one tick took about 3 h (1080 one after another), after 10 s.
- A cache outage with the network up multiplied IMDb's traffic: with Redis down every scheduler tick rebuilt every cell's query pool, since the cache gave nothing (114 builds of 10 requests in 6 minutes of the dev proof). The builder keeps the last pool per cell in memory, replaced on every build that found titles and used within the cache's 24 h when the cache read gives nothing; a cold start without a copy still builds. Same dev setup: 24 builds in 6 minutes instead of 114, 19 of them pools without a title in their year range, which are built again on every tick as before.

### Fixed: A Capture's State Is Read After Its Stream Went Out
- A capture that found its stream read its hosts' state from its page before the stream went out, at most 0.5 s, and only while its resolve bound had 0.5 s left. A read that began just above that and ran its 0.5 s left no time for the hand-over: in production, a filemoon.to capture logged `capture_state_save_failed error=TimeoutError` in the same second as its `hoster_resolve_timeout`. A stream found within 0.5 s of the 10 s bound kept nothing, and nothing logged it; Byse's streams come at about 9.7 s, so its captcha pass was the one most often not kept (row 107 of the archived backlog).
- The stream now goes out first. The read (still at most 0.5 s), the page's close and the store's write follow in a task of their own, without the time-left guard. A host is still read at most once per 10 minutes and by one capture at a time, and a failure still logs `capture_state_save_failed`. Until it closes, the page keeps its place at the page gate and the browser's lease: `PageGate.page()` and `SharedBrowserPool.lease()` yield a `Hold` (`infrastructure/browser/page_gate.py`) that the block can hand on to such work, which ends it. So the page counts against the page limit, and the browser does not restart under it. `browser_page_seconds` ends at the hand-over.
- `scripts/probes/capture_timing.py --restore` prints when each run's read began against its stream's hand-over (`begun N ms after the stream went out`), and a run ends once its capture's page has closed.
- Live proof (dev container, 3 min): the probe with `--restore` on one link per capture resolver, staging's code and this change in turn. Filemoon (Byse and filemoon.to), Dropload, SuperVideo and Vixeo found their streams. Staging's read began 8 to 51 ms before its stream went out; this change's began 0 ms after it. The reads took 5 to 13 ms (SuperVideo's 47 ms on staging), and a context restored from the kept state streamed without a click or a challenge, as on staging (Byse 1.8 s, filemoon.to 3.3 s, Dropload and SuperVideo 0.7 s). After Vixeo's runs the store held no state, on either code. DoodStream's page did not load on either. Details in `docs/plans/challenge-reactions.md` → R4.

### Fixed: A Segment That Stalls or Cannot Be Resumed With a Range
- The HLS proxy waited the shared client's 30 s for a silent CDN, resumed a cut segment only with a `Range` request when its answer promised a length, and a fetch ahead that failed mid-body was a miss when the player came (production 2026-10-12: four segments of a 1080p playback on 97bf1 cut 16 to 27 s after their request, none asked for again, the picture jumped up to 8 s each time; ten fetches ahead failed with `ReadTimeout` or `RemoteProtocolError` on 97bf1 and acek-cdn). Segment reads now have a stall bound of their own, 15 s (`_SEGMENT_READ_TIMEOUT_S`, for the request on demand, its resume or restart and the fetches ahead; files keep 60 s): on 474 segments of 11 CDNs the headers came within 6.83 s and a flowing body left at most 1.82 s between two reads, one CDN fell silent for 16.51 s mid-body (`docs/plans/pi-performance.md` → The segments' stall bound; Mr. Fable's pick against 20 s). A segment that cannot be resumed with a range (chunked, encoded, or a CDN answering the `Range` request with the whole segment) is asked for again from its start, the bytes the player has skipped (the decoded bytes of an encoded one), once per transfer, and `hls_proxy_segment_resumed` names `how=range` or `how=restart`; files are not restarted. A fetch ahead that fails with a transport error is tried once more at once (`hls_readahead_retried`) unless its playback stopped or its host was throttled meanwhile; `hls_readahead_failed` names its attempts, and `hls_proxy_network_error` the error type (a segment's headers past 15 s show as `ReadTimeout`).
- Live proof (dev server, 11 min): two real HLS playbacks of 11 minutes each in parallel, each segment asked for at its playing time with 30 s of buffer, FireStream's Movie K in 1080p (175 segments) and VOE's Movie A: Part Two (58 segments): all 233 answered 200, read-ahead 231 hits and 2 misses (each playback's first segment), no resume, cut, retry or failed fetch ahead; FireStream's slowest answer, 14.15 s, was a hit awaiting a fetch ahead of a whole segment that flowed slowly and was not cut.

### Changed: Vixeo's Capture Clicks Its Player After 0.5 s
- The capture's wait before its first click is the resolver's: `capture_stream(..., autoplay_wait=S)` hands it through `StealthPool.capture_media()` to `_start_player()`, and without one the capture waits the 3 s for a player that starts itself (`_MEDIA_AUTOPLAY_WAIT_S`). Vixeo's player does not start itself and takes the first click at once, so its capture clicks after 0.5 s (`_AUTOPLAY_WAIT_S` in `hoster_resolvers/vixeo.py`): 6 of 6 runs streamed after that click, 2 of them on the production host (at 3.0 and 5.9 s, against 5.5 and 5.0 s with 3 s). Filemoon, Dropload, SuperVideo and DoodStream keep 3 s: on the production host Filemoon's player left 3 of 4 first clicks at 1.5 s unanswered and needs its click warm too, Dropload's missed a click below 3 s in the dev container, SuperVideo's starts itself, and DoodStream did not capture on the production host (no Cloudflare challenge). Numbers: `docs/plans/pi-performance.md` → The capture's autoplay wait (row 103). Dev proof (2026-10-12, 1 min): `capture_timing.py` with Vixeo's own wait clicked at 2.1 and 1.1 s and found the stream on the click, without a popup; with `--autoplay-wait 3` it clicked at 4.1 and 3.6 s.

### Fixed: A Paused Playback Keeps Its Read-Ahead
- The HLS proxy's read-ahead (`SegmentReadAhead`) forgot the least recently used playback, its segment order included, once 8 were followed; a VOD player fetches its media playlist once, so a playback paused while other playbacks started lost its read-ahead for good (production: a 1080p playback paused 4 min 34 s while 12 other media playlists passed the proxy, then 497 segments from the CDN on demand until the player reopened the stream). The segment order now outlives the fetches ahead: orders are kept for 32 playbacks and 3 h after a playback's last request (`_MAX_ORDERS`, `_ORDER_SECONDS`), and at most 8 playbacks hold fetches ahead (`_MAX_PLAYBACKS`: one more that schedules takes the place of the least recently used one, which keeps its order), so the 384 MiB bound holds. Live proof (dev server, 11 real HLS playbacks): a playback paused 65 s while nine others played a segment each resumed with 3 hits of its next 4 segments (the first after the pause comes from the CDN, its fetches ahead having gone at 60 s).

### Fixed: A Segment the CDN Cuts Mid-Body
- The HLS proxy let a transport error from a segment's body escape uncaught (production acek-cdn's `httpx.ReadTimeout` during a VidHide play, uvicorn's "Exception in ASGI application" with httpx's traceback and no CDN). A segment now gets the file proxy's handling, in one body generator for both (`_cdn_body` in `infrastructure/stremio/hls_proxy.py`): a transport error mid-body, or a clean end short of the promised `Content-Length`, is resumed once with a `Range` request from the next byte when the answer is unencoded (`hls_proxy_segment_resumed`); otherwise, or when the resume fails, `SegmentCut` aborts the transfer with one `hls_proxy_segment_cut` warning (CDN, error type, bytes sent and promised, whether a resume ran), so the player asks again instead of taking a truncated segment as whole. The file cut's warning names the error type too. Live proof (dev container, Movie A: Part Two's VIDHIDE · moflix on acek-cdn): the CDN answers a segment's `Range` with 206; a segment cut after 64 KiB was resumed from byte 65536 and arrived whole (313,208 bytes, identical to the CDN's); a play through the dev server's proxy went playlist, variant, segment with all 200.

### Changed: The Capture Probe Sets the Autoplay Wait
- `scripts/probes/capture_timing.py --autoplay-wait S` sets the capture's wait before its first click for the probe's runs, for every resolver alike in place of its own (`autoplay_wait`, above), and the report names the wait the captures used (`autoplay wait: 0.5 s (the resolver's)`). It measures what a shorter wait gains per hoster before the app changes it: Filemoon's player starts only on a click, so a warm capture on the production host spends 3 of its 10 s bound waiting (`docs/plans/pi-performance.md`, row 103).

### Fixed: A Frame's Failed Read Costs Its Own Host; a Refused State of Origins Alone Is Dropped Too
- The capture read every frame host's storage in one go under its 0.5 s bound, so one frame that navigated, detached or dawdled during the read (an ad's) cost the keep of every host, the player's own included. Each frame's read now ends after 0.4 s at most, and one that fails or runs out leaves out its own host only (`capture_state_save_failed` with that host and the error type); the host is read again at its next stream, and its kept entry stays as it was. Real Chromium, a page with two frames on routed pages: a detached ad frame left the other two hosts kept (the whole read failed before), an ad frame whose main thread was blocked for 5 s left nothing kept, as before, since the top page's own read waited for the same renderer.
- A refused state of origins alone (a kept host without cookies and no clearance cookie) kept its origins, so every later context failed the same way. It now falls back to an empty state, and the store drops the origins as for a state with cookies (row 97's review).

### Fixed: The Browser's Restart Launches the New Browser
- The shared browser restarts after 200 pages, since its memory grows with the pages it rendered. The restart only closed it, and the next operation launched the new one inside its own resolve bound: 6 to 11 s on the production host at the app's starts, against production's 10 s bound, and a timeout counts against the hoster's circuit breaker (code review 2026-10-12, V15). The restart now launches the new browser itself, and an operation that waits for it does so with its resolve bound stopped, as for a page. The restart is bounded to 30 s: `shared_browser_restart_failed` with the error type leaves the launch to the next operation, as before. A crash's relaunch stays with the next operation. At shutdown a running restart is cancelled instead of awaited.
- Dev container, real Chromium under Xvfb, 5 rounds each: the next operation after a restart spent 0.07 s of its bound to its page instead of 0.40 s, and one that came during the restart 0.07 s instead of 0.73 s.

### Fixed: A Refused Capture State Keeps the Cookies; the Restore Is Logged Once It Took
- When the browser refused a context with the kept state, the stealth pool created a bare one: every host's clearance cookies were gone, the stored entry stayed, and every later context failed the same way. The code review of 2026-10-12 reproduced it with an IndexedDB File value and with a unique index over invalid dates (finding 8). The context now starts from the cookies alone (the clearance cookies and the kept ones), and the store drops the kept origins and keeps their cookies (`capture_state_origins_dropped` with the hosts). A browser that refuses the cookies too gets a plain context, and the origins stay.
- `capture_state_restored` was logged before the creation it announced, and the stealth context's `clearance_restored` was gone. Both now follow the creation: `capture_state_restored` names the hosts and how many origins the context took, `clearance_restored` the clearance cookies' domains. `capture_state_restore_failed` names how many origins the refused state held.

### Fixed: A Capture Keeps Its State From Its Own Page
- The stealth pool took a captured stream's state with `storage_state(indexed_db=True)` on the live shared context. The driver's hidden page then walked every origin the context had ever committed, outside the page gate and without a lease: it raced the browser's 200-page recycle, swallowed the popups opened meanwhile, and its cost grew with the context's age (code review 2026-10-12, finding 6). The capture now reads the state from its own page before the page closes (`collect_capture_state()`): the context's cookies, and in each of its frames on a kept host, that origin's localStorage and IndexedDB. No other origin is visited. The read took 4 to 11 ms per capture in the dev container. The resolution waits for it, at most 0.5 s, and not at all when its resolve bound has less time left; the store still writes in the background, and `capture_state_saved` now names the read's `duration_ms`.
- An IndexedDB database is kept whole or not at all: one with a record that plain JSON cannot hold (a date, a file, a typed array) stays out, so no context is refused for it (finding 8's reproductions; Filemoon's two records are plain).
- What a player writes after its stream request is not kept: Vixeo's one localStorage key, on a hoster that meets no challenge.
- `scripts/probes/capture_timing.py --restore` keeps the runs' state as the app does and prints how long each read took.

### Fixed: The Newest Cookie Starts a Stealth Context
- `ClearanceStore.creation_state()` let every kept capture state's cookie replace the clearance store's of the same name, domain and path, whatever their age. A capture that kept Dropload's `cf_clearance` A and a challenge within the host's 10-minute keep interval that stored B in the clearance store left every context created before the host's next keep (a recycle, a restart, a relaunch) with A, which Cloudflare no longer accepts (code review 2026-10-12, finding 7). Each stored clearance cookie now carries the time it was saved (`saved_at`, never handed to a browser context), and per cookie the newer of the two wins; a cookie stored before carries no time and loses to a kept one.

### Changed: The Capture Probe Counts the Kept IndexedDB Records
- `scripts/probes/capture_timing.py --restore` prints, per origin with an IndexedDB database, its records and how many of them are encoded (a value or key no plain JSON holds: a date, a typed array, a file): `1 IndexedDB database (2 records, 0 encoded)`. In the dev container on 2026-10-12 Filemoon's player host held 2 records, none encoded; Dropload and Vixeo kept no IndexedDB (`docs/plans/challenge-reactions.md` → R4, row 97).

### Fixed: One Title Set Judges A Site's Series Name
- The use case fetches the TMDB titles for every language the stream plugins search in, not only the selected plugins' languages, and every title info carries the request's series titles in all of them (`TitleMatchInfo.series_titles`). The title matcher judges a partial match by them in every language group, and they go to the locating plugins as `EpisodeRef.titles`. The matcher normalises titles with the episode index's `normalize_title`, which decodes the entities the sites leave in their titles.
- Why: code review 2026-10-12, finding 11. The matcher judged a site's name by its language group's titles, `locate()` by the selected plugins' titles: aniworld's "Anime D" (TMDB's English title) was a whole title for `locate()` but a partial match of the German "Anime D" for the matcher, held until aniworld's end and dropped beside its other match; a scored selection without an English plugin flipped `locate()`'s verdict, and a joined request took the first request's titles.
- Cost: with scored selection, a request whose selection lacks a language makes one more TMDB lookup (in parallel with the others).

### Fixed: A Site Name Without Its Article Is No Parent Series
- `is_partial_title` (`domain/entities/stremio.py`) counts no article (the, a, an, der, die, das, ein, eine) and no "and"/"und" as a title word: "Series I" and "Series J" ("&" falls away when normalising) name "Series I" and "Series J" whole.
- Why: code review 2026-10-12, finding 10 (plausible: no captured page shows such a pair). The site's name for the requested series counted as its parent, so a spin-off beside it ("Series I: Spin-off", "Series J: The Anime") dropped the series in every arrival order. The matcher's partial flag and `locate()`'s `is_partial_series` share the rule.

### Fixed: A Mirror Standby's Partial Matches Go With Its Member's Search
- The search runner marks a standby's results with the member it stood in for (`standby_for`); `SearchProgress` holds and drops partial matches, and the search cache merges results, by the plugin whose search gave them (`asked_plugin()` in `application/stremio/search_cache.py`).
- Why: code review 2026-10-12, finding 4. A standby's run ends under the member's name, while its results carried only its own: hdfilme's "Anime C: Sequel" did not drop streamcloud's "Anime C" (found standing in for hdfilme's base-title query), so the parent series was served and cached, and a standby's lone partial match ("Anime E" for "Anime E: Sequel") waited for the search's end and missed the answer at the budget.

### Changed: The Capture Probe Times Each Challenge
- `scripts/probes/capture_timing.py` prints when each challenge was first met, in seconds into the run, beside the page loads and clicks (`captcha 4.1 s, captcha/verify 4.8 s`; the column is `challenge at`). Six cold Filemoon runs in the dev container met the captcha 3.8 to 4.2 s in, 0.1 to 0.5 s after the first click, and found the stream by 7.2 s (`docs/plans/challenge-reactions.md` → R4, the restart).

### Fixed: A Dead Link-Out Behind a Passed Challenge Is No Unsolved Challenge
- `BrowserFetcherPort.resolve_redirect()` answers a `Redirect` (`domain/ports/browser_fetcher.py`): the `target` and whether the browser got past the site's challenge (`passed`). The stealth pool passes on a target, a page without a challenge (an error page too) and a cleared challenge, not on a broken navigation, no page in time or a challenge that stayed; the solver on any solution; the chain when any fetcher did, the first target winning. The httpx base settles a link-out's challenge by `passed` (`settle_challenge()`), so a dead link-out behind a passed challenge counts as solved; a link-out served from the challenge memo counts nothing, as before.
- Why: code review 2026-10-12, finding 14. A link-out behind a challenge that the browser passed and that answered a same-host 404 (an expired hash) or, for sto, no redirect without its Referer, flagged the whole search as unsolved: one dead link-out inflated the plugin record's `challenges_unsolved`, which N20's 5 % rule for a solver trial reads (sto, byte and kinox; filmfans and serienfans through `_resolve_result_links`).

### Fixed: A Request's Own Cut at the Bound Cancels Its Capture; a Completion's Check Error Is Logged
- A challenged capture runs on in the background only when the bound's cancel is the only new one on the request's task (`Task.cancelling()` against its count at the attempt's start). A request cut in the loop iteration in which the bound fires (the answer went out) cancels the capture and counts as `cut`, as any request cut does.
- A completion judges its stream inside a try: an unexpected error of the playback check logs `hoster_challenge_completion_error` (outcome `none`), caches nothing and does not step the cooldown up.
- Why: code review 2026-10-12, finding 15 and V29. `clock.expired()` alone was also true when both cancels landed together: the capture was handed over, kept its page up to 20 s after the answer went out, and no cooldown started at the cut. The check's error was never retrieved.

### Fixed: Challenge Completions Leave a Browser Page Free
- The background completions of challenged captures hold at most the stealth browser's page limit − 1 pages together (the composition hands the registry the page gate, `pages`). A capture cut after its challenge while they hold the rest is cancelled at the cut and ends as `challenge` with its cooldown; on a single page none runs on.
- Why: code review 2026-10-12, finding 12. Completions were capped at one per hoster only: a Filemoon and a Dropload completion held both of the 2 pages for up to 20 s, and a /play resolution waited for a page until it ended `PageBusy` and fell back to the stale link.

### Fixed: A Request Joins Its Link's Running Completion
- A request for a link whose challenged capture runs on in the background no longer starts a second capture: it waits for the completion, at most the resolve bound, and answers the stream the completion cached (`hoster_resolve_joined`, the `hoster_resolve` outcome `joined`), `None` without one in time. The completions are kept by their link too (`_completing`), and `_complete()` returns the stream it cached.
- Why: code review 2026-10-12, finding 9. With the cooldown over (or ended by another link's stream), a second capture of a link whose completion still ran ended without the first's challenge and cached the link as dead over the completion's stream for 15 minutes.

### Fixed: A Play-Time Refresh Passes the Challenge Cooldown
- `resolve(refresh=True)` (the CDN refused a stored stream: `after_refusal()`) passes the hoster's challenge cooldown; only an open breaker refuses it, as before the cooldown. A search-time resolution still waits the cooldown out.
- Why: code review 2026-10-12, finding 5. A Filemoon link met a challenge and started the cooldown; a stored Filemoon stream whose video URL had expired was refused by its CDN, the refresh came back `None` without asking the resolver, and playback failed at once.

### Fixed: A Page Past Its Challenge Gives a Verdict; DoodStream's Widget Marks Nothing
- A resolution's challenge mark says whether its challenge still stands (`ChallengeMark.open`). The browser passes it when its page got past the challenge (`mark_resolution_passed()`): `solve_cloudflare()` after a shown interstitial cleared, `pass_turnstile_widget()` after the widget's token came and the form went out, and the capture when the page shows the hoster's offline notice. A later challenge marks it again.
- The registry judges a resolution without a stream after a pass as one without a challenge: `dead`, cached for 15 minutes, and the hoster's next link is resolved. A cut after a pass stays `challenge` and runs on in the background, but starts no cooldown (`hoster_resolve_challenge` names `passed`, with `cooldown_s=0`). A completion past its challenge caches a dead link as dead without a step up; its error or deadline steps nothing up.
- Provider frames mark by default; a resolver whose player's widget does not gate the stream passes `passive_widget=True` to `capture_stream()`, and only DoodStream does. reCAPTCHA counts by its checkbox frame (`anchor`): its puzzle frame (`bframe`) loads hidden with every widget. `scripts/probes/capture_timing.py` forwards `passive_widget`.
- Why: code review 2026-10-12, findings 2 and 3. A dead Dropload link behind a cleared interstitial ended as `challenge`, and its cooldown skipped the hoster's live next link. DoodStream's player loads an invisible Turnstile on every capture and does not wait for it (dev, 2026-10-12: the frame at 2.5 s, the stream on the click at 5.3 s, the widget's token at 6.3 s), so every DoodStream link without a stream, a dead one too, ended as `challenge`.
- Not covered: the hoster's own captcha (Filemoon's `captcha`, `captcha/verify`) and Dropload's gate frame give no pass signal before the stream, so a dead link behind them stays `challenge`. A completion that gets past a challenge which stood at the cut and finds the link dead leaves the cut's cooldown step to run out.

### Fixed: An Episode Without Its Kitsu Number Keeps Its Title Check (aniworld, sto)
- The episode reference names where its absolute number comes from (`EpisodeRef.source`): `kitsu` (a `kitsu:` request's own number, or the one the anime ids give an IMDb request), `position` (the catalog's position of a series no Kitsu entry counts whole: Anime D, Anime C: Spin-off, Anime J) or `unchecked` (the position of any other series: right after a start until the id list is in memory, the hour after a failed download, or an episode whose Kitsu number does not come out). `locate()` keeps row 87's rule for the first two; an unchecked position takes a titled row only through the neighbour and title rules, as before row 87, a number-only row (s.to's anime rows) by its number as before, and the number's row wins a title tie (code review of 2026-10-12, finding 1).
- Where the number may be the position, the use case asks the anime ids whether a Kitsu entry counts the series whole (`AnimeIdResolverPort.has_whole_series_entry()`). The search cache key carries a `u` before an unchecked position (`...:22:4:u1088`), so an answer the titles placed and one the number placed never share an entry. `aniworld_episode_located` and `sto_episode_located` log `absolute_source`.
- The app's start loads the anime id list in the background (`AnimeIdLists.load_in_background()`), so the window without Kitsu numbers after a start shrinks to the load (dev container: 0.01 s from the cache backend, 0.43 s from the network).
- Why: right after a start Anime A S22E4 got its position 1088, aniworld's #1088 is the episode before (Kitsu and the site count 1089), and the answer was cached. Measured (`docs/plans/series-episodes.md`, row 95): the review's 311 Anime A episodes from position 590 without the Kitsu number are placed right 298 times, as on main (staging 0); row 82's probe with the Kitsu numbers equals staging's cell for cell (N26 0); Anime P's 153 unchecked references stay at their rows.
- `scripts/probes/anime_offsets.py --aniworld` mirrors the source (column `Unchecked`); `--start` builds the references as right after a start and judges them by the Kitsu number, beside the same references as trusted positions.

### Added: The Kept-State Probe
- `scripts/probes/capture_state.py` (`prodctl.py probe capture_state`, read-only) prints the browser's kept capture states (`browser:capture_state:v1`: per host its age, each cookie's name, domain, path and remaining lifetime or `session`, per origin the localStorage key names with their value lengths and the IndexedDB names) and the stored clearance cookies alike; never a value. The first production reading (`docs/plans/challenge-reactions.md` → R4): Filemoon's captcha pass is a localStorage token on its player host, not a cookie, so no cookie lifetime bounds it.
- The probe masks the id-like segments of cookie names, cookie paths and localStorage key names as `…` (`mask()`: a segment between `.`, `/`, `:`, `_` and `-` of 12 or more characters with letters and digits), since a file code names the file played, like a URL; setting names such as `i18nextLng` stay readable.

### Changed: The Capture Probe Uses the App's Challenge Rule and Store
- `scripts/probes/capture_timing.py` marked a run's challenges by its own rule (any request to Cloudflare's challenge host, any `captcha` path segment) and `--restore` copied the context state into its own context, beside `ClearanceStore`. It now judges each request with the stealth pool's rule (`_challenge_of`: a captcha provider's challenge frame, or a request matching the resolver's own captcha pattern, which the probe's pool takes from the capture; the hoster captcha is still split into `captcha` and `captcha/verify`), and `--restore` keeps the state under every host it names through the app's `ClearanceStore` in a temporary directory, from which the app's own context creation starts the `restored` run. What it measures stays: a control and a restored run of the whole state (code review of 2026-10-12; backlog row 99). Dev container, one Filemoon link, `--runs 1 --restore`: run 1 and the control met `captcha, captcha/verify` (5.3 s, 4.4 s), the restored run none (1.9 s), as in row 91's measurement.

### Changed: The Filemoon Captcha-Pattern Test Mocks HTTP With respx
- `test_the_players_captcha_requests_are_named` (`tests/unit/infrastructure/test_filemoon_resolver.py`) served the embed page from an `AsyncMock` client, against the respx rule for resolver tests (AGENTS.md §6). It now runs the resolver on a real `httpx.AsyncClient` with the Byse embed page and details API mocked by respx, and reads the pattern from the recording `_FakePool` (code review of 2026-10-12; backlog row 99).

### Fixed: The Warm-up's Lifespan Test Restores the Plugin Globals
- `tests/unit/interfaces/test_browser_warmup_lifespan.py` runs the app's real lifespan, which sets the plugin bases' class globals (the shared HTTP client, the cache, the browser fetcher, the clearance store, the page timeout) and left them on the closed client and cache: plugin tests that ran after it in the same process failed with "Cannot send a request, as the client has been closed" (5 byte tests; 13 failures ahead of `tests/unit/infrastructure` and `tests/unit/application`). The test now restores the five globals (code review of 2026-10-12, finding 13; backlog row 99).

### Added: The Resolver Link Probe Takes a Next Link
- `scripts/probes/resolver_urls.py --avoid <file>` skips the links an earlier output names, so each resolver keeps its next link (write it with `--out` to a file of its own; the live test reads `resolver-urls.json` only). Used for the four live cases the suite of 2026-10-12 lost (`docs/plans/plugin-domains.md` → Live suite (2026-10-12)): playmate's first link was a removed file, firestream's CDN refuses the dev container on every link, no stream of veev or vidhide passed its CDN's check from here (their offline files are told correctly).

### Fixed: The Read-Ahead Outlives a Pause
- A playback the HLS proxy follows keeps its segment order while it idles: 60 s after its last request it loses only its fetches ahead (their memory, counted `dropped` as before), and the playback itself goes only when the least recently used of 8 makes room or its playlist is fetched again (`SegmentReadAhead._sweep` in `infrastructure/stremio/hls_proxy.py`). A player that resumes after a pause without fetching the playlist again gets the next three segments fetched ahead from its first request on.
- A segment no playback lists counts `miss` (`hls_readahead_total`), so a playback the read-ahead lost shows in the counters instead of leaving them still.
- Why: in production Stremio went on after a 20-minute pause, in which another playback's playlist had swept the idle one, at the next segment without fetching the playlist again. Every segment came from the CDN on demand, median 4.1 to 4.6 s against 9 to 19 ms before the pause (143 of 152 over 3 s), the playback stuttered and `hls_readahead_total` stopped growing (backlog row 94).
- Dev proof (FireStream, one 1080p HLS playback of 2244 segments through the dev server; segments 1 to 3, 70 s without a request, another stream's playlist fetched, then segments 4 to 7 without the playlist): the sweep dropped the three fetches ahead, and the resumed playback answered segment 4 from the CDN in 499 ms (`miss`) and segments 5 to 7 in 138, 8 and 6 ms (3 `hit`, 6 `ok` fetches ahead). The code before the fix, same steps: segments 4 to 7 in 366, 143, 144 and 133 ms, all from the CDN, the counters unchanged. The dev container's CDN answered on demand far faster than production's, so the times show the mechanism, not production's stall.

### Added: A Challenged Capture Finishes in the Background
- A capture the resolve bound cuts after its challenge is no longer cancelled: the attempt answers `challenge` at the cut, and the capture runs on for up to 20 s more on the browser page it holds (`_complete` in `hoster_resolvers/registry.py`). Its stream passes the registry's judgement, is cached under its link and counts as the hoster's stream: it ends the challenge cooldown and closes a half-open breaker, so the next request answers from the cache.
- Without a stream (none, an error, or the 20 s deadline, which cancels the capture and closes its page) the challenge stands: nothing is cached or counted, and the hoster's next cooldown step starts at once (`hoster_challenge_unsolved`, `ChallengeCooldown.unsolved()`).
- One completion runs per hoster (a second capture cut meanwhile is cancelled at the cut); `resolve_for_client()` and a request's own cut cancel the capture as before; shutdown cancels the completions (`aclose()`). New stage `hoster_challenge_completion` (`resolver`; `stream`, `none`, `cancelled`; timed from the cut).
- Why: on the production host Filemoon's and Dropload's cold captures took 13.3 to 17.8 s against the 10 s resolve bound, so a cold capture never delivered its stream (`docs/plans/challenge-reactions.md`, R2; OpenSpec `react-to-challenges`, backlog row 90).
- Dev proof (the app's registry, a cold context): Filemoon cut at 4.1 s after its captcha at 3.9 s found its stream 0.4 s after the cut, Dropload cut at 2 s after its Turnstile frame at 0.6 s 2.6 s after the cut; the next request answered from the cache, the breaker untouched. With the deadline set to 0.1 s the capture was cancelled, its page closed and the cooldown stepped up to 5 minutes.

### Added: A Capture That Meets a Challenge Is an Outcome of Its Own
- A hoster resolution whose pages showed a challenge and that found no stream in time ends as `challenge` (`hoster_resolve_challenge` with `kind` and `cooldown_s`), no longer as `timeout` or `dead`. The challenge is Cloudflare's interstitial or Turnstile widget, a captcha provider's frame, or a request the resolver names as its hoster's own captcha (Filemoon's `captcha` and `captcha/verify`). A `challenge` is not cached and neither counts for nor resets the circuit breaker; a half-open trial that ends as one frees its slot.
- The hoster's links wait out a challenge cooldown instead (`ChallengeCooldown` in `hoster_resolvers/challenge_cooldown.py`, memory only): 1, 5, 15, then 30 minutes for consecutive challenges, ended by a stream. A skipped link is logged (`hoster_resolve_challenge_cooldown`), counted (`hoster_resolve` outcome `challenge_cooldown`) and not cached; the cooldown is checked before the breaker. A capture cut before its page showed anything stays a `timeout`.
- The registry gives each attempt a `ChallengeMark` (`challenge_mark` beside `work_clock` in `browser/page_gate.py`); `solve_cloudflare()`, `pass_turnstile_widget()` and `capture_media()`'s request listener mark it (`challenge_frame()` in `captcha/detect.py`; `capture_media()` and `capture_stream()` take `challenge_requests`). `hoster_resolve_success` names the challenge a cold capture passed on its way (`challenge`) and the attempt's wall time (`duration_ms`), so the logs tell cold from warm times.
- Why: on the production host Filemoon's and Dropload's cold captures took 13 to 18 s against the 10 s resolve bound, and every half-open trial since a restart was cut, counted and reopened the breaker for an hour (`docs/plans/challenge-reactions.md`, R1 and R7; OpenSpec `react-to-challenges`, backlog row 89).
- Dev proof (the app's registry, a fresh context per attempt): Filemoon cut at 4.1 s after its captcha request at 3.7 s and Dropload cut at 2 s after its Turnstile frame at 0.6 s ended as `challenge` with the breaker untouched, and the next link was skipped with 60 s left; a capture cut at 0.3 s, before any page, stayed a `timeout` and opened the breaker.

### Changed: The Browser Starts With the App
- Once the app reports ready, its lifespan launches the shared browser and creates the stealth context, with the kept capture state, in the background (`StealthPool.warmup()`, row 93 of the archived backlog, OpenSpec `keep-capture-state`). Before, the first capture paid the launch (about 9 s on the production host): Filemoon's breaker trial after the restart spent its resolve bound on it and reopened the breaker for an hour (`docs/plans/challenge-reactions.md` → R4).
- Readiness does not wait for the warm-up; a failed one logs `browser_warmup_failed` with the error type and leaves the launch to the first capture, and shutdown cancels a running one before the pools close.

### Fixed: A Sub-Series' Request No Longer Gets Its Parent Series' Episodes (aniworld, sto)
- A series result named only by a shorter form of the request's titles is a partial match (`is_partial_title` in `domain/entities/stremio.py`: none of its titles holds a request title whole, and one is a strict word subset of one; a year is no word): "Anime C" for "Anime C: Sequel", "Anime E" for "Anime E: Sequel". TMDB's German title "Anime C: Sequel" adds the base query "Anime C", aniworld's and sto's searches found the series Anime C beside Anime C: Sequel, and the title matcher kept it (a result that only drops words scores 1.00). The matcher now returns such results apart (`TitleMatches.partial`; `title_match_summary` counts them as `partial`), and `SearchProgress` (`application/stremio/search_progress.py`) holds a plugin's partial matches until the plugin is done: beside the plugin's other match they are dropped (`stremio_partial_matches_dropped`), alone they count, so a site that lists a sub-series only under its parent's name keeps it. Movies keep their subset match ("Movie A" for "Movie A: Part One"). Row 92 of the archived backlog, OpenSpec `place-episodes-by-number-first` (tasks group 5).
- `EpisodeRef` carries the request's series titles (`titles`: each language's TMDB title and alternatives; the search cache key is unchanged), and aniworld and sto place an episode on a partial series by its title alone (`is_partial_series` and `locate(index, ref, partial=True)` in `infrastructure/plugins/episode_index.py`): both sites keep the Anime E: Sequel as Anime E's season 17, where the request's number counts Anime E's own episodes. Without a title match the series gives no result. The `aniworld_episode_located`, `sto_episode_located` and `*_episode_not_located` lines carry `partial`.
- The probes do the same: `title_match.py` names a partial verdict and drops it beside another kept hit, `series_episodes.py` passes the request's titles, and `anime_offsets.py --aniworld` builds the reference with them (through the configured title client, `build_tmdb_client`, which the composition root now uses too) and shows whether a series is partial.
- Measured in the dev container (`docs/plans/series-episodes.md`, row 92): Anime C: Sequel S1E6, S2E9, S3E1 and S9E10 answer Anime C: Sequel's episode alone through aniworld and sto (with row 87 alone both added Anime C's for all four); the Anime E: Sequel's S1E1, S1E13, S2E1 and S3E5 land on Anime E's season 17 by title through both (aniworld put all four on Anime E's own episodes with row 87 alone); none of row 82's fourteen series is partial, and `anime_offsets.py --aniworld` gives row 87's table to the count; sto's 28 requests of row 87 are unchanged but for Anime C: Sequel S8E16's Anime C result.

### Changed: The Row With the Episode's Number Is the Episode (aniworld, sto)
- `locate()` (`infrastructure/plugins/episode_index.py`) takes the row that shows the reference's absolute number, whatever its English title: the maintainer's decision on N26 (row 87, OpenSpec `place-episodes-by-number-first`). The title rules (a neighbour within 5 at 0.6, the exact normalised title, the best title at 0.85) decide only without that row or without a number, as on aniworld's Anime K and Anime L pages. Where the parts of a double-length episode share its number (Anime F), the first part is the episode. `episode_located_by` and the `aniworld_episode_located` and `sto_episode_located` lines name the rule that placed it: `number`, `neighbour`, `title` or `fuzzy_title`.
- Measured with `anime_offsets.py --aniworld` on row 82's fourteen series before and after (`docs/plans/series-episodes.md`, row 82): the 307 episodes `locate()` gave nothing (N26) and the 191 title-confirmed placements on another row now take the number's row (4559 → 5057 of 6708 episodes on it), and Anime K's and Anime L's title placements are unchanged. Row 82's check by eye found the number's row right in 69 of 69 and 114 of 115 of these cases; the miss is Anime F #1077, which aniworld counts differently. On its own the change gave a request for Anime C: Sequel aniworld's Anime C episode with the same number too, as sto gave it already; the entry above ends both.

### Added: A Probe Counts the Stored Stream Qualities
- `scripts/probes/stream_quality.py` (`prodctl.py probe stream_quality`) reads the hoster resolver registry's snapshot (`hoster_state:v1`) from the app's cache backend and counts per resolver its resolutions, dead links, streams, HLS streams, streams per known quality class and streams with a size, with the share of streams whose quality is known. filemoon, supervideo and voe name a quality themselves, so they are counted apart from the resolvers whose quality only the playback check measures. Read-only; names and counts only.
- Why: task 3.2 of `add-stream-media-quality` (backlog row 7), the production check of the quality and size the playback check reads from the stream (I2).

### Added: A Capture Hoster Stays Warm Across Restarts
- After a capture found its stream, the stealth pool keeps the state of the page's host and its frames' hosts (cookies of the host and its parent domains, localStorage and IndexedDB of its origins) in the cache backend (`browser:capture_state:v1`, beside the clearance cookies): in the background, at most once per host per 10 minutes, at most 24 hours, at most 512 KiB per host. Each new stealth context (start, recycle, relaunch) is created from the kept states and the clearance cookies; a failed creation falls back to a plain context (`capture_state_restore_failed`). Logs: `capture_state_saved`, `capture_state_restored`, `capture_state_too_large`, `capture_state_corrupt`, `capture_state_save_failed`, with hosts and counts only.
- Why: a restart, a recycle or a relaunch made every capture hoster cold again, and the cold paths outlast the production host's 10 s resolve bound (`docs/plans/challenge-reactions.md` → R4).
- Dev proof, a restart as a new process: Dropload 5.0 s with the Turnstile widget, then 1.1 s without it twice; Filemoon 4.9 s with its captcha, then 7.2 and 2.2 s without it.

### Added: The Capture Probe Restores a Context After a Relaunch
- `scripts/probes/capture_timing.py --restore` takes the runs' context state (`storage_state(indexed_db=True)`, in memory only) and prints its make-up (cookie names per domain, ids masked; localStorage keys and IndexedDB databases per origin; no values), then resolves the link in a relaunched browser twice: in a fresh context (`control`) and in one restored from the state (`restored`). Every run now names the challenges it met: the player's `captcha` and `captcha/verify`, `turnstile` for Cloudflare's challenge host.
- Why: row 91 measures R4's premise (`docs/plans/challenge-reactions.md`): whether a context restored after a restart skips the hoster's challenge.
- In the dev container both hosters skip it restored: Filemoon control `captcha, captcha/verify` and stream at 5.6 s, restored no challenge at 1.7 s (the state: two Byse cookies, an IndexedDB database); Dropload control `turnstile` and two clicks at 9.5 s, restored no challenge at 0.8 s.

### Changed: The Redis Probe Is redis_cache
- `scripts/probes/redis.py` is now `scripts/probes/redis_cache.py` (`prodctl.py probe redis_cache keys|ttl|get`): its old name shadowed the redis package for every script started from that directory, so the dev-container probes no longer need `python -P`. Their usage lines and AGENTS.md drop the flag.

### Fixed: A Link-Out the Browser Resolves No Longer Counts as an Unsolved Challenge
- `HttpxPluginBase._resolve_redirect()` hands a link-out that meets a Cloudflare challenge to the browser fetcher; it marked the challenge but never settled it, so every such search counted in `challenges_unsolved`, whatever the browser did. It now settles with the browser's outcome: solved when the browser returned the target, unsolved without one (as `_fetch_via_browser()` does for pages). Affects sto (its own link-outs) and byte and kinox (through `_resolve_own_links()`); their `challenges_unsolved` counts from before this fix overstate the misses.

## v0.4.0 - 2026-10-12

Anime and the right episode: the Kitsu catalogs' ids, an anime episode's absolute number from Kitsu (for IMDb requests too; an episode 0 entry no longer shifts it), aniworld and sto placing the episode on the site's own season pages, and a series filter that keeps other series and episodes out. Playback through Scavengarr: address-bound direct files (DoodStream, MixDrop, Vinovo, FSST) go through a byte-range file proxy, the HLS proxy keeps three segments ahead, and the browser captures keep the players' ad tags out. Cut searches continue in the background under an answer budget of their own, resolutions and circuit breakers outlive a restart, the plugins' long-term record counts results, timeouts, challenges and dead sites, and quality and size come from the stream itself. Also the filmo plugin, two resolvers for moflix's mirrors, the sites' official domain lists, every setting from the environment, a published multi-arch image (`ghcr.io/strob0t/scavengarr`), Dependabot, alert rules, and the production diagnostics' digest, Stremio round and post-deploy check.

### Added: The Anime Probe Places Episodes on aniworld's Index
- `scripts/probes/anime_offsets.py --aniworld` (row 82) places each regular Cinemeta episode of a series on aniworld's episode index as the app does: the series the plugin's search gives (`--slug IMDB=SLUG` names the page instead), its season pages read once through the plugin's fetcher, the reference `TitleResolver.episode_ref()` builds with the app's Kitsu number, and `locate()`. Per series it counts the placements at the number's row, at a neighbour (with the offsets), by title, nowhere although the number's row has an English title (N26) and nowhere, the title-confirmed placements at another row (ties apart), and prints `--cases` of each kind. Default: Anime D, Anime K, Anime L, Anime M and the long-runners. Read-only, names and counts only.
- Measured (`docs/plans/series-episodes.md`, row 82, fourteen series): `locate()` gives nothing for 307 episodes whose number's row is there (N26), and the number's row was the episode in all 69 checked by eye. It takes another row than the number's in 191 of 4745 title-confirmed placements (101 ties, where `_best` keeps the earlier of equal scores); in 114 of the 115 checked that row is the wrong episode. The maintainer's options for N26 are in the plan doc; nothing in `src/` changes.

### Removed: Dead Code and Files
- `infrastructure/common/converters.py` (`to_int`, uncalled since the YAML/scrapy removal) and its test; the unused hand-written `tests/fixtures/html/testsite/` pages and the `fixtures_dir` fixture; filmpalast's unread `search-the-last-of-us` page; `flake.nix` and `flake.lock` (an x86_64-only openspec shell nothing referenced; the dev container installs openspec through npm). The observability guide lists the `resources` and `links` probes among its examples.

### Fixed: Vixeo Captures Keep the Player's Ad Tag Out
- The Vixeo resolver's capture runs the scripts of the page's and its frames' sites only (`own_scripts_only=True`, as Filemoon's since row 79). The rule itself is unchanged.
- Why: on the production host Vixeo's player loads an ad tag (`al5sm.com/tag.min.js`, the path of Filemoon's) that turns every click into a popup: no stream in 2 of 2 runs, 3 popups each; with that one domain blocked a stream in 2 of 2 (5.8 and 5.5 s, 0 popups; row 81). The dev container's resolver refuses the ad domains, which is why Vixeo always captured there.
- In the dev container Vixeo still captures with the rule (2 of 2 at 3.9 s, 0 popups): every foreign script reads `blocked`, and the player, whose code is inline in its page, needs none of them. The production host's proof follows the deploy.

### Fixed: Filemoon Captures Let Cloudflare's Challenge Widget Run
- The own-scripts rule of Filemoon's capture lets the scripts of `challenges.cloudflare.com` through (`_CHALLENGE_HOST` in `stealth_pool.py`, the exact host). Until now a Turnstile widget that the page loads from there counted as a foreign site's script and was aborted, so a Filemoon page showing the widget could not pass it. `cdnjs.cloudflare.com` and every other site's scripts stay foreign; the ad tag still aborts.
- Not measured: no Filemoon page has shown the widget yet; unit tests cover the rule.

### Changed: An IMDb Anime Episode Carries Its Kitsu Number
- An IMDb series request's episode gets its number in the one Kitsu entry that counts the series from its start, looked up alongside the titles (`AnimeIdResolverPort.kitsu_episode()`); the plugins that locate episodes (aniworld, sto) place it by that number, as the anime sites count. The candidates are Fribb's series entries without a TheTVDB season for the IMDb id (`AnimeIdLists.whole_series()`); the Anime Kitsu addon's record of each counts when it names the IMDb id and places its episode 1 at S1E1, and exactly one of their episodes must sit at the request's season and episode. A `kitsu:` request keeps its own number. One info line per number (`anime_kitsu_number`).
- The look-up never waits for the id list: after a start the list loads in the background (one load at a time, ended at shutdown), so the first anime requests go without the number. A record missing from the cache or ending before the episode is asked for again at most once an hour per title, one fetch that concurrent requests share.
- Why: Anime A's Cinemeta list lacks Kitsu's episode 590, so from S16E12 on the position lay one below the sites' number, and s.to, whose anime rows show no English title, placed the episode before (S22E04) or nothing (S16E12). With the Kitsu number it places both right. Of row 72's eleven long-runners, Anime A's 590 episodes that were off are equal now; the other ten keep their counts.
- `scripts/probes/anime_offsets.py` compares with the app's look-up and counts the numbered episodes (`--position`: the numbering without it); `scripts/probes/series_episodes.py` gives IMDb requests the Kitsu number too.

### Fixed: Filemoon Captures Keep the Player's Ad Tag Out
- The Filemoon resolver's capture (its `/e/` pages and Byse's `/d/` watch pages) runs the scripts of the page's and its frames' sites only (`StealthPool.capture_media(own_scripts_only=True)`, through `capture_stream()`): a script of another site is aborted as the client's block and logged at debug level with its site (`stealth_capture_script_blocked`). The media cut stays, and the other captures are unchanged.
- Why: on the production host the Byse player's frame loads an ad tag (`llvpn.com`) that turns every click into a popup, so the player never starts its access flow: no stream in 10 of 10 runs (2026-10-11). With the tag blocked the player ran its access flow in 4 of 4 runs and gave a stream in 3 (row 78). The dev container's resolver refuses the ad domains, which is why it always captured.
- In the dev container both link kinds still capture with the rule (Byse 4.5 and 1.6 s, `/e/` 5.3 and 1.5 s), and the tag reads `blocked`. The production host's proof follows the deploy.

### Fixed: An Episode 0 Entry No Longer Moves an Anime's Episode Numbers
- The episode reference's absolute number (`TitleResolver.episode_ref()`) counts only the entries of season 1 and up with episode 1 and up. Cinemeta lists some episode 0 entries in regular seasons (Anime D' S2E0 and S4E0, Anime R's and Anime S Chronicle's S1E0), and every later episode was numbered one or two above Kitsu and the sites (Anime D' S2E1 was 51, the site's 50). An episode 0 entry of a regular season now has no position of its own, as a special has none; a `kitsu:` request's number is kept within 5 of the new position.
- Measured (`docs/plans/series-episodes.md`, row 77): Anime D 224 of 224 episodes now equal Kitsu's number (49 before), Anime R 112 of 112 (0), Anime S Chronicle 26 of 26 (0); row 72's other ten long-running anime unchanged. aniworld numbers these series as Kitsu does. Each affected episode misses the search cache once, since the key carries the number.

### Added: The Capture Probe Blocks Domains and Counts Popups
- `scripts/probes/capture_timing.py --block DOMAIN` (repeatable) aborts every request to the domain and its subdomains in the probe's browser: on the capture's page, ahead of the capture's own route, and in its context, for popups. Such a request reads `blocked` in the diagnosis, apart from the capture's cut of the media (`net::ERR_FAILED`) and the network's errors. `--diagnose` also counts the popups each run's page opened (the capture closes them).
- Why: on the production host the Filemoon player loads an ad tag (`llvpn.com /tag.min.js`) and then never starts its access flow, in 4 of 4 runs on two links (2026-10-11), while in the dev container the resolver answers the ad domains with `0.0.0.0` and the player plays in 4 of 4 runs. Both run Chromium 153, build 8010, with the same codec answers. `--block llvpn.com` gives the production host the dev container's state for that one domain; the popup count tells an ad that takes the clicks from a player that waits for the ad.
- In the dev container `--block llvpn.com` changes nothing: both links captured in both runs (1.4 to 5.3 s), the tag reads `blocked`, and no popup opened.

### Added: The Capture Probe Shows What the Player Asked For
- `scripts/probes/capture_timing.py --diagnose` prints per run the requests of the capture's page by domain and path, the ids masked (`/api/videos/<id>/embed/playback`), each with its resource type and outcome: the status, `redirect`, the browser's error or `pending`. After the clicks it asks each frame whether it has a video element (with its MediaError code and network state) and what MediaSource and canPlayType answer for H.264, AAC and HLS. The launch line names the Chromium's major version and build. Images, fonts and stylesheets are summed up in one line, and only web requests count. The probe still prints no URL, no id and no token.
- Why: on the production host neither Filemoon link gave a stream in 4 of 4 runs (two links, three clicks each, about 20 s), while the dev container captures both in 1.3 to 6.1 s (2026-10-11). The diagnosis separates the egress from the browser build.
- In the dev container both links use one player backend: the watch page (Byse `/d/`) or the embed page (`/e/`) frames the player's own domain, whose `access/challenge`, `access/attest`, `embed/captcha`, `embed/captcha/verify` and `embed/playback` calls answer 200 before the playlist is requested. The player frame has a video element without an error, and MediaSource plays H.264 and AAC.

### Added: A Probe Counts the Episode Offsets of Long-Running Anime
- `scripts/probes/anime_offsets.py [--kitsu 12,210,...]` runs in the dev container and reads Cinemeta and the Anime Kitsu addon only (row 72). Per long-running anime, given as a Kitsu id (default: eleven long-runners whose Kitsu entry spans the series), it takes each Kitsu episode the addon maps to an IMDb season and episode (`imdbSeason`/`imdbEpisode`). It asks the app's episode reference (`TitleResolver.episode_ref()`) for the absolute number an IMDb request for that episode gets, and compares it with the Kitsu number. Per series it prints the episodes, the mapped ones, equal, off by +1, by −1 and by more, the mapped episodes Cinemeta lacks or lists in season 0, the unmapped ones, the regular Cinemeta entries no Kitsu episode maps to, and the first episode that is off. Names and counts only.
- The run of 2026-10-11: nine of the eleven series number every listed episode as Kitsu does. Anime A is one low from S16E12 (Kitsu 591) on, 590 episodes, because IMDb lists no episode for Kitsu 590, the crossover special of 2013. Anime D is one high from S2E1 and two high from S4E1, 175 of 224 episodes, because Cinemeta lists S2E0 and S4E0 among the regular seasons and the position counts them. The table and the limits are in `docs/plans/series-episodes.md` → Row 72. There is no fix yet: the numbers size the maintainer's options.

### Changed: aniworld.cc and serienstream.cx Join the Domains
- aniworld's `_domains` are aniworld.to and aniworld.cc, and sto's are serienstream.to, serienstream.cx and its address (row 74, the maintainer's yes to row 69's finding). Both new hosts are on their sites' official lists, serve the site with its marker, and are named neither dead nor scam by JDownloader's SerienStreamTo.

### Added: The Challenge Counter Tells Solved From Unsolved
- The plugin record counts `challenges_unsolved` per plugin and UTC day (row 70): a search with a challenge the plugin did not get past. That covers a browser fallback that returned no page or failed, an answer no browser tried, a Playwright solve that gave up, and a challenge still open when the search ended. The bases mark each challenge with `mark_challenge()` and settle it with `settle_challenge(solved=...)`; the runner counts once per search.
- `GET /api/v1/stats/plugins` carries the counter in its days, and an older day without it reads 0. The digest's plugin table shows `challenges/unsolved` and a line with N20's rule over the record's last 7 days: a solver sidecar trial only for a plugin whose unsolved challenges exceed 5 % of its searches.

### Added: Plugins Read Their Sites' Official Domain Lists
- A plugin can name its site's official list of addresses (`domain_list_url`) and a marker, the CSS selector of an element only the site itself shows (`domain_marker`). When no `_domains` entry answers, `HttpxPluginBase`'s domain check reads the list through the shared client and takes the first listed host beyond `_domains` that shows the marker: up to 20 hosts, no IP literals, cached 24 h (`<plugin>:domain_list:v1`), a failed read cached 1 h with one warning. The host is logged as `plugin_domain_list_host`, and the digest names it under Plugins.
- filmo (`filmo.domains`), aniworld (`aniworld.domains`) and sto (`serien.domains`) read their lists. The survey of all 42 sites is in `docs/plans/plugin-domains.md` → Official domain lists. aniworld.cc and serienstream.cx serve their sites and are not in `_domains`; whether they go in is the maintainer's decision.
- Behaviour change: filmo and aniworld have one domain each, and their domain check used to be skipped. With a list they run it, so an unreachable site now ends in `PluginUnreachableError`, as it does for plugins with several domains.

### Added: A Probe Times a Browser Capture in the Container
- `scripts/probes/capture_timing.py URL [--hoster filemoon] [--runs 2] [--timeout S]` resolves a hoster page with the app's resolver for a hoster that captures in the stealth browser (Filemoon, SuperVideo, DoodStream, Vixeo, the XFS hosters). Per run it prints the page loads (the path's first segment, when each started, how long it took), the clicks on the player, when the stream was captured (its CDN's domain) and the resolver's whole time, then production's two bounds (`http_timeout_resolve_seconds`, `stremio.probe_stealth_timeout_seconds`). The registry's bound is left out, so a slow capture shows its whole time. For row 65's trial: production's Filemoon capture ran into its 10 s bound, and the production host's capture time decides between a capture budget in code and the YAML values.
- The probe writes nothing the app reads. It uses a Chromium of its own on the app's display with a stealth pool without a clearance store, and no cache, breaker or resolver cache. Its temporary files go to a directory of its own, removed at exit. Before the launch it reads the container's available memory, the free `/dev/shm` and whether the app's Chromium keeps out of `/dev/shm` (`--disable-dev-shm-usage`, one of Patchright's own switches), and it launches nothing below 1 GiB of memory or 32 MiB of shared memory. A run ends after 90 s at the latest, a watchdog ends the probe after its runs' share plus a minute, and at exit it kills every process it started, by parent PID and never by name.
- In the dev container (2026-10-11, filmo's Byse link for Movie F): the watch page `/d/` loaded in 0.2 s, one click at 3.7 s, the stream at 4.8 s; the second run captured it after 1.3 s without a click.

### Added: The Series Probe Compares sto's and aniworld's Files
- With `--plugins sto,aniworld`, `scripts/probes/series_episodes.py` compares the links of each request's kept results (row 71). It follows aniworld's `/redirect/<n>` links as the registry does at play time, three at a time, reduces each link to its hoster and file id, and prints per hoster the files both sites list, sto alone and aniworld alone. It prints counts only, never links.
- Finding (`docs/plans/series-episodes.md` → Row 71): aniworld places the 4 of 10 anime episodes sto cannot place, and where both place one, sto adds no hoster. N21 (a German episode title from TMDB) is shelved.

### Changed: The HLS Read-Ahead Keeps Three Segments Ahead
- The HLS proxy fetches the three segments after the one the player asks for, not two (`_AHEAD` in `infrastructure/stremio/hls_proxy.py`). The depth follows N1's rule: the connections in flight carry 1.5 times the bitrate. Row 68 measured from the production host on 2026-10-11 (`docs/plans/pi-performance.md` → Read-ahead depth): one FireStream connection carried 0.9 Mbit/s for a 1.6 Mbit/s title (0.55 times real time), three in flight 3.2 Mbit/s, four 4.8, five 5.4. The maintainer's 1080p FireStream playback in Stremio Web got 0.44 times real time per connection, which needs four connections; with three (about 1.3 times real time) its picture stalled now and then.
- The bounds stay: 8 playbacks, 16 MiB a segment, a playback dropped after 60 s idle, a 429 pauses a host for 10 minutes. The worst case grows from 256 to 384 MiB.
- From the production host the sum flattens near 5 Mbit/s (nine connections carried 4.9; the VPN or the CDN), so a stream above about 3.3 Mbit/s reaches 1.5 times real time at no depth. FireStream lists no lower variants for hls.js to step down to.
- `scripts/probes/hls_throughput.py --in-flight 3,4,5` replaces the read-ahead run with one run per count of segments in flight: whether a fourth and a fifth connection still add throughput from the production host. Each run's row shows its multiple of real time (N1's rule asks 1.5) and its failed requests by status or error (`3 failed (429 ×2, ReadTimeout ×1)`). The variant line lists the master's variants or says that the link is a media playlist, with no lower variant to step down to. A 429 ends the runs, since the production host's address is its playbacks' too. The probe's read-ahead runs follow the proxy's depth (three).
- In the dev container FireStream's CDN answered every segment of filmpalast's link with 502 (the eleventh round saw the same), so the measurement ran from the production host. The runs themselves were checked there on Filemoon's CDN.

### Fixed: Byse Videos Restricted to Their Owner's Sites Play Through the Watch Page
- The Filemoon resolver asks Byse's details API before its browser starts and gave up on a 403 `embedding from this domain is not allowed` (`filemoon_unavailable`): the owner of such a video allows its player only on authorised sites, and the embed page `/e/<id>` shows "Embedding blocked on this site". The hoster's own watch page `/d/<id>` plays the video in a player frame of a second host, so the resolver now captures that page instead (`filemoon_embedding_blocked`). A 404 stays gone, and the embed page stays first where embedding is allowed (one frame less).
- `StealthPool.capture_media(url, player=...)` clicks the centre of the named element (a CSS selector) instead of the page centre. The watch page shows its player in a frame below a header: the page centre lands in the frame above its play button (no stream after 18.7 s), the frame's centre starts the player and its manifest request about 1.8 s after the click. Without `player`, and while the element is not laid out, the page centre stays the target (the embed pages of the other capturing resolvers).
- Result (row 65, 2026-10-11, `docs/plans/filmo-plugin.md` → After): filmo's Byse link for Movie F resolves through the registry in the dev container in 5.6 s and plays (master 200, a 1280x720 variant, MPEG-TS segments). In production kinoking's Byse links meet the same 403, so other plugins gain as well.

### Fixed: The Build Identity Snippet Keeps .git Out of the Image
- The snippet in `docs/features/configuration.md` → Build Identity, for a Dockerfile that fetches the source with BuildKit's git `ADD` (the production host's build), kept the git directory (`--keep-git-dir=true`) for `docker/build_info.py` but left the runtime stage's `COPY --from=src / ./` in place, so the image would have carried `.git`. The `buildinfo` stage now writes `build_info.json` into the source and drops `.git`, and the runtime stage copies the source from there.

### Added: The Codecs of the Round's Streams
- `scripts/stremio_playcheck.py`'s verdict names a stream's codecs as `video/audio` (`OK mp4 2.10 GB h264/ac-3, seek 206`, `OK hls hevc/ec-3, 400 segments: mpegts, mpegts`; `?` for the one not read, `codecs unread` for neither), for row 59's hypothesis 2: a player without HEVC or AC-3/E-AC-3 decoding, a browser among them, refuses such a stream with "Format/Quelldatei wird nicht unterstützt". A file's codecs come from its MP4 `moov` (from the start of a faststart file in one read, else one read of its last 8 MiB; a `moov` beyond that stays unread) or an MPEG-TS head's PMT; an HLS stream's from the master's `CODECS` of the variant the check plays, else the `EXT-X-MAP` init segment of fMP4, else the first segment's PMT. Matroska is counted as unread. The reading lives in `scripts/media_codecs.py` (stdlib `struct` only); the codec read has 10 s of the check's 30 s and leaves the codecs unread when slow, never the stream failed. `scripts/stremio_round.py` adds a table of the streams per hoster and codec pair under the round table.

### Fixed: The Play Check Judges a Proxied File as a File
- `scripts/stremio_playcheck.py` took every URL with `/stremio/proxy/` for HLS, so the address-bound files the proxy passes through (`/stremio/proxy/<id>/file`: DoodStream, MixDrop, Vinovo, FSST) failed as `FAIL master 200`, 21 of the eleventh round's 22 failures, and the tenth round's hang came from the same branch. `stream_kind()` judges by the URL's path: one ending in `/file` is a file (the head and a seek), `.m3u8`, `master.txt` and the proxy's other paths are HLS. The `200 instead of 206` finding counts for a file's head and seek, and for HLS segments only when the playlist has `EXT-X-BYTERANGE`: a player asks for whole segments otherwise, so a 200 there is normal. `scripts/stremio_round.py` counts the verdicts as before, so its `Findings` column follows.

### Added: The filmo Plugin
- `plugins/filmo.py` (filmo.to, `HttpxPluginBase`, `provides = "stream"`, German and English, films only: a series request answers nothing) searches `/search?q=` (the top cards and the poster grid, cut to the relevant hits), reads each film's page (title, year, genres, per language row the hoster chips with their quality) and resolves every chip in the search's session: `POST /n` with the chip's payload, the page's CSRF token and the `XSRF-TOKEN` cookie answers a one-time token, `GET /n/<token>` the hoster (VOE's redirect, Byse's interstitial link). Results carry the hoster URLs, German rows first and a file named by both rows once, never a `/n/` token; a refused token call fetches the page once more for a new token and payloads, then the chip is skipped with a warning. `scripts/capture_pages.py` scrubs the site's `data-p` payloads and `/n/` tokens from fixtures. Live on 2026-10-11: the search for Movie F in 0.7 s with VOE (German, English) and Byse; a Stremio request on the dev server listed both VOE streams, Byse's link failed in the Filemoon resolver (`embedding from this domain is not allowed for this video`). Site analysis and proof: `docs/plans/filmo-plugin.md`.

### Added: Which CDNs Need the Playback Headers
- `scripts/probes/header_binding.py` asks the CDN of every stored resolution for its first 2 KiB from the dev container in up to four ways: the playback check's headers (the stored `Referer` and `Origin` over the browser User-Agent, which the file pass-through sends too), a bare player (a Firefox User-Agent and nothing else), the stored headers with the player's User-Agent and the check's User-Agent without them (a fresh client per request, so no cookie carries over). It names per stream and per hoster what the bare player lacks (`free`, `user-agent`, `headers`, `user-agent + headers`, `dead here`); the hosters bound on the `play` route, where the player fetches the redirect's target itself, are the candidates for the second "Format/Quelldatei wird nicht unterstützt" report (row 59 of the archived backlog). Sources: the live suite's hoster links resolved here with the app's registry (header binding only) and production's links of the last hour read through Portainer (resolved from the production host's address, fetched as a player on the LAN fetches them). When the check gets a playlist, the probe also reads the media playlist (a master's first variant) the way the HLS proxy reads it and names whether it addresses its segments or its init section by byte range (`EXT-X-BYTERANGE`, `EXT-X-MAP` with `BYTERANGE`): the proxy's segment route asks the CDN without the player's `Range` header and answers 200, so a byte-range segment would arrive as the whole file. A link without a video URL (a dev link that did not resolve) takes no route in the tables. It prints no URL, header value or stream id.
- Result (row 59, 2026-10-11, `docs/plans/header-bound-hosters.md`): no hoster needs a change. Production's 90 stored links of the eleventh round all took the proxy or the file route. In the dev container the one hoster bound on the `play` route is VEEV, whose CDN binds the User-Agent alone and which `/play` already resolves per player; the file route's bindings are what the pass-through sends, and 39 media playlists of 10 hosters use no byte ranges. The next hypotheses for the report are the device log, the player's codecs and the HLS variant.

### Added: The Round Names the Failing Hosters
- `scripts/stremio_round.py` summed the play checks into `playable n of m`, so a round could not say which streams a player would refuse (row 58's proof: 9 of 20 playable, no verdict). With play checks it prints under each title's line the failing streams as `hoster: verdict` (the hoster's name from the stream's description, never a URL; the verdict's first 60 characters) and the number of Range requests the check saw answered with 200 instead of 206; the round table gets a `Findings` column with the failing hosters and that count (`DOOD, FSST; 1× 200 instead of 206`), the median and total row unchanged. The eleventh round after the next deploy is its first use.

### Added: The Answer Budget as Its Own Setting
- `stremio.answer_budget_seconds` (`SCAVENGARR_STREMIO_ANSWER_BUDGET_SECONDS`) is the Stremio request's answer budget: the time after the request's start (a stale entry's refresh: after its own) at which the request stops waiting for the plugin search and answers with the results known by then; the plugins run on to `plugin_timeout_seconds`, the entry written at the budget names them `missing`, their results reach the cache and resolve in the background, and the response says so (`X-Search-Complete`). Unset (the default) the budget is the plugin timeout as before, so nothing changes until the maintainer sets it; at least 1 s; a value above the plugin timeout counts as the plugin timeout. Evidence: in the tenth round three series answered at the 30 s budget with 1 to 2 streams while the fast plugins were long done (`docs/plans/stremio-latency.md`); the production value is the maintainer's call from the dev-server numbers there. `TitleSearch` takes `answer_budget_s` (`answer_budget_s()` in `application/stremio/title_search.py` derives it from the two settings); the plugin search runner is untouched.

### Fixed: The Play Check Reads Only the Bytes It Judges
- `scripts/stremio_playcheck.py` buffered every answer whole (`client.get`), so the tenth round of 2026-10-10 hung for 2 h 16 min when `/proxy/<id>/file` answered the check's `Range: bytes=0-2047` request with 200 and the whole file (79.6 MB received on one connection when the run was killed). Every answer is streamed now and read only up to the bytes the judgement needs (a playlist up to 1 MiB, media bytes 2 KiB, a seek only its status), then closed; one deadline of 30 s covers the whole check of a stream, headers and bodies of all its requests, and ends it with `FAIL timeout after 30 s`. A Range request answered with 200 is a finding the verdict shows: `head 200 instead of 206` or `seek 200 instead of 206` for a file (the seek fails as before), `n of m segments 200 instead of 206` for HLS. `scripts/stremio_round.py` keeps its per-request HTTP timeout for the client (`_HTTP_TIMEOUT`); the check's deadline lives in the play check. Open for the proxy's owner: whether `/proxy/<id>/file` should turn a CDN's 200 into a 206 for a satisfiable range (a player that asked for a range and gets 200 starts from byte 0).

### Added: The Post-Deploy Check as One Command
- `scripts/prodctl.py check --base <public addon URL> [--insecure]` runs the checks of a deploy and prints one table with pass, warn or fail per check, exit code 1 on a failure: the container is running and healthy, the newest `app_startup_complete` record is younger than the container's start and names the version, `config_unknown_keys` of that start (a warning), `hoster_state_restored` and `plugin_history_restored` of that start, the three anime ids `series/<Anime A>:5:2`, `series/kitsu:<Anime A>:1089` and `series/<Anime H>:2:1` answer streams of `S05E02`, `S22E04` and `S02E01` with their request logged, and `movie/<Movie F>` answers a stream within the deadline (`--deadline`, default 60 s). The judgement lives in `scripts/deploy_check.py` and is tested from fixture records and answers; the command's only writes to production are the four stream requests, and its output passes `portainer.mask()` (`docs/features/observability.md` → Production Diagnostics). `Portainer.inspect()` (`scripts/portainer.py`) reads the container's start time.

### Added: Playback Under Search Load Measurement
- `scripts/playback_under_load.py` plays a stored HLS stream through the proxy at the playback pace from a machine on the server's network (per segment the time to the headers and to the last byte, stalls), requests stream ids during the playback (the searches' wall time, streams and cache headers), samples the container's CPU through Portainer and reads the `/metrics` deltas of the run (the plugin searches, the proxy's segment stage, the read-ahead, the event-loop lag): the evidence for row 56 of the archived backlog (N12, playback-aware scheduling), method and numbers in `docs/plans/pi-performance.md` → "Playback under search load". `scripts/prodctl.py` shares its CPU reading (`cpu_cores`) and its Portainer client (`portainer_client`) with it. Measured on production on 2026-10-10 (four runs, two of them loaded): a clean search (a cache miss, 12 plugin searches) left the segments as fast as idle, and a burst of 54 plugin searches at 3.1 cores peak cost about a third of a second at p90 on 8-second segments without a stall, so the search runner keeps its concurrency and N12's playback signal is not built.

### Changed: An Unreachable Site's Rechecks Back Off
- The health monitor checked an unreachable site every 5 minutes until it answered, so a site that stays dead cost 288 checks a day against 48 for a live one (production 2026-10-09: 381 against 66 in two days). The recheck comes 5 minutes after the check that found the site down, then after 10, 20 and so on up to `stremio.plugin_health_interval_seconds`: a dead site costs one check per interval, a site that comes back is reachable again within one pause, and an answer resets the pause. A search's own mark starts the same schedule.

### Fixed: cineby Reports Its Search Host Unreachable
- cineby's searches run on the TMDB proxy `db.videasy.net`, and that name no longer exists (NXDOMAIN at the public resolvers; the dev container's search domain turns it into the router's address, which the request guard refuses). The plugin never checked reachability (`search()` did not call `_verify_domain()`), so every search since 2026-10-07 logged `cineby_fetch_error` and answered nothing, as if the site had no results, and the plugin record counted searches, never an unreachable mark. The API host is the plugin's domain now (`_domains`, `base_url`): `search()` sends `HEAD` to it once per process, an answer of any status is reachable, a transport failure (the name does not resolve, no connection, a non-public address, a timeout) raises `PluginUnreachableError` (`cineby_api_unreachable`), checked again by the next search, and the health monitor probes the same host. The result links name the site's current domain `cineby.at` (`cineby.gd` and `cineby.app` redirect there; its name servers refuse queries on 2026-10-10, and the six other former mirrors are parked or landing pages, so they left the list). The request guard stays as it is. In production the plugin is disabled by config (`plugin_disabled_by_config`), so no production search ever ran on it, and the container's resolver does not know the API host either; the fix changes production only once the plugin is enabled there. Reading: `docs/plans/plugin-domains.md` → cineby; row 48 of the archived backlog.

### Removed: Six Settings That Were Never Read
- `stremio.preferred_language`, `stremio.stremio_deadline_ms`, `stremio.max_items_total`, `stremio.max_items_per_plugin` and the model's flat `cache_dir` and `cache_ttl_seconds` attributes (duplicates of `cache.directory` and `cache.ttl_seconds`) are gone from the config model, the example YAML and the docs. A config that still sets one starts as before, and the startup line `config_unknown_keys` names the nested keys; a top-level `cache_dir` or `cache_ttl_seconds` and the `SCAVENGARR_CACHE_DIR` and `SCAVENGARR_CACHE_TTL_SECONDS` variables keep working as flat aliases of `cache.dir` and `cache.ttl_seconds`. The validation `ttl_seconds >= 0` moved to the `cache` section; the guard test's list of declared-unused settings is empty. Replacements: the ranking's language preference is `stremio.language_scores`, the request budget `stremio.stream_deadline_seconds` (`docs/features/configuration.md`, Removed settings).

### Fixed: The Digest's Unreachable Share Stays Under 100 %
- The search runner's unreachable marks (a Stremio search whose domain check found no domain) went into the record's `unreachable` counter next to the health monitor's, without a `checks` count, so a dead site read over 100 % (movie4k 375 of 372 checks in 24 h). They have their own counter now, `unreachable_searches` (`GET /api/v1/stats/plugins`); `unreachable` and `unreachable_share` are the health monitor's checks alone. The digest's Plugins table shows both in one cell (`checks/searches`) and names the plugins whose marks still exceed their checks: the days recorded before this change hold the searches' marks in `unreachable` too, until they leave the window.

### Added: upns and rpmplay Resolvers for moflix's Mirrors
- moflix's `moflix.upns.xyz` and `moflix.rpmplay.xyz` links (UPN Share and RPM Share, one vidstack player family with the video id in the URL fragment) had no resolver (`hoster_without_resolver` in every round since step 40; idea N15, row 47 of the archived backlog). `UpnsResolver` (`hoster_resolvers/upns.py`, one instance per name, so the two mirrors stay two hosters) asks the player's own API the way the player does, `GET /api/v1/video?id=<id>&w=1280&h=720&r=` with the player host as `Referer`, decrypts the hex answer (AES-128-CBC, the player's fixed key and IV) and returns the JSON's `source` as the HLS master with `Origin` and `Referer` of the player host, after the CDN verification; 404 `Video not found or deleted` is offline, 429 `Rate limit exceeded` (bursts) not resolved. The player refuses headless browsers, so there is no browser capture. The site analysis found every moflix link on the two hosters deleted (28 of 28 over the 19 round titles, uploads from 2023 to 2026-05), so the resolver turns them from `hoster_without_resolver` into `offline` today and the success path is proven against the player's script and three public implementations of the same flow, not live (`docs/plans/plugin-domains.md` → upns and rpmplay; `docs/features/hoster-resolvers.md`). The live suite's dead case alters a fragment id too (`dead_url()` in `tests/live/test_resolver_live.py`).

### Fixed: Two Settings Were Loaded But Never Read
- `playwright.timeout_ms` (default 30 s) is the Playwright plugins' page timeout now: `PlaywrightPluginBase.set_page_timeout()` (composition) sets it as the default timeout and default navigation timeout of every browser context the base creates, so every `page.goto` and action without an explicit timeout honours it, and `_fetch_page_html()` navigates with it unless the caller passes one. `stremio.probe_stealth_timeout_seconds` (default 15 s) reached the stealth pool as `timeout_ms` but nothing read it; it is the timeout of the resolvers' stream capture now (`StealthPool.capture_media()` without a caller's timeout; `capture_stream()` of `hoster_resolvers/_browser.py` dropped its own 15 s constant). The httpx plugins' Cloudflare fallback keeps its own 30 s budget per page, the Cloudflare wait its 30 s.
- Guard: `tests/unit/infrastructure/test_config_settings_read.py` fails for a setting of the config model that no module in `src/` outside the config package reads as an attribute, unless its description says it is unused; the six declared ones (`stremio.preferred_language`, `stremio.stremio_deadline_ms`, `stremio.max_items_total`, `stremio.max_items_per_plugin`, the flat `cache_dir` and `cache_ttl_seconds` duplicates of the `cache` section) are listed in the test and in `docs/features/configuration.md` as removal candidates.

### Fixed: The CDN Verification Rejects HTML Answers
- `verify_video_url()` (`hoster_resolvers/_verify.py`; the XFS video path, VOE, Streamtape) counted any `200`/`206` as reachable, so a dead file that the CDN serves as an error page with 200 (supervideo's and mixdrop's CDNs, the finding of steps 40 and 42; Stremio reports "Format/Quelldatei wird nicht unterstützt" for such a link, the user's second report) passed to the playback check or, with `stremio.verify_streams` off, to Stremio. An answer typed `text/html` is dead now, a CDN that does not allow HEAD (405) is asked for the first bytes with a Range GET, which must not be HTML either, and the playback check shares the rule and the fetch (`_Answer`, `_first_bytes`); the registry caches the dead link for 15 min as before. The log lines name the CDN's domain, never the URL (`<hoster>_video_not_media`). The resolver live suite before and after: `docs/plans/plugin-domains.md` → HTML answers fail the CDN verification.

### Added: The Plugin Record Counts Challenges
- `PluginHistory` has a `challenges` counter next to the timeouts and unreachable marks: a search in which a page of the plugin's site showed a challenge, counted once per search however many pages did. The search runner sets a `ChallengeFlag` (`domain/ports/plugin_history.py`, a context variable) for each plugin search and counts it when the search ends, with a timeout or a cancellation too; the httpx base marks it where `_fetch_text` or `_safe_fetch` sees a challenge (the host's browser memo included), the Playwright base where a navigation lands on a challenge page. `GET /api/v1/stats/plugins` reports it with the other counters, and `prodctl.py digest` shows a `Challenges` column and names the challenged plugins of the window below the table (or says that no search met one); the digest's count of stream requests per id scheme (`tt`, `kitsu`, `tmdb`) existed already. The decision about a solver sidecar (`docs/plans/cloudflare-solvers.md`, gap (d)) stands on these numbers instead of log lines counted by hand (`docs/features/observability.md` → Plugin Record).

### Fixed: The Search Cache Key Carries the Episode's Placement
- `search_cache_key` (`application/stremio/search_cache.py`) named the title, season and episode only, so a Kitsu request (Kitsu number 1089) and the IMDb request for the same season and episode (list position 1088) shared one entry and one running search: in the deploy check of 2026-10-10 `kitsu:<Anime A>:1089` joined the search of `<Anime A>:22:4` 0.7 s after it and inherited its placement, one episode off on s.to. The key takes the request's `EpisodeRef` and appends its absolute number (`-` without one), prefix `stremio:search:v3` (entries from before are not answered); the use case computes it once the reference exists, and the single-flight join of `title_search.py` keys by it, so the two requests search apart while two requests with the same placement still join (`docs/features/stremio-addon.md` → Search cache).

### Fixed: Step 21 Follow-ups
- The empty-answer log lines `stremio_all_filtered` (results, none matching the title) and `stremio_search_no_results` carry `dropped`, the results the episode filter removed in the request's searches, so an empty series answer says whether the plugins found nothing or the filter dropped everything (`use_cases/stremio_stream.py`). AGENTS.md §3 names the `dropped` counter of the plugin record. Row 30 of the archived backlog.
- `PlaywrightPluginBase._verify_domain()` applies the httpx base's rule to a domain that only answers a plain error page (4xx without a challenge): without a working domain it serves unpinned for 300 s and is checked again (`{name}_domain_answers`) instead of counting as unreachable, while a challenge page the browser did not solve still does (the browser is the plugin's only way past it); `docs/features/python-plugins.md` described that rule for both bases already. The recheck time is `ANSWERING_DOMAIN_RECHECK_S` of `infrastructure/plugins/constants.py` for both ([Mirror URL Fallback](docs/features/mirror-url-fallback.md)).
- The episode filter reads the link labels of a result whose title names the episode too, and reads episode words (`Folge 5`, `Episode 5`, `Ep. 5`, `E05`) besides `1x5` and `S01E05`: the links of other episodes go, and a result whose labelled links all name other episodes is dropped. A page titled after the episode but linking the whole season passed with every link before, the remaining leak class of the step 21 review (`infrastructure/stremio/episode_filter.py`). The series audit after the change: `docs/plans/series-episodes.md`.

### Added: HLS Proxy Read-Ahead
- The HLS proxy fetches the two segments after the one the player asks for into memory and answers them from there (`SegmentReadAhead` in `infrastructure/stremio/hls_proxy.py`; idea N1, step 19 of the archived backlog). A player loads the segments one after another over one connection, and a CDN that throttles each connection starved it: FireStream's 2.8 Mbit/s title played at 1.8 Mbit/s from the production host and stuttered; with two segments ahead the throughput probe measured 7.3 (`scripts/probes/hls_throughput.py`), so this variant was chosen over parallel byte ranges (2.9). When the proxy rewrites a media playlist it remembers the segments' CDN URLs in order; a segment request starts the fetches of the next two under the CDN semaphore, a request for a segment fetched ahead is answered from memory (a fetch in flight is awaited), and the segments the player passed or jumped away from are dropped. Bounds: two segments ahead per playback, each at most 16 MiB (a larger one is left to the player's own request: a declared length costs the headers only, a body without one that grows past the cap is cut and ends the playback's read-ahead), at most 8 playbacks (the least recently used goes), a playback dropped 60 s after its last request, and no fetches ahead for a CDN host for 10 minutes after it answered one with 429 (`hls_readahead_throttled`). `HEAD` requests touch nothing. Metrics `scavengarr_hls_readahead_seconds` and `scavengarr_hls_readahead_total{outcome}` (`ok`, `failed`, `too_large`, `throttled`, `cut` for the fetches; `hit`, `miss`, `dropped` for the answers); a stage without labels of its own now records its duration. The query-string helper of the proxy route moved to the module as `resolve_query_string`. The FireStream stutter (KNOWN_ISSUES) is to be checked on the production host after the deploy.

### Fixed: One Browser User-Agent for the Checks and the Resolvers
- The domain check (`HttpxPluginBase._verify_domain`, `HEAD /`), the health prober (`infrastructure/scoring/health_prober.py`) and the link validator (`infrastructure/validation/http_link_validator.py`, HEAD and the GET fallback) sent the shared client's bot User-Agent (`Scavengarr/<version> (+repo)`), which a site behind Cloudflare challenges or blocks: the check counted the site as down or the link as dead while the plugin's own requests, with a browser's User-Agent, passed. All three send `DEFAULT_USER_AGENT` of `infrastructure/plugins/constants.py` now (the domain check the plugin's `_user_agent`, which defaults to it), with a unit test on each caller.
- The resolvers filemoon, the 25 XFS hosters and doodstream sent a truncated User-Agent without the Chrome token (`Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36`), the 10 generic DDL hosters, rapidgator, ddownload, gofile, mediafire and streamtape none of their own (the shared client's bot UA). All send `DEFAULT_USER_AGENT`. Proof: the live resolver cases of step 40 before and after the change, in `docs/plans/plugin-domains.md` → One browser User-Agent.

### Fixed: Cloudflare Challenges Are Not Retried, and `_safe_fetch` Sees Them
- `RetryTransport` (`infrastructure/common/retry_transport.py`) retried a 503 that was a Cloudflare challenge three times and halved the domain's rate each time, as if the origin were overloaded. A 403 or 503 whose answer is a challenge (`cf-mitigated: challenge`, or an HTML body `detect_challenge` recognises; the body is read and stays readable) is now returned at once: neither retried nor fed back to the rate limiter as a throttle or a success (`http_challenge` debug line). A plain 503 is still retried, a 429 still waits for `Retry-After`.
- `HttpxPluginBase._safe_fetch()` logged a challenge as `<plugin>_http_error` like any error page and left the browser memo alone. It now runs the detection of `_fetch_text()` on an error answer, logs `<plugin>_challenge` with the class and the host, puts the host into the browser memo (the plugin's `_fetch_text()` calls go straight to the browser) and returns `None`. The browser fallback itself stays with `_fetch_text()`: a plugin behind a challenge fetches its pages with it (`docs/features/python-plugins.md`). jjs (`plugins/jjs.py`, behind Cloudflare) fetched its search and detail pages with `_safe_fetch()` and never reached the browser; it uses `_fetch_text()` now.

### Fixed: Streamtape's Token Extraction
- Streamtape's embed page carries the `get_video` parameters in three hidden elements whose HTML texts hold decoy tokens; the page's script assigns the real value to the element the player reads (`botlink`) as string pieces joined with `substring` chains, and the tokens are mixed case. The resolver (`infrastructure/hoster_resolvers/streamtape.py`) took the first HTML literal and "corrected" its token with an uppercase-and-digit pattern, which on today's tokens kept a two-character prefix: the hoster answered the request with a 200 and an error JSON, which the resolver's HEAD check accepted and the registry's playback check reported as HTML (the live suite's streamtape case of step 40). `video_params()` now evaluates the assignment to the player's element (the last one, as in the browser), with the legacy literal and the script's full-alphabet token as the fallback for older pages. Tested on the captured page (`tests/fixtures/html/streamtape/embed-decoys.html.gz`, tokens replaced by synthetic ones that keep the decoys distinct); the live cases pass.

### Fixed: The Budget Scenario's Timing Margins
- `tests/unit/application/test_resolve_flow.py` plays the one-slot budget scenario three times (a continuing search's results, the answer at the budget, a retry past it): the first plugin answers before the request's budget, the second starts after it (one slot) and ends after the budget but before its own timeout. With 0.3 and 0.2 s delays against a 0.4 s budget each edge had 0.1 s, and one CI run (the suite on every core) moved the first answer past the budget. An event-based wait cannot replace the budget edge, because a request answering at its budget while a plugin runs is the behaviour under test, so the three tests now share one set of windows (`_BUDGET`, `_FIRST_DELAY`, `_SECOND_DELAY`, `_AT_ONCE`) that leave 0.4 s or more at every edge: 0.8 s before the budget for the first plugin, 0.4 s after it and 0.4 s before its own timeout for the second, and half the budget for an answer from the cache.

### Added: Resolver Cases in the Live Suite
- The live suite of 2026-10-09 had no resolver case (`_LIVE_URLS` and `_DEAD_URLS` were empty dicts), so it could not tell a dead resolver. `tests/live/test_resolver_live.py` now reads its live cases from the untracked `.cache/live/resolver-urls.json` (`{resolver name: hoster page URL}`; the module skips without the file), one per resolver name, resolved through the registry the composition root builds (the app's lifespan, a temporary cache directory), so the XFS and DDL configs and the individual resolvers are reached alike; the dead case is the live URL with the id of its last path segment altered (the last four characters reversed, the last six when four leave it unchanged, a trailing extension kept), which the hoster parses as an id and answers not found. No URL reaches the test output. `scripts/probes/resolver_urls.py` writes the file: it searches the titles of `docs/plans/round-titles.txt` through the plugin registry the way `title_match.py` does, maps every result link to its resolver (`canonical_hoster`) and keeps the first link per resolver, printing resolver names and counts only. The first run's table: `docs/plans/plugin-domains.md` → Live resolver cases.

### Fixed: kinoking's Genres and the Anime Vocabulary
- The anime vocabulary the streaming plugins label 5070 by and the Stremio title matcher reads a result's genres with (`names_anime()` in `infrastructure/plugins/categories.py`) knows the German word: `anime`, `animation` and now `zeichentrick` (sto's own genre map has it, filmpalast's and kinoger's captured pages list the genre, the series-identity spec names the three words).
- kinoking (`plugins/kinoking.py`) unescapes the keywords meta it reads the genres from (`Sci-Fi &amp; Fantasy` was stored with the entity), labels a series by its genres (`stream_category`: 5000, or 5070 when the keywords name Animation, Anime or Zeichentrick) instead of a constant 5000, answers 5070 requests itself (`served_category` over `STREAM_CATEGORIES`) and filters the scraped results by the requested category, like kinoger. Before, an anime request got every series of the site and an anime series was 5000, which the matcher dropped by category against an animation reference (`docs/plans/title-matching.md` → Reading (7.2), Anime A). No site capture backs the Animation genre: kinoking times out and challenges from the dev container; the word is inferred from TMDB's German genre names, the vocabulary the site's keywords come from.

### Fixed: boerse Names the Dead Origin
- The live suite of 2026-10-09 reported boerse as a parser miss (`no login form` after a solved Cloudflare page). Captured through the plugin's own browser, every domain answered with Cloudflare's 522 page for an origin that is gone (boerse.am, .tw, .sx, .im), a registrar's for-sale page (boerse.ai) or no connection (boerse.kz): there was no markup to find a form in. `plugins/boerse.py` now reads the page after the Cloudflare wait and treats Cloudflare's error page (`cf-error-details`, title `… | 522: …`) as no answer (`boerse_origin_error` with the status), raises `PluginUnreachableError` like the other Playwright plugins when no domain answered (the Stremio search marks it unreachable and counts it in the plugins' record instead of a search error), and keeps the `All boerse domains failed during login` error for a page that has no form; boerse.ai left `_domains`. Fixture `tests/fixtures/html/boerse/home-522.html.gz` (`scripts/capture_pages.py` scrubs Cloudflare's Ray ID and the visitor's IP from error pages). The findings: `docs/plans/plugin-domains.md` → boerse.

### Added: Digest Counts Stream Requests per Id Scheme
- `scripts/digest.py` (`prodctl.py digest`) counts the window's stream requests per id scheme of the request path (`tt`, `kitsu`, `tmdb`) and prints them as one line under *Requests*, so the maintainer sees which catalogs the players use instead of inferring the anime catalogs' use from a grep; no new log field.

### Fixed: The Right Series and the Right Episode
- The maintainer reported Anime A streams mixing the 1999 anime, the 2023 live-action series and the 2027 remake, and anime requests playing the wrong episode (2026-10-09). The reference a request is matched against knew only a title, a year and alternative titles, and the anime sites' pages were built from IMDb's season numbers, which aniworld does not count in. OpenSpec `series-identity`, in steps:
- `CinemetaClient` (`infrastructure/stremio/cinemeta.py`) reads the request's Cinemeta meta (`v3-cinemeta.strem.io/meta/<type>/<imdb>.json`, the catalog the player reads the ids from; 5 s timeout) and reduces it to `SeriesMeta` (name, start year, genres) with `EpisodeMeta` per listed episode (IMDb's season and episode, English name, release date), cached 7 days (`cinemeta:v1:<type>:<imdb>`); an id the catalog does not know is remembered for a day; a failure logs `cinemeta_failed` (reason, no URL) and answers nothing. `TitleMatchInfo` gains `imdb_id` and `animation`, and `EpisodeRef` names the episode a request means (season, episode, English title, release date, absolute number).
- The title resolution asks the catalog once per request (`SeriesMetaPort`, wired to the Cinemeta client; the `series_meta` phase records `found`, `not_found` or `error`, and an error leaves the kind unknown while the request goes on) and gives every language's reference its identity: `imdb_id` and whether the genres name animation. `TitleResolver.episode_ref` builds the episode reference from the record: the entry's English title and release date, and the absolute number, a `kitsu:` request's episode number, else the entry's position among the regular seasons (Anime A S5E2 is 62); an episode the list lacks gets no reference unless a `kitsu:` number names it, so the plugins answer it as today. The setting `stremio.title_year_penalty` is removed (the year decides in the next step instead of costing 0.3); a YAML that still sets it loads, the key reported with `config_unknown_keys`.
- The matcher decides by identity before any text is compared (`score_title` returns `TitleScore(score, reason)`; `score_title_match` stays the score alone): a result whose metadata names an IMDb id (`imdb` or `imdb_id`, `tt` plus digits, the zeros ignored) is kept at 1.2 or dropped by the id alone; with the reference's kind known, a result whose kind contradicts it is dropped: an anime label (5070) means animation, a series label (5000) with genres of its own means what the genres say (`names_anime`, the words the plugins label 5070 by: kinoking stores every series as 5000 with the page's genres, so its Anime A anime page went by category for the anime; the title probe of 2026-10-09 in `docs/plans/title-matching.md`); a known result year outside the tolerance (3 years for a series, 1 for a movie) drops the result instead of costing 0.3 (an exact title with the wrong year scored exactly the threshold and was kept), the year read from the title, the release name, guessit or `metadata["year"]` (an int or a string of digits), and a year the reference title itself carries ("Movie I") counts as a word. `title_match_filtered` names the `reason` (`score`, `year`, `imdb`, `category`) and `title_match_summary` counts the drops per reason. `relevant_hits` ignores a trailing `(YYYY)` when it counts a hit's words, so "Anime A (2023)" is scraped next to "Anime A" and the year decides (s.to lists both; captured search page as a fixture). The title probe prints the reference's IMDb id and kind and each drop's rule.
- The episode reference: for a series request whose Cinemeta list places the episode, the use case builds an `EpisodeRef` (the request's season and episode, the episode's English title and air date from the list, and an absolute number: the episode's position among the regular seasons, or the Kitsu number of a `kitsu:` request when it lies within 5 of that position (a Kitsu entry that spans the series counts as the sites do, one off at times) or the list lacks the episode (a Kitsu entry of one season counts that season alone, so its number far from the position gives way to it)) and hands it through the title search and the plugin search to the plugins that declare `locates_episodes = True` only (`locates_episodes()` in `domain/plugins/base.py`; the Playwright base's `isolated_search` forwards it the same way); every other plugin is called as before the reference existed. `stremio_episode_ref` (debug) logs season, episode, absolute and whether the title is known. The search cache key carries the version `v2`, so entries from before the reference are searched anew.
- aniworld locates the episode (`locates_episodes = True`): with a reference it reads the series' season pages once into an index of rows (the site's season and episode, the German and the English title, and the absolute number a long-runner's rows show as `[Episode 062]`; `infrastructure/plugins/episode_index.py`, one module for the plugins that number episodes by seasons of their own, the plugin passes its row selectors) and keeps it 7 days under `aniworld:episodes:v1:<slug>` (`HttpxPluginBase.set_cache`, the app's cache injected by the composition root next to the HTTP client; an index missing a page the site did not answer serves the request but is not stored). The row is found by the absolute number: the rows numbered within 5 of the reference's, the best English title match of at least 0.6 among them (the number alone when there is no title to compare: the reference has none, or the row shows the number in place of a title as s.to's anime rows do), else by the exact normalised English title, else by the best title match of at least 0.85 (the titles are translations of the Japanese ones and differ in wording: "The Man Who Will Become the Pirate King" against the catalog's "The Man Who's Gonna Be King of the Pirates" scores 0.82). The hoster links come from that row's page; the result's `season` and `episode` stay the request's and `site_season`, `site_episode` and `episode_located_by` (`number`, `title`) name the page and the evidence (`aniworld_episode_located`). No row means no result for that series (`aniworld_episode_not_located` with the slug, the reference and the index size) rather than a page built from IMDb's numbers on the site's seasons; without a reference the plugin answers as before. Captured pages of Anime A (series page, staffel-2) and Anime H (series page, staffel-3) of 2026-10-09 are fixtures.
- sto locates the episode of its anime results the same way (`locates_episodes = True`, the shared module with its own row selectors: `tr.episode-row`, the number in `th.episode-number-cell`, the titles in `strong.episode-title-ger` and `span.episode-title-eng`; index `sto:episodes:v1:<slug>`): a series page whose genres label it anime (5070) is located by the reference, by the number alone since the site's anime rows show `Episode 062` in place of the English title, and the result's title carries the request's `S05E02` with the row's German title while `site_season`, `site_episode` and `episode_located_by` name the page (`sto_episode_located`, `sto_episode_not_located`); every other series (5000, 5080) keeps the request's numbers as before, and so does an anime without a reference. The captured s.to season pages of Anime A (16 rows numbered 62 to 77) and Series G (7 rows with English titles) are the fixtures (task 6.1 in `docs/plans/series-episodes.md`). fireani's step waits for the site (dead since 2026-10-08).

- `HttpxPluginBase.isolated_search`, the search runner's entry, takes the reference like the Playwright base's and hands it to `search()` as a keyword; before, every request with a reference to an httpx plugin that locates episodes failed with a `TypeError` (the first run of the probe below found it; never deployed).
- `scripts/probes/series_episodes.py` translates a `series/kitsu:<id>:<episode>` id like the use case, builds the episode reference and hands it to the locating plugins, and lists the references and the placements (`located` column); it prints hosts and titles, no URLs. Its run of 2026-10-09 (Anime A S1E1, S5E2, S22E4, Anime H S2E1, S4E1 and kitsu:<Anime A> episode 1089 against aniworld and sto; `docs/plans/series-episodes.md`) located 11 of 12 answers, all kept and right: s.to's number-only placement is one episode off where Cinemeta's position is one short of the site's number (Anime A S22E4; the Kitsu number places it right on both sites), and s.to's Anime H season 3 shows the English titles of another arc, so S4E1 finds no row there while aniworld places it by the title.

### Added: Year and Genres from the Detail Pages
- cineby, einschalten, haschcon, kinoking, kinox and filmpalast store the detail page's start year as `metadata["year"]` (an int) and its genres as `metadata["genres"]` (comma-joined, as kinoger does), the fields the coming series-identity matcher reads; no extra request, no change to categories or titles. Two exceptions, with the evidence in `docs/plans/title-matching.md` → "Plugin years and genres": haschcon's year comes from its SEO title only (the post date is the upload date), filmpalast's year is stored for films only (an episode page shows its season's year: Series G S02E01 says 2025 for a series of 2023, now a fixture). megakino_to and movie4k had both through `DataApiPluginBase`.

### Fixed: Proxy Bodies Dropped by the Player and Files Cut by the CDN
- A player's disconnect mid-segment or mid-file left the proxy's body generator to the garbage collector, whose finalizer closed the byte-counting wrapper and the CDN body it wrapped in the same pass; the two closes raced and asyncio logged `Task exception was never retrieved: RuntimeError: aclose(): asynchronous generator is already running` (16 times in 48 h of production, 2026-10-07; that transfer's bytes went uncounted). The body is one generator now, counting its own bytes (`on_sent` of `stream_hls_segment` and `stream_file`), and the response closes it when the transfer ends, the disconnect included (`_BodyResponse` in the Stremio router), so the CDN's answer is released at once instead of at the next collection.
- The file proxy passed the CDN's `Content-Length` to the player even when the answer was chunked (`Transfer-Encoding`), where the header is not the body's length, and ended the player's answer wherever the CDN's body ended: uvicorn refused the short body (`RuntimeError: Response content shorter than Content-Length`, 9 times in 48 h of production, 2026-10-07) and the player saw the file end early. `Content-Length` passes only when it frames the body, the body passes undecoded with its `Content-Encoding`, and a body the CDN ends before the promised length (a transport error mid-body, or a clean end short of the `Content-Range` span or a framing `Content-Length`) is resumed once from the next byte with a `Range` request, continuing the same answer (`hls_proxy_file_resumed`); when the resume fails or ends short too, the transfer aborts (`FileCut`, one `hls_proxy_file_cut` warning) and the player asks again with a range of its own.

### Fixed: Build Identity in the Image
- Production's startup line said `commit=unknown built=unknown`: `Dockerfile.prod` only turned the build arguments into environment variables, and a build that passed none (the maintainer's own Dockerfile fetches the source with BuildKit's git `ADD`, which drops `.git`) had nothing to report. `docker/build_info.py` now records the build at image build time in `src/scavengarr/build_info.json`: the commit from `SCAVENGARR_COMMIT` or the checkout's `.git/HEAD` and refs (let through `.dockerignore`, no git binary needed), the time from `SCAVENGARR_BUILT` or the clock; `build_identity()` reads the environment first, then the file. `Dockerfile.prod` runs the script in a stage of its own (the git files stay out of the runtime image), so a plain `docker compose up -d --build` from a checkout names its commit without the environment prefix; the image workflow passes both arguments as before. A Dockerfile that fetches the source itself keeps the git directory (`ADD --keep-git-dir=true`) and runs the script the same way (`docs/features/configuration.md` → Build Identity).

### Chore: Domain Probe for fireani, kinox and kinoking
- Production's 48 h digest showed fireani 78 %, kinox 56 % and kinoking 22 % unreachable beside 91 challenge records. `scripts/probes/domains.py` from the dev container and the production host plus the record and the log (`docs/plans/plugin-domains.md`): fireani's one address accepts no connection from either side since 10-08 (dead host); kinox's nine domains answer Cloudflare's 522 from both since 10-09 (dead origin; the verification wall was the picture before); kinoking answers 200 but its domain check takes 5.1 s from the VPN exit against 0.3 s from home, so it trips the 5 s timeout (slow path, not a block); the 91 challenge records are all kinoger's known Cloudflare page. No change to plugins or domains.

### Added: Proxy for Address-Bound Direct Streams
- DoodStream, MixDrop, Vinovo and FSST bind a resolved file URL to the address that resolved it: a player on another address got `error_wrong_ip`, 403 or 410 (36 of 37 `/play/` redirects of production's cached streams failed from the dev container, seventh round of `docs/plans/stremio-latency.md`). Their resolvers declare `address_bound = True`, the registry stamps `ResolvedStream.address_bound`, the stored link keeps it, and the stream builder gives such a file `/api/v1/stremio/proxy/{stream_id}/file` with the HLS proxy stream's hints and no `proxyHeaders`; HLS keeps its playlist proxy, every other file, VEEV included, keeps `/play`. A stored link from before the change reads unbound and keeps `/play` until its hoster resolves again.
- The file route streams the current video URL with the stored headers over the player's User-Agent and `Accept-Encoding: identity`, forwards the player's `Range` and `If-Range`, passes the CDN's status with `Content-Type`, `Content-Length`, `Content-Range` and `Accept-Ranges` plus CORS, sends the body in 64 KiB pieces (none for HEAD) and reads with a 60 s timeout (Vinovo's first byte). A CDN refusal (403, 404, 410) gets one re-resolution and one retry, then 502; a 416 passes through; 400 for an HLS link or a file without the flag. Recorded on the HLS proxy's metrics as `kind="file"` (`hls_proxy_total`, `hls_proxy_bytes_total`); rate-limit exempt and query-masked like the rest of `/proxy/`. OpenSpec `proxy-direct-streams`.

### Chore: Plugin Domain Probe
- Whether megakino_to and movie4k (unreachable in step 21's audit) are dead, blocked from the VPN exit or slow was unmeasured. `scripts/probes/domains.py` checks every `_domains` entry of the named plugins from where it runs (DNS, TCP, the domain check's `HEAD`, a `GET`, the challenge kind, time; the reachability rule of `_site_answers`), with `--history` the plugins' long-term record from the app on that host. From the dev container and the production host alike: every domain resolves and connects, `HEAD` times out, `GET` gets Cloudflare's 522 after ~19.5 s, movie4k.ag accepts no connection. Verdict: dead origins behind the edge, not a blocked exit (`docs/plans/plugin-domains.md`); `_domains` unchanged.

### Fixed: megakino Season Pages of Season 2 and Later
- megakino labelled every episode `1x<n>`, so the Stremio episode filter dropped a season page of season 2 or later for its own episodes ("Anime A - 2 Staffel" for S02E01, "Series F - 5 Stafffel" for S05E01: 0 of 2 kept). The labels carry the season the page's title names ("Staffel N", "N Staffel", "N. Staffel", the site's "Stafffel"; 1 without one), an episode request's result states `season` and `episode` in its metadata, and a page of another season named "N Staffel" is skipped before its detail fetch, as "Staffel N" was. After: 2 of 2 right (`docs/plans/series-episodes.md`).

### Chore: File Throughput Probe
- Whether direct files proxied through Scavengarr (step 26) need a read-ahead was unmeasured. `scripts/probes/hls_throughput.py --file [ID]` reads the first 32 MiB of a stored direct link from the production host in one connection, then as three parallel 1 MiB ranges, and prints Mbit/s and whether the CDN honoured the ranges (`206` with the asked `Content-Range`); without an id it takes the newest stored direct link of `--hoster`. First run: MixDrop 5.4 Mbit/s in one connection, 22.2 in ranges; DoodStream 3.8 and 19.3; both honoured every range (`docs/plans/stremio-latency.md`, seventh round, production).

### Fixed: VidHide Segments Bypassed the HLS Proxy
- VidHide streams failed behind the HLS proxy with 403 on every segment (6 of 6 in the seventh round). Not the headers: from the production host every header set, none included, gets the playlists and segments (`scripts/probes/vidhide_segments.py`, `docs/plans/vidhide-segments.md`). VidHide names its CDN host in mixed case in the stream URL and in lower case in its playlists; the proxy compared hosts as written, left the absolute segment URLs alone, and the player fetched them from its own address, where the token bound to the production host's address answered 403. The manifest rewrite and the CDN URL guard now compare the host without case (`hls_proxy._same_origin`).

### Fixed: sto Stream Results with Gated Link-outs
- A stream request to sto answered with the site's own link-outs (`/r?t=`) when its link gate held them, and the serienstream resolver failed on each (`serienstream_invalid_url`, the production host's VPN address). A request for one episode, which only Stremio makes, now keeps only the links that resolved to a hoster and drops a result left without one; the info event `sto_gated_links_dropped` (plugin, dropped and kept count) marks each. Torznab searches pass no season or episode and keep the link-outs, which JDownloader can follow from its own address.

### Chore: sto Link-out Probe
- sto's episode links reached the serienstream resolver as sto's own link-outs and failed there (`serienstream_invalid_url`). `scripts/probes/sto_linkout.py` follows two link-outs of an episode the way the plugin does and prints per link the hops, the final host, gate markers and a token-free summary of the page, then the plugin's own resolution; it runs in the production container (`prodctl.py probe`) and in the dev container. Its reading in `docs/plans/sto-linkout.md`: the site gates link-outs for the production host's VPN address only, the plugin's browser pass solved the gate 3 of 6 times in the window, and the resolver loses nothing it could have resolved.

### Chore: Title Match Probe
- Why *Series C* and *Series E* answered without a stream in the seventh production round was suspected to be the queries or the title matcher. `scripts/probes/title_match.py` runs every stream plugin's search with the app's queries for one or more Stremio ids and prints per plugin the queries, the raw titles and the matcher's score and verdict. Its reading in `docs/plans/title-matching.md`: both titles find their series on three to four plugins at score 1.00 and the matcher drops only other titles; production's empty answers came from the search deadline cutting sto and kinoking (*Series C*) and from sto's link-outs failing to resolve (*Series E*).

### Fixed: Series Episodes from kinoger, aniworld, fireani and sto
- kinoger served the first episode for every series episode request: its live theme lists no episode tabs (`span[data-id]`), so the parser kept the player script's first URL, S01E01, without an episode label, and the episode filter let it through (Series F S04E01, 2026-10-07). The player script holds the episodes as one array per season (`pw.show(5,[[S1E1, …],[S2E1, …], …])`); the parser now reads them, labels each link `<season>x<episode>`, and a request keeps the links of its episode.
- aniworld and fireani fetch the requested episode themselves but said so nowhere in the result; they now set `metadata["season"]` and `metadata["episode"]` (ints) for the episode they fetched, which the stricter episode filter of `continue-cut-searches` reads. sto and serienjunkies store both as ints too (they were strings).

### Chore: Series Episode Audit
- Whether the Stremio episode filter keeps wrong episodes, and which plugins' series hits a stricter filter would lose, was unmeasured. `scripts/probes/series_episodes.py` (run in the dev container with `python -P`) starts the app's composition and runs every stream plugin's search for the round's series and Series H S01E05/S02E05, as a Stremio request would, and classifies each title-matching result: numbering (plugin metadata, else the release name), the filter's outcome (kept, narrowed, dropped), right episode, and leaks (kept results whose title or link labels name another episode). The baseline in `docs/plans/series-episodes.md`: no leaks in 76 results; aniworld, fireani and kinoger return their series hits without any episode information (aniworld and fireani do fetch the requested episode), so the stricter filter of step 21 needs their `metadata` season and episode first.

### Changed: Cut Searches Continue
- A Stremio request's plugin search was cut at `plugin_timeout_seconds` after the request start: every plugin still running was cancelled and contributed nothing, a plugin waiting for a slot was skipped, and the results of the plugins that had finished were cached as the whole answer for `search_ttl_seconds` (Series H S01E05 in production, 2026-10-07: sto cancelled at the 30 s mark, 2 results served for 30 minutes). Every plugin now gets its full `plugin_timeout_seconds` from the moment it holds a slot and runs when it gets one; the same number is the request's answer budget, which cuts no plugin: one that returns after it is `late` in the metrics, and its results reach the cache and the next request. A timeout always counts for the plugin's breaker, since the plugin had its whole time ([Stremio addon](docs/features/stremio-addon.md), `openspec/changes/continue-cut-searches/`).
- A search's cache entry was written once, at its end. It is now written at the answer budget, naming the plugins still to come as `missing` (a plugin that timed out or failed stays among them), again after each of them that finishes (its results replace its earlier ones) and at the end; the entry's age counts from the search's start, and entries stored before the field existed load as complete. The runner reports each plugin's end once, after its run for every query (`on_plugin_done`), and `merge()` replaces one plugin's results in an entry without thinning the others'.
- A request waited for its search until the stream deadline. It now stops waiting at the answer budget (`plugin_timeout_seconds` after its start), at the resolve target or when the search ends, whichever comes first, and answers with the results known by then and their streams resolved within `stream_deadline_seconds` (`stremio_resolve_complete` reason `budget`); results arriving later go to the cache. A request that finds the running search past its budget answers at once with what it found (source `cache`); one within the budget shares the wait (`joined`). An entry with plugins `missing` starts one completion search for those plugins (single-flight per key, one title at a time with the refreshes, `stremio_search_completion`) that merges per plugin, keeps the entry's age and clears `missing` at its end whatever each plugin's outcome. A stale refresh merges per plugin too: a plugin cut short keeps its earlier results in the entry instead of the refresh replacing the entry with a thinner one.
- Results arriving after an answer (the search continuing past its budget, a refresh, a completion) resolve in the background through the hoster resolver registry, one run per cache key (a search handed over while the key's run runs starts when it ends) and one title at a time under `stream_deadline_seconds` from the run's start, so the next request finds their outcomes cached; a retry past the budget takes the cached outcomes and starts the background resolution of the rest, like a cached request. The use case's `answer()` returns the streams with the search's source and whether the answer is complete (no plugin missing, no search running for the key); `stremio_search_complete` logs `source`, `complete` and `missing`, `stremio_stream_response` `source`, `complete` and `missing_count`.
- A plugin whose domain check found no reachable domain searched its primary domain anyway and ran into its timeout. `_verify_domain()` of both base classes now raises `PluginUnreachableError` (the `<name>_no_domain_reachable` warning stays, the next search checks again); the httpx check counts a domain answering with an error page or a Cloudflare challenge as reachable when none answers below 400 (the health check's rule: kinoger answers 403 `cf-mitigated: challenge` and searches through the browser fallback), for the searches of the next 300 s, then it checks again (only a domain answering below 400 stays, a transient 429, 403 or 404 at check time pins none); the Stremio search runner marks the plugin unreachable in the health monitor at once (`stremio_plugin_unreachable`, `plugin_unreachable` with `source` search), counts `unreachable` in its record and reports the telemetry outcome `unreachable`, and the recheck clears it. A Torznab search logs the error and answers without the plugin.
- The Stremio episode filter leaked other episodes: a series result without an episode number and without labelled links (a show page) passed with every link, and an episode without a season passed for any season. The filter now reads `season` and `episode` from the result's metadata (ints) before the release-name guess, passes a result without an episode number only through the links labelled with the requested episode (dropped without one), and an episode without a season for season 1 only. The runner counts the dropped results per plugin in the plugin record (`dropped`: stats route, digest), and `stremio_search_complete` carries `dropped`. Audit before and after: `docs/plans/series-episodes.md`.
- The stream response carries `X-Cache` (`MISS` for a fresh search, `HIT` for a cache entry, `STALE` for a stale one refreshed in the background, `JOINED` for a shared wait) and `X-Search-Complete` (`true` when no plugin is missing from the answer's entry and no search runs for it); `scripts/stremio_round.py` records both.

### Chore: HLS Throughput Probe
- Whether the HLS proxy should fetch ahead (read-ahead) or split segments into parallel byte ranges against a CDN's per-connection throttle (FireStream, the stutter) was a guess from one playback. `prodctl.py probe hls_throughput` measures it from the production host: the hoster's newest stored HLS link, its highest variant, four runs of ten segments (one connection, read-ahead 2, 3 byte ranges, both at once), with Mbit/s per run, the title's bitrate, whether the CDN honoured the ranges and the connections a stutter-free playback needs ([Observability](docs/features/observability.md#production-diagnostics)).

### Added: Every Setting from the Environment
- Only 30 settings had an environment variable; the `stremio` section, most of `cache` and `scoring` and the link validation keys were YAML-only, so a container could not be configured without a mounted file. Every key of a section now reads `SCAVENGARR_<SECTION>_<KEY>` (`SCAVENGARR_STREMIO_PLUGIN_TIMEOUT_SECONDS`), every top-level key `SCAVENGARR_<KEY>`; the field's type parses the value, JSON for the dict-typed settings. The older flat names stay and win over the sectioned name of the same key; when the two disagree the startup log warns (`config_env_conflict`), and a `SCAVENGARR_<SECTION>_*` name that names no key, such as a misspelled one, is reported (`config_unknown_env`).
- `config_effective` names the layer of each changed value (`sources`: `yaml`, `env`, `cli` or `defaults`).
- `docs/features/configuration.md` lists all 81 variables in a table generated from the schema (`scripts/generate_config_doc.py`, guarded by `tests/unit/infrastructure/test_config_doc.py`) and shows the default config file as `environment:` entries; a test checks that those entries give the same values as the file, and `docker-compose.yml` carries them commented.

### Added: A Stremio Round in One Command
- `scripts/stremio_round.py` measures the title set of `docs/plans/round-titles.txt` (the 17 titles of the fourth to sixth rounds and the baseline of `pi-performance.md`, 19 ids) one after another: the first answer (wall time, streams, `X-Cache` and `X-Search-Complete` when the route sends them), the cached answer right after it and the play check of the first answer's streams (`stremio_playcheck.py`'s check). It prints the round table of `docs/plans/stremio-latency.md` with a summary row (medians, totals, titles without stream), appends it to a Markdown file with `--out` and adds the container's CPU for the round with `--portainer` (`stremio_profile.py`'s reading). Against production at most once an hour.

### Added: `prodctl.py digest`
- Every production round was read from `prodctl.py metrics` and `logs` by hand, dozens of Portainer requests each. `scripts/prodctl.py digest [--since 24h] [--json]` prints one Markdown report of the window from one log request and one exec (`/metrics` and `/api/v1/stats/plugins` together): the stream requests by source with p50/p90 and streams per answer, the plugins from the long-term record, the hosters' resolutions and outcomes, the breakers not closed and their openings and skips, the five noisiest log events and the errors with their most frequent messages (`scripts/digest.py`, [Observability](docs/features/observability.md#production-diagnostics)). A breaker now logs each opening (`circuit_breaker_opened`: `name`, `reopened`, `cooldown_s`), which the report counts.

### Added: Dependabot
- `.github/dependabot.yml` checks the Poetry dependencies, GitHub Actions and the base images of `Dockerfile.prod` every Monday at 06:00 UTC; minor and patch updates of the Python packages come as one grouped PR, at most three Python PRs are open at a time, and every PR carries the label `dependencies`. CI runs on these PRs; AGENTS.md §4 holds the merge rule.

### Added: The Plugins' Long-Term Record
- Whether a plugin whose site died stays, is disabled by default or is removed was a guess from one round's numbers. `PluginHistory` (`infrastructure/plugins/history.py`) now counts per plugin and UTC day how often it was searched, how many results it gave, how often it ran into its timeout (`PluginSearchRunner`), how often its site was checked and found unreachable (`PluginHealthMonitor`), 180 days in the cache backend (`plugin_history:v1`, written every minute when it changed and at shutdown, restored at the start). `GET /api/v1/stats/plugins` reports it with each plugin's last day with a result and its unreachable share over 30, 90 and 180 days; the production digest reads it. The decision stays the maintainer's, from months of this record.

### Added: Checks in Worktrees
- A git worktree has no `.venv`, so `poetry run pre-commit`, the basedpyright hook and `poetry run pytest` ended there with `Command not found` (Poetry created an empty venv). `scripts/worktree_venv.sh` links the worktree's `.venv` to the main checkout's venv once, and the basedpyright hook runs `scripts/basedpyright.sh`, which finds that venv by itself (the active venv first, so CI's Poetry venv counts; then `.venv`; then the lookup of the LSP plugin's `langserver.sh`); both scripts are stored executable (AGENTS.md §9). pytest puts the checkout's own `src` first (`pythonpath` in `pyproject.toml`), because the linked venv's editable install points at the main checkout.

### Added: The Docs Name Paths That Exist
- `tests/unit/infrastructure/test_docs_paths.py` fails when `AGENTS.md`, `README.md`, `CONTRIBUTING.md` or a doc under `docs/features/` or `docs/architecture/` names a repository path in backticks that does not exist (plans and OpenSpec changes name future files and are not checked). Paths relative to the package (`infrastructure/plugins/dom.py`) or to a layer, as the architecture tables cite them (`plugins/base.py`, `cache/redis_adapter.py`), count when they exist there; the current docs name no missing path.

### Fix: The Cache Section Reads No Unprefixed `CACHE_*` Variables
- `CacheConfig` was a pydantic-settings `BaseSettings` with the prefix `CACHE_`, so validating the merged config read `CACHE_REDIS_URL`, `CACHE_SEARCH_TTL_SECONDS`, `CACHE_CRAWLJOB_TTL_SECONDS` and `CACHE_MAX_CONCURRENT` from the environment as defaults below the YAML, although the docs said they are not read. The section is a plain model like the others now; the environment speaks through `SCAVENGARR_CACHE_*` only ([configuration.md](docs/features/configuration.md)).

### Fix: An HLS Playlist's Range Answer Is No File Size
- The playback check read the `Content-Range` total of every playable answer, playlists included: a CDN answering a playlist with 206 gave the playlist's own length (53 bytes) as the stream's size, which Stremio showed as "1 MB" when the site gave none. The size now comes from files only; HLS streams show the site's size or none ([hoster-resolvers.md](docs/features/hoster-resolvers.md) → the playback check).

### Added: Anime from the Kitsu Catalogs
- Stremio's anime catalogs (the Anime Kitsu addon) open titles as `kitsu:<id>` and episodes as `kitsu:<id>:<episode>` with absolute numbers; the manifest accepted `tt` and `tmdb:` only, so an anime opened there never reached Scavengarr although four anime plugins exist. The manifest announces `kitsu:`, and the stream use case translates such a request first: the Anime Kitsu addon's meta gives the IMDb id and the episode as IMDb counts it (a split cour's episode 3 is S3E15, Anime A's 1000 is S21E109; a title's record cached 30 days), Fribb's anime-lists place the rest by TheTVDB season and episode offset (a week), and the translated request runs the existing path, sharing its search cache with the same episode asked by its IMDb id. An untranslatable id answers no streams (`anime_id_lookup_failed`); `/health` reports `anime_ids_configured`, and the phase `anime_ids` times the translation ([stremio-addon.md](docs/features/stremio-addon.md) → Anime Ids; `openspec/changes/add-anime-ids/`).
- `scripts/probes/anime_ids.py` also runs the resolver as in production and prints the request the app searches.

### Chore: Anime Ids Spike
- `scripts/probes/anime_ids.py` shows what a `kitsu:` request maps to through Kitsu's API, the public anime id lists and the Anime Kitsu addon, and what aniworld and fireani find for it; the ten-title spike ([anime-ids-spike.md](docs/plans/anime-ids-spike.md)) found that Kitsu's own mappings place no season, while the addon places every episode the way Cinemeta counts it.

### Refactor: The Stream Use Case Runs Its Phases as Collaborators
- `StremioStreamUseCase` (942 lines, 26 methods) runs five collaborators in `application/stremio/`: `PluginSelector`, `TitleResolver`, `TitleSearch`, `ResolveFlow` (next to `HosterResolution`) and the `answer.py` functions; it keeps the request flow and the tasks that outlive a request (346 lines), and its tests moved with the phases (`test_plugin_selection.py`, `test_title_resolution.py`, `test_title_search.py`, `test_resolve_flow.py`, `test_answer.py`). No behaviour change: the constructor, log events and metrics stay ([plan](docs/plans/stremio-stream-split.md)).

### Fix: einschalten, fireani and haschcon Scrape the Relevant Search Hits Only
- The three JSON-API plugins fetched the details of every search hit, though their sites also list loose matches: einschalten loaded the movie and watch answers of "Jud Süß" (1940) for "Movie B", fireani two RPCs per anime, haschcon a player page per post WordPress matched in its text. They keep the relevant hits now (`relevant_hits()`), as the other plugins do, and fireani at most 3 for a season or episode request: "Anime G" S1E1 no longer loads "Anime G: Junior High". Found by the new real-page tests.

### Chore: Real Pages of the Remaining Stremio Plugins
- einschalten, fireani, haschcon, kinox and moflix had no tests on their sites' own pages, so a changed site or API showed up in production first. Their search and detail pages and API answers are fixtures now (captured 2026-10-06, 84 KB; 16 plugins in all), and `test_real_pages.py` drives the JSON plugins' own requests against them: einschalten's search, fireani's GetAnime and GetEpisode, haschcon's player page and moflix's whole search. kinox's mirror answers sit behind the site's verification wall; its fixtures stop at the detail page.
- `scripts/capture_pages.py` records a JSON API's answer as `.json`, and `--fixture` stores it as `.json.gz`.

### Added: Resolutions and Circuit Breakers Outlive a Restart
- A restart forgot every hoster resolution (cached for an hour), every redirect and every open circuit breaker: the first cached answers after a deploy waited for the resolve grace again, and hosters known to be down cost their timeouts until five failures opened their breakers again at 60 s. `HosterStateStore` keeps one snapshot of the unexpired resolutions and redirects and of the plugin and hoster breakers that are not closed in the cache backend (`hoster_state:v1`), written every 30 s when something changed and at shutdown, and restores it before the app reports ready, every lifetime and cooldown shortened by the downtime. A breaker whose cooldown ran out meanwhile comes back with its probe due and keeps its doubled cooldown. A snapshot of another version or one that cannot be read is deleted (`hoster_state_discarded`); `hoster_state_restored` logs the counts, and `/api/v1/stats/metrics` shows them under `hoster_state`. At the cache's cap of 10,000 resolutions (2.9 MiB) a write costs 10 ms of export and 9 ms of pickling on x86, a start 39 ms ([hoster-resolvers.md](docs/features/hoster-resolvers.md#registry-features)).

### Added: Alert Rules
- `docker/prometheus-alerts.yml` holds six Prometheus alert rules: the target is down (5 min); a plugin searched for 24 h without one hit while at least five plugins had hits (the next dead site or block, found without a session); half of the first answers above 20 s over an hour; a hoster breaker open for 6 h; event-loop lag p99 above 100 ms; more than half of an hour's requests without streams. `promtool check rules` passes, and a test fails when a rule queries a family the app does not export ([observability.md](docs/features/observability.md#alerts)).

### Added: A Published Multi-Arch Image
- `.github/workflows/image.yml` builds the production image for `linux/amd64` and `linux/arm64`, each natively on its own GitHub runner, and publishes one multi-arch manifest as `ghcr.io/strob0t/scavengarr`: `staging` on every push to `staging`, `vX.Y.Z` and `latest` on release tags (a new step of the release procedure in AGENTS.md), `sha-<commit>` for every build. The first run took 5 min (amd64 4.6 min and arm64 4.3 min in parallel, without a cache; the merge 18 s), a run with the layer cache 1 min (26 s per build); the image is 481 MiB (amd64) and 484 MiB (arm64) compressed, and every run's summary lists the size. An image no longer has to be built where it runs: `docker compose pull` (or an updater such as watchtower) updates it, and it names its commit (`SCAVENGARR_COMMIT`, the label `org.opencontainers.image.revision`), which `scavengarr_build_info` and `/api/v1/healthz` report.
- The image bundles the plugins (a mount over `/app/plugins` still replaces them), and the entrypoint writes the default `config.yaml` into `/app/config/` when that directory holds none: the image's copy sat in the directory a volume hides, so a new volume left the app on its built-in defaults. `docker-compose.yml` runs the published image, with the `build:` block as the commented alternative ([configuration.md](docs/features/configuration.md#image-tags)).
- The runtime stage sets file ownership with `COPY --chown` instead of a final `chown -R`, which stored the virtualenv and Chromium a second time in a layer of its own.

### Added: Stream Quality and Size From the Stream Itself
- Most streaming sites name no quality, so most Stremio streams had no quality line and ranked by language and hoster alone. The playback check every resolution passes now reads 4 KiB instead of 1 KiB and takes from them, without another request, the largest `RESOLUTION` of an HLS master playlist and the total size of a file (`Content-Range`). A measured quality replaces the release name's or badge's (a letterboxed 1920x800 encode counts as 1080p), a measured size shows where the site gave none, and the answer is sorted again with them: a stream measured at 1080p ranks above an unmeasured one of the same language. The resolver's cache keeps the measurement, so cached answers carry it too ([stremio-addon.md](docs/features/stremio-addon.md#quality-and-size)).

### Added: Hosters Without a Resolver Are Counted
- A link no resolver claims was probed with `HEAD` and logged at DEBUG only, so nobody saw which hosters the plugins deliver without a resolver (in 6 h of production all 81 such probes were dead: embed pages). The registry now logs `hoster_without_resolver` (INFO; the hoster name, never the URL, and in a Stremio request the plugin) and counts the probes per hoster; `GET /api/v1/stats/metrics` lists the 20 most frequent under `unresolved_hosters`, the most frequent first (JSON only: the set of names is open). Streaming playlists, which need no resolver, are not counted. Every resolution of a Stremio request now logs with its plugin's name ([hoster-resolvers.md](docs/features/hoster-resolvers.md#adding-a-new-resolver)).

### Added: The Startup Log Names the Configuration
- `config_effective` (INFO) lists every setting that differs from its default after all layers, with the YAML file read; secrets show as `***`, dict-typed settings (`plugins.overrides`) their keys. `config_unknown_keys` (WARNING) names the YAML keys no setting accepts, which loading ignored silently: a misspelled key, or one a release removed (a `config.yaml` seeded months earlier ran unnoticed). `scripts/prodctl.py logs --since 7d --grep config_` answers what production runs with ([configuration.md](docs/features/configuration.md#what-the-server-logs-at-startup)).

### Added: Production Reports Which Build Runs
- `scavengarr_build_info` carries `commit` and `built` beside `version`; `/api/v1/healthz`, `/api/v1/stremio/health` and the startup line `app_startup_complete` report the same three. They come from `SCAVENGARR_COMMIT` and `SCAVENGARR_BUILT`, which `Dockerfile.prod` takes as build arguments and `docker-compose.yml` passes through (`unknown` without them; README → Docker Compose shows the build command). The family keeps its one series, so the telemetry rule's fixed label sets still hold.

### Changed: httpx Logs Its Requests at DEBUG Only
- httpx wrote one INFO line per outgoing request, 59 % of production's log lines (2026-10-06; on the production host the log lives on the SD card). With `logging.level: INFO` the `httpx` and `httpcore` loggers now log from `WARNING` up; at `DEBUG` they keep the request trace. `scripts/stremio_profile.py` counts requests per host from these lines, so its counts need a run at `DEBUG`.

## v0.3.0 - 2026-10-06

Stremio latency and playback on the production host behind a VPN: answers go out at 5 streams while links resolve during the plugin search, cached answers at once, and plugins whose site is down are skipped; the stealth browser's pages go to the most urgent work, and their count follows waits, CPU and memory. HLS plays in Stremio Web again (1080p stutter, VEEV, the proxy's 500s under Python 3.13 with anyio). Prometheus metrics, request ids and on-demand tracing, plugin parsers on selectolax, read-only production diagnostics (`scripts/prodctl.py`), and the fixes of two code reviews.

### Fix: CDN Tokens No Longer Reach the Logs Through httpx and uvicorn
- The app's `http_request` line masks query values, but two third-party lines repeated every URL whole: uvicorn's access log (each proxied HLS request with the CDN's tokens) and httpx's `HTTP Request: GET <url>` line for every outgoing request (video URLs with tokens and the client's address, `i=`). Production logs carried both (2026-10-06). uvicorn now runs with `access_log=False` (`http_request` is the access log), and third-party records show URLs by their origin only (`HTTP Request: GET https://cdn.example.net "HTTP/1.1 200 OK"`), tracebacks included.

### Chore: prodctl Prints Whole Tracebacks
- `scripts/prodctl.py logs` cut every record to 400 characters, so a traceback ended before its error. `--width 0` prints records whole (`--width N` cuts to N characters, 400 by default).

### Added: The Stealth Browser's Page Count Follows the Machine
- The stealth browser ran 2 pages on every host: a larger host could not use its CPUs, and the production host under the load of its other containers had no brake. `PageBudget` now adapts the count every 5 s between 1 and `stremio.max_concurrent_playwright` (auto-tuned from the container's CPUs and memory). One page more when a page request waited at least 1 s, the CPU is at most 70 % busy and two pages' worth of memory (400 MB) is free, at most every 30 s; one page less when less than 200 MB is free (at once) or the CPU was at least 90 % busy on two samples in a row (at most every 10 s); back to 2 after two minutes without waits and changes. The CPU is the host's busy share or, under a CPU limit, the container's share of it; free memory is the host's or, under a memory limit, what the limit leaves. A lower count takes no running page away. Changes are logged (`browser_pages_changed`) and show in `scavengarr_browser_pages{state="limit"}`.

### Fix: kinoger's Pages No Longer Queue Behind Hoster Captures
- The stealth browser handed its 2 pages out in arrival order, and since links resolve while plugins search, the hoster captures of an answer (Filemoon, Dropload, SuperVideo, DoodStream's fallback) took them during the search: 13 of 13 kinoger searches ran into the 30 s plugin timeout in the sixth production round (7.9-17.3 s alone), and titles with few streams waited the full 30 s for it. The next free page now goes to a resolution at play time, then to the earliest due work (a search's plugin pages, due when the search ends, before the captures of its answer, due at the answer deadline), and to background resolutions only while nobody else waits. A running page is never taken away.

### Fix: Waiting for a Browser Page No Longer Trips a Hoster's Breaker
- A hoster resolution's time bound (`http.timeout_resolve_seconds`, 10 s in production) included the wait for one of the stealth browser's pages: a Filemoon capture that waited 9 s had 1 s left, timed out, and the timeout counted for the hoster's circuit breaker, which opened for Filemoon, Dropload and SuperVideo in the sixth production round although they were healthy. The clock now stops while a capture waits for a page.
- Work that gets no page 3 s before its request is due (a Stremio search's end, an answer's deadline) no longer starts a page that would be cut: a capture reports `busy` (`hoster_resolve_busy`), neither cached nor counted by the breaker, a plugin's page load answers nothing as on any failure (the optional solver sidecar can still answer). Work without a due time (Torznab searches, the scoring probes) waits as before.

### Added: Metrics of the Stealth Browser's Pages
- Plugin pages behind Cloudflare, hoster captures and link-outs share the stealth browser's 2 pages, and in the sixth production round kinoger's pages queued behind captures until its 30 s timeout. The wait for a page and the work on it are now recorded by what the page is for (`scavengarr_browser_page_wait_*` and `scavengarr_browser_page_*`, `kind`: `play`, `plugin`, `capture`, `background`), the limit, pages in use and waiting requests as the gauge `scavengarr_browser_pages`; with tracing on, a request's trace shows its queueing (`browser_page_wait capture`). The application names what browser work is for and when it is due (`PageClaim`), the groundwork for handing the pages out by urgency ([browser-page-budget.md](docs/plans/browser-page-budget.md)).

### Fix: Alfafile Links With a File Name Resolve
- The Alfafile resolver's file-ID pattern ended right after the id, so a link with the file name after it (`/file/<id>/<name>`) was not recognized; the other generic DDL hosters accept trailing parts. Found by the doc review (2026-10-06).

### Fix: Search Probes Page Only As Far As They Count
- The scoring's search probes count the first `scoring.search_max_items` (20) results, but the plugins paged up to their 1000-result limit: extra requests to the sites every probe run, and a long result list could run into the probe's 10 s timeout and count as a failed probe. A probe now sets the plugins' result limit (`search_max_results`) like a Stremio search. Found by the doc review (2026-10-06).

### Fix: Plugin Requests Keep Their User-Agent
- `_safe_fetch()` with extra headers sent the app's own `Scavengarr/<version>` User-Agent instead of the plugin's (aniworld's search), and its requests to a site whose browser session httpx had taken over (the search POSTs of megakino, streamcloud and streamkiste after a Cloudflare challenge) went out without the browser's User-Agent, which the clearance cookie needs. It now sends them like `_fetch_text()`. Found by the doc review (2026-10-06).

### Fix: A Misspelled Disable Override Is Reported
- `plugins.overrides.<name>.enabled: false` with a name no plugin has disabled nothing and logged `plugin_disabled_by_config` as if it had; it now logs the `plugin_override_unknown` warning like every other unknown override. Found by the doc review (2026-10-06).

### Fix: A Search Probe of an Unknown Plugin Reports It
- `MiniSearchProber` caught `KeyError` for an unknown plugin, but the registry raises `PluginNotFoundError`, so the probe raised instead of reporting `plugin_not_found` (its test mocked the `KeyError`). The scheduler probes only registered plugins, so production never hit it. Found by the doc review (2026-10-06).

### Fix: A Mirror Member That Delivers Alone Ranks First Again
- A mirror group member that gave nothing while its standby delivered ranks behind the other members until it delivers again. It cleared that mark only when it delivered with a standby behind it; delivering alone, while the other members' breakers were open, left it behind once they were back. Any delivery clears it now. Found by the doc review (2026-10-06).

### Performance: The Title Filter Scores Each Search Result Once
- The full and the base title of a Stremio search find many results of a plugin twice, and the title filter scored both copies (about 24 ms of CPU per search); only the answer dropped the second. `PluginSearchRunner` now hands each result on once, by the key the search progress uses (plugin, title, release, links: the old `download_link` check of its unused return value would have merged another plugin's result). Found by the code review (2026-10-06).

### Performance: A Fully Cached Stremio Answer Resolves Nothing in the Background
- An answer from the search cache started a background resolution for the next request even when every link already had a cached outcome (a video or dead): it ranked the results once more and resolved nothing. It starts only for links without one now. Found by the code review (2026-10-06).

### Refactor: The HLS Proxy's Refusal Rule Lives in `StremioLinks`
- Which CDN answers to a stream's playlist resolve the hoster URL again (403, 404, 410: an expired token) was decided in the Stremio router, against the layer rule (interfaces do I/O only). `StremioLinks.after_refusal(link, status)` (application) now decides it and resolves past the resolver's cache; the router fetches and answers. Behavior is unchanged. Found by the code review (2026-10-06).

### Refactor: One Filter for Nested Matches
- Eight plugin parsers (ddlvalley, filmfans, hdfilme, kinoger, nima4k, scnsrc, serienfans, streamkiste) each wrote their own filter that drops a selector's matches nested in another match; they now share `outermost()` in `infrastructure/plugins/dom.py`. kinox and kinoger's player check test other conditions and keep theirs. Found by the code review (2026-10-06).

### Performance: diskcache Writes One at a Time
- The diskcache adapter let up to `cache.max_concurrent` writes run in parallel, but SQLite has one writer: the parallel writes only waited for its lock. A Stremio answer saves the links of its streams together, and 20 links took 80-100 ms to save; with the writes one after another (an `asyncio.Lock` for `set`, `delete` and `clear`) they take 5-6 ms. Reads stay parallel. This also helps the search cache and the plugin scores; Redis is unchanged. Found by the code review (2026-10-06).

### Fix: crawli Reads Past Page 8
- crawli took the last result page from page 1's pagination, but the site links a window of pages (page 1 up to 8, page 8 up to 11): a search stopped after 80 results. Every page now extends the window, up to 100 pages (1000 results). Checked on the live site (2026-10-06). Found by the code review (2026-10-06).

### Fix: byte Files Magazines and Movie Collections Under Their Categories
- byte's category map took its names from the site menu, which writes "Magazine-Zeitungen"; search results and detail pages write "Magazine - Zeitungen", so magazines and newspapers came out as 8000 (Other) and a book request (7000) dropped them. The lookup now spaces dashes the same way for both spellings (`_category_key`), and "Movie Collections" (missing, so 8000) counts as films. Checked on the live site (2026-10-06). Found by the code review (2026-10-06).

### Fix: Forum Plugins Share One Link-Container Check
- boerse and mygully took any host ending in a container's domain for a link container (`notfilecrypt.cc` counted as `filecrypt.cc`), and the three forum parsers kept their own container lists and anchor-text helpers. They now share `infrastructure/plugins/forum_links.py` (`is_link_container`, `hoster_from_text`, `hoster_from_url`): a container's host or one of its subdomains counts, and every forum knows every container of the lists (boerse gains hide.cx, keeplinks.co, linkcrypt.ws and tolink.to; mygully tolink.to; dataload and myboerse keeplinks.co and linkcrypt.ws). Found by the code review (2026-10-06).

### Fix: A Failing Score Store No Longer Fails a Stremio Request
- The scored plugin selection (`stremio.scoring_enabled`) read the plugin scores without catching errors: a score store that failed to read one snapshot failed the whole stream request. A snapshot that cannot be read now counts as none, as the mirror-group ranking already handled it; both read through one helper (`current_snapshots`), which logs `plugin_scores_unreadable` (replaces `stremio_mirror_scores_failed`). Found by the code review (2026-10-06).

### Fix: A Refused Probe Is No Stream
- The registry's content-type probe (playlists, URLs without a resolver) took any HEAD answer with a video type as a stream, also a 403 or 404: a CDN that types its error page by the path made a refusal a stream, cached for an hour. Only answers below 400 count now (`hoster_probe_refused`). The probe tests use `respx` instead of mocked responses. Found by the code review (2026-10-06).

### Fix: Results With Other Hoster Links Stay Apart in a Running Search
- A running Stremio search keeps each result once (the full and the base title find many twice), by plugin, title, release, link and the URLs of its `download_links`. The key read those URLs under `url`, but plugins store them under `link`: two results of one plugin with the same title, release and page link but other hoster links collapsed into one. The three readers of a link's URL (search progress, stream converter, episode filter) now share `link_url()` in `domain/plugins/base.py`. Found by the code review (2026-10-06).

### Fix: A Refused Stream Resolves Past the Cache Even While Another Request Resolves It
- When the CDN refuses a stored HLS playlist, the hoster URL resolves again past the resolver's cache. Requests for one link shared one resolution, keyed by the link only: a refresh that came while a request resolved the stale link from the cache joined it and got the refused URL again (`502`). A refresh now runs on its own, and requests that come meanwhile join it. Found by the code review (2026-10-06).

### Fix: A Plugin Leaves a Dead Host Its Site Moved To
- `HttpxPluginBase` makes a permanent move of a site (301/308 from the base host to another) the base URL, and kept it until a restart. hdfilme moves on every few days, and its old host redirects to the newest one: a new host that died kept every search on it. A request to the new host without an answer (timeout, connect or DNS error) now sends the plugin back to the base URL the site moved from (`{name}_site_move_undone`). Found by the code review (2026-10-06).

### Fix: A Plugin Site Counts as Down Only After a Retry
- The plugin health check marked a site unreachable after one try without an answer within 5 s, and the Stremio search skipped the plugin until the next check 5 minutes later (movie2k in production: no answer at one check, an answer at the next). A reachable site without an answer is now tried again after 30 s before it counts as unreachable; an unreachable one is not retried. Found by the code review (2026-10-06).

### Fix: Stale Search-Cache Entries Refresh One Title at a Time
- A stale search-cache entry answers while a background search refreshes it. Every stale title asked for started its refresh at once: the refreshes split the plugin slots with the requests' own searches (fair share), so a burst of stale titles left each search a slot or two, and a refresh cut short by `plugin_timeout_seconds` replaced its entry with a thinner one. Refreshes now run one title at a time, and a refresh's plugin time counts from its own start, so a title that waited keeps its whole time. Found by the code review (2026-10-06).

### Fix: Playback Requests Count Against No Rate Limit
- Every stream now points at `/play` (or the HLS proxy), which the per-IP rate limit (`http.api_rate_limit_rpm`, 120) counted like a search, unlike the HLS proxy: a player asks `/play` again for each seek (8 requests within a second at a playback start in production), and clients behind one proxy address share the budget, so a 429 could end a playback. `/play` is exempt like the proxy. Found by the code review (2026-10-06).

### Fix: The Answer Waits for No Link Pushed Out of the Top
- A Stremio request resolves links among its top `max_probe_count` streams while results arrive. A link that better results pushed out of the top kept resolving: the answer waited for it once the search was done, although its outcome could no longer be part of it, and it held one of the `probe_concurrency` slots. Such a resolution is now cancelled. Found by the code review (2026-10-06).

### Fix: A Mirror Group Fails Over When Its Member Gives Nothing
- A Stremio request asks one member of a mirror group (hdfilme, streamcloud, streamkiste). Empty answers trip no breaker, so a member whose parser broke after a theme change kept being asked while the others still delivered. A member that gives nothing for a query (no hits, an error, a timeout) now hands it to the next member with a closed breaker, within the search deadline; when that one delivers, the member ranks behind the others until it delivers again. A title the database lacks costs two searches instead of one, never three. Found by the code review (2026-10-06).

### Fix: SuperVideo's Ad Pages Stay Out With `verify_streams` Off
- SuperVideo has no check of its own and relies on the registry's playback check, which `stremio.verify_streams: false` turned off: its CDN's script and ad pages reached Stremio as streams. A resolver without a check of its own now sets `needs_playback_check`, and the registry checks its results with `verify_streams` off too (the hoster breaker pauses SuperVideo as before). Found by the code review (2026-10-06).

### Fix: warezomen Follows Only Its Pagination Link
- warezomen took the last link reading "next page" anywhere on a search page as the next page: on a result list's last page a result whose short title read "Next Page …" sent the search to that result's download page. Only the pagination cell's "Next Page" link counts now. The parser is also tested on a captured search page (`tests/fixtures/html/warezomen/`). Found by the code review (2026-10-06).

### Fix: HEAD on an HLS Segment Downloads Nothing
- The HLS proxy answered `HEAD` on a segment like `GET`: it downloaded the whole segment (2-10 MB) from the CDN, the server dropped the body, and `scavengarr_hls_proxy_bytes_total` counted the bytes as sent. `HEAD` now takes the CDN's status and content type and closes its answer before the bytes. Found by the code review (2026-10-06).

### Fix: Log Lines From Worker Threads Keep the Request ID
- The title filter, the stream conversion and the episode filter ran in worker threads through `loop.run_in_executor`, which does not copy the context variables: their log lines (`title_match_summary` among them) had no `request_id`. They run through `asyncio.to_thread` now, which copies them. AGENTS.md asks for `to_thread`. Found by the code review (2026-10-06).

### Fix: A TMDB Movie and Series With the Same Number Share No Cached Search
- The Stremio search cache key held the id, season and episode, not the content type. TMDB numbers movies and series separately, so `movie/tmdb:1399` and a `series/tmdb:1399` request without season and episode read each other's results. The key is `stremio:search:{content_type}:{imdb_id}:{season}:{episode}` now; entries stored under the old key are not read again and expire. Found by the code review (2026-10-06).

### Fix: A Silent Tracing Endpoint Delays the Shutdown 3 s at Most
- `Tracing.close()` flushed the queued spans with OpenTelemetry's `force_flush`, whose timeout SDK 1.45 ignores: against an endpoint that took the connection and never answered, every queued batch waited the 5 s export timeout (20 s for 2,000 spans, measured), on top of the 10 s request drain, so `docker stop` could end in a SIGKILL. The shutdown now runs in a daemon thread and the app waits 3 s for it; spans not sent by then are dropped. Found by the code review (2026-10-06).

### Fix: The Stremio Health Check Reports Its Metrics Again
- `/api/v1/stremio/health` answered `"metrics": {}` since the Prometheus metrics replaced the old collector: it still read `state.metrics`, which nothing sets any more. It returns the telemetry's statistics now, as `/api/v1/stats/metrics` does (`uptime_seconds`, `plugins`, `event_loop`). Found by the code review (2026-10-06).

### Fix: A Silent Address Holds Up a Connection 250 ms, Not the Whole Timeout
- `GuardedNetworkBackend` tried a host's checked addresses one after another and gave each the full connect timeout. When the first address dropped the SYNs, every new connection waited 5 s (15 s for plugins and resolvers, so the resolver registry cut the resolution before the second address was tried). The addresses now race under one timeout (Happy Eyeballs, RFC 8305, with asyncio's `staggered_race`): the next starts when the previous one failed or after 250 ms, as with httpcore's anyio backend before. Found by the code review (2026-10-06).

### Chore: Read-Only Production Diagnostics (`scripts/prodctl.py`)
- `scripts/prodctl.py` replaces ad-hoc Portainer scripts: `ps`, `stats` (CPU cores, memory without page cache, processes, network), `logs` (JSON records as `key=value`, health checks dropped, `--grep`, `--fields`, `--since`), `metrics`, `state` (`/api/v1/stats/metrics`) and `probe` (a Python file run inside the container). Everything printed passes `portainer.mask()`: URLs keep only scheme and host, IP addresses, tokens and credentials (also `user:password@` in URLs) are replaced. A budget shared by all processes allows 100 Portainer requests per minute; GETs are retried on 429 and 502 to 504, an exec only when Portainer refused it before it ran (429).
- The Portainer client moved from `stremio_profile.py` into `scripts/portainer.py` (shared, with credentials from `.env.devcontainer`, which wins over a stale key in the environment); it lists containers once per client instead of before every request.
- Versioned read-only probes in `scripts/probes/`: `resources`, `tasks`, `links`, `redis`. Documented in `docs/features/observability.md` and `AGENTS.md` §9, which also gains the agents' working rules (symbol lookup, short output, background CI watch, production only through `prodctl.py`).

### Chore: basedpyright Language Server Plugin for Claude Code
- `.claude/plugins/` holds a local plugin marketplace (`scavengarr-dev`) with `basedpyright-lsp`: Claude Code starts the venv's `basedpyright-langserver` (`scripts/langserver.sh` finds the main checkout's venv from a worktree and resolves imports against the venv's interpreter), so it sees type errors after each edit and looks up definitions and references through the `LSP` tool instead of text search. Wiring per machine: see `AGENTS.md` §9. A stdio smoke test from the worktree and the main checkout reported exactly the planted type error, with `httpx` resolved, within 0.8 s.

### Chore: The Test Suite Runs on Parallel Workers
- New dev dependency pytest-xdist: `poetry run pytest -n auto` runs the full suite in 15 s instead of 47 s (16 threads; at most 8 workers through `--maxprocesses=8` in `addopts`, since 16 took 20 s). CI, `AGENTS.md`, `CONTRIBUTING.md` and the `test`/`commit` skills use `-n auto`; a single test file stays faster without it (1.1 s instead of 2.4 s). Eleven parallel full runs (4 to 16 workers) passed, so the tests share no state between workers.

### Chore: The ruff Edit Hook Lints Repository Files Only and Keeps New Imports
- `.claude/hooks/format-and-lint.sh` skips Python files outside the repository (scratch scripts follow no project rules) and leaves unused imports (F401) to pre-commit: `ruff check --fix` deleted an import added before its first use, and the next edit failed with an undefined name (254 of 385 hook blocks in one week were F821).

### Fix: The App Starts on Python 3.13, and Tasks Start Lazily
- uvicorn runs on uvloop, and uvloop 0.23 hands the task factory `eager_start=None`. asyncio's `eager_task_factory` refused that keyword on Python 3.13 (the app did not start), and on 3.14, the Docker image's Python, the `None` overrode its eager start: the app logged `eager_tasks=True` while every task started lazily. Found by the code review (2026-10-06).
- A factory of the app's own that started tasks eagerly on uvloop (staging, deployed 2026-10-06) broke anyio: anyio, under Starlette's middleware and httpcore's connection locks, keeps its own tasks lazy only under asyncio's factory. A task group's child that suspended inside a cancel scope at once lost that scope ("Attempted to exit a cancel scope that isn't the current tasks's current cancel scope"), and every proxied HLS variant answered 500: the master playlist played, its variant did not, in Stremio Web as in any player.
- The event loop now keeps asyncio's lazy task start (`configure_event_loop()` in the composition root), as in every measured production round; `event_loop_configured` names the loop.

### Fix: An Empty Tracing Endpoint Turns Tracing Off
- `SCAVENGARR_TELEMETRY_TRACING_ENDPOINT=` (a compose file keeping tracing optional with `${TRACING_ENDPOINT:-}`) failed the config's URL check, and the app did not start. An empty or blank value means off now, as the telemetry factory already treated it. Found by the code review (2026-10-06).

### Fix: burningseries Gives Nothing for a Season the Series Lacks
- bs.to redirects a season it lacks to another season, and the plugin read that season's episode table: Sonarr's search for Series D S09E02 got an episode of season 1, in English, and a season search a non-existent "S09". The episode links name their season now (`episode_seasons`); a page of another season gives no result. Live: S02E02 and S05 link their pages, S09E02 and S09 give nothing. The logic predates this release; found by the code review (2026-10-06).

### Fix: jjs Takes No Size From a Season Pack's NFO
- A detail page without "Gesamtgröße" (season packs name their part size and episode count only) took the first size anywhere on the page: a bitrate ("19.6 Mb/s" became 20 MB), one episode's size or CSS (`#2b2b2b` became "2b"), on 6 of 7 and 9 of 16 live season packs. Sonarr and Radarr rejected those packs as too small. jjs reports the total size only ("Gesamtgröße", "Total size"), else no size. Live: 10 of 10 film results keep their sizes. Found by the code review (2026-10-06).

### Fix: animeloads Passes DDoS-Guard and Its Captcha Again
- Blocking images by resource type (instead of by file extension) also blocked DDoS-Guard's check beacons, which set the `__ddg*` cookies, so the challenge reloaded until it timed out (0 of 3 searches), and the grab's captcha images, so every grab gave nothing. `block_heavy_resources` lets DDoS-Guard's check images through (also for the stealth context), and animeloads lets its captcha images through with a route of its own. A live search passed again in 12 s. Found by the code review (2026-10-06).

### Fix: Logs Name a CDN, Not Its URL
- The HLS proxy's CDN errors, `/play`'s redirect, the playback check and several resolvers logged video URLs (up to 120 characters, one in full at debug level), whose path and query carry tokens and the client's address (`i=`, production's VPN exit address). They log the CDN's second-level domain now (`cdn=`); `extract_domain()` moved to `hoster_resolvers/_domain.py`. Found by the code review (2026-10-06).

### Fix: The Browser Restart Waits for Its Operations
- The shared Chromium restarted after 200 stealth pages once no context listed a page. A page another slot was still opening was not listed yet, so the restart killed it (10 of 10 trials): the capture failed and its working link was cached as dead for 15 minutes. The restart also ran inside the finishing request, while it held a page slot and its resolve timeout.
- Operations hold the browser with `SharedBrowserPool.lease()` (the stealth pool's fetches and captures, a plugin's `isolated_search()`). The last one to end after 200 pages starts the restart in a task of its own; new operations wait until it is done.
- A Playwright plugin's kept context died with the restart, and boerse, mygully and animeloads failed every search until the app restarted. `_ensure_context()` makes it again when the browser it belonged to is closed. Found by the code review (2026-10-06).

### Fix: A Later Resolution Leaves a Running HLS Playback Alone
- All answers and devices share one stored link per hoster URL (`stream_link_id`). When a second device, AIOStreams or a reopened stream list resolved the hoster URL again (another CDN node), the next variant and segment requests of a running playback went to the new node with the old path and token: 403, the proxy answered 502, and the playback stopped when its buffer ran dry.
- A served playlist points at a copy of the link it came from (`StremioLinks.pinned`: `<stream id>.<digest of the video URL>`, one per resolution), which later resolutions leave alone. Relative URIs become absolute URLs of that copy (`rewrite_manifest(..., playlist_dir)`); a playlist under the old URL form still plays. Found by the code review (2026-10-06).

### Fix: Streams Play While the Cache Fails
- Every answered stream points at `/play` or the HLS proxy, so a stream whose link could not be saved was dropped: with diskcache raising on every write (locked, disk full) every Stremio answer was empty, and with Redis losing the writes every `/play` and HLS proxy request answered 404.
- `CacheStreamLinkRepository` keeps the links of the latest answers in memory (4096) and reads them from there first; a failed cache write or read is logged (`stream_link_save_failed`, `stream_link_load_failed`), and the cache keeps the links across restarts. Found by the code review (2026-10-06).

### Fix: An Echo Leaves No Hoster Out of a Cached Answer
- A cached answer took each hoster's first cached outcome in rank order, also an echoed embed URL (a resolver that only validates a link). The answer drops echoes, so the hoster was left out of every cached answer for the hour the echo stayed cached, although a lower-ranked link of it had a video. `_cached_resolutions` passes echoes like dead links now. Found by the code review (2026-10-06).

### Fix: A Stored Link Is as Old as Its Resolution
- A stored link took the time its answer was built as `resolved_at`, also for a stream from the resolver registry's cache, which answers for an hour. `/play` and the HLS proxy therefore counted video URLs up to two hours old as fresh (fresh: one hour) and redirected to expired tokens.
- `ResolvedStream.resolved_at` carries the time of the resolution: the registry stamps it once, its cache answers with it, and `build_cache_link` and `StremioLinks` store it. Found by the code review (2026-10-06).

### Fix: Only Verdicts Count Against a Hoster's Breaker
- A resolution cut after half of `http.timeout_resolve_seconds` counted as a failure. Most cuts come from the answer going out once enough other hosters have a video, and the timed window includes the wait for the stealth browser's pages, so five cuts opened the breakers of healthy hosters (Filemoon, SuperVideo, DoodStream). Cuts count no more.
- A half-open probe that ended without a verdict (a dead link, a failed request) kept the probe slot, and the alive links after it were refused for a whole cooldown, up to an hour. `PluginCircuitBreaker.release()` frees the slot, so the next link probes.
- A failed playback check request (timeout, reset on a loaded production host) cached a working link as dead for 15 minutes and counted against the hoster, while the same error from the resolver did neither. `check_playable` raises it now, and the registry treats it like a failed resolver request (`hoster_resolve_check_error`).
- Found by the code review of `origin/main..staging` (2026-10-06), each reproduced in a test first.

### Fix: VEEV Plays in Stremio Web
- veevcdn binds a video URL to the User-Agent and the Accept-Language of its resolution: another value, or an Accept-Language the resolution did not send, gets 403. Stremio's streaming server sets the User-Agent of our `proxyHeaders` but passes the browser's other headers on, so in Stremio Web (Firefox) the probe played (206, ffmpeg sends no Accept-Language) and the playback 6 s later got 403 (production).
- A resolver whose CDN binds the video URL to the player's request headers implements `ClientBoundResolverPort` (`bound_headers`, `resolve_for_client`); VEEV binds `user-agent` and `accept-language`. `/play` resolves such a hoster again for a player that sends other values than the stored link was resolved with, and keeps that link per player (`<stream id>-<digest>`, fresh for an hour); the player sends the CDN the same headers after the redirect. Requests of one player share one resolution (VEEV: 0.5 s); a failed one falls back to the stored link.
- Checked in production with the browser's Accept-Language: resolved with it, 206; the stored URL, 403.

### Changed: A Mirror Group Asks Its Best-Scored Member
- hdfilme, streamcloud and streamkiste front one database, and a Stremio request asks one of them: the first in alphabetical order whose breaker was closed, so hdfilme whenever it answered, even with an empty or broken search. The member is now the reachable one with a closed breaker and the best plugin score of the scoring subsystem (health and search probes; a score with a confidence up to 0.1 counts as none), the first one on a tie or without scores (maintainer's decision after the dev-server end-to-end run, 2026-10-05).

### Fix: Background Resolutions Run One Title at a Time
- A cached answer resolves its other links in the background for the next request. 17 cached titles asked within seconds started 17 such runs at once: their browser captures queued for the stealth browser's 2 pages, and 12 Filemoon resolutions hit the 10 s resolve timeout, which opened Filemoon's breaker, although Filemoon resolved in 1.5–2 s on its own (dev-server end-to-end run, 2026-10-05). The runs now go one title at a time, each with its whole `stream_deadline_seconds` from its own start.

### Fix: The Access Log Masks Query Values
- Each request's `http_request` log line logged its whole query string: Prowlarr's `apikey` on Torznab requests, and on proxied HLS requests the CDN's tokens and the client's address (`i=`, production's VPN exit address; 545 of the 575 proxy lines with a query in a dev-server end-to-end run). Only Torznab's own parameters keep their values on Torznab paths now; every other value is logged as `***` (`loggable_query()` in `interfaces/app.py`).

### Feat: Request Id and On-Demand Tracing
- Every HTTP request gets a `request_id` in the log context (all its log lines and those of the searches and resolutions it starts) and the `X-Request-ID` response header, so one request can be followed through the logs.
- `telemetry.tracing_endpoint` (`SCAVENGARR_TELEMETRY_TRACING_ENDPOINT`) sends the core's stages as OpenTelemetry spans over OTLP/HTTP: one trace per request with its phases, plugin searches and hoster resolutions. Off by default; without it the trace SDK and exporter are not loaded. Spans hold no URLs or titles, errors only their exception type.
- `docker compose --profile tracing up -d tempo` starts Grafana Tempo 3.1 (`docker/tempo.yaml`, traces kept 3 days).

### Feat: Prometheus Metrics
- `GET /metrics` serves Prometheus metrics of the core (prometheus-client): every Stremio stream request by the state of its search results (cache, stale, new or joined search), its phases and why the answer went out (target, done, deadline, cached), streams per answer, every plugin search and every hoster resolution with duration and outcome (`hits`, `empty`, `cut`, `breaker_open`, `unplayable`, ...), HLS proxy requests with time to first byte and bytes, the event-loop lag, open circuit breakers and the container's CPU and memory (Chromium included). `docs/features/observability.md` has the families, a scrape job and queries.
- One port records everything: `TelemetryPort.stage()` times a step and records its outcome (`cut` for a cancellation). The plugin search runner, the hoster resolver registry, the Stremio use case and the HLS proxy route use it; plugins and resolvers stay unchanged. Labels come from fixed sets only (no titles, ids, URLs or domains).
- Cost on x86: 5.6 µs per recorded step, 4.4 ms per scrape of 672 series (rendered in a worker thread); at a 60 s scrape interval about 20 s of CPU per day on the production host. `tests/benchmark/test_telemetry_overhead.py` measures it.
- `docker/grafana-dashboard.json`: a Grafana dashboard of answers (why they went out, search state, answer and phase times), plugins and resolvers (time and outcomes), open breakers, the HLS proxy and CPU (container, Python, Chromium) and memory.
- `/api/v1/stats/metrics` keeps its JSON; its plugin statistics come from the new metrics. `MetricsCollector` (`infrastructure/metrics.py`) is replaced by `Telemetry` (`infrastructure/telemetry/`).

### Perf: Plugin Parsers on selectolax
- Every plugin parser (28 plugins and the XenForo base of dataload and myboerse) reads pages with selectolax (lexbor, C) and CSS selectors instead of `html.parser` state machines in Python, which held the GIL for every page (34% of the GIL samples of a Stremio request on the production host, 0.43 s per first request).
- Results stay the same: every parser input of the test suite and of live searches of all plugins was recorded on the base commit, and 2,989 of the 2,990 unique inputs give identical results (the other keeps a description's line breaks as `\n`, as HTML5 does). The recorded big pages (from 20 KB) parse in 1.6 instead of 17.4 s on x86.
- Every page goes through `parse_page(parser, html)` (`infrastructure/plugins/dom.py`), which parses pages from 32 KiB in a worker thread; `HttpxPluginBase._feed()` is gone, and 17 plugins (5 on Playwright) no longer parse on the event loop. `docs/features/python-plugins.md` ("Parsing Pages") has the pattern and selectolax's pitfalls.
- The migration found the bugs fixed under "Plugin Selectors That Missed the Live Theme".

### Fix: hdfilme Films Without Streams
- hdfilme.cafe moved to hdfilme.ceo (a permanent redirect, which the plugin follows), and its film pages now embed devideosrc's newer player under `/custom/movie/<imdb>`, lazily from `data-src`. `find_player` knew only `/movie/<imdb>`, so every film page had "no player" and hdfilme gave no film streams (live smoke test, 2026-10-05). The classic `/movie/<imdb>` page still carries the token, so the IMDb id is now read from either path. Series pages still embed `/serial/`.
- hdfilme is the first member of its mirror group (hdfilme, streamcloud, streamkiste), which a Stremio request asks alone while its breaker is closed; empty answers do not count as failures, so the group's film streams were missing altogether.

### Fix: Plugin Selectors That Missed the Live Theme
- Found while moving the parsers to selectolax (their results stay identical otherwise). aniworld: the current theme names the plot in `<p class="seri_des" data-full-description>`, the parser read `div.seri_des` only, so every result had the short search-API description instead of the full plot.
- streamkiste: search cards name year and genres in `span.movie-release` (the parser read `div.movie-release`), so hits had neither, and series were not told from films before their detail page; the IMDb rating sits in `span.average` inside the IMDb link (the parser read `div.average span`), so it was always empty.
- kinox: a detail page's year came from the page's last Year span, which belongs to a related entry further down; a film whose related entries had another year got theirs. The year now comes from the title's heading.
- byte: every film, series, book and XXX request returned nothing. It searched the site group's id (`c=1`, `c=2`, ...), and the site lists only entries filed directly under a group, not its subgroups (`c=1` and `c=2` answered with the empty search form). Category requests now search every group and keep the category's rows.
- warezomen: the live site's pagination is a row of the results table, which the parser read as a result ("Downloads | Page 2", a relative link) while looking for the next page outside the table only: every search stopped at page 1.
- hdsource: older posts list their filecrypt containers after `<strong>Download:</strong>` / `Mirror #N:` labels instead of `hosterlnk` links; the parser dropped them (78 of 304 articles in live searches, all 50 of one page). They are read now, named by their link text (`Rapidgator.net` → `rapidgator`).
- scnsrc: film posts bold an awards line ("Top rated movie #47; Awards: 2 wins & 2 nominations.") before the release name, and the parser took the first bold text with a period: 9 of 11 Movie B results carried that line as their title. A release name now has no spaces.
- jjs: the size was the first one on the page, the part size ("Partgröße: max. 1020 MB") on all 44 checked live pages. It is the total size ("Gesamtgröße") now; season packs, which name no total, have no size instead of their part size.
- movieblog: with several "Nächste Seite" links the pagination took the last one, unless an earlier link's URL contained "Seite" (a check meant for a match that tested the URL). The first link wins now; live pages have one, so nothing changes there.

### Fix: 1080p HLS Streams Stutter in Stremio Web
- Stremio Web has its streaming server probe every stream before it plays it. An HLS source (format `hls`) then always goes through the server's converter, which re-encodes the video with libx264: it repackages MP4 and Matroska only, because only their keyframes are indexed (`requiresTranscoding` in the server's `hls-converter`). On the production host (no usable hardware encoder) a 1480×620 stream took 1–2 cores, and 1080p, 2.3 times the pixels, stuttered. Each segment was also fetched twice, by one ffmpeg for the video and one for the audio.
- The HLS proxy refuses the streaming server's ffmpeg (User-Agent `Lavf/`) the stream's playlist (`403`, `hls_proxy_converter_refused`). The failed probe makes Stremio Web read the content type with `HEAD` and play the playlist itself (hls.js): no transcoding, the original quality, each segment fetched once.
- `stremio.allow_hls_transcoding: true` lets a server transcode again, for players that cannot decode a stream's codecs (HEVC in Firefox, AC3); hosters' HLS was H.264 and AAC in every probe.

### Changed: Stream Links Resolve Again (Autoplay, Continue Watching)
- Stremio plays a kept stream object later: autoplay plays the next episode's stream about an hour after it was fetched, "Continue Watching" days later. Every resolved stream now points at Scavengarr: a file at `/play/{id}` (a redirect to the current video URL), HLS at `/proxy/{id}/scavengarr.m3u8`, under which the proxy serves the current playlist.
- A video URL older than an hour resolves again at playback (`stremio_link_resolved_again`); a playlist the CDN refuses (403, 404, 410) resolves once more past the resolver's cache. Concurrent requests for one link share one resolution.
- When the hoster gives no video at that point, the stale video URL is still tried: in the dev-server end-to-end run, 3 FireStream links resolved no more after an hour while their stored playlists still played (they answered 502 before). A CDN refusal then resolves once more past the cache as above.
- Links are kept 7 days (`stremio.stream_link_ttl_seconds`, was 2 h; `data/config.yaml` too) under an id from the hoster URL, one per stream. In the link-lifetime measurement every proxied HLS link answered 404 after 2 h because of the old TTL, while the CDN streams still played after 92 minutes.
- `/play` answers `HEAD` (streaming servers ask with HEAD first).
- HLS streams without headers go through the proxy too (a redirect to a playlist fails on Android).

### Changed: Stremio Answers at 5 Streams, Links Resolve While Plugins Search
- The answer goes out once `stremio.resolve_target_count` hosters (default 5) have a video, or when the search and every resolution are done, at the latest `stremio.stream_deadline_seconds` (default 60) after the request (`stremio_resolve_complete` with `reason`). The fifth end-to-end round's first answers waited for the soft deadline (7 s) and the grace (4 s): titles with many streams had 5 after about 5 s, titles with few got fewer because slow plugins were not waited for.
- Links resolve while the plugins search: each plugin's results pass the title filter when they arrive (`SearchProgress`), each request ranks them and resolves each hoster's best link (`HosterResolution`: rank order per hoster, a better link that arrives later too, each URL once).
- The search runs until every plugin is done, at most `stremio.plugin_timeout_seconds` (default 30, was 10); plugins still running at the answer fill the search cache. Requests on one search read its results while it runs.
- Removed: `stremio.search_soft_deadline_seconds`, `stremio.resolve_grace_seconds` (old values are ignored) and the late plugins. `data/config.yaml` follows the new defaults (it had 10 s, 15 s and `resolve_target_count: 0`).
- Trade-off: a search holds its share of the concurrency pool until it ends, so a concurrent request gets half the plugin slots meanwhile. Behind AIOStreams the per-addon timeout must now exceed 60 s.

### Perf: Stremio Searches Skip Plugins Whose Site Is Down
- A plugin whose site is down ran in every search until the deadline: its fetch errors end as empty answers, which the circuit breaker does not count. megakino_to and movie4k held every first answer of the fifth end-to-end round to the soft deadline.
- `PluginHealthMonitor` checks every Stremio plugin's site (HEAD on its domains) every `stremio.plugin_health_interval_seconds` (default 1800, `0` = off) and the unreachable ones every 5 minutes; searches skip those (`stremio_plugins_unreachable`), and a mirror group picks a reachable member.
- Unreachable: no answer or a server error without a challenge page (522). A Cloudflare challenge counts as up. One answer from any of the plugin's domains brings it back; a check in which no site answers changes nothing (the own network is down then).

### Perf: Cached Answers Go Out at Once
- An answer from the search cache waited for the resolve grace (4.1–4.4 s in the fifth end-to-end round) when one of its links had no cached resolution. It now goes out at once with the resolutions in the resolver's cache when one of them is a stream (`stremio_resolve_from_cache`); a hoster whose best link is cached as dead or not resolved yet contributes its next cached one. A late plugin's new link of a hoster, ranked first, dropped that hoster's stream from the cached answer (3 of 17 titles in the dev-server end-to-end run, 2026-10-05).
- The links without a cached resolution resolve in the background, one run per title at a time, and fill the resolver's cache for the next request. Without a cached stream the answer resolves as before.
- The resolver registry reads its cache without resolving (`cached(url)`).
- A cancelled request (shutdown) now cancels its unfinished resolutions instead of leaving them running untracked.

### Perf: TLS Runs in the Event Loop, Not in Python
- httpx's default network backend on asyncio is anyio, which runs TLS in Python. The shared client now connects through `AsyncioNetworkBackend` (asyncio streams; TLS in the event loop, uvloop in production), underneath the SSRF guard's `GuardedNetworkBackend`. Measured on the production host with 1 MB HLS segments through the proxy: 103–112 ms of CPU per MB before, 75–88 ms after.
- An idle connection the server closed or sent something on (a 408) is retired before reuse: asyncio reads ahead into the stream's buffer, so the backend checks the buffer instead of polling the socket.
- The HLS proxy sends segments in 64 KiB pieces and decodes an encoded body. Passing the CDN's chunks through, as decided first, cost more CPU: VOE's CDN sends 4 KiB TLS records, and each became a response write. Dev-server end-to-end run (x86, 2026-10-05), CPU per relayed MB of one VOE stream: 34 ms before both changes, 41 ms with the asyncio backend and the chunks passed through, 25 ms with 64 KiB pieces.
- ChaCha20 instead of AES-GCM for TLS, decided first for the proxy's CPU, was dropped: production's OpenSSL 3.5.7 decrypts both at the same speed on the production host (0.66 against 0.68 s of CPU for 20 MB).

### Fix: SuperVideo Pauses While Its CDN Refuses Players
- SuperVideo's CDN answers a player with a "Loading..." page whose script leads to a parked ad page, and a HEAD with a redirect to an ad domain. The resolver's own HEAD check marked each link dead, which the hoster circuit breaker ignores: 13 of 13 links failed in the fifth end-to-end round, every request tried again.
- The resolver no longer checks the URL itself. The registry's playback check reads the page, counts the stream as unplayable, and the breaker pauses SuperVideo (60 s, doubling up to 1 h) until a probe finds a playlist again.

### Fix: Half-Open Hoster Probes Report Their Outcome
- The hoster circuit breaker lets one probe through after its cooldown. Filemoon's browser captures take longer than the resolve grace on the production host, so the grace cut every probe before half of `http.timeout_resolve_seconds`, the probe reported nothing, and the breaker probed again after every cooldown without doubling it: about 6 s of Chromium CPU per probe, and the cached answer that carried it waited for the grace (fifth end-to-end round, 2026-10-05).
- The probe now runs to its end in the background when its request is cut (`HosterResolverRegistry._resolve_with`, ended by `aclose()` at shutdown): a stream closes the breaker and stays in the resolution cache for the next request; a timeout or an unplayable stream reopens it with twice the cooldown (up to 1 h).

### Measured: Fifth End-to-End Round
- Production with the fixes below, the 17 titles of `stremio_measure.py` (`docs/plans/stremio-latency.md`, fifth round): median 11.1 s while the plugins search (was 12.4 s) with 102 streams (48) and none of the titles without a stream (5 of 17); 1.0 s from the search cache (4.6 s) with 110 streams, 107 of them playable from the VPN address.
- CPU per stream request (3 titles, the plugins searching again): Chromium 6.7 s instead of 11.3 s, Python unchanged at 2.5 s for 6.7 streams instead of 4.7; from the search cache Chromium 2.6 s instead of 10.1 s.
- Still open (`docs/plans/optimization-options.md`): every first answer waits for the soft deadline (megakino_to, whose site is down, still ran in all 17 requests), Filemoon's half-open probes repeat without a longer cooldown, and SuperVideo's CDN answers with a script redirect (13 of 13 links failed).

### Perf: moflix Fetches Relevant Titles Only
- moflix's search lists people next to titles (19 of 20 hits for "Movie B"), and the plugin asked the title API for every hit: 46 answers 404 in the end-to-end test of 2026-10-04, and a person's id can be another title's ("Alan Movie B" fetched a children's film).
- It now fetches titles only, and only the relevant ones (`relevant_hits()`, at most 3 for a season or episode request), as the other plugins do.

### Fix: VEEV Links That Redirect
- veev redirects some embed links to another file code (it changes per request), and the page's token belongs to that code. The resolver asked the player API for the old code, which answered "malformed request" (`hashcheck: 1`; 6 links in the end-to-end test of 2026-10-04). It now asks for the code of the page it was redirected to; the 3 failed links of the test resolve.

### Fix: Playmate Player-Frame Links
- Links to Playmate's player frame (`playmate.to/embed/<id>`) were dropped as invalid (`playmate_invalid_url`); the resolver only needs the file code for its API, so `/embed/` is accepted next to `/watch/` and `/e/`.

### Fix: FireStream Links With "-" in the Id
- FireStream ids use the URL-safe base64 alphabet (`777zhD-W`), and the resolver only accepted letters and digits (as JDownloader's pattern does), so such filmpalast and moflix links were dropped as invalid (`firestream_invalid_url`, 3 in the end-to-end test of 2026-10-04; their pages play). `-` and `_` are accepted now.

### Fix: moflix's Own Players Resolve Again
- moflix hands out two players under one name, and the end-to-end test of 2026-10-04 found all 15 of their links of an hour failing:
  - moflix-stream.click is VidHide (EarnVids) without the `/e/<id>` route the XFS resolver builds (404). Its player is under the `/embed/<id>` and `/v/<id>` links moflix hands out. An XFS video hoster whose `/e/` page answers 404 is now asked for the link's own URL.
  - Its player keeps the stream URLs in a packed `links={"hls2":…}` object; the shared extraction now reads `"hls2"` in unpacked code too (as JDownloader does), and "File is no longer available" marks a deleted file.
  - moflix-stream.link runs Filemoon's Byse player ("Byse Frontend"), which the VidHide resolver cannot read. The Filemoon resolver claims that host (`supported_hosts`); in production it resolved two links in 4.7 s (warm browser) and 15 s (cold).

### Perf: Hosters That Never Deliver Are Skipped
- Production's stream requests started a browser capture for every DoodStream and Dropload link. From the VPN address DoodStream's Turnstile is not solved (31–34 s, 4 attempts) and Dropload's captcha player gives no stream (19 s). In an hour that was 50 captures, no stream, and about 10 s of Chromium CPU per stream request, a cached search included.
- `HosterResolverRegistry` now has a circuit breaker per resolver (`PluginCircuitBreaker`: 5 failures, 60 s cooldown doubling up to 1 h). A timeout, a cut after half of `http.timeout_resolve_seconds` and an unplayable stream count; a stream resets it; a dead link neither counts nor resets it. While open, the hoster is skipped (`hoster_resolve_circuit_open`).

### Measured: The Performance Plan on the Production Host
- Production, 3 titles, the plugins searching again (`docs/plans/pi-performance.md`):
  - a stream request took 11.3 s instead of 13.9 s;
  - it used 2.55 s of Python CPU instead of 4.1 s (−55% of the CPU on the GIL);
  - the event loop's lag p99 fell from ~130 ms to 40 ms.
- From the search cache an answer takes 4.2 s.
- Release-name parsing no longer shows up in the profile; `html.parser` fell from 0.67 s to 0.20 s per request.
- End-to-end test with the 17 titles of `stremio_measure.py` (`docs/plans/stremio-latency.md`, fourth round): median 12.4 s while the plugins search, 4.6 s from the search cache; 64 streams, 61 of them playable from the VPN address.

### Security: Connections Go to the Addresses the SSRF Guard Checked
- The address guard of the shared HTTP client resolved a hostname to check that it is public, and httpcore resolved it again to connect. A hostile DNS server could answer the check with a public address and the connection with a LAN one (DNS rebinding).
- The client now connects to the addresses of the guard's lookup (`GuardedNetworkBackend`, IPv4 first, the next address when one refuses). TLS still verifies the hostname. A lookup answers checks and connections for 60 s (was 5 min for checks only).

### Perf: Lighter Chromium
- On the production host Chromium held 1.7 GB in 15 processes.
- Main frames share at most 2 renderer processes (`--renderer-process-limit=2`). Frames of other sites keep their own (site isolation): turning it off cut the renderers from 7 to 2 with 5 open pages, but made s.to's Turnstile gate fail in 2 of 2 tries.
- Browser contexts block service workers, and Playwright plugins abort heavy resources by type (image, font, stylesheet, media, text track) like the stealth context, instead of by file extension.
- The shared Chromium restarts after 200 stealth pages once no page is open, since its memory grows with the pages it rendered.
- Checked in production: kinoger's and moflix's challenges and s.to's gate (Turnstile with ALTCHA) pass with these settings; ddlvalley and scnsrc return the same results as before.

### Perf: Plugins Searched With the Titles of Their Languages
- A stream request searched every plugin with the localised title, its base before a colon, and the TMDB original title and its base: "Movie J" and "Movie J" doubled the fan-out (205 requests against 105 for Movie F).
- A recall check in production (12 titles, 13 plugins, `docs/plans/pi-performance.md`) measured the original-title queries at 23% of the search requests for 2 of 58 streams, both on one title. A plugin is now searched with the titles of its languages and their base titles only; the title matching still accepts results under the original title.
- The same check found no effect of a lower result cap (no plugin returned more than 24 results for an exact title), so `max_results_per_plugin` stays at 50.

### Perf: Big Pages Parsed Off the Event Loop or in C
- html.parser took 21–27% of the Python CPU of a stream request on the production host (py-spy in production). It runs in Python on the event loop: a 300 KB detail page took 20 ms on x86 and several times as long on the production host, and every timeout and request waited for it.
- `HttpxPluginBase._feed(parser, html)` parses pages from 32 KB in a worker thread, where the loop gets the GIL back every few ms. sto, kinoger, kinoking, kinox, megakino, movie2k and hdfilme's detail pages use it.
- The two hottest parsers on the production host use selectolax (lexbor, a C parser; new dependency): filmpalast's detail pages (8.4% of the Python CPU; 20 ms → 2.3 ms per page on x86) and search pages, and hdfilme's search pages (5.9% with its detail pages; 8.3 ms → 1.4 ms). They return the same results on the captured real pages of hdfilme, streamcloud, streamkiste and filmpalast.

### Perf: s.to Seasons Stop Requesting Gated Link-outs
- A Torznab search for "Series C" on s.to took 83 s and sent about 950 link-out requests: every episode and hoster of every matching series. Behind the VPN the gate let 3 of them through per pass, so 97 of 100 results kept the s.to link-out anyway.
- Whole seasons (Torznab) no longer pass the gate, since a pass unlocks 3 link-outs. Once an episode's link-outs stay gated, the next episodes return theirs unresolved for 5 min, without requests (JDownloader can still follow them). Stream requests (one episode) still pass the gate in the browser as before.

### Perf: Plugins Follow a Moved Site
- hdfilme answered every search with a 301 from `hdfilme.cafe` to `hdfilme.ceo`, one more round trip per request.
- `HttpxPluginBase` now adopts the new host as `base_url` when a request to the base host ends on another host after only permanent redirects (301/308) and with a status below 400 (`{name}_site_moved`). Temporary redirects and moves to an error page change nothing. Every httpx plugin gets this without a code change.

### Perf: Stremio Search Cache, Late Plugins and an Early Answer
- Stream requests were not cached. Production searched the same title twice within 18 s, each time a full fan-out of about 15 s and 50–270 requests. A plugin cut by the search deadline lost all its results, and every answer waited for the slowest plugin up to the 10 s search budget.
- **Search cache:** the title-matching search results of a request are cached per title, season and episode for `cache.search_ttl_seconds` (diskcache or Redis). Hoster resolution still runs on every request, since stream URLs expire and some are bound to the resolving IP.
  - **Stale-while-revalidate:** an expired entry still answers for 6 h while a background search refreshes it.
  - **Single-flight:** requests for one title share one running search.
- **Late plugins:** a plugin cut by the deadline runs on for up to `plugin_timeout_seconds` more, and its results are added to the cache entry for the next request (`stremio_late_plugins_done`).
- **Early answer:** the search answers at `stremio.search_soft_deadline_seconds` (new, default 7 s) when it has results; without results it waits for the late plugins until `plugin_timeout_seconds`, as before.
- **Circuit breaker:** a late plugin is not blamed for the cut. It counts as a failure only when it is still running at the end of its extra time; its answer reports like any other. Counting the 7 s cut opened the breaker for plugins that answered a few seconds later without hits (kinox for movies in the end-to-end test of 2026-10-04).
- `cache.search_ttl_seconds: 0` turns off all three and restores the previous behavior. App shutdown cancels background searches.

### Perf: uvloop, httptools, Eager Tasks and Python 3.14
- On the production host the event loop took 13–16% of the Python CPU (py-spy in production, `docs/plans/pi-performance.md`).
- **uvloop and httptools** are dependencies now, and uvicorn uses both when they are installed (`loop="auto"`, `http="auto"`): the event loop and the server's HTTP parser run in C. Of uvicorn's `standard` extra only these two are installed; websockets and watchfiles are not used.
- **Eager tasks:** new tasks start eagerly (`asyncio.eager_task_factory`, set in the lifespan). A task runs until its first await when it is created, so a task that never suspends (cache hit, guard) skips a trip through the loop. The whole suite also passes with every test loop eager. The startup log `event_loop_configured` names the loop (`uvloop` or `asyncio`).
- **Python 3.14:** the Docker image runs Python 3.14 (`python:3.14-slim`), whose interpreter and asyncio are faster.
  - `pyproject.toml` allows 3.12–3.14 (it was `<3.14`).
  - CI tests 3.12 (the dev container's version) and 3.14.
  - The suite passes on 3.14.8.
  - Images built from their own Dockerfile change `python:3.12-slim` to `python:3.14-slim`.

### Perf: Each Release Name Parsed Once
- On the production host guessit, which parses release names, took 25–33% of the Python CPU of a stream request (py-spy in production, `docs/plans/pi-performance.md`).
- The title matcher (title candidates, year), the release parser (quality, language) and the episode filter each parsed the same names, and the next request for the same title parsed them all again.
- `infrastructure/stremio/release_guess.py` parses a name once and caches the result: read-only, the last 4096 names.
- Measured on x86 with 120 results: 3.5 s → 1.0 s for the first request, 3 ms for the same titles again.

### Perf: Connections Stay Open Between Stream Requests
- The shared HTTP client used httpx's defaults: idle connections closed after 5 s, at most 20 kept. One stream request talks to 18–42 hosts, so every pause between two requests closed them all, and the next request paid the TCP and TLS handshakes again, one or two round trips through the VPN each. TLS handshakes were 21% of the Python CPU (`docs/plans/pi-performance.md`).
- Idle connections now stay open for 60 s, at most 20 of them (httpx's default count). With 100 kept, production showed httpcore's pool scan, which runs for every request and finished response and is quadratic in the idle connections, holding the GIL 10–20% of the time during stream requests (2% before). A connect may take at most 5 s, so a host that does not answer no longer costs the full read timeout (`http.timeout_seconds`).
- `http.http2` (`SCAVENGARR_HTTP_HTTP2`, off by default) offers HTTP/2, so the requests to one host share a connection. It needs `httpx[http2]` (h2). Measured both ways in production: the plugin searches used 22% more CPU with HTTP/2 (its framing runs in Python) and were not faster, so it stays off.

### Feat: Event-Loop Lag in the Metrics
- On the production host the Python process was busy for 34–82% of a stream request's wall time (`docs/plans/pi-performance.md`). CPU work on the event loop (parsing, TLS handshakes, logging) delays every callback, and with them the timeouts and deadlines.
- A timer every 0.5 s records how late it fires. `/api/v1/stats/metrics` shows the lag's p50, p99 and maximum over the last 5 min (`event_loop`), and a stall of 250 ms or more is logged as `event_loop_lag`. This is the yardstick for the performance plan.

### Chore: Profile Script for Stream Requests
- `scripts/stremio_profile.py` measures stream requests against a running container. Per request it reports:
  - wall time;
  - CPU seconds of the Python and Chromium processes;
  - httpx requests per host, counted from the JSON log.

  At the end it reports the event-loop lag.
- `--py-spy` adds a CPU profile per category, taken in the container: py-spy runs as root and the container needs `cap_add: [SYS_PTRACE]`.
- `--repeat` adds cold and warm passes.
- Access goes through the Portainer API or the docker CLI. Usage: `docs/plans/pi-performance.md`.

## v0.2.3 - 2026-10-04

Production fixes from the production host behind a VPN: kinoger and moflix pass their challenges once and go on over httpx, s.to's link-out gate is passed (ad layers, Turnstile and ALTCHA), and HLS-proxy streams play in Stremio Web. Each fix was verified on the production instance before the release.

### Fix: moflix Without Results Behind a Stored Clearance
- In production moflix returned 0 results on every search, without an error event. A restarted browser gets the stored clearance cookies (`ClearanceStore`), so it loaded moflix's API without a challenge and got 401 (`stealth_http_error`): the API (Laravel Sanctum) serves only requests that carry its site's Referer, and a page load sends one only in a challenge's reload. The browser fetch returned nothing, httpx never took over the session, and the host stayed in the browser memo for 30 min.
- `StealthPool.fetch_text()` asks a URL that answers the page load with an error (no challenge) once more by in-page `fetch()` from that page, the way the site's own pages call their API. Reproduced in the dev container with a second API load in one browser context (401); with the fix httpx takes over the session and the next searches run over httpx (1.4 s, 0.3 s).

### Fix: s.to Episode Streams in Production (Ad Layers, ALTCHA Gate)
- s.to gave no episode streams in production (`sto_link_gate_unsolved`). The browser's click on the hoster link box never reached it: s.to's ad script lays layers over the page (random class names, after a delay) that take the click, and Playwright waited until its click timeout ("<div …> subtree intercepts pointer events"). In the dev container the layer showed up only now and then, in production on every try.
- `StealthPool.click_through()` lets only its targets take pointer events (a stylesheet that stays until the page closes): the link box and the form of the Turnstile gate the click may bring up. The same layers cover that widget: with the stylesheet removed after the link-box click, production's gate failed with `turnstile_widget_unsolved` (the checkbox click: "<div class=\"edyaqwc\">… intercepts pointer events"), in the dev container now and then. The widget's iframe sits in a closed shadow root and inherits the value of its host; checked in Chromium with such a widget under a layer. Live: Series C S01E01 through the gate in 5.8 s, the next episodes in 0.5–0.7 s.
- With that fix production passed the Turnstile widget (`turnstile_widget_passed`), but no redirect followed (`stealth_click_through_no_target`). For a VPN IP s.to's gate is the tier `turnstile_altcha`: the same form holds an ALTCHA widget whose checkbox is required, so the submit never left the page; in the dev container the tier is `turnstile`. In our browser the widget does not verify on a click (its checkbox stays unticked). `pass_turnstile_widget()` now solves a form's ALTCHA widget before the submit, like the widget does: the page fetches the challenge from the widget's `challengeurl`, `solve_altcha()` (now also the classic format: the number whose SHA-256 of salt + number is the challenge) solves it in a thread, the payload goes into the form under the widget's name, and `form.submit()` sends it (the required checkbox would block `requestSubmit()`); a failure logs `altcha_widget_unsolved`. Verified in production with the new code: Series C S01E06 through the gate in 23.0 s (proof of work 0.3 s on the production host), the next episodes in 6.4–6.7 s.
- Production's Turnstile widget took 16–70 s on the production host, and the first wait for the redirect had 1.85 s left after it: a submitted gate now gets up to 10 s for its redirect even past the timeout, and s.to gives the browser 60 s for the gate (`_GATE_TIMEOUT_S`; the pass runs in the background, a Stremio request does not wait for it).

### Perf: httpx Goes On With the Browser's Session After a Challenge
- Production (behind a datacenter VPN) got nothing from kinoger: its site challenges the VPN IP, and after one challenge every page of the host went through the browser for 30 min, too slow for the 10 s Stremio budget on a production host.
- Measured from production's VPN IP: after a 3–4 s browser solve, plain httpx with the browser's cookies and User-Agent got kinoger's pages (HostAdmin WAF) and moflix's API (Cloudflare) in 0.3–0.4 s; curl_cffi (Chrome TLS fingerprint) did no better, so no new dependency.
- `BrowserFetcherPort.session(url)` returns the browser's cookies for a site and its User-Agent (`StealthPool`, `SolverFetcher`, `ChainedBrowserFetcher`). `HttpxPluginBase._fetch_text()` takes them over after a browser fetch, so later requests to the host run through httpx (`{name}_browser_session_adopted`). A challenge within 5 min of a takeover sends the host to the browser for 30 min as before (`{name}_browser_session_rejected`); an expired clearance is solved again.
- Covers every plugin that reads pages with `_fetch_text()` (kinoger, filmfans, serienfans, burningseries, kinox, sto). Docs: `docs/features/python-plugins.md`, `docs/plans/antibot-patchright.md` (Phase 4).
- moflix 1.2.0 runs on httpx instead of the browser: the homepage once for the site's session, then its JSON API with the headers its own app sends (`_fetch_text(..., headers=...)`); a challenged call goes through the browser once. Live in dev: 0.9 s per search after the first (4.3 s with the 2 s solve); before, every search ran in the browser, one at a time.
- A browser solve runs on when the Stremio deadline cuts the request that started it, so the next request gets the session. In production's logs every kinoger solve after a config reseed was thrown away at the 10 s cut (20 s per solve under load), so kinoger never recovered. A failed background solve is logged as `{name}_browser_solve_failed`.

### Fix: HLS-Proxy Streams in Stremio Web
- In Stremio Web every stream through the HLS proxy (VOE, Vidsonic, StreamUp, XFS hosters) ended in error 83, "Video is not supported", whenever the streaming server could not probe it. Stremio Web then reads the stream's content type with a `HEAD` request (stremio-video's `getContentType`), and the proxy answered `HEAD` with 405 without CORS headers.
- `HEAD` on `/api/v1/stremio/proxy/{stream_id}/{path}` now answers like `GET`; the server drops the body.
- `docs/features/stremio-addon.md`: Stremio Web plays `proxyHeaders` streams through a streaming server, so the old "Web: not supported" row is fixed. New notes on self-hosted streaming servers: they must reach Scavengarr's and their own public names (a VPN container's DNS and firewall prevent it), and tsaridas/stremio-docker's nginx answers disguised HLS segments (`…_000.css`) with 404.

## v0.2.2 - 2026-10-03

Reverse-proxy fix: `docker-compose.yml` trusts the proxy's forwarded headers from private networks, so stream proxy and Torznab links use `https://`.

### Fix: http:// Links Behind a Reverse Proxy
- Behind a reverse proxy the production instance built its stream proxy URLs and Torznab links as `http://scavengarr.example.lan/…`: uvicorn honors `X-Forwarded-Proto` only from 127.0.0.1, and the proxy reaches the container from the Docker gateway. Every playlist and segment request through the HLS proxy then took a 308 redirect first, and a browser would block the links as mixed content.
- `docker-compose.yml` sets `FORWARDED_ALLOW_IPS` to the private networks. Checked: a request from 172.17.0.2 with `X-Forwarded-Proto: https` gets `https://` links, without the header `http://`.

## v0.2.1 - 2026-10-03

Fixes from the first end-to-end test against Stremio Web: Vidsonic streams through the HLS proxy, moflix without its paid player, kinoger behind its new WAF page, kinox without work for episode requests, and a play check script that follows every stream to its media bytes.

### Chore: Play Check Script for Stremio Streams
- `scripts/stremio_playcheck.py` fetches every stream of a running instance the way a player does: HLS from the master to the first segments, files from the start and once in the middle, with the stream's `proxyHeaders`. The server's playback check reads only the start of a stream; this one found the Vidsonic proxy bug, moflix's paid player and the IP-bound streams of a VPN setup. Results of the 2026-10-03 end-to-end test: `docs/plans/stremio-latency.md`.

### Perf: kinox Skips Episode Requests Without a Request
- kinox cannot answer a season or episode request (its mirror API serves a series page's default episode, and films are another category), but it searched and loaded the closest hits with their mirrors before dropping them: "Series C" S01E01 loaded "Series C Paradise", "Series C Harvest" and "Series C Hearts". In the Stremio test s.to started 2 s late on that request (plugin slots busy) and was cut. kinox now returns at once for season requests.

### Fix: kinoger Returned Nothing Behind Its New Verification Page
- Since 2026-10-03 kinoger answers browsers with a "Verification..." page (HostAdmin WAF behind Cloudflare): a proof of work in a web worker, about a second, then a redirect titled "Loading <url>" and cookies `ha-waf-ticket`/`ha-waf-hash` (30 min). The stealth browser knew only Cloudflare's challenge titles and returned the verification page as the search result, so every kinoger search found 0 hits (25 of 25 in the end-to-end test).
- Both titles count as challenge titles now (`is_challenge_page`), so the browser waits for the real page; the clearance store keeps the `ha-waf-*` cookies like `cf_clearance`. Checked live: in the stealth browser the verification page cleared by itself after about a second (twice, with fresh cookies), and searches return their hits again (Movie B 3, Barbie 10, Movie A 9 cards). In that last run the WAF did not challenge again, so the wait itself is covered by the unit tests.

### Fix: moflix Served Its Paid Player as a Stream
- moflix lists a "Premium (No Ads)" video next to the hoster mirrors: HLS on `moflix-stream.day` (`/movies/<release>/master.m3u8?md5=…&expires=…`). It is moflix's paid player (5 EUR a month): the master playlist answers anyone, every variant playlist answers 403 without a paid session (also with the master's token, Referer or Origin). The playback check reads only the master, so these streams were offered as "VIDHIDE · moflix" and failed in the player. v0.2.0's entry "moflix's Own HLS Streams Were Never Played" fixed their dispatch but not this.
- The plugin drops videos named "Premium". Found by the end-to-end test against Stremio: 2 of 2 checked variants answered 403; moflix's watch page shows the paywall.

### Fix: Vidsonic Streams Did Not Play Through the HLS Proxy
- Found by the end-to-end test against Stremio: Vidsonic's master playlist lists its variant from the CDN root (`/secure/98/<id>/video.m3u8`). The HLS proxy rewrote only URIs starting with the stream's CDN directory, so the player resolved that path against Scavengarr's host and got a 404; every VIDSONIC stream (filmpalast) stopped after the master playlist.
- The proxy now rewrites every URI of the stream's CDN, in URI lines and in the `URI="…"` attributes of tags (audio renditions, keys, init segments): root-relative and protocol-relative URIs and absolute CDN URLs outside the stream's directory become `<proxy>/<stream-id>//<path>`, which the proxy joins with the CDN origin. Relative URIs stay as they are; URIs of other origins stay direct (the proxy fetches from the stream's CDN only).
- Checked live: Vidsonic, StreamUp and the XFS hosters play master, variant and segments through the proxy.

## v0.2.0 - 2026-10-02

Massive expansion of the plugin ecosystem (2 → 41 plugins), Stremio addon integration, 60 hoster resolvers, plugin base class standardization, search result caching, circuit breaker, global concurrency pool, graceful shutdown, multi-language search, and growth of the test suite from 160 to 4808 tests (4767 excluding the opt-in live tests).

### Chore: One Version Source
- The version stood in eight places as `0.1.0`: `pyproject.toml`, the FastAPI app, the Stremio manifest (Stremio compares it to notice addon updates), Torznab caps, the default User-Agent in `defaults.py` and `schema.py`, and `data/config.yaml`. `infrastructure/version.py` now reads the installed package's version (`importlib.metadata`) once; the others use `APP_VERSION` / `APP_USER_AGENT`, and the shipped config leaves `http.user_agent` at its default. A release bumps `pyproject.toml` only.

### Fix: kinoger.ru Links Went to the Vidara Resolver
- The kinoger.pw support (below) claimed the second-level name `kinoger` for the `strmup` resolver, so kinoger.ru links (kinoger's VOE tab, a redirect to a VOE mirror such as `jeremyparticipantanything.com`) were sent to the Vidara API and failed instead of following the redirect. Found by the live check: 2 of 2 kinoger.ru links were dead.
- Resolvers can now claim full host names (`supported_hosts`); the registry checks them before the second-level name. `strmup` claims the host `kinoger.pw` only, `canonical_hoster()` maps claimed hosts, and the Stremio stream converter asks for the URL host before its second-level name.

### Feature: fsst Streams Play (kinoger's First Player Tab)
- fsst was a validate-only generic DDL config whose ID pattern (`/<id>`) did not match the `fsst.online/embed/<id>/` links kinoger serves, so every fsst link resolved to nothing. On kinoger's single-player pages ("Series L", "Movie T") fsst is the only hoster.
- `FsstResolver` (`fsst.py`) replaces the config: the embed page redirects to its Kernel Video Sharing player host (incvideo1.online), whose Playerjs setup lists every quality (`file:"[360p]<url>,[720p]<url>,[1080p]<url>"`). The best quality's `get_file` link is returned; it redirects to the MP4 on the CDN and needs no headers. A 404 page (its player plays `video_error.mp4`) means gone.
- Checked live: 8 of 8 kinoger fsst links (films and episodes) resolve in 0.3–1.1 s to a 1080p MP4 that answers range requests; a `get_file` link still played after 25 minutes. Generic DDL hosters: 10 (was 11); 60 resolvers in total.

### Feature: kinoger's Own Player Resolves (kinoger.pw)
- kinoger's "Stream HD" tab plays from `kinoger.pw/e/<id>`, which no resolver handled. The page is a white-label Vidara player: it credits "Vidara" and loads its stream with `POST /api/stream` (`{"device": "web", "filecode": id}`), like vidara.so. The `strmup` resolver's Vidara path now covers the `kinoger` domain. Checked live: 4 of 4 kinoger.pw links (films and episodes) resolve in 0.4–0.7 s, playlists and segments load; an unknown id answers 404.

### Feature: gxplayer Resolver (megakino's "Stream in HD")
- megakino links every film to VOE and to `watch.gxplayer.xyz/watch?v=<id>` ("Stream in HD"), which no resolver handled. `GxplayerResolver` (`gxplayer.py`, a port of JDownloader's `GxplayerXyz`) reads the watch page's video object (`id`, `uid`, `md5`) and returns the HLS master `/m3u8/{uid}/{md5}/master.txt?s=1&id={id}&cache=1`; no playback headers are needed. Checked live: master, 720p variant and MPEG-TS segments load without Referer.
- 60 hoster resolvers now (24 individual).

### Fix: kinoger Returned No Films and Nothing From Single-Player Pages
- kinoger's player widget lists a film's stream as episode 1-1 too, in a hidden list (`<ul id="kinog-serial" style="display: none;">`, entry "1 Часть"). Since the episode parser (2026-10-01) every film counted as a series with the label "1x1", so film requests (category 2000, Stremio movies) got no kinoger results. A hidden episode list now marks a film's player.
- A page with one player has no tabs: its player container (`<div id="container-video">`) is not inside a `<section id="contentN">`, and the parser only read sections. Such pages returned no links at all ("Series L", "Movie T", "El Camino"); a lone player container is now read like a tab without a label.
- Checked on 19 live pages (12 films, 7 series, 9 of them with a single player): all parse with their kind and links now. New real-page fixtures: `detail-john-wick-kapitel-4`, `detail-wednesday`.

### Chore: Dead cineby Disabled in the Shipped Config
- cineby's API host `db.videasy.net` no longer resolves (NXDOMAIN since 2026-10-01), so each search failed and the circuit breaker kept probing it. `data/config.yaml` (the Docker image's config) disables it with `plugins.overrides.cineby.enabled: false`; the plugin stays in the code, and removing the entry brings it back when the site returns. Without `data/config.yaml` it stays enabled.

### Fix: Other Series With the Same Word Were Served as Streams
- The title filter scored a result that adds words to the requested title as a perfect match (`token_set_ratio` is 100 when one token set contains the other), so "Series C" S01E01 listed "Series A" (filmpalast), "Anime B" and "Bastard!! Heavy Metal, Dark Fantasy" (aniworld) next to the series; with autoplay, the next episode could come from the wrong series. Such a result loses `title_extra_words_penalty` (0.35) on the subset score: it passes with a matching year (0.85), not without one (0.65) or with a wrong one (0.35). Results that only drop words ("Movie A" for "Movie A: Part One") and release names of the right title (guessit's clean title) score as before. Live audit with the plugins' answers for 17 titles: the old filter kept 12 results of 10 other series for "Series C" (Series A, Series B, His Series C Materials...) and 10 wrong results for 4 other titles ("To End All War: Movie B & the Atomic Bomb", "Our Last Crusade or the Rise of a New World" for "Series G", "Anime A Log: Fish-Man Island Saga"); the new one drops exactly those.

### Fix: German Titles Without a TMDB Key Needed the Example Config
- Without a TMDB key, the German title of a Stremio request comes from Wikidata ("Series E" for "Series E"). Wikidata answers 403 to a User-Agent without contact information, and the code default `Scavengarr/0.1.0` had none (only `data/config.yaml` set the contact URL): without that file, German-titled films and series were searched under their English title only. The default is `Scavengarr/0.1.0 (+https://github.com/Strob0t/Scavengarr)` now.

### Perf: filmpalast Scrapes Real Matches Only
- filmpalast loaded the 220–320 KB detail page of every search hit of the requested kind: "Movie B" also "Fireball: Visitors from Darker Worlds" and "Into the Inferno", "Series C" S01E01 also "Series A S01E01" and "His Series C Materials S01E01". It goes through `relevant_hits()` now, comparing the series name without its episode tag, so an episode request scrapes the exact series alone. It was the largest stream source of the measurement (18 of 82 streams).

### Fix: movie2k Had No Series Streams
- movie2k lists a series' episodes as `<table data-episode-id="…">` (base64 of `<Series G>-s1e1-1`) whose mirrors are `<a href="#" onclick="return loadMirror('<url>')">`. The parser only took `http` hrefs (what film pages have), so every series came back without links, and series were labelled as films (it looked for `type=tv`, the URLs say `type=series`). Episode mirrors are links labelled `1x1 vidoza.net` now, narrowed to the requested episode; a page with episodes is a series.
- movie2k scraped the detail page of every search hit ("Movie B" also loaded "Fireball" and "Movie R"); it uses `relevant_hits()` now, like the other plugins. Its description was the page's inline script (the longest text block); script text is skipped.
- Found by the parser tests on real pages (`tests/fixtures/html/movie2k/`).

### Perf: One Site per Mirror Group in Stremio
- hdfilme, streamcloud and streamkiste are one database in three themes: same news ids, titles, order, texts and links (checked on 6 searches and their detail pages). A Stremio request ran all three and the stream dedup threw two thirds away. Plugins now declare a `mirror_group` (the three: `"hdfilme"`), and a Stremio request asks the first member whose circuit breaker is closed; the next takes over when it opens, and with no closed member all go to their breakers' probes (`stremio_mirrors_skipped`, `PluginCircuitBreaker.is_closed`). Torznab keeps the three indexers. A member with a broken parser answers empty and stays chosen; the real-page tests watch for that.

### Perf: Episode Requests Scrape the Exact Series Only
- A season or episode request scraped the 3 closest search hits, so "Series C" S01E01 also loaded "Series A" and "Series B" (series, season and episode pages plus link-outs on s.to), which the title matcher drops anyway. In the measurement s.to started 3 s late (all plugin slots busy) and was cut by the search deadline: Series C S01E01 had no stream. With a limit, `relevant_hits()` now keeps an exact hit alone; without an exact hit the 3 closest stay. kinoking filters its cards by kind before the cut, so the film "Movie O" takes no slot of a request for the series "Movie O".

### Perf: One devideosrc Fetch per Title Instead of Three
- hdfilme, streamcloud and streamkiste are three themes of one DataLife Engine database: same news ids (Movie B is 23684 on all three), same devideosrc player, same hoster links. A Stremio request ran all three, so each title's player page and `embed-links` POST went out three times at once (devideosrc answers bursts with 429, retried after 2–4 s). Concurrent `fetch_links` calls for one player now share one fetch; a caller cut by its deadline leaves it running for the others.

### Fix: Wrong Years, Genres and Descriptions on streamkiste, kinoger and megakino
- streamkiste read the year of the last related film listed under a title (Movie B: 2020 instead of 2023), and kinoger's detail parser found neither year nor genres in the live theme. The title matcher scores a wrong year −0.3 and needs a year to accept a title with extra words. streamkiste keeps the first `.release` (the film's own), kinoger reads the year from the page title ("Movie B (2023)") and the genres from the post's category list (`<li class="category">`), which also marks series by their "Serie" category. megakino's description was the last user comment (comments are "full-text" divs like the plot); it is the plot now. Found by the parser tests on real pages.

### Fix: kinoger Served the First Episode for Every Episode
- A kinoger series page holds every season in each player tab: the player script starts at the first episode, and the episodes are listed as `<span onclick="pw.player('<url>', this);" data-id="1-5">`. The plugin took the script's first URL, so "Series G" S01E05 (and with autoplay every next episode) played S01E01. Each tab now yields one link per episode, labelled `1x5 <tab>`, and a season/episode request keeps the links of that episode (4 hosters for S01E05). Found by the parser tests on real pages; the series page also counts as a series now.

### Fix: Season Pages Served Every Episode's Links
- The episode filter narrowed a result's links by their episode labels (`1x5`, `S01E05`) only when the title had neither season nor episode. A title with a season but no episode (a season pack `Show.S01...`, and with guessit 4 also a season page "Show - Staffel 1") kept the links of every episode, so S01E02 could play episode 1. Such titles drop the result on a season mismatch and otherwise narrow their links like a show page.

### Fix: Stremio Catalog Items Opened Nothing
Found in the Stremio live test (2026-10-01).
- **Items had `tmdb:` ids**: TMDB's trending and search lists carry no IMDb ids, so every catalog item got a `tmdb:<id>` id, and Stremio opens an item only through a meta addon for its id prefix; Cinemeta knows IMDb ids only, so Stremio showed "No addons were requested for this meta!" and no stream list (series had no episode list either). Catalog items now carry IMDb ids from `/{movie|tv}/{id}/external_ids` (cached 30 days); titles without one are left out. Trending and search lists cached before the update keep `tmdb:` ids until they expire (6 h, 1 h); `tmdb:` stream ids stay accepted.
- **Empty board rows without a TMDB key**: the IMDB fallback has no trending lists, but the manifest declared both catalogs as rows, so Stremio's board showed two empty "Scavengarr Trending" rows. Without a TMDB key the catalogs are now search-only (`"isRequired": true`, named "Scavengarr Movies"/"Scavengarr Series"); the search through IMDB Suggest works as before.

### Fix: moflix's Own HLS Streams Were Never Played
- moflix hands out its own HLS playlists (`https://<name>.moflix-stream.day/movies/<release>/master.m3u8?md5=…`, 1080p, German and original audio) besides hoster embeds. The registry gave them to the resolver of their domain (`moflix-stream` → VidHide), which expects an embed page: 60 of 60 failed in the live test. Streaming playlist URLs (`.m3u8`, `.mpd`) now go straight to the content-type probe.

### Fix: English Streams Listed as German Dub
- The language parser knew English words only ("English", "Sub", "Untertitel"), so s.to's label "Englisch" fell back to the plugin's default language: English audio was listed as German Dub, ranked as German and continued by autoplay in the German binge group, and its VOE link collided with the German one in the per-hoster dedup. "Englisch(en)", "deutschen" and "Untertiteln" are recognized now ("Japanisch mit deutschen Untertiteln" → German Sub).

### Feature: Mixdrop Streams Play in Stremio
- **New `MixdropResolver`** (`hoster_resolvers/mixdrop.py`): mixdrop was a validate-only generic DDL config, so every mixdrop link (36 in the live test) came back as its embed page and was dropped. The resolver reads `MDCore.wurl` from the embed player's packed setup: the MP4 on the delivery CDN, no captcha (JDownloader's download form needs one). Domains from JD2 `MixdropCo` without its dead ones; mixdrop left the generic DDL configs (23 individual + 11 generic DDL + 25 XFS = 59 resolvers). The packed-block loop of `extract_video_url()` became the shared helper `unpacked_scripts()`.
- **The player's User-Agent for checks and the HLS proxy**: the playback check and the HLS proxy fetched with the app's own agent (`Scavengarr/0.1.0`), but Stremio plays with the browser agent of the `proxyHeaders`; mixdrop's CDN answers other agents with 403, so the check dropped streams the player could play. Both send `DEFAULT_USER_AGENT` now (a stream's own `User-Agent` header wins).

### Perf: Stremio Answers Do Not Wait for Slow Hosters
- **`stremio.resolve_grace_seconds`** (new, default 4.0): once the first stream is resolved, unfinished resolutions get at most this long, instead of the rest of `stream_deadline_seconds`. 4 s keeps the DoodStream mirrors, which land 3.2–4.0 s after the first stream (3 s cut them in a test run), and cuts Dropload's captcha (7 s). Browser-resolved hosters (DoodStream mirrors such as playmogo, Dropload's captcha, Byse/Filemoon) take 3–7 s; measured 2026-10-01, Movie F had 5 streams after 4.9 s but was answered after 10.8 s, Anime G had 8 after 8.0 s and was answered after 15.0 s. `stremio_resolve_complete` logs `grace_hit`. 0 restores the old behavior.

### Perf: Stremio Saves Only the Stream Links It Serves
- The stream use case saved a `CachedStreamLink` for every ranked stream, although only the HLS proxy and `/play/` look links up: "Movie A" (73 ranked streams) spent 6 s saving links and was answered after 21.5 s. Links are now saved only for the streams served through those endpoints (`build_cache_link()`); direct video URLs need none.

### Perf: Plugins Scrape Only Real Matches
Site searches also list loose matches ("Movie E" finds "Movie E: Crossover", "Movie B" found "Fireball" and "Norman" on the DataLife Engine sites), and plugins loaded every hit's detail pages: kinoking needed 34–45 s per search (a cold movie page takes up to 15 s there), streamcloud and streamkiste 8–12 s, so in Stremio they were always cut at the search deadline. The new helper `relevant_hits()` (`infrastructure/plugins/relevance.py`) keeps the hits whose title contains every query word (case, accents, punctuation folded), else the site's first 3 (titles in another language); sto, aniworld, kinoking, kinox, hdfilme, kinoger, megakino, streamcloud and streamkiste scrape only those, closest titles first (fewest extra words), and for a season or episode request at most 3 (`SINGLE_TITLE_HITS`): "Series C" also matches "Series A", "Series B", …, whose pages and link-outs overran the search budget, so "Series C S01E01" got no stream at all. Torznab searches no longer return the loose matches either (Prowlarr and the Arr apps rejected them by title anyway).
- **Circuit breaker per plugin and category**: kinoking's movie pages take 12–17 s to answer (its series pages 1 s), so every Stremio movie request waited the whole 10 s search budget for a plugin that never delivered, while its series results reset the breaker. The Stremio plugin search now keys the breaker by plugin and category (`kinoking:2000`), so a site too slow for one content type is skipped for that type only (`stremio_plugin_circuit_open`, now logged at info). Answers without results no longer reset the breaker: kinoking answers searches without hits at once, which closed it again between its movie timeouts (measured 2026-10-01: it never opened).
- **aniworld scraped FAQ pages**: its ajax search also lists support FAQ pages and single episodes ("Anime A": 3 series, 11 episodes, 50 FAQ pages), and the plugin fetched a detail page and a made-up episode page for each, about 128 requests per search on the sister site of s.to, which gates link-outs after bursts. Only series pages are scraped now. A search without hits (empty answer) is no longer logged as `aniworld_invalid_json`.
- **cine had no links and serves downloads only**: the links API answers `{"status": false}` without the language the site's own page sends (`lang=1` German, `lang=2` English), so every title came back without links (`cine_no_links`). Links are fetched per language the search entry lists and tagged with it; only entries matching the query are scraped ("Movie B" also listed "Toy Story 4"). Every `/out/` link opens a reCAPTCHA gateway, so no resolver plays them: `provides = "download"` keeps cine out of Stremio.
- **animeloads serves downloads only** (`provides = "download"`): its Stremio results were one series preview embed per series, no episode stream, and no resolver plays the site's embeds, so every Stremio request spent a browser and 11–15 s on it for nothing.

### Fix: s.to Delivered No Playable Episode
Found in the Stremio live test (2026-10-01): every s.to stream was dropped, so German series had one stream or none.
- **The search found no series**: the site's search cards now nest one `/serie/` anchor in another with the title after the inner one, so the parser read no card and took the episode hits below them instead (series whose episode titles contain the term): "Series C" became "It's Always Sunny in Philadelphia" (episode "A Series C Day for Baseball"), and titles without such an episode hit found nothing. The parser now reads the cards' `h6.show-title`, skips the episode hits and keeps each series once (the page renders its results twice); fixtures use the live markup.
- **The official provider counted as hoster**: episode pages also link the streaming service that owns a series ("Anbieter", `data-provider-name="Provider"`, no embed; the link-out answered 410 for Series D). The plugin skips it now instead of returning an unplayable stream and spending a link-out on it.
- **Dead domain first**: `s.to` no longer resolves (NXDOMAIN; JDownloader's SerienStreamTo lists it as dead) but was the first of `_domains`; the plugin now uses `serienstream.to` and `186.2.175.5`.
- **Link-outs stayed unresolved**: s.to answers `/r?t=<token>` with a redirect only when it is opened from its episode page (or with that page's session); without `Referer` it returns a page that works only inside its player iframe, and the plugin fell back to the unresolvable link-out. The plugin now sends the episode page as `Referer` (`HttpxPluginBase._resolve_redirect(..., referer=...)`).
- **Link-outs behind Turnstile**: after bursts of link-outs from one IP the site answers them for every new session with a Turnstile widget in its player iframe, for minutes. When no link-out of an episode resolves, the plugin now lets the browser pass the gate once (`BrowserFetcherPort.click_through`: open the episode page, click a hoster, tick the widget if needed, submit; verified live: about 6 s with the widget, 1 s without) and continues in httpx with the browser's session cookies (`HttpxPluginBase._use_browser_session`), which the site trusts afterwards. The pass runs as its own task, so a search cut by the Stremio deadline does not cancel it and the next request profits; a failed pass is not retried for 5 minutes. `SolverFetcher` cannot click and returns `None`.
- **Unrelated series were scraped**: the site's search also lists other series ("Series D" finds 18, among them "Series D: Spin-off"), and the plugin fetched each one's detail page, episode page and link-outs: 7 s and about 40 link-outs per request, a burst after which the site gates link-outs behind Turnstile for a while. Only series whose title contains every query word are scraped now (else the site's top 3, for titles in another language), each once (the result page links a series twice).

### Feature: Stremio Autoplay of the Next Episode, Readable Stream List
Found in a live test with Stremio Web (2026-10-01).
- **Autoplay never picked a Scavengarr stream**: Stremio's binge watching plays the next episode's first stream whose `behaviorHints.bingeGroup` equals the current one, and Scavengarr set none. Every stream now carries `bingeGroup: scavengarr|<language>` (a German dub continues in German, at the best quality and hoster the next episode has) and, when the site has one, the release name as `filename` for subtitle addons.
- **Stream list**: `name` was the whole title plus quality ("Movie B (2023) HD 1080P", three lines in Stremio's narrow name column) and the description one long line that Stremio cut off before hoster and size. `name` is now `Scavengarr` plus the quality (`1080p`, `720p`, `4K`, …), the description one short line each for the site's own title (release name if any, which also shows a wrong match), `language · size` and `HOSTER · plugin`.
- **One stream per hoster and language** (was: per hoster): a German-sub VOE stream was dropped whenever a German-dub VOE stream resolved, so anime fans had no sub option. Series titles that already contain the episode (`… s01e01`) no longer get it twice.
- **Hoster names**: plugins label hosters inconsistently (`VOE`, `voe.sx`, `unknown`), so two VOE streams were returned as different hosters, the hoster bonus missed, and the list showed "UNKNOWN" or "VOE.SX". Hoster names are now resolver names (`HosterResolverRegistry.canonical_hoster`): a label naming a known hoster wins, then a known URL domain (mirror domains such as `d0000d.com` become `doodstream`); otherwise domain labels are reduced to their second-level part and placeholders fall back to the URL.

### Fix: ddlvalley and scnsrc Were Registered as German
- Both English sites set `default_language = "en"`, a class attribute that shadowed the base's `default_language` property while the registry reads `languages` (left at the base default `["de"]`); 15 more plugins repeated `default_language = "de"` to no effect. The two sites declare `languages = ["en"]` now (`docs/plugins.md` regenerated) and the dead overrides are gone; `default_language` stays the property returning `languages[0]`.

### Fix: Found by the Type Checker
- **Torznab reachability probe**: when a site answers `HEAD` with 405/501, the probe falls back to a ranged `GET`, but passed `timeout=` to `AsyncClient.send()`, which has no such parameter: every fallback raised `TypeError` (the test mocked `send`). The timeout now goes on the request.
- **Plugin `timeout` override on Playwright plugins**: `plugins.overrides.<name>.timeout` set an attribute Playwright plugins never read; it is reported as unsupported (`plugin_timeout_override_unsupported`) instead of silently ignored. `max_concurrent`/`max_results` apply to both bases as before.

### Chore: Type Checking in the Gate
- `[tool.basedpyright]` (`typeCheckingMode = "standard"`, `src` and `plugins`) replaces the editor-only setting in `.vscode/settings.json`, and `basedpyright` is a dev dependency, so `poetry run basedpyright` checks with the editor's rules (first step of next-steps item 4).
- The 120 findings are fixed (`src/` and `plugins/` have 0 errors in standard mode) and basedpyright runs as a local pre-commit hook with the project venv, so CI checks types too. Among the fixes: concurrency ports return async context managers, plugin request kwargs are typed for httpx, the shared browser pool and the cookie hand-over of the login plugins (`PlaywrightPluginBase._cookie_params`) are typed, and the dead YAML-plugin branch of the Stremio plugin search is gone.

### Fix: streamcloud's Fallback Domain Was a Gambling Site
- `streamcloud.my`, streamcloud's fallback domain, now serves an Indonesian online-slot site: had `streamcloud.download` failed, the plugin would have scraped it. The fallback is `streamcloud.plus` (it, `.press`, `.uno` and `.forum` redirect to the primary, so a new primary domain is followed). Found by probing every plugin domain while comparing the CUII block list (`docs/plans/cuii-coverage.md`); no other plugin domain is parked or hijacked.

### Chore: Stremio Measurement Harness in the Repository
- `scripts/stremio_measure.py` requests the 17 titles of the latency runs like Stremio does and prints latency, streams and sources per title plus a summary (`docs/plans/stremio-latency.md`). It lived outside the repository; a test pins its title set, whose id for *Movie G* was wrong for 8 runs.

### Test: Parsers Run on Real Pages
- `tests/unit/infrastructure/test_real_pages.py` runs the parsers of the five DataLife Engine sites (hdfilme, kinoger, megakino, streamcloud, streamkiste) on 13 search and detail pages captured from a live run (`tests/fixtures/html/<plugin>/*.html.gz`, 230 KB, the per-visitor `dle_login_hash` scrubbed), with values read off the pages. The hand-written fixtures of the plugin tests only show a parser what it expects; the real pages found the kinoger episode bug and the wrong years, genres and descriptions fixed above (next-steps item 5).
- `scripts/capture_pages.py <plugin> "<query>"` records every page a live search fetches (Cloudflare pages through the stealth browser) and `--fixture <page> <name>` stores one as a fixture, for the other plugins and for recapturing when a site changes its theme. It scrubs per-visitor values: DLE's `dle_login_hash`, the Laravel `csrf-token` meta and s.to's encrypted `/r?t=` redirect tokens.
- The top stream sources of the measurement are covered too: filmpalast, movie2k, aniworld, s.to and kinoking (search, film, series and episode pages; 21 more pages). movie2k's and filmpalast's pages showed the fixes above.

### Chore: Dependency Updates
- fastapi 0.128 → 0.142, uvicorn 0.40 → 0.54 and respx 0.22 → 0.23 (constraints in `pyproject.toml`), plus the in-range updates of the lock file, among them starlette 0.46 → 1.7, pydantic 2.11 → 2.13, rebulk 3.2 → 6.0 (guessit's parser), pytest 9.1, pytest-asyncio 1.4 and pre-commit 4.6. The two movieblog URL tests ran the coroutine with `asyncio.get_event_loop()`, which pytest-asyncio 1.4 no longer provides outside a test loop; they are async tests now. Starlette's test client warns that it will move off httpx (`StarletteDeprecationWarning`), nothing to change yet.
- pydantic-settings 2.10 → 2.15 and python-dotenv 1.1 → 1.2: both were pinned to their first minor release (`>=2.10.1,<2.11.0`, `>=1.1.1,<1.2.0`) since the config loader was added, without a recorded reason; they use caret constraints like the other dependencies now.
- structlog 25 → 26: the suite passes and both log formats (JSON lines, console) render as before, exceptions included.
- cryptography 46 → 50 (AES decryption of Click'n'Load link containers in `infrastructure/plugins/clicknload.py`): the suite passes.
- redis 7 → 8 (optional cache backend): redis-py 8 speaks RESP3 by default (Redis 6 or newer; the compose profile runs `redis:7-alpine`) and sets 5 s socket timeouts. Its typed async client returns `bytes | str` for `GET`: a text reply counts as a cache miss now (`redis_get_not_bytes`) instead of failing in `pickle.loads`, and the health-check PING is awaited directly. The adapter had no tests; it has unit tests with a mocked client now (no Redis server in the dev container, so no live check).
- ruff 0.15 → 0.16 with the `ruff-pre-commit` rev: no new lint findings. ruff 0.16 also formats the Python blocks of Markdown files (the pre-commit hook passes `.md` files now); `[tool.ruff.format] exclude = ["*.md"]` keeps the hand-aligned, partly pseudo-code doc snippets as written.
- guessit 3.8 → 4.4: on 249 titles and release names from a live run of the stream plugins, 7 parse differently, all for the better: a German "Staffel 1" or "1 Staffel" is read as season 1, and "Series G" keeps its last word (3.8 read "Us" as a language). Title-match decisions on these results are identical; the season pages that now carry a season narrow their links by episode (see "Season Pages Served Every Episode's Links").

### Chore: `xvfb-run` Works in the Dev Container
- `.devcontainer/setup.sh` installs `xauth` with `xvfb`: `--no-install-recommends` left it out, and `xvfb-run -a <cmd>` (headful browser tests, AGENTS.md §9) failed with "xauth command not found". The step also runs when Xvfb is present but xauth is missing.

### Chore: CI on GitHub Actions
- `.github/workflows/ci.yml` runs `pre-commit run --all-files` and the offline suite (`pytest`, live tests excluded) on every push to `staging`, on pull requests to `staging` and `main`, and on demand: Python 3.12, Poetry, cached virtualenv and pre-commit environments, read-only token. Checked in a clean clone without browsers, credentials or dev container environment: install 25 s, pre-commit 40 s, 4547 tests in 62 s; no offline test needs a real browser.
- Live smoke tests stay out of CI: GitHub's datacenter IPs get harder Cloudflare challenges than a residential network, where the addon runs.

### Chore: Dev Container Port Reachable from the LAN
- `.devcontainer/devcontainer.json` publishes port 7979 on all host interfaces (`runArgs`: `-p 0.0.0.0:7979:7979`) instead of `forwardPorts`, which only tunnels the port to the editor's machine. Stremio and other LAN clients can now reach a server started in the container with `--host 0.0.0.0 --port 7979`, for live tests against the local media stack.

### Chore: Dev Container Extensions Work in VSCodium
- `.devcontainer/devcontainer.json` drops `ms-python.pytest` (not on Open VSX; test discovery is part of `ms-python.python`) and `ms-python.black-formatter` (the project formats with ruff) and adds `detachhead.basedpyright`, the Open VSX replacement for Pylance, which VSCodium/Code - OSS may not use.
- `.vscode/settings.json` sets `basedpyright.analysis.typeCheckingMode` to `standard` (Pylance-like); basedpyright's own default `recommended` flags the whole code base.

### Fix: Code Review of `staging` (plan: `docs/plans/code-review-fixes.md`)
- **Security — HLS proxy was an open proxy (SSRF)**: `/api/v1/stremio/proxy/{id}/{path}` joined the client path with `urljoin`, so `…/proxy/<id>/http://192.168.x.x/…` fetched any internal address and returned the body. Paths that leave the stream's CDN (other scheme or host) now get `400`.
- **HLS segment errors leaked connections**: a 4xx/5xx segment response was raised without closing the streamed response; about 100 CDN errors (expired segment tokens) exhausted the shared HTTP pool and blocked every plugin and resolver. The response is closed before the error propagates.
- **Docker container did not start from a fresh clone**: `docker/entrypoint.sh` was stored in git as 100644 (the local `core.fileMode=false` hid it), so the container exited 126 in a restart loop. The executable bit is committed and `Dockerfile.prod` sets it too. Same for `.claude/hooks/*.sh` (a non-executable guard hook exits 126 and lets every command through) and `.devcontainer/*.sh`; `tests/unit/infrastructure/test_repository_files.py` guards the modes.
- **Browser dead after `docker compose restart`**: the Xvfb lock of the killed display survived in the container's `/tmp`, the new Xvfb refused to start, and every browser plugin failed. The entrypoint removes the stale lock and waits for the display socket (reproduced with a stale lock: old entrypoint no Xvfb, new one running).
- **Local start with the shipped config failed**: `data/config.yaml` set `cache.dir: /data/cache`, which is not writable outside Docker (`poetry run start --config data/config.yaml` from the README aborted with PermissionError). Now `./.cache/scavengarr`; the image keeps `SCAVENGARR_CACHE_DIR=/app/cache`.
- **Dev container on a fresh clone**: `--env-file .env.devcontainer` and the `.continue` copy needed gitignored files. `initializeCommand` now creates `.env.devcontainer` from the new `.env.devcontainer.example`, the copy is skipped when the file is missing.
- **Docker build hygiene**: the unused root `Dockerfile` (invalid `CMD`, picked by a plain `docker build .`) is removed; `.dockerignore` keeps `.venv`, `.devdata`, `.env*` (with `GH_TOKEN`), tests and docs out of the build context; compose runs the service with `init: true` so orphaned Chromium processes are reaped.
- **ruff pinned to the pre-commit version** (0.15.0) so the edit hook and pre-commit format identically.
- **aniworld found no episodes**: episode URLs were built as `/anime/<slug>/staffel-N/episode-M` without the `/stream/` segment (404 live, the correct URL answers 200 with hosters), so every series/anime episode request returned nothing — 0 aniworld results in all Stremio measurements. A season without episode now starts at that season's first episode (aniworld and fireani; before, season 1 was used).
- **kinox returned the wrong episode**: its mirror API only serves a series page's default episode, but the result was presented for any requested season/episode. Series are now skipped for season/episode requests (movies unaffected), and the mirror AJAX calls of all entries share one concurrency limit (before: a new limit per entry, ~5 × N parallel requests).
- **megakino**: pagination started at `search_start=0`, which DLE serves as page 1 again, so the first 20 hits were scraped and returned twice. Season/episode requests skip pages of other seasons ("X - Staffel N") before fetching them, and a page without the requested episode no longer falls back to all of its episodes.
- **Resolvers marked live files dead**: 7 resolvers treated `"error"` anywhere in the final URL as an error redirect, so "The.Terror.S01E01.mkv" or `serienstream.to/…/the-terror` were dead (and cached as dead for 15 min). One shared `is_error_redirect()` now checks path segments and query keys only. nitroflare, uploaded, 1fichier and mixdrop links with a file name or extra parameters after the ID (`/view/<id>/Movie.mkv`, `?<id>&af=…`) were rejected as invalid URLs; alphaddl's `"404"` and 1fichier's `"not found"` offline markers matched live pages.
- **Grab failed with 500 for titles outside Latin-1** (en dash, Polish/Czech letters, CJK): `/download/{job}` put the raw title into HTTP headers. `filename` is now ASCII with the real name in `filename*=UTF-8''…`, `X-CrawlJob-Package` is percent-encoded.
- **`.crawljob` injection**: `packageName`, `filename`, `comment` (scraped descriptions), `downloadFolder` and `downloadPassword` were written without removing line breaks, so a description containing `\ndownloadFolder=/x` added a JDownloader key. Line breaks are collapsed to spaces.
- **Stremio episode filter dropped multi-episode releases**: guessit returns lists for `S01E01-E03` / `S01-S03`, and `[1, 2, 3] != 2` removed a release that contains the requested episode. Membership is checked now. `StreamSorter.sort()` also dropped each stream's `title` (the stream-name fallback) because it rebuilt the objects field by field.
- **XFS form POST to the wrong host**: when a rotating mirror redirected the embed page, the `/dl` form was posted to the original host (redirected, re-sent as GET without the form) and extraction failed; the CDN `Referer` also named the wrong page. Both now use the host/page that actually served the form and player.
- **Packed player JS in base 62 was not unpacked**: the unpacker decoded words with `int(word, base)`, which fails above base 36, so the packer's default "Normal" (base-62) encoding came back unchanged and XFS/Filemoon extraction found nothing. Words are decoded with the packer's own digit set now.
- **moflix returned its own title page as the link** when a title had no videos (or the detail API failed), and returned every episode's videos for an episode request. Titles without videos give no result now, and season/episode requests keep only videos with that `season_num`/`episode_num`.
- **serienfans episode results were titled "Show - E5"**, which Sonarr cannot parse, so every per-episode result was rejected. Titles are `Show S02E05 - Episode title` now.
- **movie4k was a stale copy of megakino_to** (same "/data" API): no season/episode filter (a series request returned every episode's streams), deleted streams were returned, a list-shaped `tmdb.movie` raised `AttributeError` and silently dropped the title, and Torznab quality subcategories were sent as genre filters (2040 Movies/HD searched only comedies). Both plugins now share `DataApiPluginBase` (`infrastructure/plugins/data_api.py`) and only set their name and domains.
- **sto (s.to)**: a full-series search (no season) only returned season 1; it now covers every season up to the result limit. The series of a search are processed in parallel (bounded) instead of one after another, and the hoster redirects of an episode resolve together.
- **cine**: one non-JSON answer (e.g. a DDoS-Guard page with status 200) raised in `resp.json()` and aborted the whole search. The three API calls now share `_post_api` (base `_safe_fetch` + `_safe_parse_json`), a failing title is skipped and logged, and titles without hoster links give no result instead of cine.to's own page as the "link".
- **dataload stopped working until restart once its session expired**: the login state was never reset. A search answered as for a guest (`data-logged-in="false"`) or rejected (expired CSRF token) now logs in again and retries once, and the login check only accepts an `xf_user` cookie of data-load.me (the shared client can hold other XenForo forums' cookies).
- **Search terms with `&`, `+` or `#` were cut off or split** in animeloads, cineby, ddlvalley and scnsrc: the query went into the URL unencoded ("Fast & Furious" searched for "Fast "). It is now `quote_plus`-encoded. filmpalast puts the term into a path segment: it is `quote`d there, and `/`, `?` and `#` become spaces (the site answers an encoded `/` with 404 and finds "Wer ist Hanna?" only without the `?`).
- **filmpalast returned at most 32 results**: only the first search page was read. The plugin now follows `/search/title/<term>/<n>` while a page links "vorwärts", up to `_max_results` (32 pages).
- **GoFile kept a token the API had dropped**: every GoFile link counted as dead until the 25-minute cache expired. A 401 `error-wrongToken` now renews the guest token once, and concurrent resolves share one guest account (GoFile throttles account creation with 429). Known issue found on the way: GoFile currently refuses guest lookups altogether (401 `error-notPremium`, its website adds a token from an obfuscated script); that is logged as `gofile_guest_access_refused` and not retried.
- **burningseries scraped scam clones and could not deliver streams**: bs.to is gone, so the plugin fell back to `burning-series.io`/`.net`, clones that swap the player for their own redirect (JDownloader lists `.io` as scam). It now uses the genuine domains (`burningseries.ac`, `bs.cine.to`, `burningseries.sx`). The hoster links sit behind reCAPTCHA v2, so the plugin now declares `provides = "download"` (no longer queried for Stremio, where its pages never resolved); its results are pages for JDownloader's BsTo crawler. Episode searches link the episode page from the German season page as `Title S02E02` (the old `/serie/<slug>/2/2` URL does not exist; episodes without hosters give no result), season searches the German season page as `Title S02`.
- **aniworld fell back to a scam copy**: `aniworld.info` imitates the site with ad pages (JDownloader, 2026-09-09) and was the plugin's second domain. The plugin now uses `aniworld.to` only. A check of all plugin domains against JDownloader's fake/scam notes found no other hit; the plugin guide and AGENTS.md now require genuine domains.
- **Exception logs of the standard library were lost**: the logging queue handler deep-copied every record, which fails on tracebacks (and on log fields that cannot be copied), so e.g. uvicorn's "Exception in ASGI application" only produced "--- Logging error ---". Records are now handed over as a shallow copy, and stdlib tracebacks are rendered to text (`exception` field; the JSON format used to show a repr of the `exc_info` tuple).
- **Plugin registry re-imported plugin files on every name lookup, and one broken file broke Stremio**: `list_names()` executed all plugin modules again on every call, on the event loop (`/healthz` calls it on every probe), and a plugin file that failed to import made `get_by_provides()` raise on every Stremio request. The registry now imports each file once on first use and caches instances and metadata; failing files are logged and skipped, duplicate names logged (`plugin_name_duplicate`).
- **Concurrency pool fair share was not enforced under load**: a slot counted against the request only after the global semaphore was acquired, so all tasks of one request queued behind a full pool passed the fair-share check and later took more than their share. The share is now reserved before waiting (and given back when a waiter is cancelled).
- **Secrets in logs**: the TMDB `api_key` appeared in retry logs and in rendered httpx errors ("… for url '…?api_key=…'"), the Torznab `apikey` in every request log (`query`), a Redis password in the Redis URL. A structlog processor now masks secret parameters and URL passwords in every log field, tracebacks included, for structlog and stdlib records alike.
- **Hoster resolution had no overall time bound, and timeouts marked links dead**: a resolver's requests each had their own timeout (mostly 15 s), so one resolution (e.g. a `/play` click) could hang for a minute; `http.timeout_resolve_seconds` only applied to the registry's own requests. `resolver.resolve()` now gets that time in total. A timeout or network error is no longer cached as a dead link for 15 minutes.
- **ALTCHA solving had no bound on site-supplied parameters**: a hostile or broken challenge (huge `cost`, long or non-hex `keyPrefix`, huge `keyLength`) could pin a worker thread for hours (`asyncio.to_thread` cannot be cancelled). `cost`, `keyLength` and `keyPrefix` are now validated, and the solver gives up after 20 s.
- **Failed cache writes were swallowed or broke the whole answer**: a Torznab item whose CrawlJob could not be saved was still returned (the grab then answered 404); now it is dropped and logged (`crawljob_save_failed`). In Stremio one failed stream-link save failed the whole request; now only streams that need the link (HLS proxy, `/play/`) are dropped (`stremio_stream_link_save_failed`).
- **CrawlJob lifetime was hard-coded to 1 hour** (AGENTS.md promised a configurable TTL): new key `cache.crawljob_ttl_seconds` (default 3600, > 0) sets both the cache entry and the job's `expires_at`. `CrawlJobFactory(default_ttl_hours=…)` became `CrawlJobFactory(ttl_seconds=…)`.
- **API rate limit could stall playback**: the 120 requests/min per IP also counted HLS proxy requests (a player loads dozens of segments at start, then one every few seconds) and health probes. Both are exempt now. The limiter also forgets clients idle for a minute (it only evicted empty entries, which a client that never came back does not leave).
- **Link validation downloaded whole files and kept every result forever**: the GET fallback read the full response body (for a direct download link the file itself); it is now streamed and only the status is read. Expired validation results and unreachable-host marks are pruned every 1,000 validations.
- **HLS manifest cache grew forever**: expired manifests were only removed when the same URL came again, and rotating manifest URLs (tokens in the query) never do. The cache now holds at most 512 manifests (expired ones are dropped first, then the oldest).
- **Circuit breaker let every request through while half-open**: after the cooldown all concurrent Stremio requests hit the (probably still dead) plugin and paid its full timeout, not just one probe. Now a single probe is in flight; the others skip the plugin until it reports, and a probe that never reports is replaced after the cooldown.
- **Plugin scores could vanish**: the score index was only written when a new (plugin, category, bucket) appeared, so it expired 30 days later while the snapshots were still updated, and concurrent updates could drop each other's index entries. The index is now rewritten with every update, under a lock.
- **Redis ignored `cache.max_concurrent`**: the factory hard-coded 50 parallel operations for Redis. The configured value now applies to both backends; with the default (10) Redis gets fewer parallel operations than before, so set `cache.max_concurrent: 50` to keep the old Redis behaviour.
- **Own-host link resolution was unbounded**: `_resolve_result_links()` (filmfans, serienfans) and `_resolve_own_links()` (kinox, byte) followed every `/external/…` redirect at once, up to hundreds of requests to the plugin's own, usually Cloudflare-protected host. At most `_max_concurrent` run at once now.
- **Playwright driver leaked after a browser crash**: when a plugin's own (standalone) Chromium disconnected, the plugin launched a new one but left the old Playwright driver process running. It is stopped now; the shared pool's driver stays with the pool.
- **moflix bypassed the Turnstile solver**: its `_wait_for_cloudflare()` override polled for the XSRF-TOKEN cookie in a sleep loop that swallowed every error and never called the base solver (Turnstile click, clearance memo). It now solves the challenge through the base class and then waits for the cookie with a condition (`moflix_xsrf_cookie_timeout` when it does not appear); live smoke test passes.
- **Scraped URLs could reach the local network (blind SSRF)**: link validation, hoster resolution, playback checks and redirects followed whatever a scraped page pointed to, including `192.168.x.x`, `localhost`, `169.254.169.254` or Scavengarr itself. The shared HTTP client now refuses every request and redirect hop to a non-public address (`private_address_refused`); hostnames are checked after a DNS lookup, so a blocked domain that resolves to the router is refused too. The solver sidecar (`playwright.solver_url`) stays reachable.
- **`moflix-stream` claimed by two resolvers**: VidGuard and Vidhide both listed it and registration order decided. VidGuard (offline per JDownloader, including the former moflix-stream.day) no longer claims it; moflix-stream.click is Vidhide. The registry now keeps the first resolver for a domain claimed twice and logs `hoster_domain_conflict`.
- **Removed the unused stream-time liveness probe**: `probe.py` (`probe_urls_stealth()`) only ran without a hoster resolver, and the composition always wires one; resolution is the liveness check. Removed with it: `StealthPool.probe_url()`, the `probe_fn` parameter of `StremioStreamUseCase`, the always-empty `probe` section of `/api/v1/stats`, and the config keys `stremio.probe_at_stream_time`, `probe_timeout_seconds`, `probe_stealth_enabled`, `probe_stealth_concurrency` (old configs still load, the keys are ignored). `probe_concurrency`, `max_probe_count` and `probe_stealth_timeout_seconds` stay (resolution and `StealthPool`).
- **ddlspot/ddlvalley lost every result on one slow page, ddlvalley paged without limit**: a navigation timeout on search page N threw away pages 1..N-1; now the pages already collected are kept (`ddlspot_search_page_failed`, `ddlvalley_search_page_failed`). ddlvalley also stops at `_MAX_PAGES`. burningseries no longer crashes on a production-year text without a year.
- **Plugins bypassed the base fetch helpers** (per-plugin timeout and User-Agent on the shared client, Cloudflare browser fallback, uniform error logging): page requests now go through `_fetch_text()` / `_safe_fetch()` in burningseries, kinox (search, detail and mirror AJAX), sto (search, detail and episode pages; the `/r?t=` link-outs resolve through `_resolve_redirect()`), and megakino, streamcloud, streamkiste, hdfilme and movie2k (search, browse and detail pages; the DLE search POSTs go through `_safe_fetch()`, and megakino's `yg` token only counts once its request succeeded, so a failed one is retried).
- **myboerse never found anything, and neither XenForo forum filtered by category** (checked live): myboerse's search POST lacked the session's CSRF token (`_xfToken`), which the forum answers with HTTP 400, and it only knew `page-N` pagination (search pages use `?page=N`). On both forums `c[nodes][]` was ignored because XenForo applies it only with `search_type=post`, so a movie search also returned tutorials, music and audiobooks. The two plugins were copies; they now share `XenForoPluginBase` (`infrastructure/plugins/xenforo.py`: login with an own-host session cookie, CSRF token, one re-login, `search_type=post`, pagination, thread links) and only set their domains and forum map. The forum maps are rebuilt from the live forum index: software was labelled 5020 (TV/Foreign) and is now PC (4000/4030/4040/4060/4070), consoles 1000 (dataload filed them as PC games), mobile games 4060/4070 (myboerse filed them as consoles), PC games 4050, foreign-language films 2010, lossless audio 3040, music videos and concerts 3020, sport 5060, myboerse's XXX section 6000; missing subforums are added (dataload's foreign films, myboerse's foreign comics, English audiobooks, Cydia apps). A category without a forum returns `[]` without a request, a child category the forum does not tell apart uses its parent's forums, and results of unknown forums are labelled 8000 instead of a forum-name guess. myboerse no longer returns its `/xtra/` link (an affiliate redirect to a fixed Rapidgator file) as a download.
- **Animated films and documentaries were missing from movie searches** (megakino, streamcloud, streamkiste, kinoger, movie2k, hdfilme): films with the genre Animation/Anime were labelled 5070 (TV/Anime), hdfilme's documentaries 5080 (TV/Documentary) and its horror and animation films 2040 (Movies/HD), so a movie request (Stremio always sends 2000) dropped them. Films are now 2000 whatever the genre; series 5000, anime and animation series 5070. The six plugins carried copies of the same category code, which let Audio/PC/Books/Other requests through unfiltered and ignored 2070/2080/5090; they now use the shared `categories.py` (`served_category()`, `filter_by_category()`, `stream_category()`): a category the site does not serve returns `[]` before any request, a child it does not tell apart (2040) is answered with its parent's results. `_category_matches()` of both plugin bases is `categories.category_matches()`.
- **filmpalast and kinoking labelled results with the requested category**: a series request returned filmpalast's films labelled 5000; kinoking answered Audio/PC requests with films and Books/Other with series. Results now carry the site's label (filmpalast lists series per episode, `... S03E08` is 5000, everything else 2000; kinoking: the card type), other categories return `[]` without a request, and filmpalast filters by category and season/episode on the search titles before it loads detail pages.
- **nima4k labelled results with the requested category and never filtered**: a movie request returned series and concerts labelled 2000, and without a category every result was 2000 (the site's listings carry genre pills, not the section names the plugin looked for; documentaries were mapped to 5070, TV/Anime). Results are now labelled from the release (checked live): season packs (`Show.S03...`, "Staffel") 5000, animation series 5070, concerts 3020, sport 5060, everything else 2000 (documentary films included), filtered by the requested category; a category without a section returns `[]` without a request.
- **scnlog labelled results with the requested category and missed German releases**: every result carried the request (or 2000), and a movie request only searched `movies/`, while scnlog files German and other non-English films and episodes under `foreign/`. Results are now labelled by their section (checked live: the release URL starts with it): movies 2000, tv-shows 5000, foreign episodes 5020 and films 2010, games 4050, apps 4000, pda 4040, music 3000, ebooks 7000, xxx 6000. A request searches every section holding its category in parallel (films: `movies/` and `foreign/`) and keeps only matching rows before loading detail pages; categories without a section (e.g. consoles) return `[]` without a request. The unused `categories` attribute is gone.
- **scnsrc labelled results with the requested category, and applications as TV/Foreign**: a request's category replaced the post's own (a movie request returned games labelled 2000); applications were 5020, console games PC games (4000), concerts and music videos plain audio, unknown categories films. Posts keep their site category: PC games 4050, consoles 1010-1180 (NDS, PSP, Wii, Xbox 360, PS3, Wii U, PS4), applications 4000/4030 (macOS)/4060 (iPhone), concerts and music videos 3020, unknown 8000. A request searches the sections holding its category (PC: applications and games), keeps only matching posts before their pages are loaded, stops after 100 result pages (it paged until an empty page), and categories without a section return `[]` without a request.
- **warezomen labelled every row with the requested category (or 2000)**: the results table's Type column was never read. Rows are now labelled by it (checked live: Movie 2000, TV 5000, Game 4050, Software 4000, Music 3000, Other 8000), a request keeps only its rows (the page cap counts those), and categories the site has no type for return `[]` without a request.
- **crawli found nothing, and never more than films**: the site now sends its pages base64-encoded for a script to write, so the parser saw no results (0 for every query, checked live); it also only accepted film rows (`a.sres3`), so TV, music, apps and games searches always came back empty, and every result carried the requested category (apps were 5020). The page is decoded, rows of every section are parsed and labelled by their section class (sres1 apps 4000, sres2 music 3000, sres3 film 2000, sres5 games 4050, sres7 serie 5000, unsorted 8000; episode titles are TV even where filed as films). A PC request searches apps and games, a TV request every section (`/serie/` only lists series pages, the episodes are filed as films), results are filtered by the requested category, and categories without a section return `[]` without a request.
- **mygully and boerse labelled every thread 2000**: series, music, books and games alike, and XXX/Other requests searched the Video forum. Threads are now labelled by the forum searched (Video 2000, series by their title 5000, Audio 3000, Text/Dokumente 7000, Games 4050), filtered by the requested category, and categories without a forum return `[]` before the login; console requests too, since the Games forums hold PC and console games alike. Not checked live (both need credentials). `categories.is_series_title()` (scene `S01E02`/`S03` tokens, "Staffel") replaces the series regexes of nima4k, crawli and scnlog; scnlog now also labels foreign season packs 5020.
- **ddlvalley labelled every post 2000, ddlspot dropped games from PC requests**: ddlvalley now labels posts by the WordPress category searched (games 4050, apps 4000 instead of 5020 TV/Foreign; site-wide posts by their title, series 5000, otherwise 8000) and searches apps and games for a PC request. ddlspot labels games 4050 (were 4000 like software, and a PC request kept software only), unknown types 8000 (were films), filters rows by the requested category while paging (child and unmapped categories used to return every row). Categories without a section return `[]` before the browser starts. Not checked live (Cloudflare Turnstile).
- **byte labelled episodes, software, lossless music and more as films**: its category map knew a third of the site's categories and fell back to 2000, audiobooks were 7020 (EBook), documentaries 5000, consoles PC games, programs 5020. The map now covers the site's menu (checked live: films 2000, English films 2010, series/season packs/episodes 5000, documentaries 5080, PC games 4050, consoles 1000/1030/1180, programs 4000/4030/4070, music 3000, lossless 3040, concerts 3020, audiobooks 3030, books 7000, XXX 6000, unknown 8000). A request sends the site category only where one group holds the whole family (films, TV, books, XXX), otherwise it searches every group; rows are filtered by the requested category before their pages load, and categories the site lacks return `[]` without a request.
- **hdsource, jjs, movieblog and serienjunkies answered categories they do not have**: their filters only knew movie and TV requests, so Audio/PC/Books/Other requests got every film and series, and the TV-only serienjunkies answered movie requests with series. They now return `[]` without a request for such categories, filter with `categories.category_matches()` (a season request means series), and hdsource labels games 4050 (was 4000). jjs and movieblog carried the same copied `_filter_by_category`; it is gone, as is the unused `categories` attribute of serienjunkies.
- **sto labelled series with the requested TV category and with quality codes**: a 5070 request labelled every series anime, and genres were mapped to quality subcategories (drama 5030 TV/SD, horror 5040 TV/HD, fantasy 5050). Series are now labelled from their genres alone (anime/animation 5070, documentaries 5080, otherwise 5000) and filtered by the requested category (an anime request no longer returns every series); non-TV requests return `[]` before any request.
- **Removed `is_tv_category()` / `is_movie_category()`** from `infrastructure/plugins/constants.py`: the plugins answer category requests with `categories.py` now and nothing used them any more.
- **megakino_to and movie4k answered an anime request with every series**: `DataApiPluginBase` filtered by the API's film/series type only. Results are now filtered by the served category (`categories.py`), so TV/Anime and TV/Documentary requests keep their series.

### Docs: README Overhaul, CONTRIBUTING, Docker Compose, Generated Plugin List
- **README rewritten for self-hosters** (Stremio first, Arr indexer second): header with badges, "How it works" Mermaid diagram, features grouped by area, Docker Compose quick start, step-by-step Stremio/Prowlarr setup, table of the most important settings, FAQ/troubleshooting, disclaimer, acknowledgements, and an open "How Scavengarr is built" section (largely AI-written, under strict review, TDD, Clean Architecture, quality gates). It names no sites.
- **`CONTRIBUTING.md`**: development setup, tests, code style, project structure, tech stack, plugin and resolver guides, branch/commit rules, AI-assisted contributions (moved out of the README).
- **`docker-compose.yml`**: builds `Dockerfile.prod` locally, mounts `data/` and `plugins/`, keeps the cache in a named volume (the image runs as a non-root user), `shm_size: 1gb` for Chromium; optional profiles `solver` (Byparr) and `redis`.
- **`docs/plugins.md`** is generated from the plugin metadata by `scripts/generate_plugin_list.py` (website, mirrors, content, engine, languages, disclaimer on top); `tests/unit/infrastructure/test_plugin_list_doc.py` fails when it is outdated. Regenerate after adding or changing a plugin.
- `pyproject.toml` description updated.

### Feature: Stremio Answers Within a Deadline, Only Playable Streams
Measured with a Stremio-style harness (18 titles, every returned stream played): answers took 17–38 s (median 19.8 s) and 24 % of the returned streams did not play. Plan and results: `docs/plans/stremio-latency.md`.
- **`plugin_timeout_seconds` is a search budget from the request start** (new default 10 s, was 30 s per plugin). Plugins queue for concurrency slots (two query variants × all plugins), and each plugin's timeout used to start only when it got a slot, so the search alone took up to 35 s. Plugins still running at the deadline are cut, queued ones skipped. A timeout counts for the circuit breaker when the plugin had at least half the budget.
- **New `stremio.stream_deadline_seconds`** (default 15 s): overall budget per stream request. Hoster resolution stops there (at least 2 s after the search) and returns what is resolved; unfinished resolutions are cancelled. `stremio_deadline_ms` stays unused.
- **Per-hoster resolution in rank order**: hosters resolve in parallel, the streams of one hoster one after another until one works, so the best *working* stream per hoster is returned; before, only the best-ranked link per hoster was resolved and the hoster disappeared when that link was dead. Resolving all candidates at once is not an option: the burst of connections to dozens of CDNs made the home router block the machine like a port scan.
- **Playback check (`stremio.verify_streams`, default on)**: `HosterResolverRegistry` fetches the first bytes of every resolved URL with its playback headers (`check_playable`); error status, HTML or an HLS answer without `#EXTM3U` drop the stream, and the result is cached like a failed resolution. Catches e.g. mixdrop/supervideo pages returned instead of video, CDN 404/502 and expired TLS certificates.
- **Circuit breaker cooldown doubles** with every failed half-open trial (60 s → … → 1 h), reset on success.
- **`data/config.yaml`**: `plugin_timeout_seconds: 10`, `stream_deadline_seconds: 15`, `verify_streams: true`. Measured cold (18 titles): answers within 15.1 s (was up to 38.5 s, median 19.8 s), 96 % of the returned streams play (was 76 %), 17/18 titles with a playable stream as before; 12 s / 17 s gave the same streams 2 s later. Behind AIOStreams set the addon timeout to 17000 ms (`docs/features/stremio-addon.md`).

### Fix: A Network Blip No Longer Hides Hosters for 15 Minutes
- **Link validation backs off on unreachable hosts** instead of skipping them for a flat 15 minutes: the first connection failure skips a host (and the failed URL) for 60 s, every further one doubles that up to 15 min, and the first answer from the host resets it. Measured 2026-09-29: a 40 s outage of the local network marked voe.sx, vinovo, kinoger, fsst and the moflix hosts unreachable, and every Stremio request of the next 15 minutes came back without them (anime and series with zero streams).

### Chore: AGENTS.md Is the Single Agent Instruction File
- **`CLAUDE.md` merged into `AGENTS.md` and removed**: one instruction file for every coding agent (AGENTS.md convention). The OpenSpec-managed block stays at the top of `AGENTS.md` (`openspec update` rewrites it); the former `CLAUDE.md` content follows unchanged apart from its title and self-references. Claude Code (v2.1.277+) reads `AGENTS.md` automatically when no `CLAUDE.md` exists; `.claude/` (hooks, skills, settings) is unaffected. References in the commit skill, `openspec/project.md` and the integration test plan now point to `AGENTS.md`; historical CHANGELOG and plan entries keep the old name.

### Chore: Editor and Tool Output Hygiene
- `.vscode/settings.json` sets `"files.eol": "\n"`: VS Code saves new files with LF, matching `.gitattributes` and the `mixed-line-ending` hook.
- `.gitignore` ignores `.playwright-mcp/` (snapshots, console logs and screenshots written by the playwright-mcp browser tool).

### Fix: No Site Pages or Login Pages as Download Links
- **kinox**: the mirror AJAX (`/aGET/Mirror/...`) now answers JSON with the iframe HTML escaped inside (`"Stream": "<iframe src=\"\/redirect\/<hash>\"...>"`); the plugin found no iframe and fell back to its own detail page as the "download" link, which link validation accepted (200) for Torznab. It now reads the JSON, makes relative iframe URLs absolute, resolves kinox's own `/redirect/<hash>` links to the hoster (`_resolve_own_links`) and drops results without a hoster link. Live the redirects currently loop on a JavaScript "Verifizierung" page, even in a real browser with the site's own mirror click, so kinox returns no results until the site fixes them (KNOWN_ISSUES).
- **filmpalast** skips hoster account pages listed as streams (`https://vixeo.io/login` for "Vixeo HD").
- Kept on purpose: movie4k's `cuty.io` / `clk.asia` shortener links and `streampalace.org` pages. JDownloader decrypts both shorteners (`CutyIo`, `ClicksflyCom`), so they are useful in Torznab crawljobs; the Stremio path already drops streams no resolver can play.

### Feature: VOE Mirror Domains, Vixeo Resolver, Thumbnail-Safe Capture
- **VOE mirror domains**: VOE rotates its domains; the resolver now exposes 134 of them (`hoster_resolvers/_voe_domains.py`, from JD2 `VoeSxCrawler` plus `goofy-banana` and `jeremyparticipantanything` seen on plugin sites). Live: a goofy-banana link resolves in 0.7 s; before, no resolver was found. JD2 also lists three domains that Scavengarr maps to Vidhide; they stay there so each domain has one owner.
- **Vixeo resolver** (`vixeo.io`, Vidsonic's new player): the page builds the signed HLS URL in JavaScript, so the stream comes from the browser capture. Live: 4.3 s, playable without headers; dead IDs fail in 0.2 s.
- **Capture ignores seek-preview playlists**: `capture_media` took vixeo's `thumbnails.m3u8` (a playlist of JPEGs) for the stream. URLs containing `thumbnail`, `sprite` or `preview` no longer count.
- Checked and dropped from the uncovered list: `streamdav.com`, `upload.do` and `voe-stream.space` are parked domains (all redirect to `router.parklogic.com`), `odysseusa.cc` answers 404 for its video.

### Feature: FireStream and Playmate Resolvers
- Two hosters from the plugin link scan had no resolver. Both are ports of JDownloader plugins and need no browser:
  - **FireStream** (`firestream.to` → `firestream.site`): the embed page carries a token that `/api/videos/<id>/resolve` trades for a signed HLS URL, on the host that served the page only. Live: 1.0–1.2 s (the browser capture took 14.7 s).
  - **Playmate** (`playmate.to`): `/api/video-meta` checks the file, `/api/s` returns the HLS master; the API rejects non-browser user agents (403). Live: 0.5–0.6 s, dead file recognised in 0.2 s.
- Not implemented, documented instead (see KNOWN_ISSUES): gxplayer bans this network (redirect loop to `banned.php`), embedrise serves only a placeholder `video.mp4` (404) for every video, frdl.to (DDL) sits behind the same ad-tracker JavaScript redirect as vidmoly.

### Fix: Hoster Mirrors (dr0pstream, streamhls, Byse Domains) and Captcha-Gated Players
- **Mirror domains** from the plugin link scan: `dr0pstream.com` → dropload (JD2 `DroploadIo`; 13 of ~190 scanned links), `streamhls.to` → savefiles (same player, image proxy `img.savefiles.com`), and 14 Filemoon/Byse domains (`bysezejataos`, `byse`, `filemooon`, …; JD2 `FilemoonSxCrawler`) now reach their resolver. Filemoon exposes `supported_domains` for the first time.
- **Captcha-gated XFS players**: a page without a video URL but with a Turnstile/reCAPTCHA widget in front of the player (dr0pstream's play button) goes to the stealth browser, whose click passes the widget. Live: dr0pstream → dropcdn HLS master in 0.7–5 s. The dropcdn servers were unreachable from the test network, so playback itself is unverified.
- **Filemoon skips hopeless browser runs**: before starting the browser the resolver asks the Byse details API; a gone video (404) or an embed restricted to other domains (403 `embedding … not allowed`) fails in 0.2 s instead of 18 s of clicking. A Cloudflare 403 is not taken as a verdict.

### Fix: Vidara Streams via the JSON API
- vidara.so and its mirror vidaraa.cc serve the StreamUp backend through a JSON API (`POST /api/stream`, JD2 `VidaraTo`), not the page/AJAX flow the Strmup resolver used, so every vidara link failed (`strmup_no_hls_url`) and vidaraa was not dispatched at all. Vidara hosts now use the API; file IDs may carry an `/e/` prefix and be 12+ characters. Live: both links → HLS master in 0.3 s.

### Test: Live Stremio End-to-End Use Case
- `tests/live/test_stremio_e2e_live.py` (opt-in, `-m live`) starts the real app in-process (composition lifespan, `httpx.ASGITransport`), asks for the streams of Movie B and Series D S01E01 and plays them like Stremio: `proxyHeaders`, HLS proxy or direct CDN, master → media playlist → first segment. Passes when one stream delivers media. Links are scraped fresh on each run. Live run after the resolver fixes: film 6 of 7 streams play (supervideo's CDN is the exception), episode 2 of 2; both tests pass in about 2 minutes.

### Fix: Veev Streams Failed to Play in Stremio
- veevcdn binds the stream token to the User-Agent that resolved it. The resolver used the app client's UA (`Scavengarr/0.1.0`), Stremio played with the browser UA from `proxyHeaders`, and every veev stream answered 403 (found by the end-to-end Stremio run: resolved, listed, unplayable). The resolver now resolves with the browser UA and returns it in `ResolvedStream.headers`, which `build_behavior_hints` passes on (live: 206 with the returned headers).

### Fix: GoodStream Links on goodstream.one
- GoodStream moved from `.uno` to `.one` and links now look like `/video/embed/4Ky4/680x420` (short IDs); the resolver rejected them as `invalid_url`. The config accepts `/video/embed/<id>` next to the 12-character XFS IDs and knows the new dead-file page ("No such file").

### Fix: Cloudflare-Protected Hoster Players via Browser Capture
- **XFS video hosters, DoodStream and SuperVideo fall back to the stealth browser** when the embed page answers with a Cloudflare challenge: savefiles, bigwarp, streamwish mirrors and every dood mirror (all redirect to the challenged `playmogo.com`) returned `None` before. The shared helper `hoster_resolvers/_browser.py` (`capture_stream`) turns `StealthPool.capture_media` into a `ResolvedStream`; `create_all_xfs_resolvers()` and `DoodStreamResolver` take an optional `stealth_pool`, wired in `composition.py`. SuperVideo's own Playwright HTML fetch is replaced by the same capture (live: `supervideo.cc` behind Cloudflare → HLS master in 1.2 s).
- **Dead files end the capture early**: `capture_media` checks the page title and visible text for dead-file notices after the Cloudflare step and after every play click. Live: a dead dood link fails in 0.7 s, a dead savefiles link (the notice appears only after the click) in 8.5 s instead of 18 s.
- **XFS**: offline-marker and error-redirect checks shared by the video and DDL paths (`_is_dead`).
- Known issue: SuperVideo's CDN redirects non-browser clients to ad trackers (see `docs/features/hoster-resolvers.md`).

### Fix: Filemoon Streams via Browser Capture
- **Filemoon resolved nothing**: the Byse player added a proof-of-work captcha ("click play to verify you're a human") between attestation and playback, and the attestation now rejects the invented viewer/device IDs (HTTP 400). The PoW is a custom memory-hard hash (~65k attempts at difficulty 16), far too slow in Python and one more thing that changes with every Byse update.
- **`StealthPool.capture_media(url, timeout=...)`**: opens a player page in the stealth browser (Cloudflare solved if present), waits for autoplay, clicks the play button up to 3 times (ad popups closed) and returns the first stream request (`.m3u8`/`.mpd`/`.mp4`/`master.txt`) with its Referer. The page loads with CSS (only media downloads are cut) so the click hits the button.
- **Filemoon** parses legacy pages (packed JS, direct HLS) as before and captures the stream of Byse player pages or blocked pages from the browser. Live: `filemoon.to` → HLS master playlist in 2–5 s, playlist fetchable with the returned Referer. The Byse API code (ECDSA attestation, AES-GCM decryption) is gone, and with it the `cryptography` dependency.

### Fix: Hoster Mirror Domains Reach Their Resolver
- **Mirror dispatch**: DoodStream, VidGuard, Strmup, DDownload and Serienstream kept their mirror lists private (`_DOMAINS` checked inside `resolve()`), so the registry never routed `d0000d.com`, `dood.to`, `myvidplay.com`, `vgembed.com`, `vidara.so`, … to them; without a plugin hint such links fell through to content-type probing. They now expose `supported_domains`. Streamtape gets a mirror list (JD2 `StreamtapeCom` + mirrors seen on plugin sites: `streamta.pe`, `strtape`, `shavetape`, `tapeblocker`, `streamtapeadblockuser`, `gettapeads`, …), DoodStream adds `playmogo`/`pooop` (every dood mirror currently redirects to `playmogo.com`).
- **Whitespace in links**: the registry strips the URL before dispatch; a scraped streamtape link ending in `\n` raised inside the resolver.

### Captcha: animeloads Releases with Real Download Links
- **One Torznab result per release** (was one per series with the media page as "download"): for the first 10 series, the media page's release tabs are read (group, resolution → `1080p`/`720p`/…, notes, audio/subtitle languages, package size, archive password), e.g. `Anime N (2015) [12/12] [720p WebRip] [Japanese | Sub: German] [Riitz-chan]`. Stremio (`isolated_search`) keeps series results with their preview stream.
- **Links on grab** (`GrabResolvingPlugin`): the site's "odd one out" image captcha (5 × 48 px images) is solved inside the page by comparing pixels on a canvas (no image library); verification and link requests use the site's jQuery in the page's main world. Links arrive as Click'n'Load packages, decrypted by the new `infrastructure/plugins/clicknload.py` (`cryptography` becomes a direct dependency). Anonymous users need one captcha per episode, so only releases up to 13 episodes are resolved; with `SCAVENGARR_ANIMELOADS_USERNAME`/`_PASSWORD` the whole release comes with one captcha (login path covered by unit tests only, no test account). Rejected answers (the site answers the same for a wrong pick and a rate limit) are retried up to 5 times with a pause.
- **Archive passwords**: `SearchResult.metadata["archive_password"]` goes into the crawljob's `extractPasswords` (`CrawlJobFactory`).
- Live: search "Anime N" → 30 release results in 8 s; grab of a 12-episode release → 12 rapidgator links in ~70 s. Grabs take about 6 s per episode, which can come close to an Arr app's download timeout.

### Anti-Bot: Challenge Clearances Survive Restarts
- **`ClearanceStore`** (`infrastructure/browser/clearance_store.py`): after a solved Cloudflare challenge, the clearance cookies (`cf_clearance`, DDoS-Guard `__ddg*`) are stored per name/domain in the cache (`CachePort`: diskcache or Redis) until they expire, and restored into every new browser context (stealth context and all Playwright plugin contexts, isolated ones included). Other cookies (sessions, logins) are not stored; cookie values are never logged.
- Live (kinoger): first process solves the Turnstile in 4.9 s; a second process restores the cookie and loads the page without a challenge in 0.9 s. Useful for restarts within the cookie lifetime (~30 min for `cf_clearance`).
- Chosen over a persistent Chromium profile, which has a single browser context (no per-plugin/per-request isolation) and allows one process per profile (`docs/plans/captcha-solving.md`, Decisions).
- `PlaywrightPluginBase._remember_clearance(page)` for plugins whose gate is not Cloudflare (DDoS-Guard).

### Resolver: vinovo Works Again, DoodStream Plays
- **New dedicated `VinovoResolver`** (`hoster_resolvers/vinovo.py`, port of the JDownloader `VinovoTo` stream path): Turnstile only guards vinovo's official download button; the player path needs no captcha — page token from `<meta name="token">` and CDN base from `data-base` on `/e/{id}`, `POST /api/file/url/{id}` → stream token → `{data-base}/stream/{token}`. The token is bound to the resolving User-Agent (returned in the playback headers, as for veev). Live: vinovo links from movie2k resolve and play (206 `video/mp4`); dead files ("Video not found") return `None`. The CDN can take ~30 s to the first byte. vinovo left the XFS configs: 22 individual + 12 generic DDL + 25 XFS = 59 resolvers.
- **DoodStream streams are captured again**: in the stealth browser the player passes its invisible Turnstile, but its CDN URL (`…cloudatacdn.com/…~id?token=…`) has no file extension, so `StealthPool.capture_media()` missed it. Requests of the page's video element (resource type `media`) now count as the stream too. Live: `doodstream.com/d/…` → playable MP4 (206) with `Referer: https://playmogo.com/`.

### Anti-Bot: Optional Byparr/FlareSolverr Sidecar
- **New config `playwright.solver_url`** (env `SCAVENGARR_PLAYWRIGHT_SOLVER_URL`, unset by default): base URL of a Byparr or FlareSolverr sidecar. `SolverFetcher` (`infrastructure/browser/solver_fetcher.py`) implements `BrowserFetcherPort` over the FlareSolverr v1 API (`request.get`; JSON bodies rendered in a bare `<pre>` are unwrapped; `resolve_redirect` returns the solver's final URL when it left the host).
- **Order**: own browser first, solver when it fails (`ChainedBrowserFetcher`); with `browser_fallback: false` the solver is used alone. Not verified against a running Byparr (no Docker in the dev container); covered by respx tests of the documented API.

### Captcha: Shared Challenge Detector
- **`detect_challenge(status, html, headers)`** (`infrastructure/captcha/detect.py`) classifies a response as `cloudflare_page`, `ddos_guard`, `turnstile`, `hcaptcha`, `recaptcha` or `altcha` (page blocks before embedded widgets). `is_cloudflare_challenge()` is now a view on it (unchanged semantics).
- **Health prober** counts DDoS-Guard blocks (body markers or `server: ddos-guard` on 403/503) as captcha like Cloudflare, so DDoS-Guard-protected plugins no longer score as healthy; a captcha widget on a working homepage does not count. Hits log `health_probe_challenge` with the kind.
- **`HttpxPluginBase._fetch_text()`** logs the challenge kind on errors and browser fallbacks.

### Captcha: nox Download Links via ALTCHA, Resolved at Grab Time
- **ALTCHA solver** (`infrastructure/captcha/altcha.py`): solves ALTCHA v2 proof-of-work challenges (PBKDF2/SHA-256/384/512) in-process, no browser and no external service. ALTCHA is a cost-based captcha, not a human test; nox's challenge (cost 5000, prefix `00`) takes well under a second (run via `asyncio.to_thread`).
- **Grab-time link resolution**: new optional plugin capability `GrabResolvingPlugin.resolve_download(url)`. Jobs of such plugins carry `CrawlJob.resolve_plugin`; `GET /api/v1/download/{job_id}` resolves the links through `CrawlJobResolveUseCase` when the job is grabbed, stores the resolved job (repeated grabs need no second captcha) and answers `502` if nothing could be resolved. Links behind a captcha or a download quota are no longer resolved for every search result.
- **nox serves real hoster links** (live: release page → `https://filer.net/folder/…` in 0.8 s): the crawljob used to contain only the release page, which JDownloader cannot handle. `resolve_download()` looks up the release's online links, solves one ALTCHA challenge for a pass token that unlocks all of them (`/go/{downloadToken}/url?cp=…`) and skips offline links before the captcha. Every unlocked link counts against nox's hourly/weekly limit for anonymous users, hence grab time instead of search time.
- **Refusals are logged**: a refused gateway link logs `nox_unlock_refused` with status, `message` and `reason` (`hourly_limit`, `weekly_limit`, `captcha_required`, `expired`), so a grab that ends in `502` shows why. Live smoke: `tests/live/test_grab_resolve_live.py` (one grab per run to spare the quota).

### Fix: Devcontainer Chromium System Libraries
- `setup.sh` installs the app's Patchright Chromium with `--with-deps`: the system libraries (`libatk` etc.) came only from the optional playwright-mcp step, and when that failed no browser could start, headless or headful.

### Chore: Leaner Claude Code Context
- **Slash commands → skills**: `.claude/commands/` replaced by `.claude/skills/` (`commit`, `test`, `new-plugin`, `new-resolver`). Skills load only their description up front and can be picked by the model itself. `new-plugin` no longer describes the removed YAML/Scrapy plugins; `new-resolver` is new and checks XFS/generic-DDL reuse and JDownloader sources first.
- **`format-and-lint.sh` reports what ruff cannot fix**: remaining lint/syntax errors go back to Claude (exit 2) instead of being swallowed until pre-commit. Uses the project `.venv` ruff directly (falls back to the main checkout's venv inside git worktrees, skips when none), no ANSI colors.
- **Compact pytest output**: `addopts` gains `-q --tb=short`; under Claude Code (`CLAUDECODE=1`) `tests/conftest.py` also disables colors, because the agent shell's `FORCE_COLOR` wrapped every progress dot in ANSI escapes.
- **Fewer caveman skills**: `setup.sh` installs only `caveman`, `cavecrew`, `caveman-explore`, `caveman-review`, `caveman-compress`, `caveman-help`, `caveman-stats` instead of all 14 (Cloud-only skills and the `/commit`-colliding `caveman-commit` dropped).

### Fix: Bugs Found by the Docs Audit
- **Torznab: unknown plugin returns 404 everywhere**: `/torznab/{plugin}/health` and the `extended=1` test probe caught only `TorznabPluginNotFound`, but the registry raises `PluginNotFoundError`, so unknown plugins produced 500 (dev) / 200 (prod). Both exceptions are now mapped to 404. E2E tests now mock the real registry exception (the old mocks hid the bug).
- **Torznab: non-numeric `cat` returns 400**: `cat=abc` raised an unhandled `ValueError` (500). It now raises `TorznabBadRequest` → empty feed with HTTP 400.
- **Torznab caps: `limits default` is 100**: caps advertised `default="50"` while search defaults to `limit=100`; `TorznabCaps.limits_default` now matches.
- **Config: rate-limit/retry env vars work**: `SCAVENGARR_RATE_LIMIT_ADAPTIVE`, `_MIN_RPS`, `_MAX_RPS` and `SCAVENGARR_HTTP_RETRY_MAX_ATTEMPTS`, `_BACKOFF_BASE`, `_MAX_BACKOFF` were read by `EnvOverrides` but dropped by the loader (missing from its flat-key map); they now apply.
- **Config: cache backend via env**: new `SCAVENGARR_CACHE_BACKEND`, `SCAVENGARR_CACHE_REDIS_URL` and `SCAVENGARR_CACHE_MAX_CONCURRENT`. The unprefixed `CACHE_*` variables suggested by a comment were never read (the section is validated from the merged dict); the comment now says so.
- **CLI: `HOST`/`PORT` from `--dotenv` apply**: the CLI read them before `load_config()` loaded the `.env` file; they are now resolved afterwards (`--host`/`--port` still win). First CLI unit tests (`tests/unit/interfaces/test_cli.py`).
- **Config: one set of defaults**: Pydantic field defaults in `schema.py` disagreed with `defaults.py` (`scoring.enabled`, `stremio.max_concurrent_plugins`, `http.user_agent`, `cache.dir`). The schema now mirrors the effective values (no runtime change); a test keeps them in sync.
- **Scoring: alias domains count as supported**: `MiniSearchProber` classified links only against resolver names, so alias domains (`filelions` → Vidhide, `luluvdo` → Lulustream) lowered the supported-hoster ratio. New `HosterResolverRegistry.supported_domains` (names + aliases) is wired in instead. The docs' claim that background probes skip `provides="both"` plugins was wrong (`get_by_provides("stream")` includes them) and is removed.
- **Removed unused dependencies**: `lxml` and `beautifulsoup4` (plus transitive `soupsieve`) were declared but imported nowhere; plugins parse HTML with stdlib `html.parser`. Stale `load_all()` mention removed from the `PluginRegistry` docstring.
- **Stremio `/health` lists supported hosters**: the endpoint called a non-existent `list_hosters()` and swallowed the error, so `supported_hosters` was always empty. It now reads `HosterResolverRegistry.supported_hosters`; the E2E test mock is spec'd against the real class.

### Chore: LF Line Endings and Versioned Claude Code Hooks
- **All text files normalized to LF**: `.gitattributes` widened from `*.md` to `* text=auto eol=lf` and the index renormalized (227 files, mostly `.py`; EOL-only, `git diff --ignore-cr-at-eol` is empty). New `mixed-line-ending --fix=lf` pre-commit hook catches CRLF before commit.
- **Claude Code hooks fixed and versioned**: `.claude/hooks/` and `.claude/commands/` are no longer gitignored. Both hooks had CRLF shebangs, failed with exit 127 and therefore never ran (Claude Code treats non-2 exits as non-blocking). `block-dangerous.sh` rewritten: one `jq` call, no `grep` subprocesses, per-command matching (no false hits across `&&`/`;`/`|`), and new blocks for `git push -f`/`+refspec`, pushes to `…:main`, commits/pushes while `main` is checked out, `rm -fr`/`--recursive` on `/`, `~`, `$HOME`, and `git clean -f`; `--force-with-lease` is allowed.

### Fix: Playwright Live Smoke Tests Never Ran
- **`tests/live/conftest.py` Chromium check is async**: it used the sync API inside the running event loop, raised every time and made all Playwright smoke tests skip with "Chromium not installed". With the fix, 2 of 9 Playwright plugins pass live (animeloads, moflix); ddlspot, ddlvalley, scnsrc (Cloudflare Turnstile) and streamworld fail; boerse, byte hit a network error; myboerse, mygully need credentials. Findings in `docs/plans/plugin-repair.md`.

### Anti-Bot: Patchright instead of playwright + playwright-stealth
- **Browser driver swapped to Patchright** (`patchright` ^1.63, Chromium 153; drop-in Playwright fork): removes the `Runtime.enable`/`Console.enable` and automation-flag leaks that Cloudflare detects. `playwright` and `playwright-stealth` are no longer dependencies; all imports use `patchright.async_api`.
- **No forced User-Agent in browser contexts**: contexts keep Patchright's real UA (a fixed Chrome 131 UA disagreed with the Chromium client hints). New `_browser_user_agent` (default `None`) and `_context_options()`, also used by the boerse/mygully login contexts; `_user_agent` stays for httpx side requests.
- **`PlaywrightPluginBase._stealth` renamed to `_block_resources`**: it now only controls aborting image/font/CSS requests; singleton and per-request contexts share `_configure_context()`. `StealthPool` no longer applies playwright-stealth.

### Fix: Torznab Link Validation Flooded the Network
- **Only the requested page is validated.** A Torznab search validated every result (1000 results ≈ 3000 hoster links) and built a CrawlJob for each before slicing to the requested page (Prowlarr: `limit=100`). The search cache now holds the unvalidated plugin results; each request validates them in order, `limit` at a time, until `offset + limit` valid results exist, and builds CrawlJobs only for that page. Live ("Movie O"): scnlog 299 instead of 2999 link checks, streamcloud 32 s instead of 257 s.
- **Unreachable hosts are skipped.** `HttpLinkValidator` remembers a host for 15 minutes after a connection-level failure (`ConnectError`/`ConnectTimeout`) and sends no GET retry; at most 4 validations per host run at once. Dead hosters (uploaded.net, ul.to, go4up, uptobox, ...) used to get one connection attempt per link. These bursts made the home router treat the machine as a port scanner and block it ("No route to host"), after which every other request failed as well; the live run now shows 0 blocked connection checks (was 24 of ~85).

### Fix: hdfilme Links from the devideosrc Player
- Movies and series now take their hoster links from the embedded devideosrc.co player via the shared `devideosrc` helper (meinecloud and the `su-spoiler` episode lists are gone from the site); season/episode filtering via `devideosrc.filter_episodes()`. Live: category browsing returns results again (36 movies, 34 series per 40 items; S01E01 filter works). Keyword search still returns nothing until the site fixes its search (PHP fatal error).

### Removed: streamworld Plugin
- The site is gone: streamworld.ws serves an empty web-server page and streamworld.co became a legal watchlist/subscription app without hoster links. Plugin, unit tests and live smoke entry removed; 41 plugins (34 httpx + 7 Playwright).

### Test: Live Smoke Tests Use the Browser Fallback
- `tests/live/conftest.py` wires the Cloudflare browser fallback (`StealthPool` via `HttpxPluginBase.set_browser_fetcher`) like `composition.py`, per test and lazily (Chromium only starts on the first browser fetch). Before, filmfans, kinoger and serienfans failed the live smoke with 0 results although they work in the app. filmfans and serienfans still hit the 60 s smoke budget (the sites rate-limit, a full run takes ~140 s) and show up as skipped.

### Fix: boerse (and mygully session hand-over)
- **Back to results** (live: 74 relevant results for "Movie O", ~200 s; was a "network error"): the login ran in its own context, but its session cookies (and Cloudflare clearance) only reached a context through `_prepare_context()`, which `isolated_search()` calls *before* `search()` logs in, and a plain `search()` never. The search page therefore met a fresh challenge without session ("no searchform"). `search()` now hands the session to the context it actually uses right after `_ensure_session()`; mygully uses the same pattern and gets the same fix.
- Search results are the `a#thread_title_NNN` anchors only; the sidebar's "latest threads" links used to leak in (games like "Caves of Qud" for "Movie O"). The next page is the `rel="next"` link (`›`); `»` is vBulletin's *last* page and used to skip straight to it.

### Fix: dataload
- **Back to results** (live: 107 for "Movie O" in ~34 s; was 0): the search POST lacked XenForo's CSRF field, which the forum now enforces (HTTP 400). The session token is read from the post-login page (`<html data-csrf="...">`) and sent as `_xfToken`. Search result pages paginate with `?page=N`, which the parser missed (it only knew `page-N`); the next page now comes from XenForo's `pageNav-jump--next` link, so pagination works again (was 1 page).

### Fix: kinoking
- **Back to results** (live: 73 for "Movie O" in ~9 s, Series D S01 episodes; was 0): the site was redesigned. Search cards are `div.fav-data-source` with `data-id`/`data-type`/`data-title`, paginated with `&page=N` (50 per page, up to 20 pages). Movie pages embed `const SERVERS = [...]` (named servers with hoster mirrors): aggregator players (meinecloud, vidsync, cinesrc), non-German servers (`(EN)`, `(FR)`) and the title-matching `group_kk_*` servers (they mix up sequels) are skipped, and each server contributes at most 3 mirrors. Series pages embed `const allEpisodesData = [...]` with each episode's own `video_links`, so a series costs one request; results are per episode (`<Series> S01E02`), first season unless a season is requested. Genres are no longer on the pages, so the genre→category map is gone (movies 2000, series 5000, caller's category wins). Per-request timeout raised to 30 s: a cold movie page collects its "(LIVE)" servers first.

### Fix: streamkiste
- **Back to results** (live: 52 for "Movie O" in ~18 s, 24 for "Series D"; was 0): links come from the embedded devideosrc.co player via the shared `devideosrc` helper, like streamcloud (MeineCloud is gone). The site embeds the *series* player for movies too; `devideosrc.fetch_links()` now falls back to the movie player when the series page carries no token and reports which kind answered (`PlayerLinks.kind`), so movies stay movies. New `devideosrc.filter_episodes()` (moved from streamcloud) gives streamkiste season/episode filtering. The detail parser reads metadata only; the dead meinecloud/onclick helpers are gone. `_DOMAINS` now starts with `streamkiste.bid` (`.taxi` redirects there).

### Fix: streamcloud
- **Back to results** (live: 52 for "Movie O" in ~16 s, 24 for "Series D"; was 0): hoster links moved from meinecloud.click and the season tabs to an embedded **devideosrc.co** player (`/movie/<imdb>`, `/serial/<imdb>`). New shared helper `scavengarr.infrastructure.plugins.devideosrc`: detects the player on a detail page, reads the signed token from the player page and loads the hoster embeds from `POST /api/embed-links` (no captcha; only the separate download embed is Turnstile-gated). Series links are labelled `<season>x<episode> <hoster>`, so the existing season/episode filter keeps working. The detail parser now reads metadata only (values in `<div>` or `<span>`); dead meinecloud/tab parsing and `_domain_from_url` are gone. `_DOMAINS` is now `streamcloud.download` (`.plus` → `.uno` → `.download`).
- devideosrc's player pages are always loaded past Cloudflare's cache (cached copies carry expired tokens and even cached 429 answers); a 429 there is retried with a fresh URL.

### Fix: RetryTransport Retried Cached 429s
- A 429/503 served from Cloudflare's cache (`cf-cache-status: HIT/STALE/UPDATING`) is now returned at once. Before, the transport retried it with backoff although a cached answer never changes, and each retry halved the domain's adaptive rate (a streamcloud search slowed from ~16 s to ~140 s).

### Fix: nox
- **Back to results** (live: 31 for "Movie O" in ~1.5 s; browse: 73 recent releases; was 0): the `/api/frontend/...` API is gone. Search now pages through `GET /api/search?q=&page=` (media entries, 20 per page, up to 10 pages) and lists each entry's releases from `GET /api/media/{slug}` (bounded concurrency; releases without online links are skipped). Browse (empty query) uses `GET /api/releases/recent/{days}`. Release links point to the new release page `/media/{slug}?release={id}` (the old `/release/{slug}` is 404); posters come from `/api/image/w342/…`. Type `episode` is now `series`; documentaries (`doku`) map to 5080. Category filtering uses the shared `_category_matches()`.

### Fix: fireani
- **Back to results** (live: 4 for "Anime C", 32 over 2 pages for "one", ~2–4 s; was 0): the REST API (`/api/anime/...`) is gone. Search is now server-rendered: `/search?q=&page=` is parsed from the page's `__NUXT_DATA__` payload (small devalue resolver in the plugin; 30 per page, paginated up to ~1000 items). Seasons and links come from the site's Connect RPC endpoints (`POST /api.v1.anime.AnimeService/GetAnime` and `/GetEpisode`, JSON). Fields are camelCase now (`animeSeasons`, `animeEpisodeLinks`, `voteAvg`). The site's player sits behind a Turnstile check, but only in the browser: the RPC answers without a token.

### Fix: hdfilme Domain (Site Still Broken Upstream)
- `_DOMAINS` now `hdfilme.cafe`: hdfilme.legal → .press → .party → .bid all redirect there. The plugin still returns 0 results because the site's own search is broken (every `?do=search` request, from httpx and from a real browser, answers with a PHP fatal error in `engine/mods/sfilter/filter.php`; DLE quick search is disabled). Film links also moved from meinecloud.click to `devideosrc.co/embed/download/<imdb>`, behind a Turnstile gate. Listed under KNOWN_ISSUES until the site is fixed.

### Fix: byte
- **Back to results, now an httpx plugin** (live: 266 results for "Movie O" in ~30 s, was 0 or a timeout): byte.to serves search, detail pages and link widgets as plain HTML, so the plugin moved from `PlaywrightPluginBase` to `HttpxPluginBase` (Cloudflare challenges, should they return, go through the shared browser fallback). Links now come from the per-hoster widgets (`/widgets/button.php?…`, fetched directly instead of rendering iframes); the hoster is read from `<img title="rapidgator.net">`, links flagged offline (`red-dot`) are skipped, and byte's own `go.php?hash=` redirector is resolved to its target (e.g. filecrypt). Size and category are parsed from the new `<B>Größe:</B> 7,14 GB` cells (label and value share a cell). Plugin count: 34 httpx + 8 Playwright. byte.to slows its responses down after a burst of ~2000 requests (one full 1000-item search), so back-to-back full searches can take several minutes.

### Fix: scnlog
- **Back to results** (live: 992 of the 1000-item cap for "Movie O", was 0): the site moved to a new layout. Search results are `li.row` › `div.title` › `a`, the next page is `a.next`; detail pages have the title in `h1.single-title` and plain links (no `external` class, URL as link text) inside `div.download`, so the hoster name comes from the link's domain.

### Resolver: veev.to Works Again
- **New dedicated `VeevResolver`** (`hoster_resolvers/veev.py`, port of JDownloader `VeevTo`): the player API path needs no captcha — LZW-decode the `window._vvto` token, call `/dl?op=player_api&cmd=gi`, decode `file.dv[0].s` into a direct MP4 URL. Live: 2 of 4 veev links from movie2k/moflix/megakino resolve to playable MP4 (206 `video/mp4`); the other two are offline and correctly return `None`. veev left the XFS configs (`needs_captcha`): 18 individual + 12 generic DDL + 26 XFS = 56 resolvers.
- **vinovo and wolfstream stay disabled** after a headful retest: vinovo needs an embedded Turnstile token posted to its API, wolfstream redirects to an ad domain via anti-bot JS.

### Fix: serienfans
- **Back to results** (live: 35 releases for "Series D", was 0): search API, series pages, season API and index pages go through `_fetch_text()` (Cloudflare → browser fallback); `/external/2/<hash>` links of the returned results are resolved to their filecrypt containers. Same 429 rate limit as filmfans (~2.5 min uncached).

### Fix: kinoger
- **Back to results** (live: 4 streams for "Movie O" in 7 s, was 0): search and detail pages go through `_fetch_text()` (Cloudflare → browser fallback). Stream links point to external hosters and need no resolution. In the Stremio path (`plugin_timeout_seconds` 15 s in `data/config.yaml`) the very first search after start can time out while the challenge is solved; later searches reuse the clearance cookie of the stealth context.

### Fix: filmfans
- **Back to results** (live: 13 releases of "Movie O" 2008, was 0): search API, movie pages and the release API go through `_fetch_text()` (Cloudflare → browser fallback); `/external/<hash>` download links are resolved to their filecrypt containers, dead ones dropped. The site rate-limits bursts (429): an uncached search takes ~2–2.5 min, which can exceed Prowlarr's request timeout (results are cached 15 min).

### Anti-Bot: Link-Out Resolution, Rate-Limit Retry, Host Memo
- **`BrowserFetcherPort.resolve_redirect()`** / `StealthPool.resolve_redirect()`: first off-site URL of a redirect chain, via `request` events (routes only see the first URL of a chain). `HttpxPluginBase._resolve_redirect()` tries httpx first (`Location` header), `_resolve_result_links()` applies it to final results: `/external/<hash>` links behind Cloudflare would otherwise fail link validation and downloaders.
- **Rate limits**: `StealthPool.fetch_text()`/`resolve_redirect()` retry 429/502/503/504 after 2 s, 5 s, 10 s (shared `_navigate()`).
- **Cloudflare host memo**: after a challenge, a host skips plain httpx for 30 min (`HttpxPluginBase._cf_blocked_until`).
- `HttpxPluginBase._parse_json_text()` for JSON bodies from `_fetch_text()`.

### Anti-Bot: Browser Fallback for httpx Plugins
- **New port `BrowserFetcherPort`** (`domain/ports/browser_fetcher.py`): `fetch_text(url, *, timeout) -> str | None`.
- **`StealthPool.fetch_text()`** implements it: navigate, solve the challenge, return the DOM for HTML or re-fetch non-HTML (JSON) in-page for the raw body; bounded by `fetch_concurrency` (`min(stremio.max_concurrent_playwright, 2)`). Live: filmfans page 22 s (challenge) then its JSON API 2 s, kinoger search 13 s, serienfans detail 5 s.
- **`HttpxPluginBase._fetch_text(url, params=...)`**: plain GET; on a Cloudflare challenge the injected fetcher loads the URL instead. `HttpxPluginBase.set_browser_fetcher()` is wired in composition.
- **New config `playwright.browser_fallback`** (default `true`, env `SCAVENGARR_PLAYWRIGHT_BROWSER_FALLBACK`).
- **`read_when_settled()`**: page reads that race a post-challenge reload ("Execution context was destroyed") are retried after `domcontentloaded`; used by `fetch_text()` and `_fetch_page_html()`.

### Test: Live Smoke Caps Results at 50
- `tests/live/conftest.py` sets `search_max_results` to 50 (autouse fixture, same mechanism as the Stremio path): smoke tests check that a plugin works, not that it scrapes 1000 items within 90 s. Playwright smoke now: animeloads, ddlspot, ddlvalley, moflix, scnsrc pass; byte (timeout), boerse (network error), streamworld (0 results) remain for `docs/plans/plugin-repair.md`.

### Fix: scnsrc
- **Back to results** (live: 37 of 42 posts for "Movie O", was 0): search pages now list only title and category, so release name and links are loaded from each post page (new `_PostPageParser`, covers the TV `tvshow_info` layout and the film/P2P info table; only Torrent/Usenet/NZB anchors inside `storycontent`). Titles are the scene release names. Post pages are rate-limited (nginx 503): concurrency 2 with retry backoff; search pages skip `networkidle`.

### Browser: Post-Challenge Settle and Shared Retry
- **`solve_cloudflare()` waits for the post-challenge redirect** (drops `__cf_chl_tk`) and `domcontentloaded` before returning; reading the page right after the title changed failed with "page is navigating".
- **`PlaywrightPluginBase._fetch_page_html()`** gains `wait_for_idle` and `retry_backoff_s`: transient failures (429/502/503/504, no response) are retried after each backoff, other errors (e.g. 404) fail at once. ddlspot and ddlvalley use it instead of their own page handling.

### Fix: ddlvalley
- **Back to results** (live: 250 hits for "Movie O", was 0; 58 before the rate-limit fix): Turnstile solved by the new solver. Post pages are rate-limited by nginx (503 "Service Temporarily Unavailable" for ~75% of posts at 5 parallel fetches), so detail concurrency is 2 and 503s are retried after 2 s and 4 s. Search pages skip the `networkidle` wait (server-rendered WordPress): 27 search pages in 13 s instead of ~2 min.

### Fix: ddlspot
- **Back to results** (live: 30 hits for "Movie O" in 8 s): Turnstile solved by the new solver; detail pages now load in the cleared browser context (plain HTTP gets an empty 200 body, which silently yielded 0 links); domain `www.ddlspot.com` (bare domain redirects); full titles from the link's `title` attribute instead of the truncated, space-less link text.

### Anti-Bot: Turnstile Solver
- **New `infrastructure/browser/turnstile.py`**: `solve_cloudflare(page, timeout_ms=...)` returns at once on a normal page, gives a challenge ~3 s to auto-clear, then clicks the Turnstile checkbox inside the `challenges.cloudflare.com` iframe (re-click every 8 s). Used by `PlaywrightPluginBase._wait_for_cloudflare()` (timeout default 15 s → 30 s) and `StealthPool.wait_for_cloudflare()`. Live: ddlspot and scnsrc challenges solved with one click in ~4 s (headful).
- **Challenge responses no longer abort navigation**: Cloudflare answers with 403/503, and `_navigate_and_wait()`, `_fetch_page_html()` and `_verify_domain()` gave up on any status `>= 400` before the challenge could be solved. New `_passes_cloudflare()` only fails on error statuses that are not a challenge page.

### Anti-Bot: One Chromium Process
- **Browser code moved to `infrastructure/browser/`**: `SharedBrowserPool` (from `plugins/`), `StealthPool` and `cloudflare.py` (from `hoster_resolvers/`).
- **`StealthPool` runs on the shared Chromium** (`browser_pool=` instead of its own launch): one browser process instead of two, saving roughly 420–700 MiB PSS when both were in use. It recreates its context after a browser relaunch; composition creates the shared pool first and cleans up the stealth context before the browser.

### Anti-Bot: Headful Browser by Default (Xvfb)
- **`playwright.headless` now defaults to `false`**: headful Chromium when a display exists, because interactive Cloudflare Turnstile rejects every headless browser. New `infrastructure/browser/display.py` (`resolve_headless()`): without `DISPLAY` all three launch sites (shared pool, stealth pool, standalone plugin) fall back to headless and log `browser_headful_no_display` once.
- **Docker**: runtime image installs `xvfb`; new `docker/entrypoint.sh` starts Xvfb on `:99` and `exec`s the CLI (SIGTERM still reaches the app). `SCAVENGARR_PLAYWRIGHT_HEADLESS=false`.
- **RAM** (PSS, measured): Chromium idle 230 → 420 MiB, 3 pages 451 → 697 MiB, Xvfb ~70 MiB.

### Chore: Patchright Chromium Install
- `Dockerfile.prod` installs the browser with `python -m patchright install chromium` (stage renamed `browsers`; cache path `~/.cache/ms-playwright` unchanged). `.devcontainer/setup.sh` installs the Patchright Chromium for the venv on every attach.

### Chore: Xvfb in the Dev Container
- **`.devcontainer/setup.sh` installs `xvfb`** (only if `Xvfb` is missing): interactive Cloudflare Turnstile rejects every headless browser, while headful Patchright under `xvfb-run` clears filmfans, kinoger, serienfans, ddlspot, ddlvalley and scnsrc (anti-bot Phase 0, `docs/plans/antibot-patchright.md`).

### Docs: Audit and Style Unification
- **Every doc checked against the code**: all feature, architecture, plan, refactor and OpenSpec documents plus README were audited claim by claim and corrected. Among the fixes:
  - health endpoints are `/api/v1/healthz` and `/api/v1/readyz`, including the Docker healthcheck examples
  - `CACHE_*` env vars are ignored, so Redis is configured via YAML
  - CrawlJob TTL is fixed at 1 h, and CrawlJobs are stored as JSON, not pickle
  - the plugin concurrency default is 5, not 3
  - all plugins are imported at startup, not lazily
  - `HttpxSearchEngine` only validates links
  - removed non-existent APIs: `LinkValidatorPort`, `PluginValidationError`, `load_all()`, the stage engine and result dedup
  - effective config defaults are documented
  - README facts corrected: license GPL-3.0, Python 3.12–3.13, clone URL, no `--factory` flag
- **Current behaviour documented**: known bugs are documented as they behave today, with `Known issue` notes, and config keys nothing reads are marked "currently unused". Code fixes follow separately.
- **Consolidation**: `plugin-system.md` covers discovery, registry, overrides and dispatch, and `python-plugins.md` is the plugin author guide. `docs/architecture/codeplan.md` shrank from 1641 to 270 lines (module map, design invariants, dependency chains). Plans and OpenSpec changes carry accurate, dated status lines and ticked checklists.
- **Unified style**: every doc has the same header (back link, H1, one-line summary), `---` between sections, unwrapped paragraphs, ` — ` dashes and a `Source Code References` table.
- **Config comments**: `data/config.yaml` comments now state the real precedence (`.env` acts as env vars) and that `cache.max_concurrent`/`cache.redis_url` are YAML-only. The remaining German comments in `pyproject.toml`, `.pre-commit-config.yaml` and `Dockerfile` are translated.
- **Markdown syntax cleanup**: every code fence now declares a language (`text`, `python`, `http`, `bash`, ...), `***` separators replaced by `---`, non-breaking hyphens in `docs/PYTHON-BEST-PRACTICES.md` replaced so its table-of-contents anchors resolve.
- **Root `AGENTS.md` reduced** to the `openspec update`-managed block (restored missing `<!-- OPENSPEC:START -->` marker) plus a pointer to `CLAUDE.md`. The removed agent guide was outdated (Docker commands, `commitlint`/`mypy` pre-commit hooks and a `redact_config_for_logging()` helper that do not exist). The Conventional Commits rule moved into `CLAUDE.md`.

### Docs: Slim CLAUDE.md
- **`CLAUDE.md` cut from 42 KB to 9 KB**: it is loaded into every AI session, so it now keeps only the rules that apply to every change (workflow, dependency rule, Python rules, mock patterns, dev container pitfalls) and links to `docs/` for details. The hand-maintained test file tree was dropped (derivable from `tests/`), the unconfigured docs-mcp-server section removed.
- **Markdown line endings unified**: all `.md` files converted to LF; `.gitattributes` enforces `eol=lf` for `*.md`.
- **Guides moved to feature docs**: "Adding a New Plugin" (site analysis, mandatory search standards) now lives in `docs/features/python-plugins.md`, "Adding a New Resolver" (non-XFS workflow, test checklist, JDownloader sources) in `docs/features/hoster-resolvers.md`.

### Refactor: StremioStreamUseCase Split
- **Episode filter moved to infrastructure**: `filter_by_episode()` (guessit-based) now lives in `infrastructure/stremio/episode_filter.py` and is injected into `StremioStreamUseCase` as `episode_filter_fn`. The application layer no longer imports guessit directly.
- **Stream building extracted**: stream formatting, hoster dedup, direct-video detection, behaviorHints, cache links and proxy URL building moved to `application/stremio/stream_builder.py` (pure functions, tests in `test_stremio_stream_builder.py`).
- **Query building extracted**: search query normalisation, base-title fallback queries and multi-language reference/query construction moved to `application/stremio/queries.py` (tests in `test_stremio_queries.py`).
- **`PluginSearchRunner` extracted**: plugin fan-out (query fallback dedup, budget slots, per-plugin timeout, circuit breaker, metrics, episode filter, validation, browser warmup) moved to `application/stremio/plugin_search.py`. `StremioStreamUseCase` builds it from its existing dependencies, so the constructor API is unchanged. Benchmarks exercise the runner directly. Removed the unused `max_concurrent_*` attributes. `stremio_stream.py` shrank from 1374 to 670 lines. 14 new runner tests.

### Live Tests Opt-In
- **`poetry run pytest` excludes live tests by default** (`addopts = "--ignore=tests/benchmark -m \"not live\""`). Live smoke tests hit real websites, so broken external sites made the mandatory pre-commit test run permanently red. Run them explicitly with `poetry run pytest -m live`.

### Dev Container: Node 22 + Caveman
- **Node 22 via devcontainer feature**: `ghcr.io/devcontainers/features/node:1` (version 22) replaces the apt `nodejs` fallback in `setup.sh` (Debian bookworm ships Node 18, too old for the `skills` CLI). `setup.sh` now fails early if Node lacks `node:util.styleText` (< 20.12) and installs npm globals without `sudo` (nvm prefix).
- **Caveman auto-install**: `setup.sh` installs the `@caveman-ai/cli` CLI and the `JuliusBrussee/caveman` Claude Code skills (`npx skills add ... -g -a claude-code`) on every attach, so a rebuilt container needs no manual setup. Failures only warn.

### Dev Container: No Docker, playwright-mcp via stdio
- **Docker removed from the devcontainer**: the docker-in-docker feature never worked on nftables-only host kernels ("can't initialize iptables table `nat'"), and the `docker-compose.yml` MCP stack (docs-mcp-server, llm-context, jaeger, nginx proxy) was unused by Scavengarr. Removed the dind feature, the compose file, the Docker steps in `setup.sh` and the MCP `forwardPorts` (only 7979 remains).
- **playwright-mcp over stdio**: `.mcp.json` is now committed and starts `@playwright/mcp@0.0.82` via `npx` (headless Chromium, isolated profile). `setup.sh` installs the matching Chromium with system dependencies. No container, port or daemon needed.
- **docs-mcp-server** is no longer configured.

### Dev Container Git Access
- **Push without DevPod tunnel**: the devcontainer installs `gh` (feature `github-cli`) and `setup.sh` runs `gh auth setup-git` when `GH_TOKEN` is set in `.env.devcontainer`, so `git push`/`gh pr` work even when the DevPod credential tunnel (`localhost:12049`) is down. `setup.sh` also sets `user.name`/`user.email` from `GIT_AUTHOR_NAME`/`GIT_AUTHOR_EMAIL`.

### JDownloader Reference Sync
- **Auto-updating JDownloader sources**: `.devcontainer/sync-jdownloader.sh` keeps `.devdata/JDownloader2/plugins/` and `controlling/` as SVN working copies of `svn://svn.jdownloader.org/jdownloader/trunk/src/jd/` (replaces the former manual copies). Runs on every devcontainer start via `postStartCommand`, never blocks startup on network errors, and writes changed files + commit messages of the last update to `.devdata/JDownloader2/CHANGES.md`.

### Documentation Drift Fixes
- **CLI docs corrected**: the CLI uses stdlib `argparse` (entry point `poetry run start` → `scavengarr.interfaces.cli:start`), not Typer. Fixed in `CLAUDE.md`, `AGENTS.md`, `README.md`, `docs/features/`.
- **Test inventory**: `CLAUDE.md` test tree now lists all 21 previously missing test files (incl. new `unit/interfaces/`); test counts updated across docs (4137 total = 3905 unit + 169 E2E + 25 integration + 38 live).

### animeloads Plugin Tests
- **56 unit tests** for the `animeloads` Playwright plugin (`tests/unit/infrastructure/test_animeloads_plugin.py`): category mapping/filtering, `SearchResult` building (embed vs. media page links, metadata, truncation), search flow incl. season/episode restriction, pagination (page URLs, empty page stop, `_MAX_PAGES`, `max_results`), DDoS-Guard wait handling, and page cleanup on errors. `animeloads` was the only plugin without unit tests.

### Dependency Cleanup
- **Fix: uninstallable lockfile**: `poetry.lock` pinned `lancedb 0.5.7` (pulled in via `crewai-tools`), which no longer exists on PyPI — `poetry install` failed on every fresh environment. Removed the unused dev dependencies `crewai`, `crewai-tools[mcp]`, `openinference-instrumentation-crewai` and `mcp` (not imported anywhere) and re-locked; ~100 transitive packages dropped.

### Concurrency Benchmark Suite & Auto-Tune Fix
- **Benchmark suite** (`tests/benchmark/`): synthetic E2E benchmarks for ConcurrencyPool slot tuning, probe/validation semaphore sweeps, and formula-vs-empirical comparison. Runs manually via `poetry run pytest tests/benchmark/ -s -v` (excluded from the default `pytest` run via `addopts = "--ignore=tests/benchmark"`).
- **Fix: probe/validation hard-caps**: `probe_concurrency` capped at 100 (was unbounded — 128 on 32 cores), `validation_max_concurrent` capped at 120 (was 160). Caps derived from benchmark diminishing-returns analysis (<5% throughput gain beyond threshold).
- **New test**: `test_extreme_host_probe_validation_capped` verifies caps on 32-core hosts.

### Code Review: Tests, Performance & Quality
- **HLS proxy E2E tests** (11 tests): full request-response cycle for `GET /proxy/{stream_id}/{path}` — manifest rewriting, segment streaming, error codes (400/404/502/503), query string fallback, CORS headers, header forwarding.
- **`_build_stream_from_resolved` unit tests** (8 tests): proxy URL construction for HLS with/without headers, direct MP4, echo-URL skip, query string preservation, custom manifest filenames.
- **`_resolve_query_string` unit tests** (5 tests): request query priority, video URL fallback, empty handling.
- **guessit offloaded to thread pool**: `_filter_by_episode()` and `convert_search_results()` now run in `run_in_executor()` to avoid blocking the async event loop during CPU-bound release name parsing.

### HLS Proxy Query String Fix & Resolver HEAD Verification
- **Fix: HLS proxy preserves CDN auth tokens**: proxy URL now extracts the actual manifest filename and query string from the video URL instead of hardcoding `master.m3u8`. CDN auth tokens (e.g. `?t=abc123&expires=...`) are forwarded correctly, fixing 403 errors on all HLS streams routed through the proxy.
- **Fix: proxy endpoint query string fallback**: when Stremio strips query params from the proxy URL, the endpoint falls back to the original video URL's query string to recover CDN auth tokens.
- **HEAD verification for VOE, Streamtape, SuperVideo resolvers**: extracted video URLs are now HEAD-checked before returning. Unreachable CDN URLs (403, timeout) return `None` instead of reaching Stremio as "video is not supported".
- **6 new tests**: HEAD verification failure tests for VOE (2), Streamtape (2), SuperVideo (2).

### HLS Proxy Endpoint & XFS Video Verification
- **HLS proxy endpoint** (`GET /api/v1/stremio/proxy/{stream_id}/{path:path}`): proxies HLS manifest and segment requests with correct CDN headers (Referer etc.) for hosters like Dropload whose CDNs require headers on all sub-requests, not just the master manifest. Rewrites absolute CDN URLs in variant playlists so the HLS player routes all fetches through the proxy.
- **XFS video URL verification**: after extracting a video URL from an XFS embed page, the resolver now performs a HEAD check against the CDN to verify the URL is actually reachable. Filters out IP-locked CDN tokens (e.g. LULUVID/LULUVDOO) that always return 403 because the token was bound to Cloudflare's edge IP.
- **Extended CachedStreamLink entity**: new `video_url`, `video_headers`, and `is_hls` fields support HLS proxy routing. Backward-compatible deserialization for existing cache entries.
- **New module** `infrastructure/stremio/hls_proxy.py`: manifest rewriting (`rewrite_manifest`), CDN base extraction (`cdn_base_from_url`), CDN fetch helper (`fetch_hls_resource`), URL builder (`build_cdn_url`).
- **34 new tests**: HLS proxy helpers (18), XFS video verification (5), stream link cache HLS fields (3), E2E streamable assertion updated for proxy URLs.

### Container-Aware Resource Detection & Adaptive Auto-Tuning
- **cgroup-aware resource detector** (`infrastructure/resource_detector.py`): reads actual CPU/memory limits from Linux cgroups (v2 → v1 → OS fallback) instead of host values. Detection order mirrors JVM `UseContainerSupport` and Go 1.25. On a 16-core/64GB host with `--cpus=2 --memory=2g`, the system now correctly sees 2 CPUs and 2GB RAM
- **Extended auto-tuning** (`_auto_tune()` in composition root): when `stremio.auto_tune_all=true` (default), ALL concurrency parameters are scaled proportionally to detected resources:
  - `max_concurrent_plugins`: `min(cpu*3, mem_gb*2, 30)` — was only CPU-based
  - `max_concurrent_playwright`: `min(cpu, mem_gb/0.15, 10)` — RAM-limited (~150MB per BrowserContext)
  - `probe_concurrency`: `cpu * 4` — lightweight HEAD requests scale linearly
  - `validation_max_concurrent`: `cpu * 5` — same as probes
- **Adaptive AIMD rate limiting** (`TokenBucket` in `rate_limiter.py`): per-domain request rates now adjust automatically based on target-server feedback using TCP-style AIMD (Additive Increase / Multiplicative Decrease):
  - Success → rate increases by 10% (capped at `rate_limit_max_rps`, default 50)
  - 429/503 → rate halved immediately (floored at `rate_limit_min_rps`, default 0.5)
  - Timeout → rate reduced by 25%
  - Each domain has its own independent adaptive rate — throttling on site A doesn't affect site B
- **RetryTransport feedback integration**: after every HTTP response, the transport now calls `record_success()` or `record_throttle()` on the rate limiter, enabling real-time rate adaptation
- **New config fields**: `stremio.auto_tune_all` (bool, default true), `http.rate_limit_adaptive` (bool, default true), `http.rate_limit_min_rps` (float, default 0.5), `http.rate_limit_max_rps` (float, default 50.0)
- **48 new tests**: resource detector (cgroup v2/v1/fallback, fractional CPUs, unlimited, frozen dataclass), adaptive rate limiter (AIMD, min/max bounds, domain independence, compounding), auto-tune (5 container scenarios from 1CPU/512MB to 16CPU/64GB), retry transport feedback

### Performance Tuning
- **Aggressive timeout cuts**: HTTP scraping 30→15s, hoster resolution 15→10s, Playwright page load 30→20s, plugin timeout 30→15s, probe timeout 10→5s, stealth probe 15→10s, link validation 5→3s
- **Higher concurrency**: `max_concurrent_plugins` 5→15 with auto-tune cap raised 10→20, `max_concurrent_playwright` added at 7, `validation_max_concurrent` 20→30, `probe_concurrency` 10→20, `max_probe_count` 50→80, plugin default `_max_concurrent` 3→5
- **Configurable resolve semaphore**: `_resolve_top_streams()` now uses `probe_concurrency` from config (was hardcoded at 10)
- **Faster retries**: `retry_max_attempts` 3→2, `retry_backoff_base` 1.0→0.5s, `retry_max_backoff` 30→10s
- **Higher throughput**: `rate_limit_rps` 5→10 per domain, `max_results_per_plugin` 100→50 (less work per plugin, faster turnaround)
- **Longer cache**: `search_ttl_seconds` 900→1800 (30min cache for repeated searches)
- **`resolve_target_count` convention**: 0 = disabled (resolve all streams), replaces magic number

### Playwright Stealth Default
- **Stealth mode now on by default**: `PlaywrightPluginBase._stealth` changed from `False` to `True` — all 9 Playwright plugins (boerse, mygully, moflix, streamworld, animeloads, byte, scnsrc, ddlvalley, ddlspot) now use stealth evasions automatically
- **SuperVideoResolver uses shared StealthPool**: replaced dedicated Playwright browser lifecycle with injected `StealthPool` — eliminates a redundant Chromium process and reuses the stealth-enabled browser pool. Graceful degradation to httpx-only when no pool is available
- **StealthPool `wait_for_cloudflare()` public**: renamed from `_wait_for_cloudflare()` to allow external callers (SuperVideoResolver) to use the Cloudflare wait logic
- **StealthPool always created**: composition root now creates `StealthPool` unconditionally (was gated by `probe_stealth_enabled`), since SuperVideoResolver needs it regardless of probe configuration

### Plugin Fixes (megakino, boerse)
- **megakino**: Fix broken plugin (0 results in live tests). Three issues resolved:
  1. Domain redirect: `megakino.me` now redirects to `megakino1.biz` — updated `_DOMAINS` list with 4 mirrors (`megakino1.biz`, `megakino1.ws`, `megakino1.net`, `megakino.me`)
  2. yg_token JS challenge: detail page GET requests require a `yg_token` cookie — added `_ensure_token()` that fetches `/index.php?yg=token` (204 response sets cookie) before scraping detail pages
  3. iframe extraction: site changed from `<a href="/dl/...">` to `<iframe data-src="https://voe.sx/e/...">` for hoster links — updated `_DetailPageParser` to extract iframe `data-src`/`src` attributes
- **boerse**: Add missing `boerse.tw` mirror domain to `_DOMAINS` and `_INTERNAL_HOSTS` (6 mirrors total: am/tw/sx/im/ai/kz)

### Stremio Streamable Link E2E Tests
- **Fix existing E2E tests**: `test_stremio_endpoint.py` and `test_stremio_series_e2e.py` updated to pass `pool=ConcurrencyPool()` and mock `get_languages`/`get_mode` on the plugin registry — required after the global concurrency pool became mandatory
- **New `test_stremio_streamable_e2e.py`**: 31 comprehensive E2E tests verifying the full Stremio stream pipeline produces genuinely streamable links (direct `.mp4`/`.m3u8` video URLs with `behaviorHints`, or `/play/` proxy URLs). Covers movie resolution (MP4, HLS, mixed, echo filtering, dedup, behaviorHints), series resolution (episode filtering, multi-plugin, high episode numbers), circuit breaker integration, concurrency pool integration, edge cases (all plugins error, all resolvers fail/echo, empty results), and full pipeline roundtrips
- **Test suite total**: 3900 unit + E2E tests (158 E2E)

### Global Concurrency Pool & Playwright Request Isolation
- **ConcurrencyPool**: new infrastructure component (`infrastructure/concurrency.py`) provides a global concurrency budget with separate httpx and Playwright slot pools. Fair-share algorithm dynamically divides slots across active requests: `fair_share = max(1, total_slots // active_requests)`. When a request exits, remaining requests automatically get more slots
- **Per-request BrowserContext isolation**: Playwright plugins now create a fresh `BrowserContext` per request via `isolated_search()`, preventing state corruption when concurrent requests hit the same singleton plugin. Uses `ContextVar[BrowserContext]` to pass the per-request context transparently through `_ensure_context()`
- **`isolated_search()` method**: added to both `PlaywrightPluginBase` and `HttpxPluginBase`. Playwright plugins create an isolated BrowserContext; httpx plugins pass through to `search()` unchanged
- **`_serialize_search` mode**: Playwright plugins that rely on persistent page state (streamworld, moflix) set `_serialize_search = True` to serialize searches via `asyncio.Lock` instead of creating per-request contexts
- **Cookie-based session transfer**: authenticated Playwright plugins (boerse, mygully) now login in a temporary BrowserContext, export cookies, and inject them into per-request contexts via `_prepare_context()` override — enables concurrent searches without session conflicts
- **Domain ports**: `ConcurrencyPoolPort` and `ConcurrencyBudgetPort` protocols in `domain/ports/concurrency.py` keep the use case decoupled from the concrete infrastructure
- **Composition root wiring**: `ConcurrencyPool` is created with `httpx_slots=max_concurrent_plugins` and `pw_slots=max_concurrent_playwright`, then injected into `StremioStreamUseCase`
- **Unified code path**: pool is now required (not optional) — eliminated the dual code path that maintained a local semaphore fallback. `_dispatch_search()` static method cleanly routes to `isolated_search()` or `search()` based on plugin capability

### Resilience & Observability Improvements
- **Circuit breaker for plugins**: new `PluginCircuitBreaker` (infrastructure/circuit_breaker.py) tracks per-plugin failure counts. After 5 consecutive failures (configurable), the breaker opens and skips the plugin for 60s (configurable cooldown). Half-open state allows a single probe request. Integrated into `StremioStreamUseCase` — failures, timeouts, and successes are all recorded. `snapshot()` exposes per-plugin state for diagnostics
- **Graceful shutdown**: new `GracefulShutdown` (infrastructure/graceful_shutdown.py) tracks in-flight HTTP requests via `request_started()` / `request_finished()`. On shutdown, `wait_for_drain(timeout=10.0)` blocks until all in-flight requests complete or the timeout elapses. Integrated into the HTTP middleware and composition root lifespan
- **Health & readiness endpoints**: `/api/v1/healthz` (liveness) and `/api/v1/readyz` (readiness) — readiness returns 503 until startup is complete and during shutdown drain
- **`/api/v1/stats/metrics` endpoint**: exposes runtime metrics as JSON — plugin search stats (count, success rate, avg duration), probe stats, circuit breaker state per plugin, concurrency pool utilisation (slots total/available/active), and shutdown status
- **Playwright browser relaunch retry**: `_launch_standalone(*, retries=1)` retries browser launch once after a 1s delay on failure, with proper cleanup of partial Playwright state between attempts
- **`isolated_search()` context leak fix**: moved `_prepare_context()` and stealth setup inside the `try` block so that the `BrowserContext` is always closed even if preparation fails. Uses `Token[BrowserContext | None] | None` pattern for safe ContextVar reset

### Cineby Plugin Timeout Fix
- **Increase cineby concurrency**: override `_max_concurrent` from 3 → 8 (lightweight JSON API at db.videasy.net handles higher concurrency)
- **Cap detail fetches**: add `_MAX_DETAIL_FETCH = 25` — only the first 25 search results get detail-fetched (IMDB ID, runtime); remaining results are built from search data only. Prevents timeout on broad queries like "Movie P" (100+ results × 3 concurrency = ~15s detail phase → now 25 results × 8 concurrency = ~1.5s)

### Parallel Language Group Search
- **Parallelize `_search_lang_groups()`**: language groups (e.g. German plugins + English plugins) now search concurrently via `asyncio.gather()` instead of sequentially. Saves ~2-5s on multi-language requests where the slower group no longer blocks the faster one

### Shared Playwright Browser Pool & Pre-Warming
- **SharedBrowserPool**: new infrastructure component (`shared_browser.py`) manages a single Chromium process shared by all 9 Playwright plugins. Each plugin gets its own `BrowserContext` for isolation while sharing the underlying browser — eliminates per-plugin ~1-2s browser startup overhead
- **Composition-time pool injection**: plugins receive the shared pool reference at startup via `set_shared_pool()` instead of per-request task injection — eliminates race conditions on plugin state and simplifies the search orchestration
- **Browser pre-warming**: when a Stremio search request arrives and Playwright plugins are present, the browser warmup fires as a background task (named `browser-warmup` with exception callback) immediately while httpx plugins begin searching
- **Parallel Playwright plugins**: Playwright plugins now run concurrently on the shared browser (bounded by `max_concurrent_playwright`, default 5) instead of sequentially via `Semaphore(1)`. PW semaphore is dynamically sized to `min(pw_plugin_count, max_concurrent_playwright)` per request
- **Add `max_concurrent_playwright` config** (default 5): upper bound for parallel Playwright plugin searches; actual concurrency is dynamically capped at the number of PW plugins in the request
- **Ownership-aware cleanup**: `PlaywrightPluginBase.cleanup()` only closes the browser/Playwright when the plugin owns it (standalone mode). When using a shared pool, only the context and page are closed
- **Disconnection recovery**: `_ensure_browser()` checks `browser.is_connected()` and relaunches transparently if the browser has crashed or disconnected. Context and page state are reset on disconnect
- **Resilient cleanup**: `SharedBrowserPool.cleanup()` logs warnings instead of silently swallowing exceptions during browser close / Playwright stop
- **`get_mode()` on PluginRegistryPort**: use case checks plugin mode without loading the full plugin object — avoids double plugin fetch in search orchestration

### Stremio Stream Resolution Performance
- **Skip probe when resolve is active**: probe phase (`probe_at_stream_time`) is now skipped when a resolve callback is configured, since resolution implicitly checks liveness — saves one entire I/O phase (~5-10s)
- **Early-stop resolve**: `_resolve_top_streams()` now uses `asyncio.wait(FIRST_COMPLETED)` and stops once `resolve_target_count` (default 15) genuine video URLs have been extracted, cancelling remaining tasks. Avoids waiting for slow hosters when enough playable streams are ready
- **Add `resolve_target_count` config** (default 15): target number of successfully resolved video streams before early-stop
- **Shared semaphore across query variants**: `_search_with_fallback()` now shares a single semaphore across all query variants (e.g. "Movie A: Part Two" + "Movie A") instead of creating independent semaphores per variant — prevents connection overload
- **Increase `max_concurrent_plugins` default** from 5 → 10: allows more httpx plugins to search in parallel

### Multi-Language Search & unidecode Migration
- **unidecode for universal transliteration**: replace manual 4-character German umlaut table (`_UMLAUT_TABLE`) and 15-character transliteration table (`_TRANSLITERATION`) with `unidecode` library — supports 130+ Unicode scripts for title matching and search query generation
- **Multi-language plugin support**: plugins now declare `languages: list[str]` (default `["de"]`) instead of `default_language: str`. Backward-compatible property `default_language` returns `languages[0]`
- **Per-language TMDB title resolution**: `get_title_and_year()` and `find_by_imdb_id()` accept a `language` parameter; cache keys include language to avoid cross-language collisions
- **Wikidata title lookup generalized**: IMDB fallback client `_fetch_wikidata_title()` supports any language (was German-only)
- **Multi-language search dispatch**: Stremio use case groups plugins by language, fetches TMDB titles for each unique language in parallel, and searches each group with language-specific queries. A plugin with `languages=["de", "en"]` gets searched with both German and English title queries. Combined `TitleMatchInfo` reference merges all language titles for the title matcher
- **Registry `get_languages()`**: `PluginRegistryPort` exposes `get_languages(name)` to retrieve a plugin's language list

### E2E-Discovered Fixes (Stream Resolution)
- **Domain alias dispatch**: `HosterResolverRegistry` now maps all `supported_domains` from XFS/DDL resolvers, not just the resolver name — fixes dispatch for vidhide family domains (filelions, streamhide, louishide, etc.)
- **Drop unresolvable proxy streams**: when a resolve function is configured but returns `None`, the stream is excluded from Stremio responses instead of creating a `/play/` proxy URL that always 502s
- **Subtitle fallback search queries**: titles with colons (e.g. "Movie A: Part One") now generate a second search query using just the base title ("Movie A"), because German streaming sites often omit subtitles — improves Movie A from 2 to 3 streams, Starship Troopers from 5 to 6
- **Punctuation-safe title matching**: `_normalize()` now strips punctuation (colons, hyphens, etc.) before token comparison, so "dune:" and "dune" are correctly recognized as matching tokens
- **rapidfuzz title matching**: replace `difflib.SequenceMatcher` + custom `_token_similarity()` with `rapidfuzz.fuzz.token_sort_ratio` / `token_set_ratio` for faster, more robust fuzzy matching (C++ backend) — also enhance sequel detection to penalise ANY sequel number mismatch (bidirectional: "Movie O" ref vs "Movie O" result, or "Movie O" ref vs "Movie O" result)
- **Add goodstream XFS config**: new video hoster resolver for goodstream.one/goodstream.uno (XFS-based, confirmed via JDownloader plugin)
- **Add 6 vidhide domain aliases**: streamhide, louishide, streamvid, availedsmallest, tummulerviolableness, tubelessceliolymph (all parklogic.com anti-adblock protected vidhide family)
- Fix XFS two-step form hosters: detect `<form id="F1" action="/dl">` splash pages and POST to `/dl` with `op=embed&file_code={id}&auto=1` to obtain the actual player page (affects bigwarp, savefiles, streamruby, and other form-based XFS hosters)
- Mark wolfstream as `needs_captcha=True` — embed pages return obfuscated JS redirect (anti-bot), not extractable with httpx
- Fix vidking resolver regex: accept `/embed/tv/{tmdb_id}/{season}/{episode}` paths for series content (was only matching `/embed/movie/`)

### XFS Video Hoster Extraction
- Upgrade XFS resolver from validate-only to full video URL extraction for 18 video hosters
- Extract playable HLS/MP4 URLs from embed pages via JWPlayer config, Dean Edwards packed JS, and Streamwish `hls2` patterns
- Shared video extraction module (`_video_extract.py`) reused by both XFS and Filemoon resolvers
- Add `is_video_hoster` / `needs_captcha` flags to `XFSConfig` for per-hoster behavior
- Video hosters: fetch `/e/{file_id}` embed page → extract video URL → return `ResolvedStream` with Referer header
- DDL hosters (katfile, hexupload, clicknupload, filestore, uptobox, hotlink): keep validate-only behavior
- Captcha-required hosters (veev, vinovo): return None immediately (Cloudflare Turnstile required)
- Add `extra_domains` field to `XFSConfig` for JDownloader-sourced domain aliases (vidhide has 19 aliases)
- Supported video hosters: streamwish, vidmoly, vidoza, vidhide, lulustream, upstream, wolfstream, vidnest, mp4upload, uqload, vidshar, vidroba, vidspeed, bigwarp, dropload, savefiles, funxd, streamruby

### Stremio Playback Fixes
- Filter non-video URLs from Stremio responses: `_is_direct_video_url()` detects embed pages vs actual video URLs (.mp4, .m3u8, HLS patterns)
- Skip unplayable streams at search time: resolvers that only validate availability (XFS, DDL) but cannot extract video URLs are excluded from Stremio results instead of producing guaranteed-502 proxy URLs
- Guard in `/play/` endpoint rejects resolved URLs that are just the embed page echoed back (returns 502 instead of redirecting to HTML)
- Fix VOE resolver: follow JS redirects from voe.sx → rotating domains (e.g. lauradaydo.com), fetch token array from external loader.js script

### Production Bug Fixes (Stream Resolution)
- Fix `http-equiv=` garbage treated as URL in megakino_to/movie4k `_collect_streams()` — reject non-HTTP stream values
- Add belt-and-suspenders URL scheme validation in `HttpLinkValidator.validate_batch()`
- Fix veev resolver regex: accept 12+ char alphanumeric IDs (was exactly 12, veev.to now uses 43-char IDs)
- Fix vidking resolver regex: accept `/embed/movie/{id}` paths used by cineby/videasy plugins
- Re-add goodstream XFS config (previously removed in error — confirmed XFS-based via JDownloader GoodstreamUno.java plugin)

### Torznab Pagination
- Wire `TorznabQuery.offset`/`limit` fields through router → use case for server-side result pagination
- Add `offset` and `limit` query parameters to the Torznab search endpoint (defaults: 0 / 100)
- Prowlarr can now page through cached result sets via standard Torznab pagination

### Cloudflare Detection in Health Probes
- `HealthProber` now detects Cloudflare challenges during HEAD/GET probes:
  - HEAD path: `cf-ray` header + 403/503 status code heuristic
  - GET fallback: body-based marker detection via `is_cloudflare_challenge()`
- `ProbeResult.captcha_detected` is now set by the health prober (was always `False`)
- `compute_health_observation()` returns 0.0 for captcha-blocked probes — CF-blocked plugins rank lower

### Dead Code Cleanup
- Remove empty `infrastructure/scraping/` package (stale from Scrapy removal)
- Remove dead `TorznabAction` type alias (defined but never used)
- Remove dead `CacheBackend` re-export from `infrastructure/cache/__init__.py`
- Remove dead `AgeBucket` re-export from `domain/entities/__init__.py`
- Fix duplicate `AgeBucket` in `query_pool.py` — import from domain instead of redefining
- Remove 3 dead config field assignments in `StremioStreamUseCase` (`stremio_deadline_ms`, `max_items_total`, `max_items_per_plugin`) — stored but never read
- Delete dead `/indexers` data file (obsolete Scrapy reference)
- Delete empty `.env.example`
- Clean orphaned `__pycache__` directories
- Remove dead `PluginRegistry.load_all()` method (never called)
- Remove dead `router` re-export from `interfaces/api/__init__.py`
- Remove dead `PluginStats.last_search_ns` field (written but never read)
- Remove dead `StageResult` dataclass from `domain/plugins/base.py`
- Remove dead `PluginValidationError` from `domain/plugins/exceptions.py`
- Remove dead `LinkValidatorPort` protocol (entire file deleted)
- Remove dead `validation_schema.py` module (entire file deleted)
- Remove dead `test_auth_env_resolution.py` test file (entire file deleted)
- Remove dead `probe_urls()` function from `infrastructure/hoster_resolvers/probe.py`
- Remove dead `_DOMAINS` set and `_is_streamtape_domain()` from `streamtape.py`
- Remove dead `get_german_title()` from `TmdbClientPort`, `HttpxTmdbClient`, and `ImdbFallbackClient`

### HTTP Rate Limiting & 429 Retry (Defense in Depth)
- Add `RetryTransport` — custom httpx transport wrapping all outgoing HTTP requests
  - Proactive: per-domain token-bucket rate limiting via existing `DomainRateLimiter` (5 RPS default)
  - Reactive: automatic retry on 429/503 with exponential backoff + jitter + `Retry-After` header support
  - Configurable: `retry_max_attempts` (default 3), `retry_backoff_base` (1s), `retry_max_backoff` (30s)
- Wire `DomainRateLimiter` (previously dead code) into shared `httpx.AsyncClient` via transport layer
- Remove manual 429 retry from `SuperVideoResolver` (now handled transparently by transport)
- Add 3 config fields: `http.retry_max_attempts`, `http.retry_backoff_base`, `http.retry_max_backoff`

### Plugin Scoring & Probing
Background plugin scoring system that measures plugin health and search quality via EWMA-based probes, then selects only the top-N plugins per Stremio request.

- Add domain entities: `ProbeResult`, `EwmaState`, `PluginScoreSnapshot` with age buckets
- Add `PluginScoreStorePort` protocol and `CachePluginScoreStore` persistence (JSON via CachePort)
- Add pure EWMA scoring functions: `alpha_from_halflife`, `ewma_update`, `compute_confidence`, `compute_health_observation`, `compute_search_observation`, `compute_final_score`
- Add `HealthProber` (HEAD with 405/501 GET fallback, Cloudflare detection) and `MiniSearchProber` (limited search + hoster HEAD checks)
- Enhance `MiniSearchProber` to filter HEAD-checks by supported hosters (from `HosterResolverRegistry`)
- Add `supported_ratio` (5th component, weight 0.25) to `compute_search_observation()` — scores now reflect whether a plugin's result links point to hosters with registered resolvers
- Add `hoster_supported` / `hoster_total` fields to `ProbeResult`
- Add `QueryPoolBuilder` with dynamic TMDB-based query generation (trending + discover endpoints, weekly rotation, German locale, bundled fallback lists)
- Add `ScoringScheduler` background task (health probes daily, search probes 2x/week per plugin/category/bucket)
- Add `ScoringConfig` and extend `StremioConfig` with scoring budget parameters
- Add per-plugin YAML overrides (`PluginOverride` model: timeout, max_concurrent, max_results, enabled)
- Fix YAML config loading for `stremio` and `scoring` sections (pre-existing gap in `_SECTION_KEYS`)
- Wire scoring components in composition root with clean cancellation on shutdown
- Add scored plugin selection in `StremioStreamUseCase` with cold-start fallback and exploration slot
- Add `GET /api/v1/stats/plugin-scores` debug endpoint with query filters
- Add `PluginRegistry.remove()` method for disabling plugins via config overrides

### Hoster Resolver Expansion
- Add 6 new XFS hoster configs: Mp4Upload, Uqload, Vidshar, Vidroba, Hotlink, Vidspeed (27 XFS hosters total)
- Add new SendVid streaming resolver (two-stage: API status check + page video extraction)
- Add new Mediafire DDL resolver (public file info API, offline detection via error 110 + delete_date)
- Add new GoFile DDL resolver (ephemeral guest token with 25-min cache, content availability API)
- Add 6 new XFS hoster configs: StreamRuby, Veev, Lulustream, Upstream, Wolfstream, Vidnest
- Add 20 new StreamWish domain aliases from JDownloader (obeywish, awish, embedwish, etc.)
- Add 5 new Streamtape domain aliases (scloud, strtapeadblock, tapeblocker, etc.)
- Add new StreamUp (strmup) standalone HLS resolver with page + AJAX fallback extraction
- Add `vidara` domain alias to StreamUp resolver (Vidara = StreamUp infrastructure)
- Add new Vidsonic standalone HLS resolver with hex-obfuscated URL decoding
- Wire StrmupResolver and VidsonicResolver in composition root

### Stremio Stream Deduplication
- Add per-hoster deduplication: only the best-ranked stream per hoster is returned
- Prevents duplicate links from the same hoster (e.g., 5 VOE links → 1 best VOE link)
- Applied after sorting, before probing/caching — keeps highest-ranked link per hoster

### Architecture Fixes (Clean Architecture Compliance)
- Remove all infrastructure imports from `StremioStreamUseCase` (application layer)
  - Define `_StremioConfig`, `_StreamSorter`, `_MetricsRecorder` protocols locally
  - Inject `sorter`, `convert_fn`, `filter_fn`, `user_agent`, `max_results_var` via constructor
  - Composition root (interfaces layer) now owns all infrastructure wiring
- Add `@runtime_checkable` to all 9 domain Protocol ports (was only on 2 of 9)
- Make `CrawlJob` entity immutable (`frozen=True`) — built once by factory, never mutated
- Remove explicit Protocol inheritance from `CacheCrawlJobRepository` (duck-typing consistency)

### Stremio Playback: behaviorHints.proxyHeaders
Pre-resolve hoster embed URLs at `/stream` time and emit `behaviorHints.proxyHeaders` so Stremio's local streaming server sends the correct `Referer` and `User-Agent` headers to hoster CDNs. This eliminates buffering caused by 403 rejections on missing headers.

- Add `behavior_hints` field to `StremioStream` domain entity
- Add `_build_behavior_hints()` and `_resolve_top_streams()` to `StremioStreamUseCase`
- Add `ResolveCallback` type and wire `HosterResolverRegistry.resolve` via composition root
- Add `Referer` header to all streaming resolver returns (VOE, Filemoon, SuperVideo, Streamtape)
- Emit `behaviorHints.notWebReady` + `proxyHeaders.request` in Stremio stream JSON
- Fallback to `/play/` proxy redirect for streams that fail pre-resolution

### Performance (Audit)
- Parallelize `_select_plugins()` score fetching with `asyncio.gather()` (was sequential await loop)
- Parallelize `_run_search_cycle()` probes: collect all due probes first, then run concurrently with semaphore
- Offload CPU-bound `filter_by_title_match()` (guessit + SequenceMatcher) to thread pool via `run_in_executor()`
- Add periodic eviction of expired entries in `HosterResolverRegistry` caches (prevents unbounded memory growth)

### Code Quality (Audit)
- Consolidate 12 identical DDL hoster resolvers into parameterised `GenericDDLConfig` + `GenericDDLResolver` (alfafile, alphaddl, fastpic, filecrypt, filefactory, fsst, go4up, mixdrop, nitroflare, 1fichier, turbobit, uploaded)
- Add shared `extract_domain()` utility for URL domain extraction, replacing 15 inline duplicates across resolver modules
- Add `exc_info=True` to 4 `except Exception` handlers in business logic (stremio_stream.py, composition.py)
- Remove dead code across domain, application, infrastructure, and plugin layers
- Consolidate duplicate constants and unused imports

### YAML Plugin Infrastructure Removal (Refactor)
Migrated 3 remaining YAML plugins (warezomen, filmpalast, scnlog) to Python httpx plugins. Removed entire YAML plugin infrastructure: ScrapyAdapter, YAML schema models, YAML loader, YAML discovery, and all associated tests (~3,500 lines deleted). Renamed `HttpxScrapySearchEngine` to `HttpxSearchEngine`. Removed the `scrapy` dependency from `pyproject.toml`.

- Add warezomen Python httpx plugin replacing YAML (`fd4bc98`)
- Add filmpalast Python httpx plugin replacing YAML (`3ae7921`)
- Add scnlog Python httpx plugin replacing YAML (`0fa4f36`)
- Remove YAML plugin infrastructure and scrapy dependency (`42fced9`)
- Rename HttpxScrapySearchEngine to HttpxSearchEngine (`12aa0a5`)

### Plugin Standardization (Refactor)
All 29 Python plugins migrated to shared base classes (`HttpxPluginBase` / `PlaywrightPluginBase`), eliminating 50–100 lines of duplicated boilerplate per plugin (client setup, domain fallback, cleanup, semaphore, user-agent).

- Add `HttpxPluginBase` shared base class for httpx plugins (`16b084b`)
- Add `PlaywrightPluginBase` shared base class for Playwright plugins (`16b084b`)
- Add shared plugin constants and CSS-selector HTML helpers (`b12c5a7`)
- Migrate 5 API-only plugins (einschalten, fireani, haschcon, megakino_to, movie4k) to HttpxPluginBase (`407fef9`)
- Migrate aniworld, dataload, nima4k plugins to HttpxPluginBase (`21030d3`, `bded483`, `e4f7f13`)
- Migrate all remaining 21 plugins to shared base classes (`10d23db`)
- Add missing `season`/`episode` params to 10 plugin `search()` signatures (`deef995`)
- Reorganize configurable settings (`_DOMAINS`, `_MAX_PAGES`, etc.) to top of all 28 plugins with section headers (`a79fb8e`)
- Replace hardcoded year boundary with dynamic `datetime.now().year + 1` in cine plugin (`b3e40e3`)

### New Plugins (40 Python plugins added)
Expanded from 2 plugins (filmpalast YAML + boerse Python) to 42 total plugins (33 httpx + 9 Playwright), covering German streaming, DDL, and anime sites.

**Httpx plugins (33):**
- aniworld.to — anime streaming with domain fallback (`3321775`)
- burningseries (bs.to) — series streaming (`b1e46ff`)
- cine.to — movie streaming via JSON API (`3153df0`)
- dataload (data-load.me) — DDL forum with vBulletin auth (`94004e6`)
- einschalten.in — streaming via JSON API (`a729041`)
- filmfans.org — movie DDL with release parsing (`7924969` → `7cd46ed`)
- fireani.me — anime via JSON API (`160171f`)
- haschcon.com — streaming (`0d65a50`)
- hdfilme.legal — streaming with MeineCloud link extraction (`fdaf283`)
- kinoger.com — streaming with domain fallback (`1c03b95`)
- kinoking.cc — streaming with movie/series detection (`067a634`)
- kinox.to — streaming with 9 mirror domains and AJAX embed extraction (`d645ccf`, `20e40e9`)
- megakino.me — streaming (`ff68aeb`)
- megakino_to (megakino.org) — streaming via JSON API (`df2cf77`)
- movie2k.cx — streaming with 2-stage HTML scraping
- serienfans.org — TV series DDL with JSON search API and season/episode support
- movie4k.sx — streaming via JSON API with cross-language title matching (`52f07dd`, `dfc58db`)
- myboerse.bz — DDL forum with multi-domain fallback (`27b42b4`, `d80c69a`)
- nima4k.org — DDL with category browsing (`d001135`)
- nox.to — DDL archive with JSON API, movies + TV episodes
- sto (s.to/SerienStream) — TV-only streaming (`7924969`, `2a73f16`)
- streamcloud.plus — streaming with domain fallback (`10f3808`)
- streamkiste.taxi — streaming with 5 mirror domains (`ff8c662`, `bea8be1`)
- cineby.gd — streaming via JSON API
- crawli.net — single-stage download search engine
- hd-source.to — DDL with multi-page scraping
- hd-world.cc — DDL archive via WordPress REST API, movies + TV series
- jjs (jjs.page) — DDL with multi-stage scraping
- movieblog.to — DDL blog (WordPress)
- serienjunkies.org — DDL with captcha-protected links
- filmpalast.to — movie/TV streaming (migrated from YAML)
- scnlog.me — scene log with pagination (migrated from YAML)
- warezomen.com — DDL site (migrated from YAML)

**Playwright plugins (9):**
- animeloads (anime-loads.org) — anime with DDoS-Guard bypass (`75176af`, `08cced5`)
- boerse.sx — DDL forum with Cloudflare + vBulletin auth (rewritten, see v0.1.0)
- byte.to — DDL with Cloudflare bypass and iframe link extraction (`2cdab77`)
- ddlspot.com — DDL with pagination up to 1000 results (`fca8947`, `21a0657`)
- ddlvalley.me — DDL WordPress with pagination (`0fedecf`, `3d80cec`)
- moflix (moflix-stream.xyz) — streaming via internal API with Cloudflare bypass (rewritten from httpx, `eaa0002`)
- mygully.com — DDL forum with Cloudflare + vBulletin auth
- scnsrc.me (SceneSource) — scene releases with multi-domain fallback (`cb34282`, `2d930bb`)
- streamworld.ws — streaming (rewritten from httpx to Playwright, `de29957`)

**YAML plugins (removed):**
- filmpalast.to, scnlog.me, warezomen.com — all migrated to Python httpx plugins (see YAML Plugin Infrastructure Removal)

### Stremio Addon
Full Stremio addon integration with manifest, catalog search, and stream resolution. Allows using Scavengarr as a Stremio source for all indexed plugins.

- Add Stremio domain entities, TMDB port, and StremioConfig (`c055303`)
- Add TMDB httpx client with caching and German locale (`c7950ef`)
- Add release name parser with guessit integration (`89b8ca9`)
- Add stream converter for SearchResult → RankedStream (`a4b2e0c`)
- Add configurable stream sorter for Stremio addon (`015dde6`)
- Add StremioCatalogUseCase for TMDB trending and search (`8d7dfbc`)
- Add StremioStreamUseCase for IMDb-to-streams resolution (`526e0c5`)
- Add Stremio router with manifest, catalog, and stream endpoints (`0d5854e`, `fed81df`)
- Add title-match scoring module for Stremio stream filtering (`6a06df9`, `b9454cf`)
- Add `get_title_and_year()` to TMDB client and IMDB fallback (`55a7bf7`, `2af65b1`)
- Add IMDB fallback title resolver for Stremio without API key (`23fe5c4`)
- Add Wikidata German title lookup for IMDB fallback client (`eb8094a`)
- Robust title matching via guessit + multi-candidate scoring (`e0b6e76`)
- Thread `plugin_default_language` through stream converter (`8bf0911`)
- Add `default_language` attribute to all plugins (`c53e04c`)
- Add per-plugin timeout to prevent slow plugins blocking response (`c03a28b`)

### Hoster Resolver System
56 hoster resolvers across three categories: 17 individual resolvers (streaming + DDL), 12 generic DDL resolvers (parameterised `GenericDDLConfig`), and 27 XFS-consolidated resolvers (generic `XFSResolver` with parameterised `XFSConfig`). All resolver tests use respx (httpx-native HTTP mocking).

**Core infrastructure:**
- Add ResolvedStream entity and HosterResolverPort protocol (`f6a3676`)
- Add HosterResolverRegistry with content-type probing fallback (`8a7642b`)
- Add hoster hint fallback for rotating redirect domains (`cfe3314`)
- URL domain priority + redirect following in hoster registry (`b083c0b`)
- Add `cleanup()` to HosterResolverRegistry (`c148640`)
- Integrate hoster resolvers into `/play/` endpoint (`2b1f82c`)
- Cache stream links and generate proxy play URLs (`686b4bf`, `f61e30a`)
- Add `/stremio/play/{stream_id}` endpoint with 302 redirect (`08be69c`)
- Add stream preflight probe to filter dead hoster links at `/stream` time
- Add hybrid Playwright Stealth probe for Cloudflare bypass

**Streaming resolvers (10):**
- Add VOE hoster resolver with multi-method extraction (`242ce2d`)
- Add Streamtape hoster resolver with token extraction (`b163637`)
- Add SuperVideo hoster resolver with XFS video extraction (`d980ebe`)
- Add DoodStream hoster resolver with pass_md5 extraction (`5ba3a58`)
- Add Filemoon hoster resolver with packed JS unpacker (`e9353f3`)
- Add Filemoon Byse SPA API extraction and challenge/attest/decrypt flow (`ad62013`, `8592356`)
- Add packed JS decoder for SuperVideo video URL extraction (`e7baaa6`)
- Add Playwright fallback to SuperVideo for Cloudflare bypass (`7ce90dd`, `4438322`)
- Add 429 rate-limit retry with back-off to SuperVideo resolver (`67babee`)
- Add Mixdrop hoster resolver with token extraction (multi-domain)
- Add VidGuard hoster resolver with multi-domain embed resolution
- Add Vidking hoster resolver with embed page validation
- Add Stmix hoster resolver with embed page validation
- Add SerienStream hoster resolver (s.to / serien.sx domain matching)

**DDL resolvers (15):**
- Add filer.net DDL hoster resolver via public status API
- Add Katfile DDL hoster resolver (XFS offline marker detection)
- Add Rapidgator DDL hoster resolver (website scraping validation)
- Add DDownload DDL hoster resolver (ddownload.com / ddl.to, XFS page check)
- Add Alfafile DDL hoster resolver (page scraping)
- Add AlphaDDL hoster resolver (page scraping)
- Add Fastpic image host resolver (fastpic.org / fastpic.ru)
- Add Filecrypt container resolver (container validation)
- Add FileFactory DDL hoster resolver (page scraping)
- Add FSST hoster resolver (page scraping)
- Add Go4up mirror link resolver (mirror link validation)
- Add Nitroflare DDL hoster resolver (page scraping)
- Add 1fichier DDL hoster resolver (multi-domain page scraping)
- Add Turbobit DDL hoster resolver (multi-domain page scraping)
- Add Uploaded DDL hoster resolver (uploaded.net / ul.to)

**XFS consolidation (27 hosters):**
- Add generic `XFSResolver` with `XFSConfig` dataclass consolidating 27 XFS hosters into one module (`xfs.py`)
- Original 15: Katfile, Hexupload, Clicknupload, Filestore, Uptobox, Funxd, Bigwarp, Dropload, Goodstream, Savefiles, Streamwish (9 domains), Vidmoly, Vidoza, Vinovo, Vidhide (6 domains)
- Added 12 more: Mp4Upload, Uqload, Vidshar, Vidroba, Hotlink, Vidspeed, StreamRuby, Veev, Lulustream, Upstream, Wolfstream, Vidnest
- Parameterised tests auto-generated from all 27 configs
- Delete 15 individual resolver files + 15 individual test files (~4,200 lines removed)

**Test improvements:**
- Migrate all 17 non-XFS resolver test files from AsyncMock to respx (httpx-native HTTP mocking)
- Add live contract test skeleton for resolver smoke tests (`tests/live/test_resolver_live.py`)

### Plugin Improvements
Various fixes and enhancements to individual plugins.

- Rewrite kinoger search parser for redesigned site template (`3cf475c`)
- Rewrite streamworld plugin from httpx to Playwright mode (`de29957`)
- Rewrite moflix plugin from httpx to Playwright mode (`eaa0002`)
- Fix streamkiste parser to handle `<span class="movie-title">` tags (`bea8be1`)
- Fix sto plugin to reject non-TV categories (TV-only site) (`2a73f16`)
- Fix filmpalast.to plugin selectors and change provides to stream (`dfc48a3`)
- Fix animeloads DDoS-Guard detection excludes h1 selector (`08cced5`)
- Optimize sto plugin to fetch only requested episode instead of full season (`bb48c58`)
- Add season/episode filtering to mixed plugins (`9d433f5`, `d109844`, `ea8385f`, `ec643ae`)
- Add `provides` attribute to plugin system (`e38a07b`)
- Add domain fallback to aniworld plugin (`f72fc2d`)
- Add pagination to ddlspot, ddlvalley, scnlog, warezomen, boerse (`21a0657`, `3d80cec`, `a30164b`, `3cfa20f`)
- Add Torznab category filtering for YAML plugins (`5dc3018`)
- Add kinox AJAX embed URL extraction for hoster resolution (`20e40e9`)

### API & Router Improvements
- Centralize `/api/v1/` prefix for all endpoints (`d25ee5c`)
- Rename `main.py` → `app.py`, `cli.py` → `__main__.py` (`b25bf5c`)
- Delegate router to use cases, remove inline business logic (`7c36166`)
- Wire Stremio use cases into AppState and composition (`d3f076d`)

### Search Result Caching
Cache layer for repeated search queries with configurable TTL and cache-hit indicators.

- Add `_search_cache_key()` with SHA-256 hashing of plugin + query + category
- Add cache read/write to `TorznabSearchUseCase` with graceful error handling
- Add `search_ttl_seconds` config (default 900s / 15 minutes, 0 = disabled)
- Add `X-Cache: HIT/MISS` response header to Torznab search responses

### Plugin Fixes (website changes)
Five plugins updated to match changed website structures.

- Fix filmfans release loading: extract `initMovie()` hash and fetch releases via `/api/v1/{hash}` JSON endpoint
- Fix kinoger search parser: update selectors for redesigned DLE template (`shortstory` → detail link extraction)
- Fix megakino_to: add GET fallback for domain verification (HEAD returns 405)
- Fix movie4k: add GET fallback for domain verification (HEAD returns 405)
- Fix streamkiste: rewrite detail parser to extract streams from meinecloud.click external script

### Test Suite Growth (160 → 3963 tests)
Test suite expanded from 160 to 3963 tests (3742 unit + 158 E2E + 25 integration + 38 live) with comprehensive coverage across all layers.

- Add unit tests for all 42 plugin test files
- Add unit tests for all 56 hoster resolvers (17 individual + 12 generic DDL + 27 XFS consolidated)
- Add unit tests for HttpxPluginBase and PlaywrightPluginBase
- Add unit tests for Stremio components (stream converter, stream sorter, TMDB client, title matcher, IMDB fallback)
- Add unit tests for release name parser, plugin registry, HTML selectors
- Add unit tests for stream link cache and hoster registry
- Add unit tests for circuit breaker, concurrency pool, graceful shutdown, metrics endpoint
- Add unit tests for EWMA scoring, plugin score cache, query pool, health prober, search prober, scoring scheduler
- Add 158 E2E tests (46 Torznab endpoint + 112 Stremio endpoint including 31 streamable link tests)
- Add 25 integration tests (config loading, crawljob lifecycle, link validation)
- Add 38 live smoke tests (plugin smoke tests + resolver contract tests)
- Migrate all resolver tests from AsyncMock to respx (httpx-native HTTP mocking)
- Add parameterised XFS resolver tests auto-generated from 27 configs

### Documentation
- Add plugin search standards (categories + pagination up to 1000) (`c1fa2c4`)
- Update agent policy — only for simple mechanical tasks (`e01246c`)
- Add team agents rules to CLAUDE.md (`2a0eddc`)
- Restructure documentation following MasterSelects pattern (`dea6fad`)

---

## v0.1.0 - 2026-02-09 (Initial Release)

First release of Scavengarr as a self-hosted Torznab/Newznab indexer. Includes the core scraping pipeline, plugin system (YAML + Python), Torznab API, CrawlJob packaging, link validation, and a comprehensive unit test suite.

### Boerse Plugin Rewrite
Complete rewrite of the boerse.sx plugin to handle the real site structure, including Cloudflare JS challenge bypass via Playwright and vBulletin form-based authentication.

- Rewrite boerse.py plugin with Playwright for Cloudflare JS challenge bypass (`502c2b7`)
- Rewrite login, search, and link extraction to match real vBulletin site structure (`7e41ad3`)
- Resolve nested `<div>` parsing bug in post content and use full `#searchform` (`9bfecf6`)
- Filter download links to known container hosts only (keeplinks.org, filecrypt.cc, etc.), deduplicate thread URLs by thread ID (`533f6aa`)
- Read boerse credentials lazily in `_ensure_session()` to avoid startup failures when env vars are not yet set (`e090033`)

### Mirror URL Fallback
Automatic domain failover for plugins with multiple mirror URLs. When the primary domain is unreachable, the system probes mirrors and falls back transparently.

- Add `mirror_urls` field to YAML plugin schema for declaring alternative domains (`1591072`)
- Add mirror domain fallback to ScrapyAdapter: probe mirrors on connection failure (`9543e2c`)
- Probe mirror URLs in health endpoint when primary domain is unreachable (`b1b8901`)
- Merge `mirror_urls` into `base_url` as a single-or-list field for simpler plugin config (`4eab6b5`)

### Multi-Link CrawlJob Packaging
CrawlJob system extended to bundle multiple validated download links from different hosters into a single `.crawljob` file, with automatic promotion of alternatives when primary links are dead.

- Multi-link CrawlJob packaging: bundle all valid hoster URLs into a single `.crawljob` artifact (`35326b7`)
- Promote alternative download links when primary link fails HEAD/GET validation (`078fcae`)

### Python Plugin System
New imperative plugin type for sites that require complex logic beyond what YAML selectors can express (authentication, JavaScript interaction, custom parsing).

- Add boerse.sx Python plugin with domain fallback across 5 mirrors and anonymizer link handling (`bf0a9d3`)
- Add Python plugin dispatch to TorznabSearchUseCase: detect `.py` plugins and call their `search()` method (`98e6081`)
- Add env var support to AuthConfig for YAML plugin credentials: `$ENV{VAR_NAME}` syntax (`5b53f00`)
- Align `PluginRegistryPort.get()` return type with concrete registry implementation (`a73c6b9`)

### Link Validation
HTTP-based link validation with parallel execution, HEAD-first strategy, and GET fallback for hosters that block HEAD requests.

- Add GET fallback to HttpLinkValidator for hosters that return 403/405 on HEAD requests (`e69cd54`)
- Add `validate_results()` method to SearchEnginePort protocol for post-search filtering (`d7d1dab`)

### Test Suite
Comprehensive unit test suite covering all three architecture layers with proper mock patterns (sync MagicMock for PluginRegistryPort, AsyncMock for async ports).

- Add comprehensive unit test suite: 160+ tests across domain, application, and infrastructure (`e0674c5`)
  - Domain: CrawlJob entity, TorznabQuery/Item/Caps, SearchResult, plugin schema validation
  - Application: CrawlJobFactory, Torznab caps/indexers/search use cases
  - Infrastructure: parsers, converters, extractors, presenter, link validator, search engine, cache
- Apply ruff format to test files for consistent style (`2040852`)

### Clean Architecture Refactor
Three-phase migration from flat codebase to Clean Architecture with Domain, Application, Infrastructure, and Interfaces layers. See `docs/refactor/COMPLETED/clean-architecture-migration.md` for full details.

**Phase 1: Domain layer cleanup**
- Remove Pydantic from Domain layer, convert all entities to `@dataclass` (`7726ba8`)

**Phase 2: Entity consolidation**
- Consolidate SearchResult definition into single canonical location (`b7bc0be`)

**Phase 3: Adapter reorganization**
- Reorganize all adapters into `infrastructure/` namespace by concern (`d97d7a3`)

**Follow-up commits:**
- Move presenter to infrastructure layer (`8729319`)
- Rename `httpx_scrapy_engine` to `search_engine` for clarity (`56b48df`)
- Rename cache factory for naming consistency (`d32066c`)
- Use shared size parser across layers, eliminating duplication (`de788dc`)
- Consolidate duplicate int parsing into `infrastructure/common/` utils (`7610b9b`)
- Add common utils structure: parsers, converters, extractors (`b0f4cca`)
- Move composition root from application to interfaces layer (correct placement) (`a9eab40`)
- Remove redundant `discover()` calls from use cases and router (`028c932`)
- Parallelize multi-stage scraping with `asyncio.gather` for non-blocking I/O (`f419b5e`)
- Prevent duplicate search results from multi-stage scraping via dedup logic (`6b7fd8d`)

### Code Quality
Codebase-wide standardization of typing patterns, docstring conventions, and language consistency.

- Standardize typing to modern Python 3.10+ syntax (`T | None`, `list[T]`, `dict[K, V]`) and replace ABC with Protocol across all ports (`84995a1`)
- Standardize docstrings: remove redundant comments, ensure consistent English documentation (`2c6278a`)
- Translate all remaining German comments and docstrings to English for international consistency (`04f4b81`, `bcfe059`, `b18711e`, `4e440d7`)
- Apply pre-commit auto-fixes: trailing whitespace, end-of-file, import sorting (`dccc4ad`, `0e6c937`)

### Documentation
Project documentation covering architecture, coding standards, plugin system, and test suite organization.

- Add comprehensive project documentation covering all architecture layers (`d1d4a56`)
- Add typing standards and test suite information to CLAUDE.md (`9c7106a`)
- Document all infrastructure components and their responsibilities in CLAUDE.md (`9abf1c3`)

### Core Infrastructure (Initial)
Foundation of the project: FastAPI server, Scrapy scraping engine, plugin loader, configuration system, and CrawlJob generation.

- Initial content commit: FastAPI/Uvicorn server, Scrapy-based scraping, Playwright integration, structlog logging, diskcache backend (`7fd6747`)
- Add YAML configuration system with pydantic-settings and plugin loader with filesystem discovery (`3889847`)
- Add CrawlJob system for `.crawljob` file generation and assorted bug fixes (`df3e952`)
- Refactoring: improve module structure, separate concerns, clean up imports (`ed53426`)

---

## KNOWN_ISSUES

The open defects are listed in [docs/current/known-issues.md](docs/current/known-issues.md).
