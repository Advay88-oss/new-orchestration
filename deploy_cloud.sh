#!/usr/bin/env bash
# Deploy the whole Vanna GTM OS to GCP — the dashboard, the pipeline (every
# agent, the Brain MCP server), the brand brain (Cloud SQL Postgres +
# pgvector, row-level security), the scheduler and the Telegram webhook.
#
#   bash deploy_cloud.sh all            # everything, in order
#   bash deploy_cloud.sh <step> ...     # secrets sql iam build jobs schema migrate service scheduler telegram monitoring
#
#   service   vanna-gtm-mission    Cloud Run: the dashboard (owner actions via OWNER_KEY)
#   job       vanna-gtm-pipeline   Cloud Run Job: a GTM cycle, or the scheduler's tick
#   job       vanna-gtm-admin      Cloud Run Job: Cloud SQL schema + brain migration
#   schedule  vanna-gtm-tick       Cloud Scheduler: the tick, hourly (Notion sync, metrics)
#   database  brand-brain          Cloud SQL, Postgres 17, db-f1-micro
#
# Secrets go from pipeline/.env to Secret Manager through a pipe — never
# printed, never on a command line. Every step is safe to re-run.
set -euo pipefail

PROJECT="sales-agent-504607"                  # project number 114262736718
REGION="us-central1"
SA="114262736718-compute@developer.gserviceaccount.com"
BUCKET="vanna-gtm-state-504607"
SQL="brand-brain"; DB="brand_brain"; CONN="${PROJECT}:${REGION}:${SQL}"
SERVICE="vanna-gtm-mission"; JOB="vanna-gtm-pipeline"; ADMIN_JOB="vanna-gtm-admin"; TICK="vanna-gtm-tick"
REPO="us-central1-docker.pkg.dev/${PROJECT}/vanna-repo/vanna-gtm-os"
URL="https://vanna-gtm-mission-114262736718.us-central1.run.app"
ROOT="$(cd "$(dirname "$0")" && pwd)"
PY="${ROOT}/.venv/Scripts/python.exe"; [ -x "$PY" ] || PY="${ROOT}/.venv/bin/python"

GCLOUD="$(command -v gcloud)"
TOKEN_FILE="$(mktemp -t gcloud_token.XXXXXX)"
trap 'rm -f "${TOKEN_FILE}"' EXIT
"${GCLOUD}" auth application-default print-access-token > "${TOKEN_FILE}"
gc() { "${GCLOUD}" "$@" --project "${PROJECT}" --access-token-file="${TOKEN_FILE}"; }
say() { printf '\n== %s\n' "$*"; }

# A value from pipeline/.env (or the environment), to stdout, for a pipe.
envval() { (cd "$ROOT" && "$PY" -c "import sys; from pipeline.brand_brain.store import _env_file as e; sys.stdout.write(e(sys.argv[1]) or '')" "$1"); }
has_secret() { gc secrets describe "$1" >/dev/null 2>&1; }
# put_secret NAME < value   (creates the secret on first use)
put_secret() {
  has_secret "$1" || gc secrets create "$1" --replication-policy=automatic >/dev/null
  gc secrets versions add "$1" --data-file=- >/dev/null
}
gen() { "$PY" -c "import secrets; print(secrets.token_urlsafe(32), end='')"; }
secret_val() { gc secrets versions access latest --secret="$1"; }

# env var -> secret name, for everything the pipeline reads
MAP=(GEMINI_API_KEY:gemini-api-key VEO_API_KEY:veo-api-key APIFY_TOKEN:apify-token
     TELEGRAM_BOT_TOKEN:telegram-bot-token TELEGRAM_REVIEWER_CHAT_ID:telegram-reviewer-chat-id
     RUNWAY_API_KEY:runway-api-key BRAIN_SECRET_KEY:brain-secret-key BRAIN_INVITE_SECRET:brain-invite-secret
     NOTION_OAUTH_CLIENT_ID:notion-oauth-client-id NOTION_OAUTH_CLIENT_SECRET:notion-oauth-client-secret)

step_secrets() {
  say "secrets: pipeline/.env -> Secret Manager (values are piped, never shown)"
  for pair in "${MAP[@]}"; do
    k="${pair%%:*}"; s="${pair##*:}"
    v="$(envval "$k")"
    if [ -z "$v" ]; then echo "  $k: not set locally, skipped"; continue; fi
    printf '%s' "$v" | put_secret "$s"; unset v
    echo "  $k -> $s"
  done
  for s in telegram-webhook-secret brain-app-password brain-pg-admin-password; do
    if has_secret "$s"; then echo "  $s: exists"; else gen | put_secret "$s"; echo "  $s: generated"; fi
  done
  # The Cloud SQL connection strings, built from the generated passwords.
  (printf 'postgresql://brain_app:'; secret_val brain-app-password; printf '@/%s?host=/cloudsql/%s' "$DB" "$CONN") | put_secret brain-database-url
  (printf 'postgresql://postgres:'; secret_val brain-pg-admin-password; printf '@/%s?host=/cloudsql/%s' "$DB" "$CONN") | put_secret brain-pg-admin-url
  echo "  brain-database-url, brain-pg-admin-url: set"
}

step_sql() {
  say "Cloud SQL ${SQL}: database and admin password"
  until [ "$(gc sql instances describe "$SQL" --format='value(state)')" = "RUNNABLE" ]; do echo "  waiting for the instance..."; sleep 20; done
  gc sql databases describe "$DB" --instance "$SQL" >/dev/null 2>&1 || gc sql databases create "$DB" --instance "$SQL"
  # The password travels in a request body from stdin, not on a command line.
  secret_val brain-pg-admin-password | "$PY" -c "import json,sys; print(json.dumps({'name':'postgres','password':sys.stdin.read()}))" |
    curl -sf -X PUT -H "Authorization: Bearer $(cat "$TOKEN_FILE")" -H "Content-Type: application/json" --data-binary @- \
      "https://sqladmin.googleapis.com/v1/projects/${PROJECT}/instances/${SQL}/users?name=postgres" >/dev/null
  echo "  database ${DB} ready; admin password set"
}

step_iam() {
  say "IAM: the runtime service account can read secrets, reach Cloud SQL, start the pipeline job and call the image/Veo models"
  for role in roles/secretmanager.secretAccessor roles/cloudsql.client roles/run.developer roles/aiplatform.user; do
    gc projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:${SA}" --role="$role" --condition=None >/dev/null
    echo "  $role"
  done
  gc iam service-accounts add-iam-policy-binding "$SA" --member="serviceAccount:${SA}" --role=roles/iam.serviceAccountUser >/dev/null
  echo "  roles/iam.serviceAccountUser (on itself, to run jobs as itself)"
}

IMAGE_FILE="${ROOT}/.last_cloud_image"
step_build() {
  IMAGE="${REPO}:$(date +%Y%m%d-%H%M%S)"
  say "build ${IMAGE} (Cloud Build, ~10-15 min)"
  (cd "$ROOT" && gc builds submit . --tag "$IMAGE" --timeout=3600s --machine-type=e2-highcpu-8)
  echo "$IMAGE" > "$IMAGE_FILE"
}
image() { [ -s "$IMAGE_FILE" ] || { echo "no image built yet: run the build step" >&2; exit 1; }; cat "$IMAGE_FILE"; }

# Secret env for the pipeline, only those that exist.
secrets_flag() {
  local out="BRAIN_DATABASE_URL=brain-database-url:latest"
  for pair in "${MAP[@]}"; do
    k="${pair%%:*}"; s="${pair##*:}"
    has_secret "$s" && out="${out},${k}=${s}:latest"
  done
  [ "${1:-}" = "web" ] && out="${out},TELEGRAM_WEBHOOK_SECRET=telegram-webhook-secret:latest"
  [ "${1:-}" = "admin" ] && out="${out},BRAIN_PG_ADMIN_URL=brain-pg-admin-url:latest,BRAIN_APP_PASSWORD=brain-app-password:latest"
  echo "$out"
}
COMMON_ENV="VANNA_STATE_BUCKET=${BUCKET},VANNA_CLOUD=1,GOOGLE_CLOUD_PROJECT=${PROJECT},VANNA_MEDIA_PROJECT=${PROJECT},DASHBOARD_URL=${URL},VANNA_REGION=${REGION}"

step_jobs() {
  local img; img="$(image)"
  say "jobs: ${JOB} (cycle / tick) and ${ADMIN_JOB} (schema / migration)"
  gc run jobs deploy "$JOB" --image "$img" --region "$REGION" --service-account "$SA" \
    --command=//app/docker-entrypoint.sh --args=job,tick \
    --set-cloudsql-instances "$CONN" --set-secrets "$(secrets_flag job)" --set-env-vars "$COMMON_ENV" \
    --cpu 2 --memory 4Gi --task-timeout 3600 --max-retries 0
  gc run jobs deploy "$ADMIN_JOB" --image "$img" --region "$REGION" --service-account "$SA" \
    --command=//app/docker-entrypoint.sh --args=job,admin-schema \
    --set-cloudsql-instances "$CONN" --set-secrets "$(secrets_flag admin)" --set-env-vars "$COMMON_ENV" \
    --cpu 1 --memory 2Gi --task-timeout 1800 --max-retries 0
}

step_schema() {
  say "schema: Cloud SQL tables, row-level security and the ops tables (idempotent)"
  gc run jobs execute "$ADMIN_JOB" --region "$REGION" --wait --args=job,admin-schema
}

step_monitoring() {
  # From outside GCP's jobs: an uptime check on the dashboard, and an email
  # to the gcloud account's address when it fails for 10 minutes. The hourly
  # watch covers everything else, on Telegram.
  say "monitoring: uptime check on ${URL}/api/health, email on failure"
  local email host channel check policy
  email="$("${GCLOUD}" config get-value account 2>/dev/null)"
  host="${URL#https://}"
  channel="$(gc beta monitoring channels list --filter='displayName="Mission Control owner"' --format='value(name)' | head -1)"
  if [ -z "$channel" ]; then
    channel="$(gc beta monitoring channels create --display-name="Mission Control owner" --type=email \
      --channel-labels=email_address="$email" --format='value(name)')"
  fi
  check="$(gc monitoring uptime list-configs --filter='displayName="Mission Control dashboard"' --format='value(name)' | head -1)"
  if [ -z "$check" ]; then
    gc monitoring uptime create "Mission Control dashboard" --resource-type=uptime-url \
      --resource-labels=host="$host",project_id="$PROJECT" --path=/api/health --protocol=https \
      --period=5 --timeout=10 >/dev/null
    check="$(gc monitoring uptime list-configs --filter='displayName="Mission Control dashboard"' --format='value(name)' | head -1)"
  fi
  local cid="${check##*/}"
  if [ -z "$(gc alpha monitoring policies list --filter='displayName="Mission Control dashboard down"' --format='value(name)' | head -1)" ]; then
    policy="$(mktemp -t policy.XXXXXX).json"
    cat > "$policy" <<JSON
{
  "displayName": "Mission Control dashboard down",
  "combiner": "OR",
  "conditions": [{
    "displayName": "uptime check failing",
    "conditionThreshold": {
      "filter": "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND metric.label.check_id=\"${cid}\" AND resource.type=\"uptime_url\"",
      "comparison": "COMPARISON_GT",
      "thresholdValue": 1,
      "duration": "600s",
      "aggregations": [{"alignmentPeriod": "300s", "perSeriesAligner": "ALIGN_NEXT_OLDER",
                        "crossSeriesReducer": "REDUCE_COUNT_FALSE", "groupByFields": ["resource.label.host"]}],
      "trigger": {"count": 1}
    }
  }],
  "notificationChannels": ["${channel}"],
  "documentation": {"content": "The Mission Control dashboard has failed its health check for 10 minutes: ${URL}"}
}
JSON
    gc alpha monitoring policies create --policy-from-file="$policy" >/dev/null
    rm -f "$policy"
  fi
  echo "  uptime check ${cid}; alerts go to the gcloud account's email"
}

step_migrate() {
  say "migrate: local brain -> bucket snapshot -> Cloud SQL"
  (cd "$ROOT" && "$PY" -m pipeline.gtm_os.state_sync push-state | tail -5)
  gc run jobs execute "$ADMIN_JOB" --region "$REGION" --wait --args=job,admin-schema
  gc run jobs execute "$ADMIN_JOB" --region "$REGION" --wait --args=job,admin-migrate
}

step_service() {
  local img; img="$(image)"
  say "service: ${SERVICE} (the dashboard, cloud mode)"
  gc run deploy "$SERVICE" --image "$img" --region "$REGION" --platform managed --service-account "$SA" \
    --allow-unauthenticated --port 8080 --cpu 1 --memory 2Gi --no-cpu-throttling \
    --min-instances 0 --max-instances 1 --timeout 300 \
    --add-cloudsql-instances "$CONN" --update-secrets "$(secrets_flag web)" \
    --update-env-vars "${COMMON_ENV},VANNA_PIPELINE_JOB=${JOB},VANNA_REGION=${REGION},NOTION_OAUTH_REDIRECT_URI=${URL}/api/connect/notion/callback"
}

step_scheduler() {
  say "Cloud Scheduler ${TICK}: the pipeline tick, hourly"
  local uri="https://run.googleapis.com/v2/projects/${PROJECT}/locations/${REGION}/jobs/${JOB}:run"
  if gc scheduler jobs describe "$TICK" --location "$REGION" >/dev/null 2>&1; then
    gc scheduler jobs update http "$TICK" --location "$REGION" --schedule "0 * * * *" --uri "$uri" \
      --http-method POST --oauth-service-account-email "$SA" >/dev/null
  else
    gc scheduler jobs create http "$TICK" --location "$REGION" --schedule "0 * * * *" --uri "$uri" \
      --http-method POST --oauth-service-account-email "$SA" --time-zone "Etc/UTC" >/dev/null
  fi
  echo "  hourly -> ${JOB} (tick: notion_sync, metrics_collect, ops_watch)"
}

step_telegram() {
  say "Telegram: buttons and replies now arrive by webhook at ${URL}/api/telegram/webhook"
  { envval TELEGRAM_BOT_TOKEN; printf '\n'; secret_val telegram-webhook-secret; } | "$PY" -c "
import json, sys, urllib.request
token, secret = sys.stdin.read().split('\n', 1)
body = json.dumps({'url': '${URL}/api/telegram/webhook', 'secret_token': secret.strip(),
                   'allowed_updates': ['callback_query', 'message'], 'drop_pending_updates': False}).encode()
req = urllib.request.Request('https://api.telegram.org/bot' + token.strip() + '/setWebhook', data=body,
                             headers={'Content-Type': 'application/json'})
print('  setWebhook:', json.load(urllib.request.urlopen(req, timeout=20)).get('description'))"
}

steps=("$@"); [ "${#steps[@]}" -eq 0 ] && steps=(all)
[ "${steps[0]}" = "all" ] && steps=(secrets sql iam build jobs schema migrate service scheduler telegram monitoring)
for s in "${steps[@]}"; do "step_$s"; done
say "done: ${URL}"
