'use client';

/**
 * The share page: the latest finished post, as it would look on each
 * channel, beside the source it was written from. Anyone with the link can
 * read it; asking for another post is the owner's (the route says so).
 */
import { useCallback, useEffect, useState } from 'react';
import { HeraldMark, IconMoon, IconSun } from '@/components/icons';
import { companyHue } from '@/lib/tenant';
import { useTheme } from '@/lib/theme';

type Source = { title: string; url: string | null; excerpt: string; publisher: string };
type Brief = {
  ok: boolean;
  runId: string | null;
  status: string;
  review?: string;
  headline?: string;
  tenant?: string | null;
  startedAt?: string | null;
  visual?: string | null;
  platforms: string[];
  posts: Record<string, string>;
  sources: Source[];
  error?: string;
};

const LABEL: Record<string, string> = { x: 'X', linkedin: 'LinkedIn', reddit: 'Reddit' };
const REVIEW: Record<string, { text: string; fg: string; bg: string }> = {
  ready: { text: 'Ready for review', fg: 'var(--vn-warn)', bg: 'var(--vn-warn-soft)' },
  held: { text: 'Held at review', fg: 'var(--vn-bad)', bg: 'var(--vn-bad-soft)' },
  approved: { text: 'Approved', fg: 'var(--vn-ok)', bg: 'var(--vn-ok-soft)' },
  revised: { text: 'Revision requested', fg: 'var(--vn-warn)', bg: 'var(--vn-warn-soft)' },
  killed: { text: 'Killed', fg: 'var(--vn-bad)', bg: 'var(--vn-bad-soft)' },
  running: { text: 'Being written', fg: 'var(--vn-accent-ink)', bg: 'var(--vn-accent-soft)' },
};

function when(iso?: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const today = new Date();
  const time = d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: false });
  if (d.toDateString() === today.toDateString()) return 'Today, ' + time;
  const y = new Date(today); y.setDate(today.getDate() - 1);
  if (d.toDateString() === y.toDateString()) return 'Yesterday, ' + time;
  return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short' }) + ', ' + time;
}

const card: React.CSSProperties = {
  background: 'var(--vn-surface)', border: '1px solid var(--vn-line)', borderRadius: 14, boxShadow: '0 1px 2px rgba(28,27,25,0.03)',
};

export default function BriefPage() {
  const [data, setData] = useState<Brief | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [platform, setPlatform] = useState('x');
  const [request, setRequest] = useState('');
  const [busy, setBusy] = useState(false);
  const [anchor, setAnchor] = useState<string | null>(null);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [theme, setTheme] = useTheme();
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const read = () => setDark(theme === 'dark' || (theme === 'system' && mq.matches));
    read();
    mq.addEventListener('change', read);
    return () => mq.removeEventListener('change', read);
  }, [theme]);

  const load = useCallback(async () => {
    try {
      const r = await fetch('/api/brief', { cache: 'no-store' });
      const j = await r.json();
      if (!r.ok || j.ok === false) throw new Error(j.error || 'Could not read the post');
      setData(j);
      setErr(null);
      setPlatform((cur) => (j.platforms || []).includes(cur) ? cur : (j.platforms?.[0] || 'x'));
    } catch (e: any) {
      setErr(String(e?.message || e));
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, busy ? 4000 : 15000);
    return () => clearInterval(t);
  }, [load, busy]);

  useEffect(() => {
    if (!busy) return;
    if (startedAt && Date.now() - startedAt > 25 * 60 * 1000) {
      setBusy(false);
      setNote('No new post appeared within 25 minutes. It may still be running; it will show in Posts.');
      return;
    }
    if (!anchor || !data?.runId || data.runId === anchor || data.status === 'running') return;
    setBusy(false);
    const hasPost = Object.keys(data.posts || {}).length > 0;
    setNote(hasPost ? 'The new post is ready.' : 'That run finished without a post. Status: ' + data.status);
  }, [busy, data, anchor, startedAt]);

  const text = data?.posts?.[platform] || '';
  const tenant = data?.tenant || 'vanna';
  const company = tenant.charAt(0).toUpperCase() + tenant.slice(1);
  const review = REVIEW[data?.status === 'running' ? 'running' : data?.review || ''];
  const source = (data?.sources || [])[0];

  async function copy() {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setNote('Copy was blocked by the browser.');
    }
  }

  async function send() {
    const q = request.trim();
    if (!q || busy) return;
    setBusy(true);
    setNote(null);
    try {
      const r = await fetch('/api/brief', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ request: q }),
      });
      const j = await r.json();
      if (!r.ok || !j.ok) throw new Error(j.error || 'The pipeline did not start');
      setAnchor(data?.runId || 'none');
      setStartedAt(Date.now());
      setNote(j.note || 'Started. A post takes about 15 minutes.');
      setRequest('');
    } catch (e: any) {
      setBusy(false);
      setNote(String(e?.message || e));
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--vn-bg)', color: 'var(--vn-ink)' }}>
      <header style={{ borderBottom: '1px solid var(--vn-line)' }}>
        <div style={{ maxWidth: 1000, margin: '0 auto', padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <a href="/" style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--vn-ink)', textDecoration: 'none', fontWeight: 600, fontSize: 16 }}>
              <HeraldMark size={20} />Herald
            </a>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, border: '1px solid var(--vn-line)', borderRadius: 7, padding: '2px 8px 2px 3px', fontSize: 12.5, color: 'var(--vn-ink-body)', background: 'var(--vn-surface)' }}>
              <span style={{ width: 16, height: 16, borderRadius: 4, background: companyHue(tenant), color: '#fff', fontSize: 10, fontWeight: 600, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>{company.charAt(0)}</span>
              {company}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <a href={data?.runId ? '/app?view=run&run=' + data.runId : '/app'} style={{ fontSize: 13, color: 'var(--vn-ink-body)', fontWeight: 500 }}>Open workspace</a>
            <div role="radiogroup" aria-label="Theme" style={{ display: 'flex', background: 'var(--vn-raised)', borderRadius: 8, padding: 2 }}>
              {([['light', IconSun], ['dark', IconMoon]] as const).map(([t, Icon]) => {
                const on = (t === 'dark') === dark;
                return (
                  <button key={t} role="radio" aria-checked={on} aria-label={t} onClick={() => setTheme(t)}
                          style={{ width: 28, height: 24, border: 'none', borderRadius: 6, display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                                   background: on ? 'var(--vn-surface)' : 'transparent', color: on ? 'var(--vn-ink)' : 'var(--vn-ink-muted)', cursor: 'pointer' }}>
                    <Icon size={14} />
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: 1000, margin: '0 auto', padding: '40px 20px 80px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', fontSize: 13, color: 'var(--vn-ink-muted)' }}>
          Latest post
          {review && (<>
            <span>·</span>
            <span className="hd-pill" style={{ background: review.bg, color: review.fg }}>
              <span className="hd-dot" style={{ width: 5, height: 5, flex: '0 0 5px', background: review.fg }} />{review.text}
            </span>
          </>)}
          {data?.startedAt && <span>{when(data.startedAt)}</span>}
        </div>
        <h1 style={{ margin: '12px 0 28px', fontSize: 'clamp(26px, 2vw + 16px, 36px)' }}>
          {data?.headline || (data && !data.runId ? 'No post yet' : data ? 'The latest post' : '')}
          {!data && !err && <span className="vn-skel" style={{ display: 'inline-block', width: 420, maxWidth: '80%', height: 30, borderRadius: 8 }} />}
        </h1>

        {err && <p style={{ color: 'var(--vn-bad)', fontSize: 14 }}>{err}</p>}

        <div className="brief-grid" style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 290px', gap: 20, alignItems: 'start' }}>
          <section>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, gap: 10 }}>
              <div role="tablist" style={{ display: 'flex', background: 'var(--vn-raised)', border: '1px solid var(--vn-line)', borderRadius: 10, padding: 3 }}>
                {(data?.platforms?.length ? data.platforms : ['x', 'linkedin', 'reddit']).map((p) => (
                  <button key={p} role="tab" aria-selected={platform === p} onClick={() => setPlatform(p)}
                          disabled={!data?.platforms?.includes(p)}
                          style={{ minWidth: 64, border: 'none', borderRadius: 7, padding: '5px 14px', fontSize: 13,
                                   background: platform === p ? 'var(--vn-surface)' : 'transparent',
                                   boxShadow: platform === p ? 'var(--vn-shadow)' : 'none',
                                   color: platform === p ? 'var(--vn-ink)' : 'var(--vn-ink-muted)', fontWeight: platform === p ? 550 : 450 }}>
                    {LABEL[p] || p}
                  </button>
                ))}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 12.5, color: 'var(--vn-ink-muted)' }}>Preview</span>
                {text && <button className="hd-btn" onClick={copy} style={{ padding: '4px 10px', fontSize: 12.5 }}>{copied ? 'Copied' : 'Copy'}</button>}
              </div>
            </div>
            <article style={{ ...card, padding: 18 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ width: 36, height: 36, borderRadius: 999, background: companyHue(tenant), color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600 }}>{company.charAt(0)}</span>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600 }}>{company}</div>
                    <div style={{ fontSize: 12, color: 'var(--vn-ink-muted)' }}>@{tenant} · now</div>
                  </div>
                </div>
                <span style={{ fontSize: 11.5, border: '1px solid var(--vn-line)', borderRadius: 6, padding: '1px 7px', color: 'var(--vn-ink-muted)' }}>{LABEL[platform] || platform}</span>
              </div>
              {text ? (
                <div style={{ whiteSpace: 'pre-wrap', fontSize: 15, lineHeight: 1.6, margin: '14px 0 0', color: 'var(--vn-ink)' }}>{text}</div>
              ) : (
                <p style={{ color: 'var(--vn-ink-muted)', margin: '14px 0 0' }}>
                  {!data ? 'Loading the latest post…' : data.status === 'running' ? 'This post is still being written.' : !data.runId ? 'Ask for a post on the right; it appears here when it is done.' : 'This run did not record a post.'}
                </p>
              )}
              {data?.visual && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={data.visual} alt={'Visual for ' + (data.headline || 'the post')}
                     style={{ display: 'block', width: '100%', aspectRatio: '1 / 1', objectFit: 'cover', borderRadius: 10, marginTop: 16, background: 'var(--vn-sunken)' }} />
              )}
            </article>
          </section>

          <aside style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={card}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 14px', borderBottom: '1px solid var(--vn-line)', fontSize: 13 }}>
                <span style={{ fontWeight: 600 }}>Source</span>
                <span style={{ color: 'var(--vn-ink-muted)' }}>{source?.publisher ? 'Cited' : ''}</span>
              </div>
              <div style={{ padding: 14 }}>
                {source ? (
                  <>
                    <div style={{ fontSize: 14, fontWeight: 550, lineHeight: 1.4 }}>{source.title}</div>
                    {source.publisher && <div style={{ fontSize: 12.5, color: 'var(--vn-ink-muted)', marginTop: 3 }}>{source.publisher}</div>}
                    {source.excerpt && source.excerpt !== source.title && (
                      <div style={{ fontSize: 13, lineHeight: 1.55, marginTop: 10, padding: '10px 12px', background: 'var(--vn-raised)', borderRadius: 8, color: 'var(--vn-ink-body)' }}>{source.excerpt}</div>
                    )}
                    <div style={{ display: 'flex', gap: 6, marginTop: 12 }}>
                      {source.url && <a className="hd-btn" href={source.url} target="_blank" rel="noreferrer" style={{ padding: '5px 11px', fontSize: 12.5 }}>Open</a>}
                      <a className="hd-btn" href="/app?view=references" style={{ padding: '5px 11px', fontSize: 12.5, border: 'none', background: 'transparent' }}>References</a>
                    </div>
                    {(data?.sources || []).length > 1 && (
                      <div style={{ fontSize: 12, color: 'var(--vn-ink-faint)', marginTop: 10 }}>+ {(data?.sources || []).length - 1} more source{(data?.sources || []).length > 2 ? 's' : ''} used</div>
                    )}
                  </>
                ) : <div style={{ fontSize: 13, color: 'var(--vn-ink-muted)' }}>{data ? 'No source was recorded.' : '…'}</div>}
              </div>
            </div>

            <form onSubmit={(e) => { e.preventDefault(); send(); }} style={card}>
              <div style={{ padding: '12px 14px', borderBottom: '1px solid var(--vn-line)', fontSize: 13, fontWeight: 600 }}>Ask for another post</div>
              <div style={{ padding: 14 }}>
                <div className="hd-composer" style={{ borderRadius: 12, boxShadow: 'none' }}>
                  <textarea value={request} onChange={(e) => setRequest(e.target.value)} rows={3} disabled={busy}
                            placeholder="Describe the topic in one sentence…"
                            style={{ width: '100%', resize: 'none', border: 'none', background: 'transparent', padding: '10px 12px 4px', fontSize: 13.5, lineHeight: 1.5, fontFamily: 'inherit', color: 'var(--vn-ink)' }} />
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 8px 8px 12px' }}>
                    <span style={{ fontSize: 12, color: 'var(--vn-ink-muted)' }}>Still image · ~15 min</span>
                    <button type="submit" className="hd-btn hd-btn-dark" disabled={busy || !request.trim()} style={{ padding: '5px 12px', fontSize: 12.5 }}>
                      {busy ? 'Writing…' : 'Send'}
                    </button>
                  </div>
                </div>
                <div style={{ fontSize: 12, color: 'var(--vn-ink-muted)', marginTop: 10, lineHeight: 1.5 }}>
                  Your topic is kept as written. It may be declined, never swapped.
                </div>
                {note && <div style={{ fontSize: 12.5, color: 'var(--vn-ink-body)', marginTop: 8 }}>{note}</div>}
              </div>
            </form>
          </aside>
        </div>
      </main>
      <style>{`@media (max-width: 820px) { .brief-grid { grid-template-columns: 1fr !important; } }`}</style>
    </div>
  );
}
