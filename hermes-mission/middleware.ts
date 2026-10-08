/**
 * Sets the viewer cookies lib/viewer.ts reads.
 *
 *   vn_since  the first time this browser opened the dashboard; a visitor
 *             sees runs from then on. Signed (`<epoch>.<hmac>`), so it
 *             cannot be backdated to see older runs.
 *   vn_all    `?all`: this browser sees the whole history; `?fresh` ends it
 *             and starts the browser over from now. No login: anyone on the
 *             link can do everything (lib/viewer.ts).
 *   vn_client `?client=<link>` (a signed link for one company, made by the
 *             owner): this browser becomes that company's client. The token
 *             is verified on every request in lib/viewer.ts; `?client=` ends it.
 *
 * Edge runtime: Web Crypto here, node:crypto in lib/viewer.ts, same HMAC.
 */
import { NextResponse, type NextRequest } from 'next/server';

const YEAR = 60 * 60 * 24 * 365;

function sessionSecret(): string {
  return process.env.SESSION_SECRET || process.env.OWNER_KEY || (process.env.K_SERVICE ? '' : 'local-dev-session');
}

async function hmacHex(secret: string, msg: string): Promise<string> {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(msg));
  return Array.from(new Uint8Array(sig)).map((b) => b.toString(16).padStart(2, '0')).join('');
}

/** `<epoch seconds>.<hmac>` for now; empty when no secret is configured. */
async function signedSince(): Promise<string> {
  const secret = sessionSecret();
  if (!secret) return '';
  const t = String(Math.floor(Date.now() / 1000));
  return t + '.' + (await hmacHex(secret, 'vn-since:' + t));
}

// The app moved from / to /app; / is the front page. Old links that carry an
// app parameter (the owner key, a client link, a view) still open the app.
const APP_PARAMS = ['key', 'client', 'as', 'view', 'fresh', 'all'];

export async function middleware(req: NextRequest) {
  const url = req.nextUrl;
  if (url.pathname === '/' && APP_PARAMS.some((p) => url.searchParams.has(p))) {
    const moved = url.clone();
    moved.pathname = '/app';
    return NextResponse.redirect(moved);
  }
  // Cloud Run terminates TLS in front of the container, so the request the
  // server sees is http: deployed, every cookie is Secure regardless.
  const secure = Boolean(process.env.K_SERVICE) || url.protocol === 'https:'
    || req.headers.get('x-forwarded-proto') === 'https';
  const opts = { httpOnly: true, sameSite: 'lax' as const, secure, path: '/', maxAge: YEAR };

  let res: NextResponse;
  if (url.searchParams.has('all')) {
    const clean = url.clone();
    clean.searchParams.delete('all');
    res = NextResponse.redirect(clean);
    res.cookies.set('vn_all', '1', opts);
  } else if (url.searchParams.has('key') || url.searchParams.has('as')) {
    // Old owner-key and preview links: there is no login any more.
    const clean = url.clone();
    clean.searchParams.delete('key');
    clean.searchParams.delete('as');
    res = NextResponse.redirect(clean);
    res.cookies.delete('vn_owner');
    res.cookies.delete('vn_preview');
  } else if (url.searchParams.has('client')) {
    const given = (url.searchParams.get('client') ?? '').slice(0, 600);
    const clean = url.clone();
    clean.searchParams.delete('client');
    res = NextResponse.redirect(clean);
    res.cookies.delete('vn_preview');
    if (given) res.cookies.set('vn_client', given, { ...opts, maxAge: 60 * 60 * 24 * 30 });
    else res.cookies.delete('vn_client');
  } else if (url.searchParams.has('fresh')) {
    // `?fresh` starts this browser over as a new visitor: nothing before now.
    const clean = url.clone();
    clean.searchParams.delete('fresh');
    res = NextResponse.redirect(clean);
    res.cookies.set('vn_since', await signedSince(), opts);
    res.cookies.delete('vn_all');
    return res;
  } else {
    res = NextResponse.next();
  }

  // A missing cookie, or one from before signing (an ISO date), starts now.
  if (!/^\d{9,11}\.[0-9a-f]{64}$/.test(req.cookies.get('vn_since')?.value || '')) {
    const since = await signedSince();
    if (since) res.cookies.set('vn_since', since, opts);
  }
  return res;
}

// Pages only: API calls carry the cookie the page load set.
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|svg|mp4|ico)$).*)'],
};
