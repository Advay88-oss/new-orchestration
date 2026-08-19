'use client';

import { useEffect, useMemo, useState, type CSSProperties } from 'react';
import { Bar, Metric, NoData, Pill, Section } from '@/components/primitives';

// ---------------------------------------------------------------------------
// Transparency-first Mission Control. Every view answers "where did this come
// from and why", drilling: Trend → Content → Source → Evidence → Agent
// reasoning → Debate → Decision → Recommendation. Nothing is a black box.
// ---------------------------------------------------------------------------

const NAV = [
  { id: 'activity', label: 'Live activity' },
  { id: 'scout', label: 'Trend scout' },
  { id: 'debate', label: 'Agent debate' },
  { id: 'trace', label: 'Traceability' },
  { id: 'agents', label: 'Agents' },
  { id: 'cost', label: 'Cost' },
] as const;
type NavId = (typeof NAV)[number]['id'];

const AGENT_COLOR: Record<string, string> = {
  system: 'var(--ink-4)',
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
const colorFor = (a: string) => AGENT_COLOR[a] ?? '#8b5cf6';

const PLATFORM = {
  reddit: { label: 'Reddit', color: '#ff4500' },
  twitter: { label: 'Twitter/X', color: '#1d9bf0' },
  x: { label: 'Twitter/X', color: '#1d9bf0' },
  rss: { label: 'News/RSS', color: '#a855f7' },
  web: { label: 'Web', color: '#64748b' },
} as const;
const platformOf = (c: string) => (PLATFORM as any)[c] ?? { label: c || 'Web', color: '#64748b' };

type Ev = { ts: number; agent: string; stage?: string; text: string; tenant?: string };

// A feed event's real meaning, parsed from the "Label: <payload>" the pipeline logs.
function parseEvent(e: Ev) {
  const text = e.text || '';
  const idx = text.indexOf(':');
  let label = '';
  let body = text;
  if (idx > 0 && idx < 40) {
    label = text.slice(0, idx).trim();
    body = text.slice(idx + 1).trim();
  }
  let json: any = null;
  const b = body.indexOf('{');
  if (b >= 0) {
    try {
      json = JSON.parse(body.slice(b));
    } catch {
      /* not json */
    }
  }
  let kind: 'source' | 'analysis' | 'proposal' | 'challenge' | 'ruling' | 'visual' | 'system' | 'step' = 'step';
  let verb = 'working';
  if (e.agent === 'system') {
    kind = 'system';
    verb = 'run event';
  } else if (/Trendjack Decision/i.test(label)) {
    kind = 'source';
    verb = 'chose the trend';
  } else if (/Synthesis/i.test(label)) {
    kind = 'analysis';
    verb = 'synthesized the angle';
  } else if (/Initial Draft/i.test(label)) {
    kind = 'proposal';
    verb = 'proposed a draft';
  } else if (/Debate Rebuttal/i.test(label)) {
    kind = 'challenge';
    verb = 'challenged the others';
  } else if (/Ruling Decision/i.test(label)) {
    kind = 'ruling';
    verb = 'ruled the winner';
  } else if (e.agent === 'visual-creator') {
    kind = 'visual';
    verb = 'designed the card';
  }
  const hook = json?.hook || json?.final_hook || json?.winner?.final_hook || '';
  const post = json?.post || json?.body || json?.final_body || json?.winner?.final_body || '';
  return { label, body, json, kind, verb, hook, post };
}

function relTime(ts: number) {
  const s = Math.max(0, Math.floor(Date.now() / 1000 - ts));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

export default function Page() {
  const [nav, setNav] = useState<NavId>('activity');
  const [events, setEvents] = useState<Ev[]>([]);
  const [live, setLive] = useState(false);
  const [scout, setScout] = useState<any>(null);
  const [spend, setSpend] = useState<{ spent_usd: number; cap_usd: number } | null>(null);
  const [calls, setCalls] = useState<any[]>([]);
  const [winner, setWinner] = useState<any>(null);
  const [runs, setRuns] = useState<any[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  useEffect(() => {
    let stop = false;
    async function poll() {
      try {
        const [dRes, sRes, spRes, cRes, mRes, rRes] = await Promise.all([
          fetch('/api/live-debate', { cache: 'no-store' }).then((r) => r.json()).catch(() => ({ events: [], mtime: 0 })),
          fetch('/api/scout', { cache: 'no-store' }).then((r) => r.json()).catch(() => null),
          fetch('/api/spend', { cache: 'no-store' }).then((r) => r.json()).catch(() => null),
          fetch('/api/calls', { cache: 'no-store' }).then((r) => r.json()).catch(() => []),
          fetch('/api/messages', { cache: 'no-store' }).then((r) => r.json()).catch(() => []),
          fetch('/api/runs', { cache: 'no-store' }).then((r) => r.json()).catch(() => ({ runs: [] })),
        ]);
        if (stop) return;
        if (Array.isArray(rRes.runs)) setRuns(rRes.runs);
        if (Array.isArray(dRes.events)) {
          setEvents(dRes.events);
          setLive(Date.now() - (dRes.mtime ?? 0) < 25000);
        }
        if (sRes) setScout(sRes);
        if (spRes && typeof spRes.spent_usd === 'number') setSpend(spRes);
        if (Array.isArray(cRes)) setCalls(cRes);
        // Latest shipped/awaiting draft = the recommendation.
        if (Array.isArray(mRes) && mRes.length) {
          const sorted = [...mRes].sort((a, b) => (a.created_at ?? 0) - (b.created_at ?? 0));
          const last = sorted[sorted.length - 1];
          try {
            setWinner(JSON.parse(last.content));
          } catch {
            setWinner(last);
          }
        }
      } catch {
        /* ignore */
      }
    }
    poll();
    const id = setInterval(poll, 3000);
    return () => {
      stop = true;
      clearInterval(id);
    };
  }, []);

  const parsed = useMemo(() => events.map((e) => ({ e, p: parseEvent(e) })), [events]);
  const tenant = events.find((e) => e.tenant)?.tenant ?? scout?.tenant ?? '';

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside
        style={{
          width: 220,
          flex: 'none',
          borderRight: '1px solid var(--line)',
          padding: '20px 16px',
          position: 'sticky',
          top: 0,
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          gap: 18,
        }}
      >
        <div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>Mission Control</div>
          <div style={{ fontSize: 10, color: 'var(--ink-4)', marginTop: 2 }}>
            transparent AI marketing team {tenant ? `· ${tenant}` : ''}
          </div>
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {NAV.map((n) => (
            <button
              key={n.id}
              onClick={() => {
                setNav(n.id);
                setSelectedRunId(null);
              }}
              style={{
                textAlign: 'left',
                padding: '7px 10px',
                borderRadius: 'var(--r-xs)',
                fontSize: 12,
                fontWeight: nav === n.id && !selectedRunId ? 600 : 400,
                background: nav === n.id && !selectedRunId ? 'var(--accent-tint)' : 'transparent',
                color: nav === n.id && !selectedRunId ? 'var(--accent-deep)' : 'var(--ink-2)',
              }}
            >
              {n.label}
            </button>
          ))}
        </nav>

        <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          <div style={{ fontSize: 10, color: 'var(--ink-4)', margin: '4px 0 6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Run history ({runs.length})
          </div>
          <div style={{ overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 4, paddingRight: 2 }}>
            {runs.length === 0 && <div style={{ fontSize: 10, color: 'var(--ink-4)' }}>No runs recorded yet.</div>}
            {runs.map((r) => {
              const running = r.status === 'running';
              const sel = r.run_id === selectedRunId;
              const tone = running ? '#10b981' : r.status === 'completed' ? 'var(--accent)' : r.status === 'blocked' || r.status === 'rejected' ? 'var(--danger)' : 'var(--ink-4)';
              return (
                <button
                  key={r.run_id}
                  onClick={() => setSelectedRunId(r.run_id)}
                  style={{
                    textAlign: 'left',
                    padding: '6px 8px',
                    borderRadius: 'var(--r-xs)',
                    border: `1px solid ${sel ? 'var(--accent)' : 'var(--line)'}`,
                    background: sel ? 'var(--accent-tint)' : 'transparent',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ width: 6, height: 6, borderRadius: 6, background: tone, flex: 'none' }} />
                    <span style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--ink-1)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {r.tenant || r.pipeline} {running && '· live'}
                    </span>
                  </div>
                  <span style={{ fontSize: 9, color: 'var(--ink-4)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {new Date((r.started ?? 0) * 1000).toLocaleString()} · {r.status}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <div style={{ fontSize: 10, color: 'var(--ink-4)', marginBottom: 4 }}>Feed</div>
            <Pill tone={live ? 'accent' : 'muted'}>{live ? '● live' : 'idle'}</Pill>
          </div>
          {spend && (
            <div>
              <div style={{ fontSize: 10, color: 'var(--ink-4)', marginBottom: 4 }}>Spend / cap</div>
              <div style={{ fontSize: 13, fontWeight: 600 }}>
                ${spend.spent_usd.toFixed(4)}{' '}
                <span style={{ color: 'var(--ink-4)', fontWeight: 400 }}>/ ${spend.cap_usd.toFixed(2)}</span>
              </div>
              <div style={{ marginTop: 6 }}>
                <Bar
                  segments={[
                    { value: Math.min(100, (spend.spent_usd / spend.cap_usd) * 100), colour: (spend.spent_usd / spend.cap_usd) > 0.8 ? 'var(--danger)' : 'var(--accent)' },
                    { value: Math.max(0, 100 - (spend.spent_usd / spend.cap_usd) * 100), colour: 'var(--bg-raised)' },
                  ]}
                  height={6}
                />
              </div>
              <p style={{ fontSize: 9, color: 'var(--ink-4)', margin: '6px 0 0', lineHeight: 1.5 }}>
                Hard cap. Every Gemini call is metered through the proxy.
              </p>
            </div>
          )}
        </div>
      </aside>

      <main style={{ flex: 1, minWidth: 0, padding: '24px 28px 60px', maxWidth: 1180 }}>
        {selectedRunId ? (
          <RunLifecycle runId={selectedRunId} onBack={() => setSelectedRunId(null)} />
        ) : (
          <>
            <header style={{ marginBottom: 20 }}>
              <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>{NAV.find((n) => n.id === nav)!.label}</h1>
              <div style={{ fontSize: 11, color: 'var(--ink-3)', marginTop: 4 }}>
                Nothing hidden — every recommendation traces back to a source, evidence, and the agents that argued it.
              </div>
            </header>

            {nav === 'activity' && <ActivityView parsed={parsed} live={live} />}
            {nav === 'scout' && <ScoutView scout={scout} winner={winner} />}
            {nav === 'debate' && <DebateView parsed={parsed} />}
            {nav === 'trace' && <TraceView parsed={parsed} scout={scout} winner={winner} />}
            {nav === 'agents' && <AgentsView parsed={parsed} />}
            {nav === 'cost' && <CostView spend={spend} calls={calls} parsed={parsed} />}
          </>
        )}
      </main>
    </div>
  );
}

// --------------------------------------------------------------- Live activity
function ActivityView({ parsed, live }: { parsed: any[]; live: boolean }) {
  const feed = [...parsed].reverse();
  return (
    <Section
      title="What the team is doing right now"
      right={<Pill tone={live ? 'accent' : 'muted'}>{live ? '● live' : 'idle'}</Pill>}
      note="Real-time stream of every agent action — researching, analysing, proposing, challenging, ruling, generating. Newest first, refreshes every 3s."
    >
      {feed.length === 0 && <p style={{ fontSize: 12, color: 'var(--ink-3)' }}>No activity yet. Kick a run and it streams here.</p>}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {feed.map(({ e, p }, i) => {
          if (p.kind === 'system') {
            return (
              <div key={i} style={{ textAlign: 'center', fontSize: 10, color: 'var(--ink-4)', margin: '4px 0' }}>
                — {e.text} —
              </div>
            );
          }
          const c = colorFor(e.agent);
          const snippet = p.hook || p.post || p.body;
          return (
            <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'baseline', padding: '6px 0', borderBottom: '1px solid var(--line)' }}>
              <span style={{ fontSize: 9, color: 'var(--ink-4)', width: 58, flex: 'none' }}>{relTime(e.ts)}</span>
              <span style={{ width: 8, height: 8, borderRadius: 8, background: c, flex: 'none', marginTop: 5 }} />
              <div style={{ minWidth: 0 }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: c }}>{e.agent}</span>{' '}
                <span style={{ fontSize: 12, color: 'var(--ink-3)' }}>{p.verb}</span>
                <div style={{ fontSize: 11.5, color: 'var(--ink-2)', marginTop: 2, lineHeight: 1.45 }}>{String(snippet).slice(0, 200)}</div>
              </div>
            </div>
          );
        })}
      </div>
    </Section>
  );
}

// ----------------------------------------------------------------- Trend scout
function ScoutView({ scout, winner }: { scout: any; winner: any }) {
  const [platform, setPlatform] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'relevance' | 'engagement'>('relevance');
  if (!scout || !scout.ok) {
    return <Section title="Trend scout"><p style={{ fontSize: 12, color: 'var(--ink-3)' }}>No scout dump yet. Run the scout to populate discovered content.</p></Section>;
  }
  const selectedTrend = String(winner?.trend_id ?? '').toLowerCase();
  let items = [...(scout.items ?? [])];
  if (platform !== 'all') items = items.filter((i) => (i.channel === platform || (platform === 'twitter' && i.channel === 'x')));
  items.sort((a, b) => (sortBy === 'relevance' ? b.relevance - a.relevance : b.engagement - a.engagement));

  const platforms: string[] = scout.monitored?.platforms ?? [];
  return (
    <>
      <Section title="What the scout is monitoring" note={`Bundle: ${scout.bundle || scout.tenant} · gathered ${scout.gathered_at || '—'} · source file ${scout.file}`}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20 }}>
          <div>
            <div style={{ fontSize: 10, color: 'var(--ink-4)', marginBottom: 4 }}>Platforms swept</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {platforms.map((p) => (
                <span key={p} style={{ fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 6, background: platformOf(p).color + '22', color: platformOf(p).color }}>
                  {platformOf(p).label}
                </span>
              ))}
            </div>
          </div>
          <ChipList label={`Keywords (${(scout.monitored?.keywords ?? []).length})`} items={scout.monitored?.keywords ?? []} />
          <ChipList label={`Subreddits (${(scout.monitored?.subreddits ?? []).length})`} items={(scout.monitored?.subreddits ?? []).map((s: string) => 'r/' + s)} />
        </div>
      </Section>

      <Section
        title={`Discovered content (${scout.items?.length ?? 0})`}
        note="Every item the scout surfaced, with its real source, platform, engagement and a relevance score. Filter and sort to inspect."
        right={
          <div style={{ display: 'flex', gap: 6 }}>
            {['all', 'reddit', 'twitter'].map((p) => (
              <button key={p} onClick={() => setPlatform(p)} style={filterBtn(platform === p)}>{p}</button>
            ))}
            <button onClick={() => setSortBy(sortBy === 'relevance' ? 'engagement' : 'relevance')} style={filterBtn(false)}>
              sort: {sortBy}
            </button>
          </div>
        }
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 12 }}>
          {items.map((it, i) => {
            const pf = platformOf(it.channel);
            const isSelected = selectedTrend && String(it.title).toLowerCase().includes(selectedTrend.split('-')[0]);
            return (
              <div key={i} style={{ border: `1px solid ${isSelected ? 'var(--accent)' : 'var(--line)'}`, borderRadius: 'var(--r-md)', padding: '11px 13px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 10, fontWeight: 700, padding: '1px 7px', borderRadius: 5, background: pf.color + '22', color: pf.color }}>{pf.label}</span>
                  <span style={{ fontSize: 10, color: 'var(--ink-4)' }}>{it.source}</span>
                  {isSelected && <Pill tone="accent">detected trend</Pill>}
                </div>
                <div style={{ fontSize: 12.5, color: 'var(--ink-1)', lineHeight: 1.4 }}>{String(it.title).slice(0, 160)}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 'auto' }}>
                  <span style={{ fontSize: 10, color: 'var(--ink-3)' }}>⚡ {it.engagement} engagement</span>
                  <span style={{ fontSize: 10, color: 'var(--ink-4)' }}>kw: {it.keyword}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ flex: 1 }}>
                    <Bar segments={[{ value: it.relevance, colour: 'var(--accent)' }, { value: 100 - it.relevance, colour: 'var(--bg-raised)' }]} height={5} />
                  </div>
                  <span style={{ fontSize: 9, color: 'var(--ink-4)', width: 62, textAlign: 'right' }}>rel {it.relevance}</span>
                </div>
                {it.url && (
                  <a href={it.url} target="_blank" rel="noreferrer" style={{ fontSize: 10, color: 'var(--accent)', wordBreak: 'break-all' }}>
                    {String(it.url).slice(0, 60)} ↗
                  </a>
                )}
              </div>
            );
          })}
        </div>
      </Section>
    </>
  );
}

function ChipList({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <div style={{ fontSize: 10, color: 'var(--ink-4)', marginBottom: 4 }}>{label}</div>
      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', maxWidth: 420 }}>
        {items.slice(0, 12).map((k, i) => (
          <span key={i} style={{ fontSize: 10, padding: '2px 7px', borderRadius: 5, background: 'var(--bg-raised)', color: 'var(--ink-2)' }}>{k}</span>
        ))}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ The debate
function DebateView({ parsed }: { parsed: any[] }) {
  const proposals = parsed.filter((x) => x.p.kind === 'proposal');
  const challenges = parsed.filter((x) => x.p.kind === 'challenge');
  const ruling = parsed.find((x) => x.p.kind === 'ruling');
  const anything = proposals.length || challenges.length || ruling;
  if (!anything) return <Section title="Agent debate"><p style={{ fontSize: 12, color: 'var(--ink-3)' }}>No debate yet — run the pipeline and the proposals, challenges and ruling appear here.</p></Section>;
  return (
    <>
      <Section title="1 · Proposals" note="Each strategist argues one arc and proposes a competing draft.">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {proposals.map(({ e, p }, i) => (
            <DebateCard
              key={i}
              agent={e.agent}
              tag="proposed"
              text={[p.hook && `“${p.hook}”`, p.post].filter(Boolean).join(' ') || p.body}
            />
          ))}
        </div>
      </Section>
      <Section title={`2 · Challenges (${challenges.length} cross-replies)`} note="Where strategists rebut each other. No challenges = parallel monologues, not a debate.">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {challenges.map(({ e, p }, i) => (
            <DebateCard key={i} agent={e.agent} tag="challenged" text={p.body} />
          ))}
        </div>
      </Section>
      <Section title="3 · Decision">
        {ruling ? (
          <DebateCard
            agent="editorial-judge"
            tag={`verdict: ${ruling.p.json?.verdict ?? 'ship'}`}
            text={`Winner: ${ruling.p.json?.winner?.arc ?? ruling.p.json?.winner_arc ?? ''} — “${ruling.p.hook}” ${ruling.p.post}`}
          />
        ) : (
          <NoData reason="not ruled yet" />
        )}
      </Section>
    </>
  );
}

function DebateCard({ agent, tag, text }: { agent: string; tag: string; text: string }) {
  const c = colorFor(agent);
  return (
    <div style={{ borderLeft: `3px solid ${c}`, padding: '4px 0 4px 12px' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: c }}>{agent}</span>
        <span style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--ink-4)' }}>{tag}</span>
      </div>
      <div style={{ fontSize: 12.5, color: 'var(--ink-1)', marginTop: 2, lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{String(text).slice(0, 600)}</div>
    </div>
  );
}

// ------------------------------------------------------------- Traceability
function TraceView({ parsed, scout, winner }: { parsed: any[]; scout: any; winner: any }) {
  const source = parsed.find((x) => x.p.kind === 'source');
  const analysis = parsed.find((x) => x.p.kind === 'analysis');
  const proposals = parsed.filter((x) => x.p.kind === 'proposal');
  const challenges = parsed.filter((x) => x.p.kind === 'challenge');
  const ruling = parsed.find((x) => x.p.kind === 'ruling');
  const topSource = scout?.items?.[0];

  const steps = [
    { n: 'Source', color: '#10b981', body: source ? source.p.body : topSource ? `${platformOf(topSource.channel).label} · ${topSource.source}: ${topSource.title}` : '—' },
    { n: 'Evidence', color: '#0ea5e9', body: analysis?.p.json ? `topic: ${analysis.p.json.selected_topic ?? ''} · competitor: ${analysis.p.json.competitor_referenced ?? analysis.p.json.competitor ?? ''}` : (topSource ? `${topSource.engagement} engagement · relevance ${topSource.relevance}` : '—') },
    { n: 'Agent analysis', color: '#8b5cf6', body: proposals.length ? `${proposals.length} strategists drafted competing angles: ${proposals.map((x: any) => x.e.agent.replace('strategist-', '')).join(', ')}` : '—' },
    { n: 'Agent debate', color: '#ec4899', body: challenges.length ? `${challenges.length} cross-replies — strategists challenged each other's drafts` : 'no challenges' },
    { n: 'Decision', color: '#ef4444', body: ruling ? `Judge verdict: ${ruling.p.json?.verdict ?? 'ship'} — winner arc ${ruling.p.json?.winner?.arc ?? ruling.p.json?.winner_arc ?? ''}` : '—' },
    { n: 'Recommendation', color: '#14b8a6', body: winner ? `“${winner.final_hook ?? winner.hook ?? ''}” ${winner.body ?? winner.final_body ?? ''}` : '—' },
  ];

  return (
    <Section title="Decision chain" note="Every recommendation traces end-to-end. Each step shows the real data that produced the next.">
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {steps.map((s, i) => (
          <div key={i} style={{ display: 'flex', gap: 14 }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 'none' }}>
              <div style={{ width: 12, height: 12, borderRadius: 12, background: s.color, marginTop: 4 }} />
              {i < steps.length - 1 && <div style={{ width: 2, flex: 1, background: 'var(--line)', minHeight: 26 }} />}
            </div>
            <div style={{ paddingBottom: 18, minWidth: 0 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: s.color, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{s.n}</div>
              <div style={{ fontSize: 12.5, color: 'var(--ink-1)', marginTop: 3, lineHeight: 1.5 }}>{String(s.body).slice(0, 400)}</div>
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

// ---------------------------------------------------------------------- Agents
function AgentsView({ parsed }: { parsed: any[] }) {
  const byAgent = new Map<string, { turns: number; last: string; kind: string }>();
  for (const { e, p } of parsed) {
    if (!e.agent || e.agent === 'system') continue;
    const cur = byAgent.get(e.agent) ?? { turns: 0, last: '', kind: '' };
    cur.turns += 1;
    cur.last = p.verb;
    cur.kind = p.kind;
    byAgent.set(e.agent, cur);
  }
  const roles: Record<string, string> = {
    conductor: 'Decides when there is a post worth making and dispatches the team. Never writes copy.',
    'trend-scout': 'Sweeps Reddit + Twitter live, ranks signals, picks the angle. Never writes copy.',
    'editorial-judge': 'Scores the competing drafts and rules the winner. Adversarial by default.',
    'visual-creator': 'Turns the winning brief into an on-brand card.',
  };
  const entries = Array.from(byAgent.entries());
  if (!entries.length) return <Section title="Agents"><p style={{ fontSize: 12, color: 'var(--ink-3)' }}>No agent activity in the current run yet.</p></Section>;
  return (
    <Section title="Who did what this run" note="Live from the run feed — turns taken, latest action, role. Idle agents did not participate in this run.">
      <div style={{ display: 'grid', gap: 10 }}>
        {entries.map(([id, v]) => {
          const c = colorFor(id);
          return (
            <div key={id} style={{ display: 'flex', gap: 12, border: '1px solid var(--line)', borderLeft: `3px solid ${c}`, borderRadius: 'var(--r-md)', padding: '11px 13px' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <strong style={{ fontSize: 12, color: c }}>{id}</strong>
                  <Pill tone="accent">active</Pill>
                </div>
                <div style={{ fontSize: 11, color: 'var(--ink-2)', marginTop: 3 }}>{roles[id] ?? `${id.replace('strategist-', '')} strategist — argues one arc, competes with the others.`}</div>
                <div style={{ fontSize: 10, color: 'var(--ink-4)', marginTop: 3 }}>latest: {v.last}</div>
              </div>
              <div style={{ textAlign: 'right', flex: 'none', fontSize: 10, color: 'var(--ink-3)' }}>{v.turns} turns</div>
            </div>
          );
        })}
      </div>
    </Section>
  );
}

// ------------------------------------------------------------------------ Cost
function CostView({ spend, calls, parsed }: { spend: any; calls: any[]; parsed: any[] }) {
  const steps = parsed.filter((x) => x.e.agent !== 'system').length;
  return (
    <>
      <Section title="Spend" note="Real ledger from the capped Vertex proxy. At the cap the proxy refuses further calls.">
        <div style={{ display: 'flex', gap: 28, flexWrap: 'wrap' }}>
          <Metric label="Spent" value={spend ? `$${spend.spent_usd.toFixed(4)}` : <NoData />} />
          <Metric label="Cap" value={spend ? `$${spend.cap_usd.toFixed(2)}` : <NoData />} />
          <Metric label="Remaining" value={spend ? `$${(spend.cap_usd - spend.spent_usd).toFixed(4)}` : <NoData />} />
          <Metric label="Vertex calls (total)" value={calls.length} />
          <Metric label="Debate steps (this run)" value={steps} />
        </div>
        {spend && (
          <div style={{ marginTop: 14 }}>
            <Bar segments={[{ value: (spend.spent_usd / spend.cap_usd) * 100, colour: 'var(--accent)' }, { value: 100 - (spend.spent_usd / spend.cap_usd) * 100, colour: 'var(--bg-raised)' }]} height={8} />
          </div>
        )}
      </Section>
    </>
  );
}

// ------------------------------------------------------- Run lifecycle timeline
const LIFECYCLE = [
  { id: 'triggered', label: 'Triggered', kinds: ['system'] },
  { id: 'researching', label: 'Researching', kinds: ['source'] },
  { id: 'processing', label: 'Processing', kinds: ['analysis'] },
  { id: 'analysis', label: 'Agent analysis', kinds: ['proposal'] },
  { id: 'debate', label: 'Agent debate', kinds: ['challenge'] },
  { id: 'decision', label: 'Decision', kinds: ['ruling'] },
  { id: 'execution', label: 'Execution', kinds: ['visual'] },
] as const;

function RunLifecycle({ runId, onBack }: { runId: string; onBack: () => void }) {
  const [meta, setMeta] = useState<any>(null);
  const [events, setEvents] = useState<Ev[]>([]);

  useEffect(() => {
    let stop = false;
    async function load() {
      try {
        const r = await fetch(`/api/runs/${runId}`, { cache: 'no-store' }).then((x) => x.json());
        if (stop) return;
        setMeta(r.meta ?? null);
        setEvents(Array.isArray(r.events) ? r.events : []);
      } catch {
        /* ignore */
      }
    }
    load();
    // Keep polling while the run is still executing.
    const id = setInterval(load, 3000);
    return () => {
      stop = true;
      clearInterval(id);
    };
  }, [runId]);

  const parsed = useMemo(() => events.map((e) => ({ e, p: parseEvent(e) })), [events]);
  const running = meta?.status === 'running';

  // Bucket events into lifecycle stages.
  const buckets = LIFECYCLE.map((st) => ({
    ...st,
    items: parsed.filter(({ p }) => (st.kinds as readonly string[]).includes(p.kind)),
  }));
  const lastWith = buckets.reduce((acc, b, i) => (b.items.length ? i : acc), -1);
  const errors = parsed.filter(({ e }) => /error|retr|⚠|fail/i.test(e.text || ''));

  function stageStatus(i: number, has: boolean): 'done' | 'running' | 'pending' | 'skipped' {
    if (has) return running && i === lastWith ? 'running' : 'done';
    if (running) return i < lastWith ? 'skipped' : 'pending';
    return 'skipped';
  }
  const completedDone = !!meta?.ended;

  return (
    <>
      <button onClick={onBack} style={{ fontSize: 11, color: 'var(--accent)', marginBottom: 12 }}>
        ← back to live views
      </button>
      <Section
        title={meta?.pipeline || 'Pipeline run'}
        right={<Pill tone={running ? 'accent' : meta?.status === 'completed' ? 'neutral' : 'danger'}>{running ? '● live' : meta?.status ?? '—'}</Pill>}
        note={`Run ID ${runId} · permanent audit record`}
      >
        <div style={{ display: 'flex', gap: 26, flexWrap: 'wrap' }}>
          <Metric label="Started" value={meta?.started ? new Date(meta.started * 1000).toLocaleString() : '—'} />
          <Metric label="Ended" value={meta?.ended ? new Date(meta.ended * 1000).toLocaleString() : running ? 'in progress' : '—'} />
          <Metric label="Duration" value={meta?.duration_s ? `${meta.duration_s}s` : running ? 'running' : '—'} />
          <Metric label="Brain / source" value={`${meta?.brain ?? '?'} · ${meta?.trend_source ?? '?'}`} />
          <Metric label="Trend" value={meta?.trend ?? <NoData />} />
          <Metric label="Telegram" value={meta?.telegram_message_id ? `msg #${meta.telegram_message_id}` : <NoData reason="not sent" />} />
        </div>
        {meta?.winner_hook && (
          <div style={{ marginTop: 14, padding: '10px 12px', border: '1px solid var(--accent)', borderRadius: 'var(--r-md)' }}>
            <div style={{ fontSize: 10, color: 'var(--ink-4)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Final result</div>
            <div style={{ fontSize: 13, color: 'var(--ink-1)', marginTop: 3, lineHeight: 1.5 }}>
              <strong>“{meta.winner_hook}”</strong> {meta.winner_body ?? ''}
            </div>
          </div>
        )}
        {errors.length > 0 && (
          <div style={{ marginTop: 10, fontSize: 11, color: 'var(--danger)' }}>⚠ {errors.length} error/retry event(s) in this run</div>
        )}
      </Section>

      <Section title="Lifecycle" note="Triggered → Researching → Processing → Agent Analysis → Agent Debate → Decision → Execution → Completed. Each stage shows the agents, timing and what they produced.">
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {buckets.map((b, i) => {
            const status = stageStatus(i, b.items.length > 0);
            const agents = Array.from(new Set(b.items.map(({ e }) => e.agent)));
            const t0 = b.items.length ? Math.min(...b.items.map(({ e }) => e.ts)) : 0;
            const t1 = b.items.length ? Math.max(...b.items.map(({ e }) => e.ts)) : 0;
            return <StageRow key={b.id} label={b.label} status={status} agents={agents} items={b.items} dur={t1 - t0} />;
          })}
          <StageRow
            label="Completed"
            status={completedDone ? 'done' : running ? 'pending' : 'skipped'}
            agents={[]}
            items={[]}
            dur={0}
            note={completedDone ? `Finished ${meta?.status} in ${meta?.duration_s ?? '?'}s` : running ? 'awaiting completion' : ''}
          />
        </div>
      </Section>
    </>
  );
}

function StageRow({
  label,
  status,
  agents,
  items,
  dur,
  note,
}: {
  label: string;
  status: 'done' | 'running' | 'pending' | 'skipped';
  agents: string[];
  items: any[];
  dur: number;
  note?: string;
}) {
  const dot = status === 'done' ? 'var(--accent)' : status === 'running' ? '#10b981' : status === 'pending' ? 'var(--ink-4)' : 'var(--line)';
  return (
    <div style={{ display: 'flex', gap: 14 }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 'none' }}>
        <div style={{ width: 12, height: 12, borderRadius: 12, background: dot, marginTop: 4, boxShadow: status === 'running' ? '0 0 0 3px rgba(16,185,129,0.25)' : 'none' }} />
        <div style={{ width: 2, flex: 1, background: 'var(--line)', minHeight: 22 }} />
      </div>
      <div style={{ paddingBottom: 16, minWidth: 0, flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--ink-1)' }}>{label}</span>
          <Pill tone={status === 'running' ? 'accent' : status === 'done' ? 'neutral' : 'muted'}>{status}</Pill>
          {dur > 0 && <span style={{ fontSize: 10, color: 'var(--ink-4)' }}>{Math.round(dur)}s</span>}
          {agents.map((a) => (
            <span key={a} style={{ fontSize: 9, fontWeight: 600, padding: '1px 6px', borderRadius: 5, background: colorFor(a) + '22', color: colorFor(a) }}>{a}</span>
          ))}
        </div>
        {note && <div style={{ fontSize: 11, color: 'var(--ink-3)', marginTop: 3 }}>{note}</div>}
        {items.map(({ e, p }: any, j: number) => (
          <div key={j} style={{ fontSize: 11, color: 'var(--ink-2)', marginTop: 4, lineHeight: 1.45 }}>
            <span style={{ color: colorFor(e.agent), fontWeight: 600 }}>{e.agent}</span>{' '}
            <span style={{ color: 'var(--ink-4)' }}>{p.verb}:</span> {String(p.hook || p.post || p.body).slice(0, 180)}
          </div>
        ))}
      </div>
    </div>
  );
}

function filterBtn(active: boolean): CSSProperties {
  return {
    fontSize: 10,
    padding: '3px 9px',
    borderRadius: 6,
    border: `1px solid ${active ? 'var(--accent)' : 'var(--line)'}`,
    background: active ? 'var(--accent-tint)' : 'transparent',
    color: active ? 'var(--accent-deep)' : 'var(--ink-2)',
    textTransform: 'capitalize',
  };
}
