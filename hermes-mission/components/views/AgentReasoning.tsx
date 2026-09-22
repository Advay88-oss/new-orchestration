'use client';

/**
 * What the agents decided, and why — the GTM system's answer to "Live Debate".
 *
 * The view this replaces rendered three competing narrative arcs with verdicts
 * of WINNER / GRAFTED / REJECTED and scores derived by subtracting 4 and 8 from
 * a single number. None of that happened, and the 13 GTM agents have no debate
 * stage at all: A02 selects, A03 formulates, A07 art-directs.
 *
 * Everything below is a real decision recorded in the run journal. The
 * rejections are the point — "why not the other eleven signals" is what makes
 * A02's choice inspectable rather than an index.
 */

import React, { useCallback, useEffect, useState } from 'react';
import { MONO } from '@/lib/colors';

const ACCENT = '#A387FF';
const DIM = '#6C6C6C';

interface Detail {
  runId: string;
  status: string;
  signal: string | null;
  signalSourceType: string | null;
  signalObservedAt: string | null;
  selection: {
    chosen: string;
    why: string;
    rejected: { headline: string; why: string }[];
    candidates: number;
  } | null;
  strategyReasoning: string[];
  problem: string | null;
  opportunity: string | null;
  audience: string | null;
  machine: string | null;
  pillar: string | null;
  proofClaims: string[];
  visualConcept: string | null;
  actionStatus: string | null;
  reason: string | null;
}

export function AgentReasoning() {
  const [d, setD] = useState<Detail | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const r = await fetch('/api/gtm/run/latest', { cache: 'no-store' });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setD(await r.json());
      setErr(null);
    } catch (e: any) {
      setErr(String(e?.message || e));
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 15_000);
    return () => clearInterval(t);
  }, [load]);

  if (err) return <Msg tone="#FC5457">Could not read the run journal: {err}</Msg>;
  if (d && (d as any).inFlight) {
    // A cycle takes 2-4 minutes. Saying so beats an empty panel or an error.
    return (
      <Msg tone={ACCENT}>
        {d.runId} is still running — A02 and A03 record their decisions as they
        finish. This refreshes every 15s.
      </Msg>
    );
  }
  if (!d) return <Msg tone={DIM}>Loading…</Msg>;

  return (
    <div>
      <header style={{ marginBottom: 18 }}>
        <h2 style={{ margin: 0, fontSize: 19, color: '#EDEDED', fontWeight: 600 }}>
          Agent Decisions
        </h2>
        <p style={{ margin: '6px 0 0', fontSize: 13, color: DIM, maxWidth: 760 }}>
          What A02, A03 and A07 actually decided in {d.runId}, and what they turned
          down. There is no debate stage in this system — these are sequential
          judgements, shown as they were recorded.
        </p>
      </header>

      {/* A02 */}
      <Section n="A02" title="Opportunity Selector" model="gemini-3.8-flash">
        {d.selection ? (
          <>
            <Field label="chose">{d.selection.chosen}</Field>
            {d.signalSourceType && (
              <div style={{ fontFamily: MONO, fontSize: 11, color: ACCENT, marginBottom: 8 }}>
                {d.signalSourceType}
                {d.signalObservedAt ? ` · observed ${d.signalObservedAt.slice(0, 19)}` : ''}
                {` · from ${d.selection.candidates} candidates`}
              </div>
            )}
            <Field label="why">{d.selection.why}</Field>

            {d.selection.rejected.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <Label>turned down ({d.selection.rejected.length})</Label>
                {d.selection.rejected.map((r, i) => (
                  <div
                    key={i}
                    style={{
                      borderLeft: '2px solid #333',
                      paddingLeft: 10,
                      margin: '8px 0',
                    }}
                  >
                    <div style={{ fontSize: 12.5, color: '#9A9A9A' }}>{r.headline}</div>
                    <div style={{ fontSize: 12, color: DIM, marginTop: 2 }}>{r.why}</div>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <Muted>
            No selection recorded — this run was given a founder directive, so A02
            deferred to the instruction rather than choosing.
          </Muted>
        )}
      </Section>

      {/* A03 */}
      <Section n="A03" title="GTM Strategist" model="gemini-3.8-flash">
        {d.actionStatus && d.actionStatus !== 'ACTION' ? (
          <>
            <Field label="verdict">{d.actionStatus}</Field>
            <Muted>{d.reason || 'No rationale recorded.'}</Muted>
          </>
        ) : (
          <>
            {d.problem && <Field label="problem">{d.problem}</Field>}
            {d.opportunity && <Field label="opportunity">{d.opportunity}</Field>}
            <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', margin: '10px 0' }}>
              {d.audience && <Chip label="audience" value={d.audience} />}
              {d.machine && <Chip label="machine" value={d.machine} />}
            </div>
            {d.pillar && <Field label="pillar">{d.pillar}</Field>}
            {d.strategyReasoning.length > 0 && (
              <div style={{ marginTop: 10 }}>
                <Label>reasoning</Label>
                <ol style={{ margin: '6px 0 0', paddingLeft: 18 }}>
                  {d.strategyReasoning.map((r, i) => (
                    <li key={i} style={{ fontSize: 12.5, color: '#9A9A9A', marginBottom: 4 }}>
                      {r}
                    </li>
                  ))}
                </ol>
              </div>
            )}
            {d.proofClaims.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <Label>proof claims it will stand behind ({d.proofClaims.length})</Label>
                {d.proofClaims.map((c, i) => (
                  <div
                    key={i}
                    style={{
                      fontFamily: MONO,
                      fontSize: 11.5,
                      color: '#9A9A9A',
                      borderLeft: `2px solid ${ACCENT}44`,
                      paddingLeft: 10,
                      margin: '6px 0',
                    }}
                  >
                    {c}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </Section>

      {/* A07 */}
      <Section n="A07" title="Creative Director" model="gemini-3.8-flash">
        {d.visualConcept ? (
          <Field label="visual concept">{d.visualConcept}</Field>
        ) : (
          <Muted>No art direction recorded for this run.</Muted>
        )}
      </Section>
    </div>
  );
}

function Section({
  n,
  title,
  model,
  children,
}: {
  n: string;
  title: string;
  model: string;
  children: React.ReactNode;
}) {
  return (
    <section
      style={{
        border: '1px solid #1E1E22',
        borderRadius: 8,
        padding: '14px 16px',
        marginBottom: 14,
        background: '#0D0D0F',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 10 }}>
        <span style={{ fontFamily: MONO, fontSize: 11, color: DIM }}>{n}</span>
        <h3 style={{ margin: 0, fontSize: 14.5, color: '#EDEDED', fontWeight: 600 }}>{title}</h3>
        <span style={{ fontFamily: MONO, fontSize: 10.5, color: ACCENT }}>{model}</span>
      </div>
      {children}
    </section>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontFamily: MONO,
        fontSize: 10,
        color: DIM,
        textTransform: 'uppercase',
        letterSpacing: 0.6,
      }}
    >
      {children}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <Label>{label}</Label>
      <div style={{ fontSize: 13, color: '#D4D4D4', marginTop: 3, lineHeight: 1.55 }}>
        {children}
      </div>
    </div>
  );
}

function Chip({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <Label>{label}</Label>
      <div style={{ fontFamily: MONO, fontSize: 12, color: '#D4D4D4' }}>{value}</div>
    </div>
  );
}

function Muted({ children }: { children: React.ReactNode }) {
  return <div style={{ fontSize: 12.5, color: DIM, lineHeight: 1.5 }}>{children}</div>;
}

function Msg({ tone, children }: { tone: string; children: React.ReactNode }) {
  return <div style={{ color: tone, fontFamily: MONO, fontSize: 13 }}>{children}</div>;
}
