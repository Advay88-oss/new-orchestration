"use client";

import React, { useState } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

export function CommandConsole({ vm }: { vm: MissionVM }) {
  const [query, setQuery] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [runResult, setRunResult] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [daemonState, setDaemonState] = useState<{ running: boolean; pid: number | null; interval_seconds?: number }>({ running: false, pid: null });
  const [daemonToggling, setDaemonToggling] = useState(false);
  const [liveStep, setLiveStep] = useState<{ step: number; total: number; agent_name: string; detail: string }>({
    step: 1,
    total: 13,
    agent_name: "—",   // filled from /api/progress once a run starts
    detail: "Initializing multi-channel scan..."
  });

  // Poll progress during active execution
  React.useEffect(() => {
    if (!executing) return;
    const pItv = setInterval(async () => {
      try {
        const res = await fetch("/api/progress", { cache: "no-store" });
        const d = await res.json();
        // Unscoped, this returns the newest run it can see — for the first
        // minute of a new cycle that is the PREVIOUS run, finished at 13/13,
        // and the ticker showed a completed run while A01 was still scraping.
        if (d.step && !d.finished) {
          setLiveStep(d);
        }
      } catch {}
    }, 1000);
    return () => clearInterval(pItv);
  }, [executing]);

  const fetchDaemon = async () => {
    try {
      const res = await fetch("/api/daemon", { cache: "no-store" });
      const data = await res.json();
      setDaemonState({
        running: Boolean(data.running),
        pid: data.pid || null,
        interval_seconds: data.interval_seconds || 1800
      });
    } catch {}
  };

  React.useEffect(() => {
    fetchDaemon();
    const itv = setInterval(fetchDaemon, 8000);
    return () => clearInterval(itv);
  }, []);

  const handleToggleDaemon = async () => {
    setDaemonToggling(true);
    try {
      const action = daemonState.running ? "stop" : "start";
      await fetch("/api/daemon", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, interval_seconds: 1800 })
      });
      await fetchDaemon();
    } catch (e: any) {
      setErrorMessage(`Daemon control error: ${e.message}`);
    } finally {
      setDaemonToggling(false);
    }
  };

  const CATEGORIZED_PROMPTS = [
    // Neutral prompts. The previous presets embedded figures — "$148.5M TVL",
    // "0.00014 XLM fixed gas", a Stellar Foundation partnership — straight into
    // the directive. That is the pattern the audit flagged: the prompt supplying
    // the facts, which the verifier then has to reject. A directive names a
    // subject; evidence supplies the numbers.
    { tag: "Lending", text: "explain composable margin across lending pools" },
    { tag: "Solvency", text: "how isolated accounts contain a liquidation failure" },
    { tag: "Institutional", text: "risk breakdown of isolated SmartAccount sandboxes" },
    { tag: "Mechanism", text: "why deterministic fees change liquidation timing" }
  ];

  const handleExecute = async (directiveText: string) => {
    const textToRun = directiveText.trim();
    if (!textToRun) return;

    setExecuting(true);
    setErrorMessage(null);
    setRunResult(null);
    // The last run's final step would otherwise stay on screen until the new
    // run's first agent reports.
    setLiveStep({ step: 0, total: 13, agent_name: "starting…",
                  detail: "waiting for the first agent to report…" });

    try {
      const seen = async (): Promise<Set<string>> => {
        try {
          const j = await (await fetch("/api/gtm/active?limit=8", { cache: "no-store" })).json();
          return new Set<string>((j.runs ?? []).map((r: any) => r.runId));
        } catch {
          return new Set<string>();
        }
      };
      // Snapshot BEFORE launching. Taken after, it raced the cycle: Python
      // creates the run directory within a second, and in dev the first
      // /api/gtm/active hit compiles for longer than that — so the new run
      // was already in `before`, never looked new, and a live run was
      // reported as "no run directory appeared".
      const before = await seen();

      // /api/run spawns `pipeline.gtm_os.autonomous_cycle` detached and
      // returns { success, pid, directive, autonomous, note, log }. It has no
      // `job` field — the console read `data.job`, which is why the failure
      // said "Queued as undefined".
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ directive: textToRun }),
      });

      const data = await res.json();
      if (!data.success) {
        setErrorMessage(
          data.error || `Could not start the cycle (HTTP ${res.status}).`,
        );
        return;
      }

      // Wait for the run to APPEAR, not to finish. The cycle creates its
      // directory when it takes the lock, so this resolves in a second or
      // two. The old code polled a listing that hides any run without a
      // summary.json — a file written only when the cycle ends, 2-5 minutes
      // later — so its 90s deadline could never be met.
      let runId: string | null = null;
      const appearBy = Date.now() + 60_000;
      while (Date.now() < appearBy && !runId) {
        await new Promise((r) => setTimeout(r, 1500));
        const now = await seen();
        runId = [...now].find((id) => !before.has(id)) ?? null;
      }

      if (!runId) {
        setErrorMessage(
          `Started (pid ${data.pid ?? "?"}) but no run directory appeared. ` +
            `Check ${data.log ?? "pipeline/state/gtm_runs/last_launch.log"}.`,
        );
        return;
      }

      setRunResult({ run_id: runId, pid: data.pid, queued: true });
      // Open the run straight away: its copy, poster and video appear there
      // as each one is made. A run with a Veo video takes 10-15 minutes, and
      // waiting for the end before showing anything looked like a dead run.
      vm.openRun(runId);

      // Now follow it to completion. A cycle is 2-5 minutes (Veo dominates),
      // so this deadline is generous; the stage ticker above updates from
      // /api/progress while it runs.
      const finishBy = Date.now() + 25 * 60_000;
      let finished = false;
      while (Date.now() < finishBy && !finished) {
        await new Promise((r) => setTimeout(r, 3000));
        try {
          const j = await (await fetch(`/api/progress?runId=${runId}`, { cache: "no-store" })).json();
          if (j.step) {
            setLiveStep({
              step: j.step,
              total: j.total ?? 13,
              agent_name: j.agent_name ?? "—",
              detail: j.detail ?? "",
            });
          }
          finished = Boolean(j.finished);
        } catch {
          /* keep waiting; a transient read must not abort the run */
        }
      }

      try {
        const stored = sessionStorage.getItem("vanna_session_runs");
        const list = stored ? JSON.parse(stored) : [];
        if (!list.includes(runId)) {
          list.unshift(runId);
          sessionStorage.setItem("vanna_session_runs", JSON.stringify(list));
          window.dispatchEvent(new Event("vanna_session_updated"));
        }
      } catch {}

      if (!finished) {
        setErrorMessage(`${runId} is still running after 25 minutes. Check the run's stages for where it stopped.`);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Network error while connecting to swarm.");
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div
      className="console-container"
      style={{
        background: "var(--vn-surface)",
        border: "1px solid var(--vn-line)",
        borderRadius: "14px",
        padding: "clamp(18px, 2.2vw, 26px) clamp(20px, 2.8vw, 32px)",
        margin: "clamp(12px, 2vw, 20px) clamp(14px, 2.5vw, 32px) 0",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
      }}
    >
      {/* Console Top Header: Title, Daemon Switch, Reasoning Engine */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        {/* A glowing dot, a letter-spaced green title, and a violet "13
            AGENTS ACTIVE" badge, all naming the same box. The heading says
            what it is; the count belongs next to the agents, not here. */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--vn-ink)" }}>
            Run a directive
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <button
            onClick={handleToggleDaemon}
            disabled={daemonToggling}
            style={{
              background: daemonState.running ? "rgba(56, 239, 125, 0.15)" : "rgba(255, 255, 255, 0.05)",
              border: `1px solid ${daemonState.running ? "#4ADE9B" : "rgba(255, 255, 255, 0.12)"}`,
              color: daemonState.running ? "#4ADE9B" : "#B8B3C6",
              borderRadius: "8px",
              padding: "5px 12px",
              fontSize: "12px",
              fontWeight: 500,
              cursor: daemonToggling ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px"
            }}
          >
            <span style={{ width: "6px", height: "6px", borderRadius: "999px", background: daemonState.running ? "#4ADE9B" : "#7B7590" }} />
            {daemonToggling
              ? "Updating…"
              : daemonState.running
                ? "Daemon on"
                : "Daemon off"}
          </button>
          <span style={{ fontFamily: MONO, fontSize: "11px", color: "var(--vn-ink-faint)" }}>
            gemini-3.8-flash
          </span>
        </div>
      </div>

      {/* Modern Floating Command Bar */}
      <div
        className="console-input-row"
        style={{
          display: "flex",
          gap: "10px",
          alignItems: "center",
          background: "var(--vn-sunken)",
          border: `1px solid ${isFocused ? "var(--vn-accent)" : "var(--vn-line-strong)"}`,
          borderRadius: "10px",
          padding: "6px 8px 6px 14px",
          transition: "all 0.2s ease",
          width: "100%",
          boxSizing: "border-box"
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: "1 1 auto", minWidth: 0 }}>
          <input
            type="text"
            value={query}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !executing) {
                handleExecute(query);
              }
            }}
            placeholder="Enter founder directive (e.g. 'post on blend', 'risk breakdown')..."
            style={{
              flex: "1 1 auto",
              minWidth: 0,
              width: "100%",
              background: "transparent",
              border: "none",
              outline: "none",
              color: "#FFFFFF",
              fontSize: "14px",
              letterSpacing: "0.01em",
              padding: "8px 0"
            }}
          />

          {query && (
            <button
              onClick={() => setQuery("")}
              style={{
                background: "transparent",
                border: "none",
                color: "#7B7590",
                cursor: "pointer",
                fontSize: "14px",
                padding: "4px 8px",
                flexShrink: 0
              }}
            >
              ✕
            </button>
          )}
        </div>

        <button
          onClick={() => handleExecute(query)}
          disabled={executing || !query.trim()}
          style={{
            flexShrink: 0,
            background: executing || !query.trim() ? "rgba(255,255,255,0.05)" : "var(--vn-accent)",
            color: executing || !query.trim() ? "var(--vn-ink-faint)" : "#FFFFFF",
            border: "none",
            borderRadius: "8px",
            padding: "9px 18px",
            fontSize: "13px",
            fontWeight: 600,
            cursor: executing || !query.trim() ? "not-allowed" : "pointer",
            whiteSpace: "nowrap",
            display: "flex",
            alignItems: "center",
            gap: "6px"
          }}
        >
          {executing ? "Running…" : "Run"}
        </button>
      </div>

      {/* Categorized Quick Directive Pills */}
      <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ fontSize: "12px", color: "var(--vn-ink-faint)" }}>
          Try
        </span>
        {CATEGORIZED_PROMPTS.map((item, i) => (
          <button
            key={i}
            onClick={() => {
              setQuery(item.text);
              handleExecute(item.text);
            }}
            disabled={executing}
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.08)",
              color: "#B8B3C6",
              borderRadius: "8px",
              padding: "5px 12px",
              fontSize: "11px",
              cursor: executing ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              transition: "all 0.15s ease"
            }}
          >
            {/* Each pill carried a second, violet-filled pill inside it
                naming a category the sentence beside it already implies. */}
            <span>{item.text}</span>
          </button>
        ))}
      </div>

      {/* Live Swarm Execution Progress Indicator */}
      {executing && (
        <div
          style={{
            background: "#080310",
            border: "1px solid var(--vn-line)",
            borderRadius: "12px",
            padding: "18px 22px",
            display: "flex",
            alignItems: "center",
            gap: "20px"
          }}
        >
          <div style={{ width: "28px", height: "28px", border: "2px solid var(--vn-accent)", borderTopColor: "transparent", borderRadius: "999px", animation: "spin 1s linear infinite", flexShrink: 0 }} />
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "#FFFFFF", display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontFamily: MONO, fontSize: "11px", color: "#A98CFF", background: "var(--vn-accent-soft)", padding: "2px 8px", borderRadius: "4px" }}>
                  STEP {liveStep.step} / {liveStep.total}
                </span>
                {liveStep.agent_name}
              </div>
              <span style={{ fontFamily: MONO, fontSize: "11px", color: "var(--vn-ink-faint)" }}>
                running
              </span>
            </div>
            <div style={{ fontSize: "12px", color: "#B8B3C6" }}>
              {liveStep.detail}
            </div>
            {/* Progress track bar */}
            <div style={{ width: "100%", height: "4px", background: "rgba(255, 255, 255, 0.08)", borderRadius: "2px", marginTop: "10px", overflow: "hidden" }}>
              <div
                style={{
                  width: `${Math.round((liveStep.step / liveStep.total) * 100)}%`,
                  height: "100%",
                  background: "linear-gradient(90deg, #703AE6 0%, #A98CFF 100%)",
                  transition: "width 0.4s ease"
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Error Message Display */}
      {errorMessage && (
        <div style={{ fontFamily: MONO, fontSize: "12px", color: "#EF4444", background: "rgba(239, 68, 68, 0.1)", padding: "12px 18px", borderRadius: "10px", border: "1px solid rgba(239, 68, 68, 0.3)" }}>
          ❌ {errorMessage}
        </div>
      )}

      {/* What the launch produced.
          This panel used to render `92/100 PASS` from a literal, a duration
          that fell back to "24.5", and copy read from `agent_outputs.debate`
          and `agent_outputs.plan` — keys the API does not emit. With
          runResult now { run_id, pid } it showed a fabricated scorecard over
          an empty body. The run's real content is on Run Detail, which this
          opens; here it only needs to say what started and where it went. */}
      {runResult && (
        <div
          style={{
            background: "#080310",
            border: "1px solid rgba(56, 239, 125, 0.3)",
            borderRadius: "16px",
            padding: "16px 20px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "999px", background: "#4ADE9B" }} />
            <span style={{ fontFamily: MONO, fontSize: "12px", fontWeight: 700, color: "#4ADE9B" }}>
              {runResult.run_id}
            </span>
            <span style={{ fontFamily: MONO, fontSize: "11px", color: "#7B7590" }}>
              {executing ? "running — all 13 agents" : "finished"}
              {runResult.pid ? ` · pid ${runResult.pid}` : ""}
            </span>
          </div>

          <button
            onClick={() => runResult.run_id && vm.openRun(runResult.run_id)}
            style={{
              background: "rgba(112, 58, 230, 0.25)",
              border: "1px solid #703AE6",
              color: "#FFFFFF",
              padding: "7px 14px",
              borderRadius: "8px",
              fontFamily: MONO,
              fontSize: "11px",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            Open run →
          </button>
        </div>
      )}
    </div>
  );
}
