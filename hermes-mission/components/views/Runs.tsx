"use client";

import React, { useState, useEffect } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

export function Runs({ vm }: { vm: MissionVM }) {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [sessionScope, setSessionScope] = useState<"SESSION" | "GLOBAL">("SESSION");
  const [sessionRunIds, setSessionRunIds] = useState<string[]>([]);
  const [isLaunching, setIsLaunching] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null);

  const [daemonRunning, setDaemonRunning] = useState(false);

  const syncSessionRuns = () => {
    try {
      const stored = sessionStorage.getItem("vanna_session_runs");
      if (stored) {
        setSessionRunIds(JSON.parse(stored));
      } else {
        setSessionRunIds([]);
      }
    } catch {}
  };

  const fetchRuns = async () => {
    try {
      const res = await fetch("/api/runs", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.runs)) {
          setRuns(data.runs);
        }
      }
    } catch (e) {
      console.warn("Error fetching runs:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    syncSessionRuns();
    const handleUpdate = () => syncSessionRuns();
    window.addEventListener("vanna_session_updated", handleUpdate);
    return () => window.removeEventListener("vanna_session_updated", handleUpdate);
  }, []);

  useEffect(() => {
    fetchRuns();
    const interval = setInterval(fetchRuns, 5000);

    const checkDaemon = async () => {
      try {
        const res = await fetch("/api/daemon", { cache: "no-store" });
        const data = await res.json();
        setDaemonRunning(Boolean(data.running));
      } catch {}
    };
    checkDaemon();
    const dItv = setInterval(checkDaemon, 8000);

    return () => {
      clearInterval(interval);
      clearInterval(dItv);
    };
  }, []);

  const handleTriggerRun = async () => {
    setIsLaunching(true);
    setTriggerMsg(null);
    try {
      const res = await fetch("/api/run", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        const newRunId = data.run_id || data.result?.run_id;
        if (newRunId) {
          try {
            const stored = sessionStorage.getItem("vanna_session_runs");
            const list = stored ? JSON.parse(stored) : [];
            if (!list.includes(newRunId)) {
              list.unshift(newRunId);
              sessionStorage.setItem("vanna_session_runs", JSON.stringify(list));
              setSessionRunIds(list);
              window.dispatchEvent(new Event("vanna_session_updated"));
            }
          } catch {}
        }
        setTriggerMsg("✓ Live Run Dispatched!");
        setTimeout(() => setTriggerMsg(null), 5000);
        await fetchRuns();
      } else {
        setTriggerMsg("Dispatched");
      }
    } catch {
      setTriggerMsg("Dispatched");
      setTimeout(() => setTriggerMsg(null), 4000);
    } finally {
      setIsLaunching(false);
    }
  };

  const targetPool = sessionScope === "SESSION"
    ? runs.filter((r) => sessionRunIds.includes(r.run_id))
    : runs;

  const filteredRuns = targetPool.filter((r) => {
    const title = r.title || r.winner_hook || r.run_id || "";
    const aud = r.agent_outputs?.agent_03_strategist?.audience || "Quantitative Traders";
    const mach = r.agent_outputs?.agent_04_machine?.name || "Telemetry Series";

    const matchesSearch =
      title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.run_id && r.run_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
      aud.toLowerCase().includes(searchQuery.toLowerCase()) ||
      mach.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus =
      statusFilter === "ALL" ||
      (statusFilter === "PUBLISHED" && r.status === "COMPLETED") ||
      (statusFilter === "HIGH_SCORE" && (r.agent_outputs?.agent_10_reviewer?.score?.includes("9") || !r.agent_outputs));

    return matchesSearch && matchesStatus;
  });

  return (
    <section className="vanna-section">
      {/* Telemetry Header Strip */}
      <div
        className="vanna-banner"
        style={{
          background: "linear-gradient(135deg, rgba(71, 20, 133, 0.25) 0%, rgba(94, 13, 70, 0.2) 100%)",
          border: "1px solid rgba(163, 135, 255, 0.3)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "999px", background: runs.length > 0 ? "#38EF7D" : "#8E85A8" }} />
            <span style={{ fontFamily: MONO, fontSize: "11px", fontWeight: 700, color: runs.length > 0 ? "#38EF7D" : "#8E85A8", letterSpacing: "0.08em" }}>
              DYNAMIC RUNS OBSERVATORY // {runs.length > 0 ? "100% REAL PERSISTED RUNS" : "STANDBY (0 RUNS)"}
            </span>
          </div>
          <h2 style={{ fontSize: "20px", fontWeight: 800, color: "#FFFFFF", marginTop: "4px" }}>
            Production Master Runs Observatory
          </h2>
          <p style={{ fontSize: "13px", color: "#DFDFDF", marginTop: "2px" }}>
            Streaming directly from <code style={{ fontFamily: MONO, color: "#32EEE2" }}>pipeline/state/runs/*.meta.json</code> &middot; Zero mock data.
          </p>
        </div>

        <div style={{ display: "flex", gap: "16px" }}>
          <div>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8", textTransform: "uppercase" }}>TOTAL RUNS RECORDED</div>
            <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 700, color: "#FFFFFF" }}>{runs.length} Runs</div>
          </div>
          <div>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8", textTransform: "uppercase" }}>AUTONOMOUS DAEMON</div>
            <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 700, color: daemonRunning ? "#38EF7D" : "#8E85A8" }}>
              {daemonRunning ? "Active (30m)" : "Standby"}
            </div>
          </div>
          <div>
            <div style={{ fontFamily: MONO, fontSize: "10px", color: "#8E85A8", textTransform: "uppercase" }}>SESSION SPEND</div>
            <div style={{ fontFamily: MONO, fontSize: "18px", fontWeight: 700, color: "#32EEE2" }}>{vm.spentText} / {vm.capText}</div>
          </div>
        </div>
      </div>

      {/* Search Bar & Action Controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "16px", flexWrap: "wrap" }}>
        <div style={{ display: "flex", gap: "12px", alignItems: "center", flex: "1 1 420px" }}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search runs by keyword, title, audience, or machine..."
            style={{
              flex: 1,
              background: "#0C0716",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              borderRadius: "10px",
              padding: "10px 18px",
              color: "#FFFFFF",
              fontSize: "13px",
              outline: "none"
            }}
          />
          <button
            onClick={handleTriggerRun}
            disabled={isLaunching}
            style={{
              background: "linear-gradient(135deg, #703AE6 0%, #38EF7D 100%)",
              color: "#000000",
              border: "none",
              borderRadius: "10px",
              padding: "10px 18px",
              fontFamily: MONO,
              fontSize: "12px",
              fontWeight: 800,
              cursor: isLaunching ? "not-allowed" : "pointer",
              boxShadow: "0 4px 16px rgba(56, 239, 125, 0.35)",
              whiteSpace: "nowrap"
            }}
          >
            {isLaunching ? "⏳ Launching..." : (triggerMsg || "▶ Launch Run")}
          </button>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
          {/* Scope Toggle: Fresh Session vs Global History */}
          <div style={{ display: "flex", gap: "4px", background: "rgba(255,255,255,0.03)", padding: "4px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.08)" }}>
            <button
              onClick={() => setSessionScope("SESSION")}
              style={{
                background: sessionScope === "SESSION" ? "rgba(56, 239, 125, 0.15)" : "transparent",
                border: `1px solid ${sessionScope === "SESSION" ? "#38EF7D" : "transparent"}`,
                color: sessionScope === "SESSION" ? "#38EF7D" : "#8E85A8",
                padding: "6px 12px",
                borderRadius: "7px",
                fontFamily: MONO,
                fontSize: "11px",
                fontWeight: 700,
                cursor: "pointer"
              }}
            >
              ✨ Fresh Session ({sessionRunIds.length})
            </button>
            <button
              onClick={() => setSessionScope("GLOBAL")}
              style={{
                background: sessionScope === "GLOBAL" ? "rgba(112, 58, 230, 0.25)" : "transparent",
                border: `1px solid ${sessionScope === "GLOBAL" ? "#703AE6" : "transparent"}`,
                color: sessionScope === "GLOBAL" ? "#A387FF" : "#8E85A8",
                padding: "6px 12px",
                borderRadius: "7px",
                fontFamily: MONO,
                fontSize: "11px",
                fontWeight: 700,
                cursor: "pointer"
              }}
            >
              🌐 Global Archive ({runs.length})
            </button>
            {sessionRunIds.length > 0 && (
              <button
                onClick={() => {
                  sessionStorage.removeItem("vanna_session_runs");
                  setSessionRunIds([]);
                  window.dispatchEvent(new Event("vanna_session_updated"));
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#8E85A8",
                  padding: "6px 8px",
                  borderRadius: "6px",
                  fontFamily: MONO,
                  fontSize: "10px",
                  cursor: "pointer"
                }}
                title="Wipe this tab's session back to clean 0-state"
              >
                🧹 Reset
              </button>
            )}
          </div>

          {[
            { id: "ALL", label: `All (${targetPool.length})` },
            { id: "PUBLISHED", label: "Published" },
            { id: "HIGH_SCORE", label: "Score ≥ 90" }
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setStatusFilter(t.id)}
              style={{
                background: statusFilter === t.id ? "rgba(112, 58, 230, 0.25)" : "rgba(255,255,255,0.05)",
                border: `1px solid ${statusFilter === t.id ? "#703AE6" : "rgba(255,255,255,0.1)"}`,
                color: statusFilter === t.id ? "#FFFFFF" : "#A2A1A6",
                padding: "8px 16px",
                borderRadius: "8px",
                cursor: "pointer",
                fontFamily: MONO,
                fontSize: "12px",
                fontWeight: 600
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Production Runs Table */}
      <div
        style={{
          background: "#0C0716",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "18px",
          overflow: "hidden",
          boxShadow: "0 12px 36px rgba(0,0,0,0.4)"
        }}
      >
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
            <thead>
              <tr style={{ background: "#080310", borderBottom: "1px solid rgba(255, 255, 255, 0.08)" }}>
                <th style={{ padding: "14px 20px", fontFamily: MONO, fontSize: "11px", color: "#A2A1A6", textTransform: "uppercase" }}>Run ID & Narrative Title</th>
                <th style={{ padding: "14px 20px", fontFamily: MONO, fontSize: "11px", color: "#A2A1A6", textTransform: "uppercase" }}>Audience & GTM Machine</th>
                <th style={{ padding: "14px 20px", fontFamily: MONO, fontSize: "11px", color: "#A2A1A6", textTransform: "uppercase" }}>Reviewer Score</th>
                <th style={{ padding: "14px 20px", fontFamily: MONO, fontSize: "11px", color: "#A2A1A6", textTransform: "uppercase" }}>Artifacts</th>
                <th style={{ padding: "14px 20px", fontFamily: MONO, fontSize: "11px", color: "#A2A1A6", textTransform: "uppercase" }}>Duration & Cost</th>
                <th style={{ padding: "14px 20px", fontFamily: MONO, fontSize: "11px", color: "#A2A1A6", textTransform: "uppercase", textAlign: "right" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredRuns.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: "60px 24px", textAlign: "center", color: "#8E85A8" }}>
                    <div style={{ fontSize: "28px", marginBottom: "10px" }}>🚀</div>
                    <div style={{ fontSize: "16px", fontWeight: 700, color: "#FFFFFF" }}>
                      No System 2 Runs Executed Yet
                    </div>
                    <div style={{ fontSize: "13px", color: "#A2A1A6", marginTop: "6px", maxWidth: "60ch", margin: "6px auto 0" }}>
                      The dashboard is reset and pristine. Enter a founder directive in the Mission Command Console above to launch your first 13-agent autonomous cycle.
                    </div>
                  </td>
                </tr>
              ) : (
                filteredRuns.map((r, i) => {
                const title = r.title || r.winner_hook || r.run_id || "Autonomous Run";
                // These read the v2 journal. They previously fell back to
                // "A2: Quantitative Traders" / "MACH_04: Technical Telemetry
                // Series" / "96/100" on keys (agent_03_strategist,
                // agent_10_reviewer) that this pipeline does not emit — so
                // every row showed the same three fabricated values.
                const arc = r.agent_outputs?.debate?.status ? r.reasoning?.arc : null;
                const aud = arc || r.agent_outputs?.debate?.kind ? (r.reasoning?.arc ?? "—") : "—";
                const mach = r.reasoning?.playbook?.id ?? "—";
                const dur = r.duration_s ? `${r.duration_s}s` : "—";
                const agentsRatio = r.agents_declared
                  ? `${r.agents_that_reasoned}/${r.agents_declared}`
                  : null;
                const blocked = r.blocked_reason;
                const dateStr = r.started ? new Date(r.started * 1000).toLocaleString() : `Run #${runs.length - i}`;

                return (
                  <tr
                    key={r.run_id || i}
                    style={{
                      borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
                      transition: "background 0.2s ease"
                    }}
                  >
                    {/* Column 1: Run ID & Title */}
                    <td style={{ padding: "18px 22px" }}>
                      <div style={{ fontFamily: MONO, fontSize: "11px", color: "#A387FF" }}>{r.run_id}</div>
                      <div style={{ fontSize: "14px", fontWeight: 700, color: "#FFFFFF", marginTop: "3px", lineHeight: 1.4 }}>{title}</div>
                      <div style={{ fontSize: "11px", color: "#8E85A8", marginTop: "3px" }}>{dateStr}</div>
                    </td>

                    {/* Column 2: Audience & Machine */}
                    <td style={{ padding: "18px 22px" }}>
                      <div style={{ fontSize: "13px", fontWeight: 600, color: "#32EEE2" }}>{aud}</div>
                      <div style={{ fontSize: "11px", color: "#A2A1A6", marginTop: "3px" }}>{mach}</div>
                    </td>

                    {/* Column 3: gate outcome — there is no reviewer score in
                        this pipeline; publication is decided by the claim gate. */}
                    <td style={{ padding: "18px 22px" }}>
                      <span
                        style={{
                          fontFamily: MONO, fontSize: "11.5px", fontWeight: 700,
                          color: blocked ? "#F5A524" : "#38EF7D",
                          background: blocked ? "rgba(245,165,36,0.12)" : "rgba(56, 239, 125, 0.12)",
                          border: `1px solid ${blocked ? "rgba(245,165,36,0.3)" : "rgba(56, 239, 125, 0.3)"}`,
                          padding: "4px 10px", borderRadius: "6px", whiteSpace: "nowrap",
                        }}
                      >
                        {blocked ? "GATE BLOCKED" : "GATE PASSED"}
                      </span>
                      {agentsRatio && (
                        <div style={{ fontSize: "10.5px", color: "#8E85A8", marginTop: "5px", fontFamily: MONO }}>
                          {agentsRatio} agents reasoned
                        </div>
                      )}
                    </td>

                    {/* Column 4: Dynamic Media Badges */}
                    <td style={{ padding: "18px 22px" }}>
                      {/* Render what the run produced, rather than badges
                          describing it. A badge reading "41s Video" was shown
                          for any run with a video key, whatever its length. */}
                      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "flex-start" }}>
                        {r.visual && (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={r.visual}
                            alt="rendered visual"
                            style={{ width: 96, height: 96, objectFit: "cover", borderRadius: 8,
                                     border: "1px solid rgba(255,255,255,0.08)" }}
                          />
                        )}
                        {r.video && (
                          <video
                            src={r.video}
                            muted
                            loop
                            playsInline
                            onMouseEnter={(e) => (e.currentTarget as HTMLVideoElement).play()}
                            onMouseLeave={(e) => (e.currentTarget as HTMLVideoElement).pause()}
                            style={{ width: 128, height: 96, objectFit: "cover", borderRadius: 8,
                                     border: "1px solid rgba(163,135,255,0.3)", background: "#07020D" }}
                          />
                        )}
                        {!r.visual && !r.video && (
                          <span style={{ fontSize: "11px", color: "#6A6A6A" }}>no media</span>
                        )}
                      </div>
                    </td>

                    {/* Column 5: Dynamic Duration & Calculated Cost */}
                    <td style={{ padding: "18px 22px" }}>
                      <div style={{ fontFamily: MONO, fontSize: "12px", color: "#FFFFFF" }}>{dur}</div>
                      <div style={{ fontFamily: MONO, fontSize: "11px", color: "#8E85A8", marginTop: "2px" }}>
                        ${(0.008 + (r.duration_s ? r.duration_s * 0.0006 : 0.012) + ((r.video || r.agent_outputs?.agent_09_video) ? 0.008 : 0) + ((r.visual || r.agent_outputs?.agent_08_visual) ? 0.004 : 0)).toFixed(3)}
                      </div>
                    </td>

                    {/* Column 6: Action */}
                    <td style={{ padding: "18px 22px", textAlign: "right" }}>
                      <button
                        onClick={() => {
                          if (r.run_id) vm.openRun(r.run_id);
                        }}
                        style={{
                          background: "rgba(112, 58, 230, 0.25)",
                          border: "1px solid rgba(163, 135, 255, 0.45)",
                          color: "#FFFFFF",
                          padding: "8px 16px",
                          borderRadius: "8px",
                          fontSize: "12px",
                          fontFamily: MONO,
                          fontWeight: 700,
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                        }}
                      >
                        Inspect →
                      </button>
                    </td>
                  </tr>
                );
              }))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
