#!/usr/bin/env bash
set -e

PROJECT_ID="sales-agent-504607"
REGION="us-central1"
SERVICE_NAME="vanna-gtm-mission"
IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/vanna-repo/${SERVICE_NAME}:latest"

# Get ADC token
GCLOUD_CMD="gcloud"
if command -v gcloud.cmd &> /dev/null; then
  GCLOUD_CMD="gcloud.cmd"
fi

TOKEN=$($GCLOUD_CMD auth application-default print-access-token)

# Use Windows-accessible Temp directory
if [ -n "$LOCALAPPDATA" ]; then
  TOKEN_FILE="$(cygpath -w "$LOCALAPPDATA/Temp/gcloud_token.txt" 2>/dev/null || echo "$LOCALAPPDATA/Temp/gcloud_token.txt")"
  echo "${TOKEN}" > "$LOCALAPPDATA/Temp/gcloud_token.txt"
else
  TOKEN_FILE="/tmp/gcloud_token.txt"
  echo "${TOKEN}" > "${TOKEN_FILE}"
fi

echo "================================================================================"
echo "🚀 DEPLOYING VANNA GTM MISSION CONTROL TO GOOGLE CLOUD RUN"
echo "================================================================================"

echo ""
echo "[1/3] Setting GCP project to ${PROJECT_ID}..."
$GCLOUD_CMD config set project "${PROJECT_ID}" --access-token-file="${TOKEN_FILE}"

echo ""
echo "[2/3] Building container image via Google Cloud Build..."
$GCLOUD_CMD builds submit --project "${PROJECT_ID}" --tag "${IMAGE_NAME}" --access-token-file="${TOKEN_FILE}" .

echo ""
echo "[3/3] Deploying to Google Cloud Run (${REGION})..."
$GCLOUD_CMD run deploy "${SERVICE_NAME}" \
    --project "${PROJECT_ID}" \
    --image "${IMAGE_NAME}" \
    --platform managed \
    --region "${REGION}" \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --port 8080 \
    --no-cpu-throttling \
    --min-instances 1 \
    --access-token-file="${TOKEN_FILE}" \
    --set-env-vars="NODE_ENV=production,PORT=8080,VERTEX_PROJECT=${PROJECT_ID},VERTEX_LOCATION=${REGION}"

if [ -n "$LOCALAPPDATA" ]; then
  rm -f "$LOCALAPPDATA/Temp/gcloud_token.txt"
else
  rm -f "${TOKEN_FILE}"
fi

echo ""
echo "================================================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "   Live Service URL: https://vanna-gtm-mission-114262736718.us-central1.run.app"
echo "================================================================================"
