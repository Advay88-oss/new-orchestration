# Vanna GTM OS on GCP — one image, two roles.
#
#   web  the Mission Control dashboard (Cloud Run service). Python is in the
#        image so owner actions (approve, Brand Brain, Notion, learning) run
#        the same pipeline code as on the laptop.
#   job  the pipeline (Cloud Run Job): python -m pipeline.gtm_os.cloud_job
#        cycle | tick | admin-schema | admin-migrate — the agents, the Brain
#        MCP server (a child process over stdio), the scheduler's tick.
#
# The brand brain is Cloud SQL (Postgres + pgvector, row-level security);
# runs, assets and learned state are in the GCS bucket. Nothing secret is in
# the image: keys arrive as environment variables from Secret Manager.

# ---- dashboard build ------------------------------------------------------
FROM node:20-bookworm-slim AS web
WORKDIR /build
COPY hermes-mission/package.json hermes-mission/package-lock.json* ./
# The lockfile is the build: no silent fallback to whatever npm resolves today.
RUN npm ci
COPY hermes-mission/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ---- runtime --------------------------------------------------------------
FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 NEXT_TELEMETRY_DISABLED=1 \
    PYTHONPATH=/app REPO_ROOT=/app VANNA_REPO_ROOT=/app VANNA_PYTHON=/usr/local/bin/python \
    PORT=8080 HOSTNAME=0.0.0.0 NODE_ENV=production \
    PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl ffmpeg fonts-liberation fonts-dejavu-core \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# Every Python package pinned with hashes (requirements.lock, compiled from
# requirements.txt): the same versions on every build, nothing tampered with.
COPY requirements.txt requirements.lock ./
RUN pip install --require-hashes -r requirements.lock \
 && python -m playwright install --with-deps chromium \
 && rm -rf /var/lib/apt/lists/*

# The dashboard: Next's standalone server, with its static files beside it.
COPY --from=web /build/.next/standalone /app/hermes-mission
COPY --from=web /build/.next/static /app/hermes-mission/.next/static
COPY --from=web /build/public /app/hermes-mission/public

# The pipeline and what it reads at run time.
COPY pipeline/ ./pipeline/
COPY config/ ./config/
COPY registry/ ./registry/
COPY knowledge/ ./knowledge/
RUN mkdir -p state/panels pipeline/state/gtm_runs pipeline/state/panels pipeline/logs

COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh && chmod +x /app/docker-entrypoint.sh

# Not root: a hole in the dashboard or a package runs as a user who owns only
# /app (state is written there) and the browser for the poster renders.
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin app \
 && chown -R app:app /app /opt/ms-playwright
USER app
EXPOSE 8080
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["web"]
