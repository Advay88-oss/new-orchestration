#!/usr/bin/env bash
# Deploy the Mission Control dashboard to Cloud Run.
#
# The 13 agents are NOT deployed and cannot be. They need the local Chrome
# bridge, the Brain DB, font files and four minutes per cycle. The pipeline
# runs on the founder's machine and pushes each run to GCS; this service reads
# from there. `pipeline/gtm_os/state_sync.py` is the writing half of that seam
# and `hermes-mission/lib/gcs.ts` is the reading half.
#
# This replaces deploy_gcp.sh, which built from the repo root — where the
# Dockerfile lived in mission-control/, a directory that no longer exists.
set -euo pipefail

PROJECT_ID="sales-agent-504607"      # project number 114262736718 — the one
                                     # the live service already runs in
REGION="us-central1"
SERVICE_NAME="vanna-gtm-mission"
IMAGE="us-central1-docker.pkg.dev/${PROJECT_ID}/vanna-repo/${SERVICE_NAME}:$(date +%Y%m%d-%H%M%S)"
STATE_BUCKET="${VANNA_STATE_BUCKET:-vanna-gtm-state-504607}"
SRC="$(cd "$(dirname "$0")" && pwd)/hermes-mission"

# Use the POSIX `gcloud` shim, not `gcloud.cmd`. The .cmd wrapper re-invokes
# itself through cmd.exe, which splits its own install path on the space in
# "Advay Anand" and dies with "\'C:\Users\Advay is not recognized".
GCLOUD="$(command -v gcloud || true)"
[ -z "${GCLOUD}" ] && { echo "gcloud not on PATH"; exit 1; }

# The CLI is not logged in on this machine; ADC is. Every call is given the
# ADC token explicitly rather than relying on `gcloud auth login`.
TOKEN_FILE="$(mktemp -t gcloud_token.XXXXXX)"
trap 'rm -f "${TOKEN_FILE}"' EXIT
"${GCLOUD}" auth application-default print-access-token > "${TOKEN_FILE}"
AUTH=(--project "${PROJECT_ID}" --access-token-file="${TOKEN_FILE}")

echo "=============================================================="
echo " Deploying ${SERVICE_NAME}"
echo "   project : ${PROJECT_ID} (${REGION})"
echo "   source  : ${SRC}"
echo "   state   : gs://${STATE_BUCKET}"
echo "=============================================================="

echo
echo "[1/2] Building image via Cloud Build..."
( cd "${SRC}" && "${GCLOUD}" builds submit . --tag "${IMAGE}" "${AUTH[@]}" )

echo
echo "[2/2] Deploying to Cloud Run..."
"${GCLOUD}" run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars "VANNA_STATE_BUCKET=${STATE_BUCKET}" \
  "${AUTH[@]}"

echo
URL=$("${GCLOUD}" run services describe "${SERVICE_NAME}" --region "${REGION}" \
      --format 'value(status.url)' "${AUTH[@]}")
echo "Deployed: ${URL}"
echo
echo "Check:"
echo "  curl -s ${URL}/api/gtm/agents | head -c 300"
