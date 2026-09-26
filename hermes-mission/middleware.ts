/**
 * Sets the two viewer cookies lib/viewer.ts reads.
 *
 *   vn_since  the first time this browser opened the dashboard; a visitor
 *             sees runs from then on.
 *   vn_owner  set by `?key=<OWNER_KEY>`, cleared by `?key=`. Holds a hash of
 *             the key, and the key is stripped from the address bar.
 *   vn_preview `?as=visitor` shows the owner what a visitor sees;
 *             `?as=owner` ends the preview.
 *
 * Edge runtime: Web Crypto here, node:crypto in lib/viewer.ts, same hash.
 */
import { NextResponse, type NextRequest } from 'next/server';

const YEAR = 60 * 60 * 24 * 365;

async function ownerHash(key: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('vn-owner:' + key));
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, '0')).join('');
}

export async function middleware(req: NextRequest) {
  const url = req.nextUrl;
  const secure = url.protocol === 'https:';
  const opts = { httpOnly: true, sameSite: 'lax' as const, secure, path: '/', maxAge: YEAR };

  let res: NextResponse;
  if (url.searchParams.has('as')) {
    const clean = url.clone();
    clean.searchParams.delete('as');
    res = NextResponse.redirect(clean);
    if (url.searchParams.get('as') === 'visitor') res.cookies.set('vn_preview', 'visitor', opts);
    else res.cookies.delete('vn_preview');
  } else if (url.searchParams.has('key')) {
    const given = url.searchParams.get('key') ?? '';
    const clean = url.clone();
    clean.searchParams.delete('key');
    res = NextResponse.redirect(clean);
    const key = process.env.OWNER_KEY;
    if (given && key && given === key) {
      res.cookies.set('vn_owner', await ownerHash(key), opts);
    } else {
      res.cookies.delete('vn_owner');
    }
  } else {
    res = NextResponse.next();
  }

  if (!req.cookies.get('vn_since')) {
    res.cookies.set('vn_since', new Date().toISOString(), opts);
  }
  return res;
}

// Pages only: API calls carry the cookie the page load set.
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|svg|mp4|ico)$).*)'],
};
