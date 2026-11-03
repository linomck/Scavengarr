# Deploy Scavengarr

> **Purpose:** Running the container image: tags, Compose profiles, Redis, a VPN container, a reverse proxy, the build identity.
> **Status:** how-to
> **As of:** 867eed7a

## Goal

Run Scavengarr from its container image, with a config that survives updates, an optional Redis cache, VPN container or reverse proxy, and a build that names its commit.
A run from a checkout without a container is described in [CONTRIBUTING.md](../../CONTRIBUTING.md); the settings themselves are listed in the [configuration reference](../reference/configuration.md).

## Prerequisites

- Docker with Compose, on `linux/amd64` or `linux/arm64`.
- A directory for the config (`./data`) that the container's user (`scavengarr`, uid 1000) can write.
- A TMDB API key, optional: without it the Stremio catalogs offer search only.

## Steps

### 1. Choose an image tag

`.github/workflows/image.yml` builds `ghcr.io/strob0t/scavengarr` for `linux/amd64` and `linux/arm64`, each natively on its own runner, and pushes one multi-arch manifest, so one tag runs on a PC and on an ARM board alike:

| Tag | Points at |
|---|---|
| `latest` | The newest release. |
| `vX.Y.Z` | One release (the tag `vX.Y.Z` on `main`). |
| `staging` | The newest push to the development branch (a merged Dependabot update included), built while its CI runs, not after it passed. |
| `sha-<commit>` | One build (the commit's first 12 characters). |

Every release tag also gets its page under the repository's Releases (`.github/workflows/release.yml`): the summary and the entry titles of its `CHANGELOG.md` section, by kind, the image tag and a link to the full section, so the page says what a `vX.Y.Z` brings before you pull it.

Every image carries its commit, in the label `org.opencontainers.image.revision` and in its build identity (step 8).

### 2. Start the container

```bash
docker run -d --name scavengarr \
  --init \
  -p 7979:7979 \
  -v ./data:/app/config \
  -v ./cache:/app/cache \
  ghcr.io/strob0t/scavengarr:latest
```

`--init` reaps orphaned Chromium and driver processes, which the app as PID 1 would not.

| Container path | Holds | Mount |
|---|---|---|
| `/app/config` | `config.yaml`, read through `SCAVENGARR_CONFIG`. | Recommended: the entrypoint writes the default there on the first start. |
| `/app/cache` | The diskcache store: search cache, CrawlJobs, clearance cookies, scores. | Recommended: without it a restart loses them. |
| `/app/plugins` | The plugins. | Optional: a mount replaces the bundled plugins (plugin work). |

### 3. Or use Docker Compose

The repository's [`docker-compose.yml`](../../docker-compose.yml) runs the published image, or builds the checkout with the block it carries commented. It joins the external `proxy` network of Traefik (labels carry its router; no port is published) and always runs Byparr, wired in through `SCAVENGARR_PLAYWRIGHT_SOLVER_URL`.

```bash
docker compose up -d                          # start
docker compose pull && docker compose up -d   # update
```

The service sets `init: true`, `shm_size: 1gb` (Chromium needs shared memory), `FORWARDED_ALLOW_IPS` for a reverse proxy (step 7) and a log rotation (Troubleshooting).
An updater such as [watchtower](https://github.com/containrrr/watchtower) can run the update on a schedule.

### 4. Configure it

The image sets these defaults as environment variables, so they win over the same keys of a mounted `config.yaml`; change them in the container's environment:

| Variable | Value |
|---|---|
| `SCAVENGARR_ENVIRONMENT` | `prod` |
| `SCAVENGARR_CONFIG` | `/app/config/config.yaml` |
| `SCAVENGARR_LOG_LEVEL` | `INFO` |
| `SCAVENGARR_LOG_FORMAT` | `json` |
| `SCAVENGARR_PLUGIN_DIR` | `/app/plugins` (the bundled plugins) |
| `SCAVENGARR_CACHE_DIR` | `/app/cache` |
| `SCAVENGARR_PLAYWRIGHT_HEADLESS` | `false` |
| `HOST`, `PORT` | `0.0.0.0`, `7979` |

`SCAVENGARR_COMMIT` and `SCAVENGARR_BUILT` are not set: the image carries its build in `build_info.json` (step 8), and set in the container they override it.

The entrypoint, `docker/entrypoint.sh`, prepares the container before the app starts:

- When `SCAVENGARR_CONFIG` names no file, it writes the image's default config there (`/app/config.default.yaml`, a copy of `data/config.yaml`) and logs one line, since a volume over `/app/config` hides the image's files.
- A config already there stays as it is, so a new release's default config does not reach it.
- When the directory is not writable for uid 1000 (a bind-mounted directory Docker created as root, for example), it says so and the app starts on its built-in defaults.
- Unless `DISPLAY` is set, it starts Xvfb on `:99` for the headful browser, removing a stale lock from before a restart, and waits up to 5 s for its socket.
- It `exec`s `python -m scavengarr.interfaces.cli`, so the app receives the stop signal itself and CLI flags appended to `docker run` reach it.

Set the TMDB key and what else your host needs either in `./data/config.yaml` or as `environment:` entries; the [configuration reference](../reference/configuration.md#production-through-the-environment) lists the entries that reproduce the default config.
`SCAVENGARR_CACHE_TTL_SECONDS` is not one of them: no cache writer uses it.

### 5. Use the Redis cache

Start Redis (the compose profile `redis`, or a service of your own) and select it with `SCAVENGARR_CACHE_BACKEND=redis` and `SCAVENGARR_CACHE_REDIS_URL`, or in the config file:

```yaml
cache:
  backend: "redis"
  redis_url: "redis://redis:6379/0"
```

Give Scavengarr a Redis database of its own: its keys carry no prefix.

### 6. Run behind a VPN container

When the sites must see a VPN address, run Scavengarr in the network namespace of a VPN container (gluetun, for example).
The ports are then published on the VPN container, and every request leaves through the tunnel, DNS too when the VPN container resolves through it, as gluetun does by default:

```yaml
services:
  scavengarr:
    image: ghcr.io/strob0t/scavengarr:latest
    container_name: scavengarr
    network_mode: service:vpn # publish 7979 on the vpn service instead
    volumes:
      - ./scavengarr/config:/app/config
      - scavengarr-cache:/app/cache
    shm_size: 1gb
    init: true
    restart: unless-stopped

volumes:
  scavengarr-cache:
```

A container in another one's namespace loses its network when that one is recreated, for example by an update of the VPN image: recreate Scavengarr after it (`docker compose up -d --force-recreate scavengarr`).
Set `telemetry.tracing_endpoint` to an IP address there, since a host name would be looked up through the VPN.

### 7. Put a reverse proxy in front

Give Scavengarr a host name of its own and proxy it at `/`.
A path prefix (`/scavengarr/`) is not supported: the feed's `<link>` and `<enclosure>` URLs and the Stremio stream URLs are built from the request without it.

The proxy must pass the `Host` header and send `X-Forwarded-Proto` and `X-Forwarded-For`:

```nginx
location / {
    proxy_pass http://scavengarr:7979;
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

Caddy's `reverse_proxy scavengarr:7979` sends these headers by default.
The app honors them only from the addresses in `FORWARDED_ALLOW_IPS` ([server variables](../reference/configuration.md#server-variables)).
In Docker the proxy reaches the container from the bridge gateway, hence the private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `fc00::/7`) that `docker-compose.yml` sets.
Every client in those networks can then set the headers too, which affects only its own links, its per-IP rate limit and its logged address.

### 8. Build the image yourself

```bash
docker build -f Dockerfile.prod -t scavengarr .
```

The build records its identity: the startup line `app_startup_complete version=<version> commit=<12 characters> built=<time>`, `/api/v1/healthz`, the Stremio manifest and the `scavengarr_build_info` metric report it (`build_identity()` of `infrastructure/version.py`).
The version is the installed package's.
The commit and the time come from `build_info.json` beside the package (`/app/src/scavengarr/build_info.json` in the image), which `docker/build_info.py` writes in a build stage of its own (`buildinfo`), so the git files stay out of the runtime image:

- The commit comes from the build argument `SCAVENGARR_COMMIT` or, without one, from the checkout's `.git/HEAD` and the ref it points at; `.dockerignore` lets those files through, and no git binary is needed.
- The time comes from `SCAVENGARR_BUILT` or the clock.
- `image.yml` passes the commit's first 12 characters and the date; a local `docker compose up -d --build` from a checkout needs no arguments.
- A rebuild of the same commit without arguments keeps the cached stage, the first build's time included.

A Dockerfile that fetches the source itself with BuildKit's git `ADD` gets no `.git` and no build arguments, so it reports `commit=unknown built=unknown` until it keeps the git directory and runs the script before the app's source is copied in:

```dockerfile
FROM scratch AS src
ADD --keep-git-dir=true ${SCAVENGARR_REPO}#${SCAVENGARR_REF} /

# The source with build_info.json and without .git
FROM python:3.14-slim AS buildinfo
COPY --from=src / /ctx
RUN python /ctx/docker/build_info.py --git /ctx/.git \
        --out /ctx/src/scavengarr/build_info.json && \
    rm -rf /ctx/.git

# in the runtime stage, in place of COPY --from=src / ./
COPY --from=buildinfo /ctx/ ./
```

Use the base image `Dockerfile.prod` uses for the `buildinfo` stage.
Stages that read single files of `src` (a dependency manifest, for one) keep reading them there; only the runtime stage's source copy moves to `buildinfo`, since `src` now holds `.git`.
Running the script in the runtime stage instead keeps the whole `.git` in the image.
Passing `SCAVENGARR_COMMIT` and `SCAVENGARR_BUILT` as build arguments from the compose file works too, when something on the host computes them.

## Verify

```bash
# Liveness: version, commit, build time, plugin count, hosters
curl http://localhost:7979/api/v1/healthz

# Readiness: 200; the port opens only after the startup has finished, and a
# network lost for 5 min turns it 503 (the image's healthcheck asks it)
curl http://localhost:7979/api/v1/readyz

# The loaded plugins
curl http://localhost:7979/api/v1/torznab/indexers
```

The startup log's `config_effective` line names every setting away from its default and the layer it came from ([startup log](../reference/configuration.md#startup-log)).
Next: [connect Prowlarr](connect-prowlarr.md) or add the Stremio addon ([Stremio addon](../current/stremio-addon.md)).

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| The app runs on its built-in defaults; the log says the config directory is not writable. | Make the mounted directory writable for uid 1000 (`chown 1000:1000 ./data`). |
| A changed default of a new release does not apply. | The seeded `config.yaml` stays as it is; compare it with `data/config.yaml` of the release. |
| Every search and lookup fails after the VPN container was updated; after 5 min and three failed checks the container turns unhealthy (with Redis; diskcache keeps it healthy). | The namespace went with the old VPN container; recreate Scavengarr (step 6). |
| Most German plugins find no site. | A German ISP's resolver blocks the domains of the CUII list, most German streaming sites among them; use a resolver that does not apply the block, such as the VPN container's (step 6). |
| Links come out as `http://` behind the proxy, and the browser blocks them as mixed content. | The proxy's address is not in `FORWARDED_ALLOW_IPS` (step 7). |
| `commit=unknown built=unknown` in the startup line. | The build had neither `.git` nor build arguments (step 8). |
| The Docker log fills the disk. | Docker's `json-file` driver keeps every record without a bound; set a rotation as below. |

The healthcheck asks `/api/v1/readyz`, which answers 503 once the cache backend's ping and the DNS resolution of a public name have both failed for longer than 5 min ([Readiness](../current/observability.md#readiness)); the third failed check in a row, 30 s apart, marks the container unhealthy, and Docker restarts nothing by itself.
A `healthcheck:` of the service in your Compose file replaces the image's: let it ask `/api/v1/readyz` too, since `/api/v1/healthz` answers over loopback whatever fails outside, and the deploy check's network row warns while nothing asks readiness ([Check a deploy](operations.md#5-check-a-deploy)).
With the diskcache backend the cache check needs no network, so a container without a network keeps reporting healthy there.
The app logs such an outage once where it can (`network_lost` and `network_recovered` for the readiness probe; `redis_unavailable` and `redis_recovered` for Redis; `query_pool_unavailable` when the scoring scheduler cannot reach IMDb), and a log rotation keeps the rest bounded:

```yaml
    logging:
      driver: json-file
      options:
        max-size: 20m
        max-file: "3"
```
