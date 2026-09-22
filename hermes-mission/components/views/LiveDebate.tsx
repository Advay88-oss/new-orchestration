'use client';

/**
 * What the pipeline actually decided.
 *
 * This view previously rendered three "competing narrative arcs" with verdicts
 * of WINNER / GRAFTED / REJECTED, reviewer scores derived by subtracting 4 and
 * 8 from a single number, and evidence references naming figures ($149.7M TVL,
 * ~320ms, 0.00014 XLM) that no stage had produced. None of that debate
 * happened: the pipeline's strategist commits to ONE arc, and the audit found
 * the tri-arc debate existed only in a legacy orchestrator that production
 * never ran.
 *
 * Everything below is read from the run's own artifacts.
 */

import React, { useCallback, useEffect, useState } from 'react';
import { MONO } from '@/lib/colors';
import type { MissionVM } from '@/lib/viewmodel';

const ACCENT = '#A387FF';
const ARC_TONE: Record<string, string> = {
  capital_efficiency: '#38EF7D',
  risk_relief: '#32EEE2',
  agentic_credit: '#A387FF',
};

const CLAIM_TONE: Record<string, string> = {
  verified: '#38EF7D',
  unverified: '#8A8A8A',
  unsupported: '#F5A524',
  refuted: '#FC5457',
};

interface Claim {
  text: string;
  kind: string;
  status: string;
  source_id: string | null;
  source_url: string | null;
  method: string | null;
  confidence: number;
}

interface Reasoning {
  runId: string;
  directive: string;
  arc: string | null;
  audience: string | null;
  problem: string | null;
  angle: string | null;
  playbook: { id: string; shape: string; forbidden: string[] } | null;
  vehicle: { id: string; shape: string; max_parts: number; reason: string } | null;
  hook: string | null;
  body: string | null;
  thread: string[];
  claims: Claim[];
  concepts: { id?: string; title: string; idea: string; layout: string; why: string }[];
  chosenConcept: { title: string; layout: string } | null;
  noveltyNote: string | null;
  gate: { passed: boolean; rule_violations: string[]; blocking_claims: Claim[]; rules_source: string } | null;
  review: { publishable: boolean } | null;
  debate: {
    winner: string | null;
    briefs: {
      arc: string; ok: boolean; error?: string;
      problem_statement?: string; angle?: string; audience?: string;
      evidence_used?: string[]; strongest_objection?: string;
    }[];
    ruling: {
      winner: string; reason: string; evidence_support: string[];
      rankings: { arc: string; evidence_grounding: number; argument_quality: number; audience_fit: number; note: string }[];
      unsupported_spotted: string[];
    } | null;
    judgeNote: string | null;
    failedStrategists: string[];
  } | null;
}

const label: React.CSSProperties = {
  fontSize: 9.5, letterSpacing: '.11em', color: '#6A6A6A', textTransform: 'uppercase',
};

export function LiveDebate({ vm }: { vm: MissionVM }) {
  const [runId, setRunId] = useState<string | null>(null);
  const [data, setData] = useState<Reasoning | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const rl = await fetch('/api/v2/runs?limit=1', { cache: 'no-store' });
      if (!rl.ok) throw new Error(`runs HTTP ${rl.status}`);
      const id = (await rl.json()).runs?.[0]?.runId ?? null;
      if (!id) { setData(null); setErr(null); return; }
      setRunId(id);
      const rr = await fetch(`/api/v2/runs/${id}/reasoning`, { cache: 'no-store' });
      if (!rr.ok) throw new Error(`reasoning HTTP ${rr.status}`);
      setData(await rr.json());
      setErr(null);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [load]);

  if (err) {
    return (
      <section className="vanna-card" style={{ borderColor: '#5E0D46' ,  }}>
        <div style={{ color: '#FC5457', fontSize: 13 }}>
          Backend unreachable: {err}. This view has no fixtures to fall back to.
        </div>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="vanna-card">
        <div style={{ color: '#7A7A7A', fontSize: 13 }}>
          No run recorded yet. Execute a directive from the Command Console.
        </div>
      </section>
    );
  }

  const verified = data.claims.filter((c) => c.status === 'verified');
  const blocking = data.claims.filter(
    (c) => c.kind !== 'creative' && c.status !== 'verified',
  );
  const arcTone = data.arc ? ARC_TONE[data.arc] ?? ACCENT : ACCENT;

  return (
    <section className="vanna-section" style={{ padding: 0 }}>
      <div>
        <h2 style={{ fontSize: 17, fontWeight: 700, margin: 0, color: '#EDEDED' }}>
          Decision trace
        </h2>
        <p style={{ fontSize: 12, color: '#7A7A7A', marginTop: 5, maxWidth: 760, lineHeight: 1.5 }}>
          Three strategists argue competing arcs from the same evidence; a judge that is given that
          same evidence rules between them. The judge ranks — it is not the last word on facts, so
          every claim in the winner is still checked below.
        </p>
      </div>

      {/* the debate itself */}
      {data.debate ? (
        <>
          <div className="vanna-card" style={{ borderLeft: `2px solid ${arcTone}` }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
              <div style={label}>Ruling</div>
              <span style={{ fontSize: 16, fontWeight: 700, color: arcTone, fontFamily: MONO }}>
                {data.debate.winner ?? "—"}
              </span>
              {data.debate.judgeNote && (
                <span style={{ marginLeft: "auto", fontSize: 11, color: "#F5A524" }}>
                  {data.debate.judgeNote}
                </span>
              )}
            </div>
            {data.debate.ruling?.reason && (
              <p style={{ fontSize: 13, color: "#EDEDED", marginTop: 8, lineHeight: 1.55 }}>
                {data.debate.ruling.reason}
              </p>
            )}
            {(data.debate.ruling?.unsupported_spotted?.length ?? 0) > 0 && (
              <div style={{ marginTop: 11 }}>
                <div style={{ ...label, color: "#F5A524" }}>
                  Judge flagged as unsupported by the evidence
                </div>
                <ul style={{ margin: "6px 0 0 16px", padding: 0 }}>
                  {data.debate.ruling!.unsupported_spotted.map((u, i) => (
                    <li key={i} style={{ fontSize: 12, color: "#B0B0B0", marginTop: 4, lineHeight: 1.45 }}>
                      {u}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: 12 }}>
            {data.debate.briefs.map((b) => {
              const rank = data.debate!.ruling?.rankings?.find((r) => r.arc === b.arc);
              const won = data.debate!.winner === b.arc;
              const tone = ARC_TONE[b.arc] ?? ACCENT;
              return (
                <div key={b.arc} className="vanna-card" style={{ borderColor: won ? tone : "#232323", opacity: b.ok ? 1 : 0.6,
                 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: tone, fontFamily: MONO }}>
                      {b.arc}
                    </span>
                    {won && (
                      <span style={{ marginLeft: "auto", fontSize: 9.5, letterSpacing: ".07em", color: tone }}>
                        WON
                      </span>
                    )}
                  </div>

                  {!b.ok && (
                    <div style={{ fontSize: 12, color: "#FC5457", marginTop: 8 }}>
                      strategist failed: {b.error}
                    </div>
                  )}

                  {rank && (
                    <div style={{ display: "flex", gap: 6, marginTop: 10 }}>
                      {[
                        ["grounding", rank.evidence_grounding],
                        ["argument", rank.argument_quality],
                        ["fit", rank.audience_fit],
                      ].map(([k, v]) => (
                        <div key={String(k)} style={{ flex: 1, border: "1px solid #1C1C1C", borderRadius: 6, padding: "6px 8px" }}>
                          <div style={{ fontSize: 8.5, letterSpacing: ".08em", color: "#6A6A6A", textTransform: "uppercase" }}>
                            {k}
                          </div>
                          <div style={{ fontSize: 15, fontWeight: 700, fontFamily: MONO, marginTop: 2,
                                        color: Number(v) >= 7 ? "#38EF7D" : Number(v) >= 4 ? "#F5A524" : "#FC5457" }}>
                            {v}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {b.angle && (
                    <p style={{ fontSize: 12, color: "#B0B0B0", marginTop: 10, lineHeight: 1.5 }}>
                      {b.angle.length > 220 ? b.angle.slice(0, 220) + "…" : b.angle}
                    </p>
                  )}

                  {b.strongest_objection && (
                    <div style={{ marginTop: 10, paddingTop: 9, borderTop: "1px solid #1A1A1A" }}>
                      <div style={label}>Its own strongest objection</div>
                      <p style={{ fontSize: 11.5, color: "#8A8A8A", marginTop: 4, lineHeight: 1.45 }}>
                        {b.strongest_objection.length > 160
                          ? b.strongest_objection.slice(0, 160) + "…"
                          : b.strongest_objection}
                      </p>
                    </div>
                  )}

                  <div style={{ fontSize: 10.5, color: "#5A5A5A", marginTop: 9, fontFamily: MONO }}>
                    evidence cited: {b.evidence_used?.length ? b.evidence_used.join(", ") : "none"}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <div className="vanna-card" style={{ borderLeft: `2px solid ${arcTone}` }}>
          <div style={label}>Chosen arc</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: arcTone, marginTop: 5, fontFamily: MONO }}>
            {data.arc ?? "—"}
          </div>
          <p style={{ fontSize: 12, color: "#7A7A7A", marginTop: 6 }}>
            Recorded before the debate stage existed, so only the winning arc was kept.
          </p>
        </div>
      )}

      {/* claims — the part that actually adjudicates */}
      <div className="vanna-card">
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
          <div style={label}>Claim adjudication</div>
          <div style={{ marginLeft: 'auto', fontSize: 11.5, color: '#8A8A8A', fontFamily: MONO }}>
            {verified.length} verified · {blocking.length} blocking · {data.claims.length} total
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 11 }}>
          {data.claims.length === 0 && (
            <div style={{ fontSize: 12.5, color: '#6A6A6A' }}>No claims recorded for this run.</div>
          )}
          {data.claims.map((c, i) => (
            <div key={i} style={{ border: '1px solid #1C1C1C', borderRadius: 8, padding: '9px 11px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{
                  fontSize: 9.5, padding: '1px 6px', borderRadius: 4, letterSpacing: '.05em',
                  background: '#1A1A1A', color: CLAIM_TONE[c.status] ?? '#8A8A8A',
                  textTransform: 'uppercase',
                }}>
                  {c.status}
                </span>
                <span style={{ fontSize: 10, color: '#5A5A5A' }}>{c.kind}</span>
                {c.source_id && (
                  <span style={{ marginLeft: 'auto', fontSize: 10, color: '#6A6A6A', fontFamily: MONO }}>
                    {c.source_id}
                  </span>
                )}
              </div>
              <div style={{ fontSize: 12.5, color: '#EDEDED', marginTop: 5, lineHeight: 1.5 }}>{c.text}</div>
              {c.method && (
                <div style={{ fontSize: 10.5, color: '#5A5A5A', marginTop: 4, fontFamily: MONO }}>
                  {c.method}
                  {c.confidence ? ` · confidence ${c.confidence.toFixed(2)}` : ''}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* concepts — real competition, where it exists */}
      {data.concepts.length > 0 && (
        <div className="vanna-card">
          <div style={label}>Visual concepts considered ({data.concepts.length})</div>
          {data.noveltyNote && (
            <div style={{ fontSize: 11.5, color: '#F5A524', marginTop: 7 }}>{data.noveltyNote}</div>
          )}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(230px,1fr))', gap: 10, marginTop: 11 }}>
            {data.concepts.map((c, i) => {
              const chosen = data.chosenConcept?.title === c.title;
              return (
                <div key={i} style={{
                  border: `1px solid ${chosen ? ACCENT : '#1C1C1C'}`, borderRadius: 8, padding: '9px 11px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                    <span style={{ fontSize: 10, color: '#6A6A6A', fontFamily: MONO }}>{c.layout}</span>
                    {chosen && (
                      <span style={{ marginLeft: 'auto', fontSize: 9.5, color: ACCENT, letterSpacing: '.06em' }}>
                        SELECTED
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 12.5, fontWeight: 600, color: '#EDEDED', marginTop: 4 }}>{c.title}</div>
                  <div style={{ fontSize: 11.5, color: '#8A8A8A', marginTop: 4, lineHeight: 1.45 }}>{c.idea}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* gate */}
      {data.gate && (
        <div className="vanna-card" style={{ borderLeft: `2px solid ${data.gate.passed ? '#38EF7D' : '#F5A524'}` }}>
          <div style={label}>Publication gate</div>
          <div style={{
            fontSize: 15, fontWeight: 700, marginTop: 5,
            color: data.gate.passed ? '#38EF7D' : '#F5A524',
          }}>
            {data.gate.passed ? 'PASSED' : 'BLOCKED'}
          </div>
          <div style={{ fontSize: 11, color: '#6A6A6A', marginTop: 4, fontFamily: MONO }}>
            rules: {data.gate.rules_source}
          </div>
          {data.gate.rule_violations?.length > 0 && (
            <div style={{ fontSize: 12, color: '#FC5457', marginTop: 9 }}>
              Rule violations: {data.gate.rule_violations.join('; ')}
            </div>
          )}
          {data.gate.blocking_claims?.length > 0 && (
            <div style={{ marginTop: 9 }}>
              <div style={{ fontSize: 11.5, color: '#F5A524' }}>
                {data.gate.blocking_claims.length} claim(s) could not be verified against evidence:
              </div>
              <ul style={{ margin: '6px 0 0 16px', padding: 0 }}>
                {data.gate.blocking_claims.slice(0, 6).map((c, i) => (
                  <li key={i} style={{ fontSize: 12, color: '#B0B0B0', marginTop: 3, lineHeight: 1.45 }}>
                    {c.text}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
