'use client';

import { useCallback, useEffect, useState } from 'react';

type Source = { title: string; url: string | null; excerpt: string; publisher: string };
type Brief = {
  ok: boolean;
  runId: string | null;
  status: string;
  platforms: string[];
  posts: Record<string, string>;
  sources: Source[];
  runs?: string[];
  error?: string;
};

const LABEL: Record<string, string> = { x: 'X', linkedin: 'LinkedIn', reddit: 'Reddit' };

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
    if (startedAt && Date.now() - startedAt > 8 * 60 * 1000) {
      setBusy(false);
      setNote('No new post appeared within 8 minutes. The pipeline may still be running under Live Trace.');
      return;
    }
    if (!anchor || !data?.runId || data.runId === anchor || data.status === 'running') return;
    setBusy(false);
    const hasPost = Object.keys(data.posts || {}).length > 0;
    setNote(hasPost ? 'The new post is ready.' : 'The run finished without a post. Status: ' + data.status);
  }, [busy, data, anchor, startedAt]);

  const text = data?.posts?.[platform] || '';

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
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request: q }),
      });
      const j = await r.json();
      if (!r.ok || !j.ok) throw new Error(j.error || 'The pipeline did not start');
      setAnchor(data?.runId || 'none');
      setStartedAt(Date.now());
      setNote(j.note || 'Started.');
      setRequest('');
    } catch (e: any) {
      setBusy(false);
      setNote(String(e?.message || e));
    }
  }

  return (
    <main style={{ maxWidth: 1080, margin: '0 auto', padding: '28px 20px 80px', color: 'var(--vn-ink)' }}>
      <p style={{ fontFamily: 'var(--font-jetbrains-mono), monospace', fontSize: 11, letterSpacing: '0.08em', color: 'var(--vn-ink-muted)', margin: 0 }}>
        POST AND SOURCE
      </p>
      <h1 style={{ fontFamily: 'var(--font-display)', fontWeight: 400, fontSize: 34, margin: '8px 0 0' }}>
        The post, and the scrape it came from
      </h1>
      <p style={{ fontSize: 14, color: 'var(--vn-ink-muted)', maxWidth: 640, lineHeight: 1.5 }}>
        {data?.runId ? data.runId : 'No run yet'}{data?.status ? ' · ' + data.status : ''}
      </p>

      {err && (
        <p style={{ color: 'var(--vn-bad)', fontSize: 14 }}>{err}</p>
      )}

      {!data && !err && <p style={{ color: 'var(--vn-ink-muted)' }}>Loading the latest post…</p>}

      {data && !data.runId && (
        <p style={{ fontSize: 15, lineHeight: 1.5 }}>
          No post has been generated yet. Ask for one below. The pipeline writes it, and this page shows that result with the source it used.
        </p>
      )}

      {data?.runId && (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.3fr) minmax(280px, 0.7fr)', gap: 20, alignItems: 'start' }} className="brief-grid">
          <section style={{ border: '1px solid var(--vn-line)', borderRadius: 12, padding: 18, background: 'var(--vn-surface)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', gap: 6 }}>
                {(data.platforms || []).map((p) => (
                  <button key={p} type="button" onClick={() => setPlatform(p)}
                    style={{
                      border: '1px solid ' + (platform === p ? 'var(--vn-line-strong)' : 'var(--vn-line)'),
                      background: platform === p ? 'var(--vn-raised)' : 'transparent',
                      color: 'var(--vn-ink)', borderRadius: 8, padding: '6px 10px', fontSize: 13, cursor: 'pointer',
                    }}>
                    {LABEL[p] || p}
                  </button>
                ))}
              </div>
              <button type="button" onClick={copy} disabled={!text}
                style={{ border: '1px solid var(--vn-line-strong)', background: 'var(--vn-cta)', color: 'var(--vn-on-accent)', borderRadius: 8, padding: '6px 12px', fontSize: 13, cursor: text ? 'pointer' : 'default' }}>
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
            {text ? (
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: 15, lineHeight: 1.55, margin: '16px 0 0' }}>{text}</pre>
            ) : (
              <p style={{ color: 'var(--vn-ink-muted)', marginTop: 16 }}>
                {data.status === 'running' ? 'The pipeline is still writing this post.' : 'This run did not record a post.'}
              </p>
            )}
          </section>

          <aside style={{ border: '1px solid var(--vn-line)', borderRadius: 12, padding: 18, background: 'var(--vn-surface)' }}>
            <div style={{ fontFamily: 'var(--font-jetbrains-mono), monospace', fontSize: 11, letterSpacing: '0.06em', color: 'var(--vn-ink-muted)' }}>
              SCRAPED SOURCE
            </div>
            {(data.sources || []).map((s, i) => (
              <div key={i} style={{ marginTop: 14, paddingTop: i ? 14 : 0, borderTop: i ? '1px solid var(--vn-line)' : 'none' }}>
                <div style={{ fontSize: 16, lineHeight: 1.35 }}>{s.title}</div>
                {s.publisher ? (
                  <div style={{ fontSize: 12, color: 'var(--vn-ink-muted)', marginTop: 6 }}>{s.publisher}</div>
                ) : null}
                {s.excerpt && s.excerpt !== s.title ? (
                  <p style={{ fontSize: 14, lineHeight: 1.5, margin: '8px 0 0' }}>{s.excerpt}</p>
                ) : null}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
                  {s.url ? (
                    <a href={s.url} target="_blank" rel="noreferrer" style={{
                      display: 'inline-flex', alignItems: 'center', border: '1px solid var(--vn-line-strong)',
                      background: 'var(--vn-hover)', color: 'var(--vn-ink)', borderRadius: 8, padding: '7px 10px',
                      fontSize: 12, fontWeight: 650, textDecoration: 'none',
                    }}>
                      Open source ↗
                    </a>
                  ) : (
                    <span style={{ fontSize: 13, color: 'var(--vn-ink-muted)' }}>No public URL was recorded for this source.</span>
                  )}
                  <a href="/?view=references" style={{
                    display: 'inline-flex', alignItems: 'center', border: '1px solid var(--vn-line-strong)',
                    background: 'var(--vn-hover)', color: 'var(--vn-ink)', borderRadius: 8, padding: '7px 10px',
                    fontSize: 12, fontWeight: 650, textDecoration: 'none',
                  }}>
                    Open in References
                  </a>
                </div>
              </div>
            ))}
          </aside>
        </div>
      )}

      <form onSubmit={(e) => { e.preventDefault(); send(); }}
        style={{ marginTop: 22, display: 'flex', gap: 8, alignItems: 'flex-end' }}>
        <label style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12, color: 'var(--vn-ink-muted)' }}>
          Ask for another post
          <textarea value={request} onChange={(e) => setRequest(e.target.value)} rows={3}
            placeholder="Create another post based on this source, focusing on a different angle."
            disabled={busy}
            style={{ width: '100%', resize: 'vertical', border: '1px solid var(--vn-line-strong)', borderRadius: 8, padding: 10, font: 'inherit', fontSize: 14, color: 'var(--vn-ink)', background: 'var(--vn-surface)' }} />
        </label>
        <button type="submit" disabled={busy || !request.trim()}
          style={{ border: 'none', background: 'var(--vn-cta)', color: 'var(--vn-on-accent)', borderRadius: 8, padding: '10px 14px', fontSize: 14, cursor: busy ? 'wait' : 'pointer' }}>
          {busy ? 'Writing…' : 'Send'}
        </button>
      </form>
      {note && <p style={{ fontSize: 13, color: 'var(--vn-ink-muted)' }}>{note}</p>}
      <style>{`@media (max-width: 800px) { .brief-grid { grid-template-columns: 1fr !important; } }`}</style>
    </main>
  );
}
