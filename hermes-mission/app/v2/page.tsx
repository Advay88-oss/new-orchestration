'use client';

/**
 * Pipeline truth view.
 *
 * The old dashboard's /api/agents/status returned 133 lines of hardcoded JSON —
 * all thirteen agents permanently "connected" with invented telemetry, in a file
 * that imported `fs` and never used it. This page renders only what the run
 * journal actually recorded, and it is explicit about the one number that
 * matters: how many stages declared as AGENT genuinely called a model.
 */

import { useCallback, useEffect, useState } from 'react';

type Kind = 'AGENT' | 'STAGE';

interface StageView {
  stage: string;
  kind: Kind | null;
  purpose: string;
  state: string;
  status: string | null;
  durationS: number | null;
  model: string | null;
  promptVersion: string | null;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  costKnown: boolean;
  attempts: number;
  toolCalls: string[];
  degradedReason: string | null;
  error: string | null;
  agentDidCallModel: boolean | null;
}

interface RunView {
  runId: string;
  directive: string;
  status: string;
  durationS: number | null;
  stages: StageView[];
  degraded: string[];
  failed: string[];
  costUsd: number;
  costComplete: boolean;
  unpricedModels: string[];
  inputTokens: number;
  outputTokens: number;
  modelCalls: number;
  agentsDeclared: number;
  agentsThatCalledModel: number;
  artifacts: { name: string; path: string; bytes: number }[];
}

const TONE: Record<string, string> = {
  succeeded: '#10b981',
  degraded: '#f59e0b',
  failed: '#ef4444',
  running: '#38bdf8',
  not_reached: '#4b5563',
};

function Dot({ state }: { state: string }) {
  return (
    <span
      style={{
        width: 8, height: 8, borderRadius: 8, display: 'inline-block',
        background: TONE[state] ?? '#4b5563', flexShrink: 0,
      }}
    />
  );
}

export default function V2Page() {
  const [runs, setRuns] = useState<RunView[]>([]);
  const [sel, setSel] = useState<string | null>(null);
  const [health, setHealth] = useState<any>(null);
  const [directive, setDirective] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [r, h] = await Promise.all([
        fetch('/api/v2/runs?limit=25', { cache: 'no-store' }),
        fetch('/api/v2/health', { cache: 'no-store' }),
      ]);
      if (!r.ok) throw new Error(`runs: HTTP ${r.status}`);
      const rj = await r.json();
      setRuns(rj.runs ?? []);
      setHealth(await h.json());
      setErr(null);
      setSel((cur) => cur ?? rj.runs?.[0]?.runId ?? null);
    } catch (e: any) {
      // No fixture fallback: if the backend cannot be read, say so.
      setErr(String(e?.message ?? e));
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [load]);

  const run = runs.find((r) => r.runId === sel) ?? null;

  async function trigger() {
    setMsg(null);
    const res = await fetch('/api/v2/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ directive }),
    });
    const j = await res.json();
    setMsg(j.note ?? 'queued');
    setDirective('');
    load();
  }

  const workerAlive = health?.worker?.alive;

  return (
    <main style={{ padding: '28px 32px 80px', maxWidth: 1180, margin: '0 auto', color: '#e5e7eb' }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Pipeline — what actually ran</h1>
      <p style={{ fontSize: 13, color: '#9ca3af', marginTop: 6, maxWidth: 760 }}>
        Rendered from the append-only run journal. A stage is only shown as an agent if the
        manifest declares it one, and only shown as having reasoned if it recorded a real model
        call.
      </p>

      {err && (
        <div style={{ marginTop: 16, padding: 12, borderRadius: 8, background: '#7f1d1d', fontSize: 13 }}>
          Backend unreachable: {err}. Nothing is being shown from cache — this panel has no fixtures.
        </div>
      )}

      {/* health */}
      {health && (
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 18 }}>
          <Pill label="stages" value={`${health.stages}`} />
          <Pill label="declared agents" value={`${health.agents}`} />
          <Pill
            label="worker"
            value={workerAlive ? `alive (${health.worker.state})` : `NOT RUNNING`}
            tone={workerAlive ? '#10b981' : '#ef4444'}
          />
          <Pill label="queue pending" value={`${health.queue?.pending ?? 0}`} />
          <Pill label="queue dead" value={`${health.queue?.dead ?? 0}`}
                tone={(health.queue?.dead ?? 0) > 0 ? '#f59e0b' : undefined} />
          <Pill label="runs" value={`${health.runs}`} />
        </div>
      )}

      {/* trigger */}
      <div style={{ marginTop: 20, display: 'flex', gap: 8 }}>
        <input
          value={directive}
          onChange={(e) => setDirective(e.target.value)}
          placeholder="Directive for the next run…"
          style={{
            flex: 1, padding: '10px 12px', borderRadius: 8, border: '1px solid #374151',
            background: '#0b0f17', color: '#e5e7eb', fontSize: 13,
          }}
        />
        <button
          onClick={trigger}
          style={{
            padding: '10px 18px', borderRadius: 8, border: 'none', cursor: 'pointer',
            background: '#a387ff', color: '#0b0f17', fontWeight: 600, fontSize: 13,
          }}
        >
          Queue run
        </button>
      </div>
      {msg && <p style={{ fontSize: 12, color: workerAlive ? '#9ca3af' : '#f59e0b', marginTop: 8 }}>{msg}</p>}

      {/* runs */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 26 }}>
        {runs.map((r) => (
          <button
            key={r.runId}
            onClick={() => setSel(r.runId)}
            style={{
              padding: '7px 11px', borderRadius: 7, fontSize: 12, cursor: 'pointer',
              border: `1px solid ${r.runId === sel ? '#a387ff' : '#374151'}`,
              background: r.runId === sel ? '#1e1b32' : '#0b0f17',
              color: '#e5e7eb', display: 'flex', alignItems: 'center', gap: 7,
            }}
          >
            <Dot state={r.status === 'ok' ? 'succeeded' : r.status} />
            {r.runId.replace('RUN-', '')}
          </button>
        ))}
        {runs.length === 0 && !err && (
          <p style={{ fontSize: 13, color: '#9ca3af' }}>No runs yet. Queue one above.</p>
        )}
      </div>

      {run && (
        <>
          <div style={{ marginTop: 24, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <Pill label="status" value={run.status}
                  tone={run.status === 'ok' ? '#10b981' : run.status === 'degraded' ? '#f59e0b' : '#ef4444'} />
            <Pill
              label="agents that called a model"
              value={`${run.agentsThatCalledModel} of ${run.agentsDeclared}`}
              tone={run.agentsThatCalledModel === run.agentsDeclared ? '#10b981' : '#f59e0b'}
            />
            <Pill label="model calls" value={`${run.modelCalls}`} />
            <Pill label="tokens" value={`${run.inputTokens}/${run.outputTokens}`} />
            <Pill
              label="cost"
              value={run.costComplete ? `$${run.costUsd}` : `$${run.costUsd} + unpriced`}
              tone={run.costComplete ? undefined : '#f59e0b'}
            />
            <Pill label="duration" value={run.durationS ? `${run.durationS}s` : '—'} />
          </div>

          {!run.costComplete && (
            <p style={{ fontSize: 12, color: '#f59e0b', marginTop: 8 }}>
              No published rate held for {run.unpricedModels.join(', ')} — the cost above is
              incomplete rather than zero.
            </p>
          )}

          {run.directive && (
            <p style={{ fontSize: 13, color: '#9ca3af', marginTop: 12 }}>
              Directive: <span style={{ color: '#e5e7eb' }}>{run.directive}</span>
            </p>
          )}

          <table style={{ width: '100%', marginTop: 18, borderCollapse: 'collapse', fontSize: 12.5 }}>
            <thead>
              <tr style={{ color: '#6b7280', textAlign: 'left' }}>
                <th style={th}>#</th>
                <th style={th}>stage</th>
                <th style={th}>kind</th>
                <th style={th}>state</th>
                <th style={th}>model</th>
                <th style={th}>prompt</th>
                <th style={th}>tokens</th>
                <th style={th}>time</th>
              </tr>
            </thead>
            <tbody>
              {run.stages.map((s, i) => (
                <tr key={s.stage} style={{ borderTop: '1px solid #1f2937' }}>
                  <td style={{ ...td, color: '#6b7280' }}>{i + 1}</td>
                  <td style={td}>
                    <div style={{ fontWeight: 600 }}>{s.stage}</div>
                    <div style={{ color: '#6b7280', fontSize: 11.5 }}>{s.purpose}</div>
                    {s.degradedReason && (
                      <div style={{ color: '#f59e0b', fontSize: 11.5, marginTop: 3 }}>
                        degraded: {s.degradedReason}
                      </div>
                    )}
                    {s.error && (
                      <div style={{ color: '#ef4444', fontSize: 11.5, marginTop: 3 }}>{s.error}</div>
                    )}
                  </td>
                  <td style={td}>
                    <span style={{
                      fontSize: 10.5, padding: '2px 6px', borderRadius: 4,
                      background: s.kind === 'AGENT' ? '#2e1065' : '#1f2937',
                      color: s.kind === 'AGENT' ? '#c4b5fd' : '#9ca3af',
                    }}>
                      {s.kind}
                    </span>
                    {s.agentDidCallModel === false && (
                      <div style={{ color: '#ef4444', fontSize: 10.5, marginTop: 3 }}>
                        no model call
                      </div>
                    )}
                  </td>
                  <td style={td}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Dot state={s.state} />
                      {s.state}
                    </span>
                  </td>
                  <td style={{ ...td, fontFamily: 'monospace', fontSize: 11.5 }}>{s.model ?? '—'}</td>
                  <td style={{ ...td, fontFamily: 'monospace', fontSize: 11 }}>{s.promptVersion ?? '—'}</td>
                  <td style={{ ...td, fontFamily: 'monospace', fontSize: 11.5 }}>
                    {s.inputTokens || s.outputTokens ? `${s.inputTokens}/${s.outputTokens}` : '—'}
                  </td>
                  <td style={{ ...td, color: '#9ca3af' }}>{s.durationS != null ? `${s.durationS}s` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {run.artifacts.some((a) => a.name.endsWith('.png')) && (
            <div style={{ marginTop: 24 }}>
              <div style={{ fontSize: 11, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '.06em' }}>
                Rendered asset
              </div>
              {run.artifacts
                .filter((a) => a.name.endsWith('.png'))
                .slice(-1)
                .map((a) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    key={a.path}
                    src={`/api/v2/artifact/${run.runId}?path=${encodeURIComponent(a.path)}`}
                    alt="rendered asset"
                    style={{ marginTop: 10, width: '100%', maxWidth: 520, borderRadius: 10, border: '1px solid #1f2937' }}
                  />
                ))}
            </div>
          )}
        </>
      )}
    </main>
  );
}

const th: React.CSSProperties = { padding: '8px 10px', fontWeight: 500, fontSize: 11 };
const td: React.CSSProperties = { padding: '10px', verticalAlign: 'top' };

function Pill({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div style={{
      padding: '8px 12px', borderRadius: 8, border: '1px solid #1f2937', background: '#0b0f17',
    }}>
      <div style={{ fontSize: 9.5, color: '#6b7280', textTransform: 'uppercase', letterSpacing: '.06em' }}>
        {label}
      </div>
      <div style={{ fontSize: 13, fontWeight: 600, marginTop: 2, color: tone ?? '#e5e7eb' }}>{value}</div>
    </div>
  );
}
