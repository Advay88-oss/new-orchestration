# 24/7 Autonomous Continuous Marketing Daemon Implementation Plan

> **For Hermes:** System 2 Autonomous Continuous Daemon implementation for non-stop 24-hour GTM execution.

**Goal:** Transform System 2 from an on-demand command-driven pipeline into a fully self-operating 24/7 autonomous marketing engine that continuously monitors market signals, generates strategy, writes platform-native copy, synthesizes bespoke visuals (`gemini-3.1-flash-image`), queues Remotion videos, enforces 100-point adversarial review, notifies the founder via Telegram, and tracks performance without manual prompting.

**Architecture:** A detached Python daemon controller (`pipeline/scripts/daemon_manager.py`) managing `run_autonomous_gtm_master.py --continuous` with PID tracking, log rotation, budget-guard checks, and a Next.js API route (`/api/daemon`) wired directly to the Mission Control Cockpit header for live control.

**Tech Stack:** Python 3.11, Next.js 14, Vertex AI (`gemini-3.8-flash`), Google Model Garden (`gemini-3.1-flash-image`), Remotion React, Telegram Bot API, `:8900` Spend Proxy.

---

### Task 1: Create Daemon Manager & Process Lifecycle Controller

**Objective:** Build a robust, background daemon manager that starts, monitors, polls, and stops the 24/7 continuous autonomous GTM cycle with PID tracking and log redirection.

**Files:**
- Create: `pipeline/scripts/daemon_manager.py`
- Test: `pipeline/tests/test_daemon_manager.py`

**Implementation Details:**
- Track PID in `pipeline/state/daemon.pid`.
- Output live execution logs to `pipeline/logs/daemon.log`.
- Status introspection: `status`, `start`, `stop`, `restart`.
- Budget safety check: Before each cycle, inspect `http://127.0.0.1:8900/_spend`. If `remaining_usd < 0.50`, halt cycles safely.

---

### Task 2: Build Next.js Dashboard Daemon Control API

**Objective:** Expose real-time daemon state and control endpoints so Mission Control can inspect running cycles and toggle autonomous execution.

**Files:**
- Create: `hermes-mission/app/api/daemon/route.ts`

**Endpoints:**
- `GET /api/daemon`: Returns current PID, status (`RUNNING` / `IDLE`), uptime, cycle count, and last cycle timestamp.
- `POST /api/daemon`: Accepts `{ action: "START" | "STOP", interval_seconds: 1800 }` to start or gracefully terminate the background process.

---

### Task 3: Mission Control Cockpit Live 24/7 Daemon UI

**Objective:** Add a real-time status pill and toggle button to the Mission Control header so the founder can observe autonomous cycles live.

**Files:**
- Modify: `hermes-mission/components/CommandConsole.tsx`
- Modify: `hermes-mission/components/views/Runs.tsx`

**UI Features:**
- Dynamic status indicator: `● 24/7 AUTONOMOUS DAEMON: ACTIVE (Cycle #N)`
- One-click **Pause / Resume** control.
- Next cycle countdown timer.

---

### Task 4: Autonomous Signal & Narrative Selection Engine

**Objective:** Ensure that when no founder directive is passed, Agent 01 & 02 automatically discover novel whitespace opportunities from live RPC/DeFiLlama/Twitter feeds with zero human intervention.

**Files:**
- Modify: `pipeline/scripts/run_autonomous_gtm_master.py`

**Key Invariants:**
- Automatic deduplication against previously executed runs in `pipeline/state/runs_archive/`.
- Automatic rotation across the 5 physical metaphor families (Optical, Hydraulic, Electromagnetic, Monolithic, Structural).
- Dynamic prompt generation for `gemini-3.1-flash-image` and Remotion video.

---

### Task 5: End-to-End Verification & Health Watchdog

**Objective:** Run diagnostic tests confirming the daemon launches in the background, executes an autonomous cycle, updates Mission Control, records spend, and handles graceful termination.

**Verification Steps:**
1. Start daemon in test mode (short cycle interval).
2. Confirm PID written to `pipeline/state/daemon.pid`.
3. Check `/api/daemon` returns `status: "RUNNING"`.
4. Verify execution log streams to `pipeline/logs/daemon.log`.
5. Terminate daemon and verify clean shutdown.
