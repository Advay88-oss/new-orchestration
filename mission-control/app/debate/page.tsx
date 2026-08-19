'use client';

import { useEffect, useRef, useState } from 'react';

type Ev = { ts: number; agent: string; stage: string; text: string; tenant?: string };

const COLORS: Record<string, string> = {
  system: '#6b7280',
  conductor: '#f59e0b',
  'trend-scout': '#10b981',
  'strategist-capital-efficiency': '#8b5cf6',
  'strategist-risk-relief': '#ec4899',
  'strategist-agentic-credit': '#3b82f6',
  'strategist-self-custody': '#eab308',
  'strategist-store-of-value': '#f97316',
  'strategist-use-your-gold': '#c4699a',
  'editorial-judge': '#ef4444',
  'visual-creator': '#14b8a6',
};

function colorFor(agent: string): string {
  return COLORS[agent] ?? '#8b5cf6';
}

// The orchestrator logs each step as "Label:\n<payload>". Make it readable and,
// for JSON drafts, surface the hook + body instead of raw JSON.
function render(text: string): { label: string; body: string } {
  const idx = text.indexOf(':');
  let label = '';
  let rest = text;
  if (idx > 0 && idx < 40) {
    label = text.slice(0, idx).trim();
    rest = text.slice(idx + 1).trim();
  }
  const brace = rest.indexOf('{');
  if (brace >= 0) {
    try {
      const j = JSON.parse(rest.slice(brace));
      const hook = j.hook || j.final_hook || j.winner?.final_hook || '';
      const body = j.body || j.final_body || j.winner?.final_body || '';
      const topic = j.selected_topic ? `topic: ${j.selected_topic}` : '';
      const verdict = j.verdict ? `verdict: ${j.verdict}` : '';
      const composed = [hook && `“${hook}”`, body, topic, verdict].filter(Boolean).join('  ');
      if (composed) return { label, body: composed };
    } catch {
      /* fall through to raw */
    }
  }
  return { label, body: rest };
}

export default function DebatePage() {
  const [events, setEvents] = useState<Ev[]>([]);
  const [live, setLive] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let stop = false;
    async function poll() {
      try {
        const r = await fetch('/api/live-debate', { cache: 'no-store' });
        const d = await r.json();
        if (!stop && Array.isArray(d.events)) {
          setEvents(d.events);
          setLive(Date.now() / 1000 - (d.mtime ? d.mtime / 1000 : 0) < 20);
        }
      } catch {
        /* ignore */
      }
    }
    poll();
    const id = setInterval(poll, 2000);
    return () => {
      stop = true;
      clearInterval(id);
    };
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events.length]);

  const tenant = events.find((e) => e.tenant)?.tenant ?? '';

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg,#0f0b16)', color: 'var(--fg,#ece8f2)', padding: 24, fontFamily: 'ui-sans-serif,system-ui,Segoe UI,Roboto' }}>
      <div style={{ maxWidth: 780, margin: '0 auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
          <h1 style={{ fontSize: 22, margin: 0 }}>Live Agent Debate</h1>
          <span style={{ fontSize: 12, fontWeight: 700, padding: '3px 9px', borderRadius: 20, background: live ? '#10b981' : '#6b7280', color: '#fff' }}>
            {live ? '● LIVE' : 'idle'}
          </span>
          {tenant && <span style={{ fontSize: 13, opacity: 0.7 }}>{tenant}</span>}
        </div>
        <p style={{ fontSize: 12.5, opacity: 0.6, margin: '0 0 20px' }}>
          Streaming the real pipeline debate step-by-step (polls every 2s). Run the pipeline and watch it fill in.
        </p>

        {events.length === 0 && (
          <div style={{ opacity: 0.55, fontSize: 14, padding: '40px 0', textAlign: 'center' }}>
            No debate yet. Start a run — events appear here live.
          </div>
        )}

        {events.map((e, i) => {
          const c = colorFor(e.agent);
          const { label, body } = render(e.text);
          if (e.agent === 'system') {
            return (
              <div key={i} style={{ textAlign: 'center', fontSize: 12, opacity: 0.6, margin: '14px 0' }}>
                — {e.text} —
              </div>
            );
          }
          return (
            <div key={i} style={{ borderLeft: `3px solid ${c}`, padding: '6px 0 6px 14px', margin: '0 0 14px' }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                <span style={{ fontWeight: 700, fontSize: 13.5, color: c }}>{e.agent}</span>
                {label && <span style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '.04em', opacity: 0.55 }}>{label}</span>}
              </div>
              <div style={{ fontSize: 14, marginTop: 3, lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{body}</div>
            </div>
          );
        })}
        <div ref={endRef} />
      </div>
    </div>
  );
}
