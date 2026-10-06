"use client";

/**
 * The run as it happens — every agent, every model call, every judgement.
 *
 * The view this replaces was called "Live Debate" and rendered three
 * competing narrative arcs with WINNER / GRAFTED / REJECTED verdicts and
 * scores derived by subtracting 4 and 8 from a single number. None of that
 * happened: these 13 agents do not debate, they run in sequence — A02
 * selects, A03 formulates, A07 art-directs, A10 reviews.
 *
 * What is real is the journal, which is append-only and written as the cycle
 * goes. This tails it. Nothing here is synthesised: a decision appears when
 * the agent records it, and an agent that fails appears as failed.
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import { MONO } from "@/lib/colors";
import { EmptyState } from "@/components/States";
import { CompanyChip } from "@/components/CompanyChip";
import { AgentReasoning } from "@/components/views/AgentReasoning";
import { GtmAgents } from "@/components/views/GtmAgents";

const DIM = "var(--vn-ink-muted)";

const TONE: Record<string, string> = {
  ok: "var(--vn-ok)",
  degraded: "var(--vn-warn)",
  failed: "var(--vn-bad)",
  skipped: DIM,
};

const KIND_TONE: Record<string, string> = {
  chose: "var(--vn-accent-ink)",
  formulated: "var(--vn-accent-ink)",
  directed: "var(--vn-accent-ink)",
  judged: "var(--vn-warn)",
  reviewed: "var(--vn-ok)",
  declined: "var(--vn-bad)",
};

function clock(iso?: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(d.getTime()) ? "" : d.toLocaleTimeString();
}


/** One line a manager can read. The full payload stays on the floor below. */
function reportLine(e: any): string {
  const p = e.payload || {};
  if (e.kind === "bandit") {
    return Object.keys(p).map((k) => {
      const v = p[k];
      const choice = v && typeof v === "object" && v.choice != null ? String(v.choice) : txt(v);
      return k.replace(/_/g, " ") + ": " + choice;
    }).join(" · ");
  }
  if (e.kind === "source_learning") return txt(p.record);
  if (e.kind === "landscape") return txt(p.summary);
  if (e.kind === "brain_context") return "Profile " + (p.profile_status || "loaded") + (p.tenant ? " · " + p.tenant : "");
  if (e.kind === "poster_brief") return txt(p.brief && (p.brief.headline || p.brief.idea));
  if (e.kind === "motion_plan") return txt(p.why);
  if (e.kind === "preferences") return "Reviewed " + (p.reviewed_runs || 0) + " runs";
  if (e.kind === "declined" || (e.kind === "reviewed" && p.passed != null)) {
    return p.passed === false ? "Held for a person to review" : "Cleared";
  }
  const lead = p.chosen || p.signal || p.concept || p.overall || p.verdict || p.why;
  return txt(lead) || String(e.kind || "");
}

function txt(v: any): string {
  if (v == null) return "";
  if (typeof v !== "object") return String(v);
  if ("choice" in v) return String(v.choice) + (v.why ? " (" + v.why + ")" : "");
  return JSON.stringify(v);
}

export function LiveTrace({ runId }: { runId?: string }) {
  const [events, setEvents] = useState<any[]>([]);
  const [meta, setMeta] = useState<{ runId: string | null; finished: boolean; status: string; company?: string }>({
    runId: null,
    finished: false,
    status: "running",
  });
  const cursor = useRef(-1);
  const seenRun = useRef<string | null>(null);
  const [floor, setFloor] = useState(false);
  const [floorTab, setFloorTab] = useState<"work" | "decisions" | "agents">("work");

  useEffect(() => {
    const apply = () => {
      let tab: string | null = null;
      try { tab = sessionStorage.getItem("vn_floor_tab"); } catch { tab = null; }
      if (tab === "brain") tab = "work";
      if (tab === "work" || tab === "decisions" || tab === "agents") {
        setFloor(true);
        setFloorTab(tab);
        try { sessionStorage.removeItem("vn_floor_tab"); } catch { /* private mode */ }
      }
      try {
        const url = new URL(window.location.href);
        if (url.searchParams.get("view") === "brain") {
          url.searchParams.delete("view");
          window.history.replaceState({}, "", url.pathname + url.search);
        }
      } catch { /* prerender */ }
    };
    apply();
    window.addEventListener("vn-floor", apply);
    return () => window.removeEventListener("vn-floor", apply);
  }, []);

  const poll = useCallback(async () => {
    try {
      const q = new URLSearchParams({ after: String(cursor.current) });
      if (runId) q.set("runId", runId);
      const r = await fetch(`/api/gtm/trace?${q}`, { cache: "no-store" });
      if (!r.ok) return;
      const d = await r.json();

      // A new run started: drop the previous one's events rather than
      // appending onto them.
      if (d.runId && d.runId !== seenRun.current) {
        seenRun.current = d.runId;
        cursor.current = -1;
        setEvents(d.events ?? []);
      } else if (d.events?.length) {
        setEvents((prev) => [...prev, ...d.events]);
      }
      cursor.current = d.cursor ?? cursor.current;
      setMeta({ runId: d.runId, finished: d.finished, status: d.status, company: d.company });
    } catch {
      /* a dropped poll must not clear what is already on screen */
    }
  }, [runId]);

  useEffect(() => {
    poll();
    // 1.5s while running is responsive without hammering; once the run has
    // finished the journal cannot change, so this stops polling entirely.
    const t = setInterval(() => {
      if (!meta.finished) poll();
    }, 1500);
    return () => clearInterval(t);
  }, [poll, meta.finished]);

  const live = !meta.finished && events.length > 0;
  const stages = events.filter((e) => e.type === "stage");
  const calls = events.filter((e) => e.type === "call");
  const decisions = events.filter((e) => e.type === "decision");
  const current = stages.filter((s) => s.status === "running").pop() || stages[stages.length - 1];

  return (
    <section className="vanna-section">
      <div className="vanna-banner">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span
              style={{
                width: 9,
                height: 9,
                borderRadius: 999,
                background: live ? "var(--vn-ok)" : DIM,
                boxShadow: live ? "0 0 0 3px var(--vn-hover)" : "none",
              }}
            />
            <span style={{ fontFamily: MONO, fontSize: 12, fontWeight: 700, color: live ? "var(--vn-ok)" : DIM, letterSpacing: "0.08em" }}>
              {live ? "RUNNING" : meta.finished ? String(meta.status).toUpperCase() : "IDLE"}
              {meta.runId ? ` · ${meta.runId}` : ""}
            </span>
            {meta.runId && <CompanyChip company={meta.company || "vanna"} />}
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 800, color: "var(--vn-ink)", marginTop: 6 }}>
            Live Trace
          </h2>
          <p style={{ fontSize: 14, color: "var(--vn-ink-muted)", marginTop: 4, maxWidth: "62ch" }}>
            Where this run is, and what it decided. The agents, their decisions, and the step-by-step work stay closed until you open them.
          </p>
        </div>
        <button type="button" onClick={() => setFloor((v) => !v)}
          style={{ background: floor ? "var(--vn-sunken)" : "var(--vn-cta)", color: floor ? "var(--vn-ink)" : "var(--vn-on-accent)",
            border: floor ? "1px solid var(--vn-line-strong)" : "none", borderRadius: 8, padding: "8px 14px", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
          {floor ? "Back to the report" : "See how it was done"}
        </button>
      </div>

      {events.length === 0 && !floor && (
        <EmptyState icon="trace" title="Nothing running right now"
          body="When a run starts, its status appears here. The agents' notes stay closed unless you open them." />
      )}

      {events.length > 0 && !floor ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, padding: "var(--vn-card-pad)" }}>
            <div style={{ fontFamily: MONO, fontSize: 11, color: DIM, letterSpacing: "0.06em" }}>NOW</div>
            <div style={{ fontSize: 18, color: "var(--vn-ink)", marginTop: 6 }}>{current ? current.name : "Waiting for the first step"}</div>
            {current && current.detail ? <p style={{ fontSize: 14, color: "var(--vn-ink-body)", margin: "8px 0 0" }}>{current.detail}</p> : null}
            <div style={{ fontFamily: MONO, fontSize: 12, color: DIM, marginTop: 10 }}>
              {stages.length} steps · {calls.length} model calls · {decisions.length} decisions
            </div>
          </div>
          {decisions.map((e, i) => (
            <div key={i} style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, padding: "16px 18px" }}>
              <div style={{ fontFamily: MONO, fontSize: 11, color: KIND_TONE[e.kind] || "var(--vn-accent-ink)", letterSpacing: "0.06em", textTransform: "uppercase" }}>{e.kind}</div>
              <div style={{ fontSize: 15, color: "var(--vn-ink)", marginTop: 6, lineHeight: 1.5 }}>{reportLine(e)}</div>
            </div>
          ))}
        </div>
      ) : null}

      {floor ? (
      <div className="backend-floor" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {([
            ["work", "The work"],
            ["decisions", "Decisions"],
            ["agents", "Agents"],
          ] as const).map(([id, label]) => (
            <button key={id} type="button" onClick={() => setFloorTab(id)}
              style={{
                background: floorTab === id ? "var(--vn-raised)" : "transparent",
                color: floorTab === id ? "var(--vn-ink)" : "var(--vn-ink-muted)",
                border: "1px solid " + (floorTab === id ? "var(--vn-line-strong)" : "var(--vn-line)"),
                borderRadius: 8, padding: "7px 12px", fontSize: 13, fontWeight: 600, cursor: "pointer",
              }}>
              {label}
            </button>
          ))}
        </div>
        {floorTab === "decisions" ? <AgentReasoning /> : null}
        {floorTab === "agents" ? <GtmAgents /> : null}
        {floorTab === "work" ? (
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {events.length === 0 && (
          <EmptyState icon="trace" title="No step-by-step notes yet"
            body="When a run is underway, each agent and each model call is recorded here." />
        )}
        {events.map((e, i) => {
          if (e.type === "stage") {
            const tone = TONE[e.status] ?? DIM;
            return (
              <Row key={i} at={e.at} tone={tone}>
                <span style={{ fontFamily: MONO, fontSize: 11, color: DIM }}>{e.agent}</span>
                <span style={{ fontSize: 13.5, color: "var(--vn-ink)", fontWeight: 600 }}>{e.name}</span>
                <span style={{ fontFamily: MONO, fontSize: 11, color: tone }}>{e.status}</span>
                {e.detail && (
                  <span style={{ fontSize: 12.5, color: "var(--vn-ink-muted)", flexBasis: "100%", lineHeight: 1.5 }}>
                    {e.detail}
                  </span>
                )}
              </Row>
            );
          }

          if (e.type === "call") {
            return (
              <Row key={i} at={e.at} tone={e.ok ? "var(--vn-line-strong)" : "var(--vn-bad)"}>
                <span style={{ fontFamily: MONO, fontSize: 11, color: DIM }}>{e.agent}</span>
                <span style={{ fontFamily: MONO, fontSize: 11.5, color: "var(--vn-accent-ink)" }}>{e.model}</span>
                <span style={{ fontFamily: MONO, fontSize: 11, color: DIM }}>
                  {e.inputTokens?.toLocaleString?.() ?? 0} in / {e.outputTokens?.toLocaleString?.() ?? 0} out · {e.durationS}s
                  {e.ok ? "" : " · FAILED"}
                </span>
              </Row>
            );
          }

          // decision
          const tone = KIND_TONE[e.kind] ?? "var(--vn-accent-ink)";
          const p = e.payload ?? {};
          return (
            <Row key={i} at={e.at} tone={tone} strong>
              <span style={{ fontFamily: MONO, fontSize: 11, color: DIM }}>{e.agent}</span>
              <span style={{ fontFamily: MONO, fontSize: 11, fontWeight: 700, color: tone, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                {e.kind}
              </span>

              <div style={{ flexBasis: "100%", marginTop: 6, display: "flex", flexDirection: "column", gap: 6 }}>
                {p.chosen && e.kind !== "bandit" && <Line label="chose">{txt(p.chosen)}</Line>}
                {p.signal && e.kind !== "bandit" && <Line label="signal">{txt(p.signal)}</Line>}
                {p.why && e.kind !== "bandit" && <Line label="why">{txt(p.why)}</Line>}
                {p.verdict && e.kind !== "bandit" && <Line label="verdict">{txt(p.verdict)}</Line>}
                {p.pillar && e.kind !== "bandit" && <Line label="pillar">{txt(p.pillar)}</Line>}
                {p.rationale && e.kind !== "bandit" && <Line label="rationale">{txt(p.rationale)}</Line>}
                {p.concept && e.kind !== "bandit" && <Line label="concept">{txt(p.concept)}</Line>}
                {p.overall && e.kind !== "bandit" && <Line label="overall">{txt(p.overall)}</Line>}

                {/* The strategist's bandit: one {choice, why} per strategy arm. */}
                {e.kind === "bandit" && Object.entries(p).map(([dim, v]: [string, any]) => (
                  <Line key={dim} label={dim.replace(/_/g, " ")}>{txt(v)}</Line>
                ))}

                {Array.isArray(p.reasoning) && p.reasoning.length > 0 && (
                  <Sub label={`reasoning (${p.reasoning.length})`}>
                    {p.reasoning.map((r: string, k: number) => (
                      <li key={k} style={{ marginBottom: 3 }}>{r}</li>
                    ))}
                  </Sub>
                )}

                {Array.isArray(p.rejected) && p.rejected.length > 0 && (
                  <Sub label={`turned down (${p.rejected.length})`}>
                    {p.rejected.map((r: any, k: number) => (
                      <li key={k} style={{ marginBottom: 5 }}>
                        <span style={{ color: "var(--vn-ink-muted)" }}>{r.headline}</span>
                        {r.why && <span style={{ color: DIM }}> — {r.why}</span>}
                      </li>
                    ))}
                  </Sub>
                )}

                {Array.isArray(p.assets) && p.assets.length > 0 && (
                  <Sub label="assets">
                    {p.assets.map((a: any, k: number) => (
                      <li key={k} style={{ marginBottom: 5 }}>
                        <span style={{ fontFamily: MONO, color: KIND_TONE[String(a.verdict).toLowerCase()] ?? "var(--vn-ink-muted)" }}>
                          {a.asset}: {a.verdict}
                        </span>
                        {a.critique && <span style={{ color: DIM }}> — {a.critique}</span>}
                      </li>
                    ))}
                  </Sub>
                )}

                {Array.isArray(p.blocked_claims) && p.blocked_claims.length > 0 && (
                  <Sub label={`blocked claims (${p.blocked_claims.length})`}>
                    {p.blocked_claims.map((c: any, k: number) => (
                      <li key={k} style={{ marginBottom: 3, color: "var(--vn-bad)" }}>
                        {typeof c === "string" ? c : JSON.stringify(c)}
                      </li>
                    ))}
                  </Sub>
                )}
              </div>
            </Row>
          );
        })}
      </div>
      ) : null}
      </div>
      ) : null}
    </section>
  );
}

function Row({ at, tone, strong, children }: {
  at?: string; tone: string; strong?: boolean; children: React.ReactNode;
}) {
  return (
    <div
      style={{
        background: "var(--vn-surface)",
        border: `1px solid ${strong ? `color-mix(in srgb, ${tone} 20%, transparent)` : "var(--vn-line)"}`,
        borderLeft: `3px solid ${tone}`,
        borderRadius: 8,
        padding: strong ? "14px 16px" : "10px 14px",
        display: "flex",
        alignItems: "center",
        gap: 12,
        flexWrap: "wrap",
      }}
    >
      <span style={{ fontFamily: MONO, fontSize: 10.5, color: "var(--vn-ink-faint)", minWidth: 62 }}>
        {clock(at)}
      </span>
      {children}
    </div>
  );
}

function Line({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ fontSize: 13, lineHeight: 1.55 }}>
      <span style={{ fontFamily: MONO, fontSize: 10.5, color: DIM, textTransform: "uppercase", marginRight: 8 }}>
        {label}
      </span>
      <span style={{ color: "var(--vn-ink-body)" }}>{children}</span>
    </div>
  );
}

function Sub({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginTop: 2 }}>
      <div style={{ fontFamily: MONO, fontSize: 10.5, color: DIM, textTransform: "uppercase" }}>
        {label}
      </div>
      <ul style={{ margin: "5px 0 0", paddingLeft: 18, fontSize: 12.5, lineHeight: 1.5 }}>
        {children}
      </ul>
    </div>
  );
}
