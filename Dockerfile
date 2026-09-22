# ── PRODUCTION DOCKERFILE FOR VANNA GTM OS ON GOOGLE CLOUD RUN ──
FROM python:3.11-slim AS base

# Install Node.js 20, Chromium for headless diagram rendering, curl, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    procps \
    git \
    ffmpeg \
    chromium \
    fonts-liberation \
    libnss3 \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || true
RUN pip install --no-cache-dir pydantic google-cloud-aiplatform requests pillow pyyaml

# Build Next.js Dashboard
WORKDIR /app/hermes-mission
COPY hermes-mission/package*.json ./
RUN npm ci --legacy-peer-deps

COPY hermes-mission/ ./
RUN npm run build

# Copy entire pipeline orchestration codebase, config, and state
WORKDIR /app
COPY config/ ./config/
COPY state/ ./state/
COPY pipeline/ ./pipeline/
COPY registry/ ./registry/
COPY ARCHITECTURE.md ./

# Create state directories
RUN mkdir -p pipeline/state/runs pipeline/state/runs_archive pipeline/state/panels state/panels pipeline/logs

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Environment settings for Cloud Run
ENV PORT=8080
ENV NODE_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV REPO_ROOT=/app
ENV CHROME_PATH=/usr/bin/chromium

EXPOSE 8080

ENTRYPOINT ["/app/docker-entrypoint.sh"]
