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

export function LiveTrace({ runId }: { runId?: string }) {
  const [events, setEvents] = useState<any[]>([]);
  const [meta, setMeta] = useState<{ runId: string | null; finished: boolean; status: string }>({
    runId: null,
    finished: false,
    status: "running",
  });
  const cursor = useRef(-1);
  const seenRun = useRef<string | null>(null);

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
      setMeta({ runId: d.runId, finished: d.finished, status: d.status });
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
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 800, color: "var(--vn-ink)", marginTop: 6 }}>
            Live Trace
          </h2>
          <p style={{ fontSize: 14, color: "var(--vn-ink-muted)", marginTop: 4 }}>
            Each agent, each model call and each judgement, as it is recorded.
          </p>
        </div>
      </div>

      {events.length === 0 && (
        <EmptyState icon="trace" title="Nothing running right now"
          body="When a run starts, each agent, model call and judgement appears here as it is recorded." />
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
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
              <Row key={i} at={e.at} tone={e.ok ? "#2A2A32" : "var(--vn-bad)"}>
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
                {p.chosen && <Line label="chose">{p.chosen}</Line>}
                {p.signal && <Line label="signal">{p.signal}</Line>}
                {p.why && <Line label="why">{p.why}</Line>}
                {p.verdict && <Line label="verdict">{p.verdict}</Line>}
                {p.pillar && <Line label="pillar">{p.pillar}</Line>}
                {p.rationale && <Line label="rationale">{p.rationale}</Line>}
                {p.concept && <Line label="concept">{p.concept}</Line>}
                {p.overall && <Line label="overall">{p.overall}</Line>}

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
        border: `1px solid ${strong ? `${tone}33` : "var(--vn-line)"}`,
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
