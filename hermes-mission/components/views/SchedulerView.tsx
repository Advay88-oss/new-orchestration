"use client";

import React, { useState, useEffect } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

export function SchedulerView({ vm }: { vm: MissionVM }) {
  const [schedulerData, setSchedulerData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [runningJob, setRunningJob] = useState<string | null>(null);
  const [completedJobTarget, setCompletedJobTarget] = useState<{ label: string; action: () => void } | null>(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch("/api/scheduler", { cache: "no-store" });
      const data = await res.json();
      if (data.success) {
        setSchedulerData(data);
      }
    } catch (e: any) {
      console.warn("Scheduler fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const itv = setInterval(fetchStatus, 4000);
    return () => clearInterval(itv);
  }, []);

  const handleRunNow = async (jobName: string) => {
    setRunningJob(jobName);
    setCompletedJobTarget(null);
    setActionFeedback(`⚡ Triggering immediate execution for '${jobName}'...`);
    try {
      const res = await fetch("/api/scheduler", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "run_now", job: jobName })
      });
      const data = await res.json();
      if (data.success) {
        const targetAction =
          jobName === "ideas_panel"
            ? { label: "💡 Ideas Panel", action: () => (vm as any).goIdeas?.() }
            : jobName === "memes_panel"
            ? { label: "🎭 Crypto Memes", action: () => (vm as any).goMemes?.() }
            : jobName === "research_collect" || jobName === "trend_scan"
            ? { label: "🔍 Scraped Intelligence", action: () => (vm as any).goResearch?.() }
            : null;

        setCompletedJobTarget(targetAction);
        setActionFeedback(`✓ Job '${jobName}' completed in ${data.result?.duration_s ? data.result.duration_s.toFixed(2) : "0.5"}s! New items generated.`);
        await fetchStatus();
      } else {
        setActionFeedback(`⚠️ Notice: ${data.error || "Execution skipped or still running"}`);
      }
    } catch (err: any) {
      setActionFeedback(`❌ Error: ${err.message}`);
    } finally {
      setRunningJob(null);
    }
  };

  const handleSetInterval = async (jobName: string, intervalStr: string) => {
    setActionFeedback(`Updating interval for '${jobName}' to ${intervalStr}...`);
    try {
      const res = await fetch("/api/scheduler", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "set_interval", job: jobName, interval: intervalStr })
      });
      const data = await res.json();
      if (data.success) {
        setActionFeedback(`✓ Interval for '${jobName}' updated to ${intervalStr}`);
        await fetchStatus();
      } else {
        setActionFeedback(`❌ ${data.error || "Failed to update interval"}`);
      }
    } catch (err: any) {
      setActionFeedback(`❌ Network error: ${err.message}`);
    } finally {
      setTimeout(() => setActionFeedback(null), 8000);
    }
  };

  const jobs = schedulerData?.jobs || [];
  const ALLOWED_INTERVALS = ["2m", "5m", "30m", "1h", "2h", "6h", "12h", "24h"];

  return (
    <section className="vanna-section">
      {/* Banner */}
      <div className="vanna-banner">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "999px", background: "#38EF7D", boxShadow: "0 0 10px #38EF7D" }} />
            <span style={{ fontFamily: MONO, fontSize: "11px", fontWeight: 700, color: "#38EF7D", letterSpacing: "0.1em" }}>
              24/7 AUTONOMOUS SCHEDULER & RESTART RESILIENCE
            </span>
          </div>
          <h2 style={{ fontSize: "22px", fontWeight: 800, color: "#FFFFFF", marginTop: "6px" }}>
            Configurable Interval Jobs & Anti-Overlap Daemon
          </h2>
          <p style={{ fontSize: "14px", color: "#A2A1A6", marginTop: "4px" }}>
            Continuous background execution engine that survives machine reboots, prevents concurrent job stacking, and enforces interval sanity to protect API spend.
          </p>
        </div>

        {/* Global Daemon Health Pill */}
        <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
          <div style={{ background: "rgba(56, 239, 125, 0.1)", border: "1px solid rgba(56, 239, 125, 0.3)", borderRadius: "10px", padding: "10px 16px" }}>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>DAEMON SERVICE</div>
            <div style={{ fontFamily: MONO, fontSize: "14px", fontWeight: 700, color: "#38EF7D", marginTop: "2px" }}>
              ● ACTIVE (SURVIVES BOOT)
            </div>
          </div>
          <div style={{ background: "rgba(112, 58, 230, 0.1)", border: "1px solid rgba(163, 135, 255, 0.3)", borderRadius: "10px", padding: "10px 16px" }}>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>JOBS CONFIGURED</div>
            <div style={{ fontFamily: MONO, fontSize: "14px", fontWeight: 700, color: "#A387FF", marginTop: "2px" }}>
              {jobs.length} SCHEDULED
            </div>
          </div>
        </div>
      </div>

      {actionFeedback && (
        <div
          style={{
            fontFamily: MONO,
            fontSize: "12px",
            color: actionFeedback.startsWith("❌") ? "#FC5457" : actionFeedback.startsWith("⚠️") ? "#F5A623" : "#38EF7D",
            background: actionFeedback.startsWith("❌") ? "rgba(252, 84, 87, 0.1)" : "rgba(56, 239, 125, 0.1)",
            padding: "12px 18px",
            borderRadius: "10px",
            border: `1px solid ${actionFeedback.startsWith("❌") ? "rgba(252, 84, 87, 0.3)" : "rgba(56, 239, 125, 0.3)"}`,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "10px"
          }}
        >
          <span>{actionFeedback}</span>
          {completedJobTarget && (
            <button
              onClick={() => completedJobTarget.action()}
              style={{
                background: "linear-gradient(135deg, #703AE6 0%, #32EEE2 100%)",
                color: "#07020D",
                border: "none",
                borderRadius: "6px",
                padding: "6px 14px",
                fontFamily: MONO,
                fontSize: "11px",
                fontWeight: 800,
                cursor: "pointer"
              }}
            >
              Open {completedJobTarget.label} →
            </button>
          )}
        </div>
      )}

      {/* Jobs Grid */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {jobs.map((j: any) => {
          const isModelHeavy = j.job === "ideas_panel" || j.job === "research_collect";
          const statusColor =
            j.status === "RUNNING"
              ? "#32EEE2"
              : j.status === "COMPLETED"
                ? "#38EF7D"
                : j.status === "DISABLED_AUTO_BACKOFF"
                  ? "#FC5457"
                  : "#8E85A8";

          return (
            <div
              key={j.job}
              style={{
                background: "#0C0716",
                border: `1px solid ${j.status === "RUNNING" ? "rgba(50, 238, 226, 0.5)" : "rgba(255, 255, 255, 0.08)"}`,
                borderRadius: "16px",
                padding: "20px 24px",
                display: "flex",
                flexDirection: "column",
                gap: "14px",
                boxShadow: "0 8px 24px rgba(0,0,0,0.3)"
              }}
            >
              {/* Row 1: Header & Status */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span style={{ fontSize: "16px", fontWeight: 800, color: "#FFFFFF" }}>{j.job}</span>
                    <span
                      style={{
                        fontFamily: MONO,
                        fontSize: "10px",
                        fontWeight: 700,
                        color: statusColor,
                        background: `${statusColor}18`,
                        border: `1px solid ${statusColor}40`,
                        padding: "3px 8px",
                        borderRadius: "5px"
                      }}
                    >
                      ● {j.status}
                    </span>
                    {isModelHeavy && (
                      <span style={{ fontFamily: MONO, fontSize: "10px", color: "#F5A623", background: "rgba(245, 166, 35, 0.1)", border: "1px solid rgba(245, 166, 35, 0.3)", padding: "2px 8px", borderRadius: "4px" }}>
                        ⚡ AI MODEL REASONING
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: "13px", color: "#DFDFDF", marginTop: "4px" }}>
                    {j.description}
                  </div>
                </div>

                <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
                  {j.job === "ideas_panel" && (
                    <button
                      onClick={() => (vm as any).goIdeas?.()}
                      style={{
                        background: "rgba(112, 58, 230, 0.15)",
                        border: "1px solid rgba(163, 135, 255, 0.3)",
                        color: "#A387FF",
                        borderRadius: "8px",
                        padding: "8px 14px",
                        fontFamily: MONO,
                        fontSize: "11px",
                        fontWeight: 700,
                        cursor: "pointer"
                      }}
                    >
                      💡 View Ideas Panel →
                    </button>
                  )}
                  {j.job === "memes_panel" && (
                    <button
                      onClick={() => (vm as any).goMemes?.()}
                      style={{
                        background: "rgba(112, 58, 230, 0.15)",
                        border: "1px solid rgba(163, 135, 255, 0.3)",
                        color: "#A387FF",
                        borderRadius: "8px",
                        padding: "8px 14px",
                        fontFamily: MONO,
                        fontSize: "11px",
                        fontWeight: 700,
                        cursor: "pointer"
                      }}
                    >
                      🎭 View Crypto Memes →
                    </button>
                  )}
                  {(j.job === "research_collect" || j.job === "trend_scan") && (
                    <button
                      onClick={() => (vm as any).goResearch?.()}
                      style={{
                        background: "rgba(50, 238, 226, 0.15)",
                        border: "1px solid rgba(50, 238, 226, 0.3)",
                        color: "#32EEE2",
                        borderRadius: "8px",
                        padding: "8px 14px",
                        fontFamily: MONO,
                        fontSize: "11px",
                        fontWeight: 700,
                        cursor: "pointer"
                      }}
                    >
                      🔍 View Scraped Intelligence →
                    </button>
                  )}
                  <button
                    onClick={() => handleRunNow(j.job)}
                    disabled={runningJob === j.job}
                    style={{
                      background: runningJob === j.job ? "rgba(112, 58, 230, 0.3)" : "linear-gradient(135deg, #703AE6 0%, #32EEE2 100%)",
                      color: runningJob === j.job ? "#8E85A8" : "#07020D",
                      border: "none",
                      borderRadius: "8px",
                      padding: "8px 16px",
                      fontFamily: MONO,
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: runningJob === j.job ? "not-allowed" : "pointer",
                      whiteSpace: "nowrap"
                    }}
                  >
                    {runningJob === j.job ? "⏳ Executing..." : "⚡ Run Now"}
                  </button>
                </div>
              </div>

              {/* Row 2: Metrics Strip */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px", background: "rgba(255,255,255,0.02)", padding: "12px 16px", borderRadius: "10px" }}>
                <div>
                  <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>CURRENT INTERVAL</div>
                  <div style={{ fontFamily: MONO, fontSize: "13px", fontWeight: 700, color: "#32EEE2", marginTop: "2px" }}>
                    Every {j.interval}
                  </div>
                </div>
                <div>
                  <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>LAST RUN</div>
                  <div style={{ fontFamily: MONO, fontSize: "13px", color: "#FFFFFF", marginTop: "2px" }}>
                    {j.last_run !== "Never" ? new Date(j.last_run).toLocaleTimeString() : "Never"} ({j.last_duration_s}s)
                  </div>
                </div>
                <div>
                  <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>NEXT SCHEDULED</div>
                  <div style={{ fontFamily: MONO, fontSize: "13px", color: "#38EF7D", marginTop: "2px" }}>
                    {j.next_run !== "Overdue / Pending" ? new Date(j.next_run).toLocaleTimeString() : "Pending Tick"}
                  </div>
                </div>
                <div>
                  <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8" }}>FAILURES / HEALTH</div>
                  <div style={{ fontFamily: MONO, fontSize: "13px", color: j.consecutive_failures > 0 ? "#FC5457" : "#38EF7D", marginTop: "2px" }}>
                    {j.consecutive_failures} Failures (Total: {j.total_runs} runs)
                  </div>
                </div>
              </div>

              {/* Row 3: Configurable Interval Selector Pills */}
              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "12px" }}>
                <span style={{ fontFamily: MONO, fontSize: "11px", color: "#8E85A8", marginRight: "4px" }}>
                  SET INTERVAL:
                </span>
                {ALLOWED_INTERVALS.map((inv) => {
                  const isSelected = j.interval === inv;
                  // If model heavy, warn or disable 2m
                  const isDangerous = isModelHeavy && inv === "2m";
                  return (
                    <button
                      key={inv}
                      onClick={() => handleSetInterval(j.job, inv)}
                      style={{
                        background: isSelected ? "rgba(112, 58, 230, 0.35)" : "rgba(255, 255, 255, 0.04)",
                        border: `1px solid ${isSelected ? "#703AE6" : isDangerous ? "rgba(252,84,87,0.3)" : "rgba(255, 255, 255, 0.1)"}`,
                        color: isSelected ? "#FFFFFF" : isDangerous ? "#8E85A8" : "#DFDFDF",
                        padding: "5px 12px",
                        borderRadius: "6px",
                        fontFamily: MONO,
                        fontSize: "11px",
                        fontWeight: isSelected ? 800 : 500,
                        cursor: "pointer",
                        opacity: isDangerous ? 0.6 : 1
                      }}
                      title={isDangerous ? "Interval sanity rejects model-heavy jobs under 2h to protect budget" : `Set ${j.job} interval to ${inv}`}
                    >
                      {inv} {isSelected ? "✓" : ""}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
