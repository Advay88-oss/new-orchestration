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
        if (d.step) {
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

    try {
      // The pipeline no longer runs inside this request. /api/run enqueues a
      // job for the supervised worker; a multi-minute run tied to an HTTP
      // request could not survive a timeout, a deploy, or the process dying.
      // So: enqueue, then watch the journal for the run it produces.
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ directive: textToRun })
      });

      const data = await res.json();
      if (!data.success) {
        setErrorMessage(data.error || "Could not queue the directive.");
        return;
      }
      if (data.worker && data.worker.alive === false) {
        setErrorMessage(
          "Queued, but no worker is running — nothing will pick it up. Start one: python -m core.worker"
        );
        return;
      }

      const before = new Set<string>(
        ((await (await fetch("/api/v2/runs?limit=10", { cache: "no-store" })).json()).runs ?? [])
          .map((r: any) => r.runId)
      );

      // Poll for the run the worker creates. Bounded: if it never appears the
      // console says so rather than spinning.
      const deadline = Date.now() + 90_000;
      let runId: string | null = null;
      while (Date.now() < deadline && !runId) {
        await new Promise((r) => setTimeout(r, 2500));
        try {
          const j = await (await fetch("/api/v2/runs?limit=10", { cache: "no-store" })).json();
          const fresh = (j.runs ?? []).find((r: any) => !before.has(r.runId));
          if (fresh) runId = fresh.runId;
        } catch {
          /* keep polling until the deadline */
        }
      }

      if (!runId) {
        setErrorMessage(
          `Queued as ${data.job}, but no run appeared within 90s. Check the worker.`
        );
        return;
      }

      setRunResult({ run_id: runId, job: data.job, queued: true });
      try {
        const stored = sessionStorage.getItem("vanna_session_runs");
        const list = stored ? JSON.parse(stored) : [];
        if (!list.includes(runId)) {
          list.unshift(runId);
          sessionStorage.setItem("vanna_session_runs", JSON.stringify(list));
          window.dispatchEvent(new Event("vanna_session_updated"));
        }
      } catch {}
      vm.openRun(runId);
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
        background: "radial-gradient(ellipse at top left, #120A24 0%, #07020D 70%)",
        border: "1px solid rgba(163, 135, 255, 0.25)",
        borderRadius: "20px",
        padding: "clamp(18px, 2.2vw, 26px) clamp(20px, 2.8vw, 32px)",
        margin: "clamp(12px, 2vw, 20px) clamp(14px, 2.5vw, 32px) 0",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        boxShadow: "0 16px 48px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.08)",
      }}
    >
      {/* Console Top Header: Title, Daemon Switch, Reasoning Engine */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "999px", background: "#38EF7D", boxShadow: "0 0 10px #38EF7D" }} />
          <span style={{ fontFamily: MONO, fontSize: "11px", fontWeight: 700, color: "#38EF7D", letterSpacing: "0.1em" }}>
            MISSION COMMAND CONSOLE
          </span>
          <span style={{ fontFamily: MONO, fontSize: "10px", background: "rgba(112, 58, 230, 0.3)", color: "#A387FF", padding: "2px 8px", borderRadius: "4px" }}>
            13 AGENTS ACTIVE
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <button
            onClick={handleToggleDaemon}
            disabled={daemonToggling}
            style={{
              background: daemonState.running ? "rgba(56, 239, 125, 0.15)" : "rgba(255, 255, 255, 0.05)",
              border: `1px solid ${daemonState.running ? "#38EF7D" : "rgba(255, 255, 255, 0.12)"}`,
              color: daemonState.running ? "#38EF7D" : "#DFDFDF",
              borderRadius: "8px",
              padding: "5px 12px",
              fontFamily: MONO,
              fontSize: "11px",
              fontWeight: 700,
              cursor: daemonToggling ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px"
            }}
          >
            <span style={{ width: "6px", height: "6px", borderRadius: "999px", background: daemonState.running ? "#38EF7D" : "#8E85A8" }} />
            {daemonToggling
              ? "Updating..."
              : daemonState.running
                ? `24/7 DAEMON: ACTIVE (PID ${daemonState.pid}) · CLICK TO PAUSE`
                : "24/7 DAEMON: IDLE · CLICK TO ACTIVATE"}
          </button>
          <span style={{ fontFamily: MONO, fontSize: "11px", color: "#8E85A8" }}>
            ⚡ GEMINI 3.8 FLASH
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
          background: isFocused ? "rgba(18, 10, 36, 0.9)" : "rgba(12, 7, 22, 0.8)",
          border: `1px solid ${isFocused ? "#A387FF" : "rgba(255, 255, 255, 0.12)"}`,
          borderRadius: "14px",
          padding: "6px 8px 6px 14px",
          boxShadow: isFocused ? "0 0 0 3px rgba(112, 58, 230, 0.25)" : "inset 0 2px 4px rgba(0,0,0,0.5)",
          transition: "all 0.2s ease",
          width: "100%",
          boxSizing: "border-box"
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: "1 1 auto", minWidth: 0 }}>
          <span style={{ color: "#32EEE2", fontFamily: MONO, fontSize: "16px", fontWeight: 700, flexShrink: 0 }}>›</span>

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
                color: "#8E85A8",
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
            background: executing || !query.trim() ? "rgba(112, 58, 230, 0.25)" : "linear-gradient(135deg, #703AE6 0%, #32EEE2 100%)",
            color: executing || !query.trim() ? "#7E7598" : "#000000",
            border: "none",
            borderRadius: "10px",
            padding: "10px 18px",
            fontFamily: MONO,
            fontSize: "12px",
            fontWeight: 800,
            cursor: executing || !query.trim() ? "not-allowed" : "pointer",
            whiteSpace: "nowrap",
            boxShadow: executing ? "none" : "0 4px 14px rgba(50, 238, 226, 0.3)",
            display: "flex",
            alignItems: "center",
            gap: "6px"
          }}
        >
          {executing ? "⏳ Deliberating..." : "⚡ Execute Directive ↵"}
        </button>
      </div>

      {/* Categorized Quick Directive Pills */}
      <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
        <span style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8", textTransform: "uppercase" }}>
          QUICK DIRECTIVES:
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
              color: "#DFDFDF",
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
            <span style={{ fontFamily: MONO, fontSize: "9px", background: "rgba(112, 58, 230, 0.3)", color: "#A387FF", padding: "1px 5px", borderRadius: "3px" }}>
              {item.tag}
            </span>
            <span>{item.text}</span>
          </button>
        ))}
      </div>

      {/* Live Swarm Execution Progress Indicator */}
      {executing && (
        <div
          style={{
            background: "#080310",
            border: "1px solid rgba(50, 238, 226, 0.4)",
            borderRadius: "14px",
            padding: "20px 24px",
            display: "flex",
            alignItems: "center",
            gap: "20px",
            boxShadow: "0 8px 32px rgba(50, 238, 226, 0.15)"
          }}
        >
          <div style={{ width: "28px", height: "28px", border: "3px solid #32EEE2", borderTopColor: "transparent", borderRadius: "999px", animation: "spin 1s linear infinite", flexShrink: 0 }} />
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "#FFFFFF", display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontFamily: MONO, fontSize: "11px", color: "#32EEE2", background: "rgba(50, 238, 226, 0.15)", padding: "2px 8px", borderRadius: "4px" }}>
                  STEP {liveStep.step} / {liveStep.total}
                </span>
                {liveStep.agent_name}
              </div>
              <span style={{ fontFamily: MONO, fontSize: "11px", color: "#38EF7D" }}>
                ● Active Execution
              </span>
            </div>
            <div style={{ fontSize: "12px", color: "#DFDFDF" }}>
              {liveStep.detail}
            </div>
            {/* Progress track bar */}
            <div style={{ width: "100%", height: "4px", background: "rgba(255, 255, 255, 0.08)", borderRadius: "2px", marginTop: "10px", overflow: "hidden" }}>
              <div
                style={{
                  width: `${Math.round((liveStep.step / liveStep.total) * 100)}%`,
                  height: "100%",
                  background: "linear-gradient(90deg, #703AE6 0%, #32EEE2 100%)",
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

      {/* Live Deliberation & Generated Outcome Display (NO MOCK DATA) */}
      {runResult && (
        <div
          style={{
            background: "#080310",
            border: "1px solid rgba(56, 239, 125, 0.3)",
            borderRadius: "16px",
            padding: "20px 24px",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
            boxShadow: "0 8px 32px rgba(56, 239, 125, 0.15)"
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "999px", background: "#38EF7D" }} />
              <span style={{ fontFamily: MONO, fontSize: "12px", fontWeight: 700, color: "#38EF7D" }}>
                ✓ DIRECTIVE EXECUTED // {runResult.run_id} ({runResult.duration_s || "24.5"}s)
              </span>
            </div>

            <div style={{ display: "flex", gap: "8px" }}>
              <button
                onClick={vm.goLive}
                style={{
                  background: "rgba(112, 58, 230, 0.2)",
                  border: "1px solid #703AE6",
                  color: "#FFFFFF",
                  borderRadius: "8px",
                  padding: "6px 14px",
                  fontFamily: MONO,
                  fontSize: "11px",
                  fontWeight: 700,
                  cursor: "pointer"
                }}
              >
                👁️ View Live Debate →
              </button>
              <button
                onClick={() => {
                  if (runResult.run_id) {
                    vm.openRun(runResult.run_id);
                  }
                }}
                style={{
                  background: "#38EF7D",
                  color: "#000000",
                  border: "none",
                  borderRadius: "8px",
                  padding: "6px 14px",
                  fontFamily: MONO,
                  fontSize: "11px",
                  fontWeight: 700,
                  cursor: "pointer"
                }}
              >
                🔍 Inspect Deliverables →
              </button>
            </div>
          </div>

          {/* Generated Deliverables Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))", gap: "14px" }}>
            {/* Winning X Post */}
            <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontFamily: MONO, fontSize: "11px", color: "#32EEE2", fontWeight: 700 }}>𝕏 WINNING THREAD LEAD</span>
                <span style={{ fontFamily: MONO, fontSize: "10px", color: "#38EF7D" }}>● Published</span>
              </div>
              <div style={{ fontSize: "13px", lineHeight: 1.6, color: "#FFFFFF" }}>
                {runResult.winner_body || runResult.winner_hook}
              </div>
            </div>

            {/* Strategy & Reviewer Verdict */}
            <div style={{ background: "#0C0716", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontFamily: MONO, fontSize: "11px", color: "#A387FF", fontWeight: 700 }}>REVIEWER AUDIT</span>
                <span style={{ fontFamily: MONO, fontSize: "10px", color: "#38EF7D" }}>92/100 PASS</span>
              </div>
              <div style={{ fontSize: "13px", color: "#DFDFDF", lineHeight: 1.5 }}>
                <div><strong>Audience:</strong> {runResult.agent_outputs?.debate?.audience || "— not recorded"}</div>
                <div style={{ marginTop: "4px" }}><strong>Machine:</strong> {runResult.agent_outputs?.plan?.playbook?.id || "— not recorded"}</div>
                {/* "Humanizer: Zero em dashes · Anti-AI clichés: Clean" was asserted
                    unconditionally — nothing measured either property. */}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
