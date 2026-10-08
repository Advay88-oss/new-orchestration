'use client';

/**
 * The owner's sign-in. The key goes in a POST body (app/api/auth/login), so
 * it never appears in an address bar, a request log or the browser history.
 */
import { useEffect, useState } from 'react';
import { HeraldMark } from '@/components/icons';

export default function LoginPage() {
  const [key, setKey] = useState('');
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState('');
  const [owner, setOwner] = useState<boolean | null>(null);

  useEffect(() => {
    fetch('/api/auth/login', { cache: 'no-store' }).then((r) => r.json())
      .then((d) => setOwner(Boolean(d?.owner))).catch(() => setOwner(false));
  }, []);

  async function signIn(e: React.FormEvent) {
    e.preventDefault();
    if (!key.trim() || busy) return;
    setBusy(true);
    setNote('');
    try {
      const r = await fetch('/api/auth/login', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: key.trim() }),
      });
      const d = await r.json().catch(() => ({}));
      if (r.ok && d.ok) { window.location.href = '/app'; return; }
      setNote(d.error || 'could not sign in');
    } catch (err: any) {
      setNote(String(err?.message || err));
    }
    setBusy(false);
  }

  async function signOut() {
    await fetch('/api/auth/logout', { method: 'POST' }).catch(() => null);
    setOwner(false);
  }

  const box: React.CSSProperties = {
    width: '100%', maxWidth: 380, background: 'var(--vn-surface)', border: '1px solid var(--vn-line)',
    borderRadius: 16, padding: 28, display: 'flex', flexDirection: 'column', gap: 14,
  };
  return (
    <main style={{ minHeight: '100vh', background: 'var(--vn-bg)', color: 'var(--vn-ink)', display: 'grid',
                   placeItems: 'center', padding: 16 }}>
      <div style={box}>
        <a href="/" style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--vn-ink)', textDecoration: 'none',
                             fontWeight: 600, fontSize: 16 }}>
          <HeraldMark size={20} />Herald
        </a>
        {owner ? (
          <>
            <p style={{ margin: 0, fontSize: 14, color: 'var(--vn-ink-body)' }}>You are signed in as the owner.</p>
            <div style={{ display: 'flex', gap: 8 }}>
              <a href="/app" style={btn(true)}>Open the workspace</a>
              <button type="button" onClick={signOut} style={btn(false)}>Sign out</button>
            </div>
          </>
        ) : (
          <form onSubmit={signIn} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <label htmlFor="owner-key" style={{ fontSize: 14, color: 'var(--vn-ink-body)' }}>Owner key</label>
            <input id="owner-key" type="password" autoComplete="current-password" autoFocus value={key}
                   onChange={(e) => setKey(e.target.value)}
                   style={{ height: 38, borderRadius: 9, border: '1px solid var(--vn-line)', background: 'var(--vn-bg)',
                            color: 'var(--vn-ink)', padding: '0 12px', fontSize: 14 }} />
            <button type="submit" disabled={busy || !key.trim()} style={btn(true)}>{busy ? 'Signing in…' : 'Sign in'}</button>
            {note ? <p role="alert" style={{ margin: 0, fontSize: 13, color: '#C0533A' }}>{note}</p> : null}
          </form>
        )}
      </div>
    </main>
  );
}

function btn(primary: boolean): React.CSSProperties {
  return {
    height: 36, padding: '0 14px', borderRadius: 9, fontSize: 14, fontWeight: 500, cursor: 'pointer',
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center', textDecoration: 'none',
    border: '1px solid ' + (primary ? 'var(--vn-ink)' : 'var(--vn-line)'),
    background: primary ? 'var(--vn-ink)' : 'transparent', color: primary ? 'var(--vn-bg)' : 'var(--vn-ink)',
  };
}
