#!/usr/bin/env bash
set -e

echo "================================================================================"
echo "🚀 STARTING VANNA GTM OPERATING SYSTEM ON GOOGLE CLOUD RUN"
echo "================================================================================"

# 0. Restore what the system has learned (brand brain, founder decisions,
#    coach rules, exemplars) from the state bucket. Missing files only; a
#    failure here must not stop the dashboard from starting.
echo "▶ Restoring brain and learning state from GCS..."
python -m pipeline.gtm_os.state_sync pull-state || echo "⚠ state restore skipped"

# 1. Start Spend Proxy Watchdog (:8900) in background
echo "▶ Launching Vertex Spend Proxy on port 8900..."
python /app/pipeline/scripts/vertex_spend_proxy.py --port 8900 &
PROXY_PID=$!
echo "✓ Spend Proxy active with PID $PROXY_PID"

# 2. Wait for spend proxy to be ready
for i in $(seq 1 15); do
  if curl -s http://127.0.0.1:8900/health > /dev/null 2>&1 || curl -s http://127.0.0.1:8900/ > /dev/null 2>&1; then
    echo "✓ Spend proxy health check passed!"
    break
  fi
  sleep 1
done

# 3. Start Configurable Autonomous Scheduler Daemon in background
echo "▶ Launching Configurable Autonomous Scheduler Daemon..."
python /app/pipeline/scheduler/configurable_scheduler_daemon.py --daemon &
SCHEDULER_PID=$!
echo "✓ Autonomous Scheduler Daemon active with PID $SCHEDULER_PID"

# 4. Start Next.js Mission Control Dashboard on $PORT (Cloud Run default: 8080)
TARGET_PORT=${PORT:-8080}
echo "▶ Launching Next.js Mission Control Dashboard on port $TARGET_PORT..."
cd /app/hermes-mission
exec npm run start -- -p "$TARGET_PORT"
