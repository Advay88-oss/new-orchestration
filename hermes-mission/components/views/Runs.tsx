"use client";

import React, { useState, useEffect } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

export function Runs({ vm }: { vm: MissionVM }) {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [sessionScope, setSessionScope] = useState<"SESSION" | "GLOBAL">("GLOBAL");
  const [showEmpty, setShowEmpty] = useState(false);
  const [sessionRunIds, setSessionRunIds] = useState<string[]>([]);

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


  // A run that recorded no model call and no agent reasoning did not run.
  // Both conditions, not either: a deterministic-only run would have agents
  // that reasoned, and a run that died inside its first model call has calls.
  // A run that produced a visual or a video started, whatever its journal
  // says — studio runs made outside a cycle have assets and no call log.
  const neverStarted = (r: any) =>
    (r.agents_that_reasoned ?? 0) === 0 && (r.spend?.calls ?? 0) === 0
    && !r.visual && !r.video;

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
      (statusFilter === "PUBLISHED" && r.dispatched === true) ||
      (statusFilter === "BLOCKED" && r.publishable !== true);

    return matchesSearch && matchesStatus && (showEmpty || !neverStarted(r));
  });

  const emptyCount = targetPool.filter(neverStarted).length;

  return (
    <section className="vanna-section">
      {/* Telemetry Header Strip */}
      <div
        className="vanna-banner"
        style={{
          background: "var(--vn-surface)",
          border: "1px solid rgba(163, 135, 255, 0.3)",
        }}
      >
        {/* Once the repeated title came out, this card was one word on the
            left and two figures on the right with a third of the row empty
            between them. It is a stats strip, so it is laid out as one. */}
        <div style={{ display: "flex", alignItems: "center", gap: "32px", flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: "11px", color: "var(--vn-ink-faint)" }}>Runs recorded</div>
            <div style={{ fontFamily: MONO, fontSize: "27px", fontWeight: 600, color: "var(--vn-ink)", letterSpacing: "-0.02em" }}>{runs.length}</div>
          </div>
          <div>
            <div style={{ fontSize: "11px", color: "var(--vn-ink-faint)" }}>Showing</div>
            <div style={{ fontFamily: MONO, fontSize: "27px", fontWeight: 600, color: "var(--vn-ink)", letterSpacing: "-0.02em" }}>{filteredRuns.length}</div>
          </div>
          {emptyCount > 0 && (
            <div>
              <div style={{ fontSize: "11px", color: "var(--vn-ink-faint)" }}>Never started</div>
              <button
                onClick={() => setShowEmpty((v) => !v)}
                style={{
                  background: "transparent", border: "none", padding: 0,
                  cursor: "pointer", fontFamily: MONO, fontSize: "22px",
                  fontWeight: 600, letterSpacing: "-0.02em",
                  color: showEmpty ? "var(--vn-ink)" : "var(--vn-ink-muted)",
                }}
                title={showEmpty ? "Hide runs that never started" : "Show runs that never started"}
              >
                {emptyCount}
                <span style={{ fontSize: "12px", fontWeight: 500, marginLeft: "8px", color: "var(--vn-accent-light)" }}>
                  {showEmpty ? "hide" : "show"}
                </span>
              </button>
            </div>
          )}
          <div>
            <div style={{ fontSize: "11px", color: "var(--vn-ink-faint)" }}>Autonomous daemon</div>
            <div style={{ display: "flex", alignItems: "center", gap: "7px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "999px", background: daemonRunning ? "#4ADE9B" : "#7B7590" }} />
              <span style={{ fontFamily: MONO, fontSize: "22px", fontWeight: 600, color: daemonRunning ? "#4ADE9B" : "var(--vn-ink-muted)", letterSpacing: "-0.02em" }}>
                {daemonRunning ? "Active" : "Standby"}
              </span>
            </div>
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
          {/* A third "Launch Run" sat here, beside the search box, with one
              in the page header and one in the command console above. Three
              buttons that fire the same POST is three chances to fire it
              twice. The header's is the one that stays. */}
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
          {/* Scope Toggle: Fresh Session vs Global History */}
          <div style={{ display: "flex", gap: "4px", background: "rgba(255,255,255,0.03)", padding: "4px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.08)" }}>
            <button
              onClick={() => setSessionScope("SESSION")}
              style={{
                background: sessionScope === "SESSION" ? "rgba(255,255,255,0.07)" : "transparent",
                border: `1px solid ${sessionScope === "SESSION" ? "var(--vn-line-strong)" : "transparent"}`,
                color: sessionScope === "SESSION" ? "var(--vn-ink)" : "var(--vn-ink-muted)",
                padding: "7px 14px",
                borderRadius: "8px",
                fontSize: "12px",
                fontWeight: 500,
                cursor: "pointer"
              }}
            >
              Fresh Session ({sessionRunIds.length})
            </button>
            <button
              onClick={() => setSessionScope("GLOBAL")}
              style={{
                background: sessionScope === "GLOBAL" ? "rgba(255,255,255,0.07)" : "transparent",
                border: `1px solid ${sessionScope === "GLOBAL" ? "var(--vn-line-strong)" : "transparent"}`,
                color: sessionScope === "GLOBAL" ? "var(--vn-ink)" : "var(--vn-ink-muted)",
                padding: "7px 14px",
                borderRadius: "8px",
                fontSize: "12px",
                fontWeight: 500,
                cursor: "pointer"
              }}
            >
              Global Archive ({runs.length})
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
                  color: "#7B7590",
                  padding: "6px 8px",
                  borderRadius: "6px",
                  fontFamily: MONO,
                  fontSize: "10px",
                  cursor: "pointer"
                }}
                title="Wipe this tab's session back to clean 0-state"
              >
                Reset
              </button>
            )}
          </div>

          {[
            { id: "ALL", label: `All (${targetPool.length})` },
            { id: "PUBLISHED", label: "Published" },
            { id: "BLOCKED", label: "Blocked by review" }
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setStatusFilter(t.id)}
              style={{
                background: statusFilter === t.id ? "rgba(255,255,255,0.07)" : "transparent",
                border: `1px solid ${statusFilter === t.id ? "var(--vn-line-strong)" : "transparent"}`,
                color: statusFilter === t.id ? "var(--vn-ink)" : "var(--vn-ink-muted)",
                padding: "7px 14px",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "12px",
                fontWeight: 500
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
              <tr style={{ background: "var(--vn-sunken)", borderBottom: "1px solid var(--vn-line)" }}>
                <th style={{ padding: "14px 20px", fontSize: "11px", color: "var(--vn-ink-faint)", fontWeight: 500 }}>Run</th>
                <th style={{ padding: "14px 20px", fontSize: "11px", color: "var(--vn-ink-faint)", fontWeight: 500 }}>Audience</th>
                <th style={{ padding: "14px 20px", fontSize: "11px", color: "var(--vn-ink-faint)", fontWeight: 500 }}>Gate</th>
                <th style={{ padding: "14px 20px", fontSize: "11px", color: "var(--vn-ink-faint)", fontWeight: 500 }}>Artifacts</th>
                <th style={{ padding: "14px 20px", fontSize: "11px", color: "var(--vn-ink-faint)", fontWeight: 500 }}>Duration & cost</th>
                <th style={{ padding: "14px 20px", fontFamily: MONO, fontSize: "11px", color: "#7B7590", textTransform: "uppercase", textAlign: "right" }}>&nbsp;</th>
              </tr>
            </thead>
            <tbody>
              {filteredRuns.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: "60px 24px", textAlign: "center", color: "#7B7590" }}>
                    <div style={{ fontSize: "28px", marginBottom: "10px" }}></div>
                    <div style={{ fontSize: "16px", fontWeight: 700, color: "#FFFFFF" }}>
                      No GTM cycles recorded yet
                    </div>
                    <div style={{ fontSize: "13px", color: "#7B7590", marginTop: "6px", maxWidth: "60ch", margin: "6px auto 0" }}>
                      Press Launch Run, or enter a founder directive above. Leaving it empty runs the fully autonomous path, where A02 picks the topic itself.
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
                const aud = r.reasoning?.audience ?? "—";
                const mach = r.machine ?? r.reasoning?.playbook ?? "—";
                const dur = r.duration_s ? `${r.duration_s}s` : "—";
                const agentsRatio = r.agents_declared
                  ? `${r.agents_that_reasoned}/${r.agents_declared}`
                  : null;
                const blocked = r.blocked_reason;
                const gate = r.publishable === true
                  ? { label: "GATE PASSED", tone: "#4ADE9B" }
                  : blocked || r.status === "review_blocked"
                    ? { label: "GATE BLOCKED", tone: "#F5A524" }
                    : r.status === "aborted" || r.status === "failed"
                      ? { label: "RUN ABORTED", tone: "#F0666B" }
                      : r.status === "NO_ACTION" || r.status === "KILL"
                        ? { label: "NO ACTION", tone: "#7B7590" }
                        : { label: "NOT REVIEWED", tone: "#7B7590" };
                const dateStr = r.started ? new Date(r.started * 1000).toLocaleString() : `Run #${runs.length - i}`;

                return (
                  <tr
                    key={r.run_id || i}
                    // The row already declared a background transition and had
                    // nothing to transition to. Fifty static rows with no
                    // response to the cursor is most of why the table read as
                    // a printout rather than a list you can act on.
                    onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.025)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                    style={{
                      borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
                      transition: "background 0.15s ease",
                      cursor: "pointer",
                    }}
                    onClick={() => { if (r.run_id) vm.openRun(r.run_id); }}
                  >
                    {/* Column 1: Run ID & Title. The title is what a reader
                        scans for, so it leads; the id and the timestamp are
                        reference and sit under it, quieter. Before, all three
                        lines competed at roughly the same weight. */}
                    <td style={{ padding: "16px 22px" }}>
                      <div style={{ fontSize: "14.5px", fontWeight: 600,
                                    color: neverStarted(r) ? "var(--vn-ink-muted)" : "var(--vn-ink)",
                                    lineHeight: 1.35 }}>
                        {neverStarted(r) ? "Never started" : title}
                      </div>
                      <div style={{ display: "flex", gap: "10px", marginTop: "5px", alignItems: "center" }}>
                        <span style={{ fontFamily: MONO, fontSize: "11px", color: "var(--vn-ink-faint)" }}>{r.run_id}</span>
                        <span style={{ fontSize: "11px", color: "var(--vn-ink-faint)" }}>{dateStr}</span>
                      </div>
                    </td>

                    {/* Column 2: Audience & Machine */}
                    <td style={{ padding: "18px 22px" }}>
                      <div style={{ fontSize: "13px", fontWeight: 600, color: "#A98CFF" }}>{aud}</div>
                      <div style={{ fontSize: "11px", color: "#7B7590", marginTop: "3px" }}>{mach}</div>
                    </td>

                    {/* Column 3: gate outcome — there is no reviewer score in
                        this pipeline; publication is decided by the claim gate. */}
                    <td style={{ padding: "18px 22px" }}>
                      <span
                        style={{
                          fontFamily: MONO, fontSize: "11.5px", fontWeight: 700,
                          color: gate.tone,
                          background: `${gate.tone}1F`,
                          border: `1px solid ${gate.tone}4D`,
                          padding: "4px 10px", borderRadius: "6px", whiteSpace: "nowrap",
                        }}
                      >
                        {gate.label}
                      </span>
                      {agentsRatio && (
                        <div style={{ fontSize: "10.5px", color: "#7B7590", marginTop: "5px", fontFamily: MONO }}>
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

                    {/* Column 5: Duration & measured token usage.
                        The dollar figure that was here came from
                        `0.008 + duration_s * 0.0006 + …` — a cost invented from
                        wall-clock time, which is not what anything costs. No
                        rate table is wired for Model Garden or the API key, so
                        this shows what is actually measured: tokens. */}
                    <td style={{ padding: "18px 22px" }}>
                      <div style={{ fontFamily: MONO, fontSize: "12px", color: "#FFFFFF" }}>{dur}</div>
                      <div style={{ fontFamily: MONO, fontSize: "11px", color: "#7B7590", marginTop: "2px" }}>
                        {(r.spend?.input_tokens || r.spend?.output_tokens)
                          ? `${(((r.spend?.input_tokens ?? 0) + (r.spend?.output_tokens ?? 0)) / 1000).toFixed(1)}k tok · ${r.spend?.calls ?? 0} calls`
                          : "no model calls"}
                      </div>
                      {/* Real now: pipeline/state/model_rates.json holds the
                          published rates and the summary holds a per-model
                          tally, so the image and video calls — which carry no
                          tokens and are most of a full run's cost — are
                          priced rather than silently skipped. Still blank,
                          never $0.00, when a model has no published rate. */}
                      {typeof r.spend?.cost_usd === "number" && (
                        <div style={{ fontFamily: MONO, fontSize: "12px",
                                      color: r.spend.cost_usd >= 1 ? "#E8B34C" : "var(--vn-ink-muted)",
                                      marginTop: "3px" }}>
                          ${r.spend.cost_usd < 1
                            ? r.spend.cost_usd.toFixed(3)
                            : r.spend.cost_usd.toFixed(2)}
                          {r.spend.cost_complete === false ? " +" : ""}
                        </div>
                      )}
                    </td>

                    {/* Column 6: Action */}
                    <td style={{ padding: "18px 22px", textAlign: "right" }}>
                      <button
                        onClick={() => {
                          if (r.run_id) vm.openRun(r.run_id);
                        }}
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "#A98CFF",
                          padding: "8px 0",
                          fontSize: "13px",
                          fontWeight: 500,
                          cursor: "pointer",
                        }}
                      >
                        Inspect
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
