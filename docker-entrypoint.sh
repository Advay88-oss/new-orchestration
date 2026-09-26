#!/usr/bin/env bash
# One image, two roles (see Dockerfile).
#   web                 the dashboard (Cloud Run service)
#   job <cloud_job ...> the pipeline (Cloud Run Job), e.g. `job cycle --directive "..."`
set -euo pipefail
role="${1:-web}"
shift || true

if [ "$role" = "job" ]; then
  exec python -m pipeline.gtm_os.cloud_job "$@"
fi

# web: restore learned state (tenant images, exemplars, the scheduler's clock,
# the Telegram notes) before serving; a failure must not keep the dashboard down.
echo "restoring state from gs://${VANNA_STATE_BUCKET:-vanna-gtm-state-504607} ..."
timeout 180 python -m pipeline.gtm_os.state_sync pull-state || echo "state restore skipped"
cd /app/hermes-mission
exec node server.js
