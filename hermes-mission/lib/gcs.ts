/**
 * Reading run state from GCS when the dashboard is deployed.
 *
 * The agents cannot run on Cloud Run — they need the local Chrome bridge, the
 * Brain DB, font files and four minutes per cycle. So the pipeline writes here
 * and the dashboard reads there, with object storage as the seam. Locally the
 * dashboard keeps reading the filesystem directly; there is no reason to make
 * a developer round-trip through a bucket to see a run they just produced.
 *
 * No `@google-cloud/storage` dependency. On Cloud Run the service account
 * token comes from the metadata server and the JSON API is a plain fetch, which
 * is a smaller thing to keep working in a container than a client library.
 */

const BUCKET = process.env.VANNA_STATE_BUCKET ?? 'vanna-gtm-state-504607';
const META =
  'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token';

/** True when running on Cloud Run, where there is no pipeline filesystem. */
export function isDeployed(): boolean {
  return Boolean(process.env.K_SERVICE) && process.env.VANNA_FORCE_LOCAL !== '1';
}

let cachedToken: { value: string; expires: number } | null = null;

async function token(): Promise<string> {
  // The metadata token lasts an hour; refreshing it per request would add a
  // round trip to every dashboard poll.
  if (cachedToken && Date.now() < cachedToken.expires) return cachedToken.value;
  const res = await fetch(META, { headers: { 'Metadata-Flavor': 'Google' } });
  if (!res.ok) throw new Error(`metadata token: HTTP ${res.status}`);
  const body = (await res.json()) as { access_token: string; expires_in: number };
  cachedToken = {
    value: body.access_token,
    expires: Date.now() + (body.expires_in - 60) * 1000,
  };
  return cachedToken.value;
}

async function authed(url: string): Promise<Response> {
  return fetch(url, { headers: { Authorization: `Bearer ${await token()}` }, cache: 'no-store' });
}

const api = (path: string) =>
  `https://storage.googleapis.com/storage/v1/b/${BUCKET}/${path}`;

/** Object names under a prefix. */
export async function list(prefix: string, delimiter?: string): Promise<{
  names: string[];
  prefixes: string[];
}> {
  const q = new URLSearchParams({ prefix, maxResults: '1000' });
  if (delimiter) q.set('delimiter', delimiter);
  const res = await authed(`${api('o')}?${q}`);
  if (!res.ok) return { names: [], prefixes: [] };
  const body = (await res.json()) as {
    items?: { name: string }[];
    prefixes?: string[];
  };
  return {
    names: (body.items ?? []).map((i) => i.name),
    prefixes: body.prefixes ?? [],
  };
}

/** One object's contents as text, or null when it does not exist. */
export async function getText(name: string): Promise<string | null> {
  const res = await authed(`${api(`o/${encodeURIComponent(name)}`)}?alt=media`);
  if (!res.ok) return null;
  return res.text();
}

/** One object's contents as bytes — used to serve artifacts. */
export async function getBytes(
  name: string,
): Promise<{ body: ArrayBuffer; contentType: string } | null> {
  const res = await authed(`${api(`o/${encodeURIComponent(name)}`)}?alt=media`);
  if (!res.ok) return null;
  return {
    body: await res.arrayBuffer(),
    contentType: res.headers.get('content-type') ?? 'application/octet-stream',
  };
}

/**
 * The GCS asset key for a pipeline media filename, or null if it isn't one.
 *
 * The panels and the run journal refer to assets by the name the pipeline
 * wrote on the founder's disk — `GTM-20260922-210800_meme.png`. `state_sync`
 * uploads the same bytes under `assets/<runId>/<kind>.<ext>`, so the two
 * halves of the seam disagree on naming and the deployed dashboard 404s on
 * every image. This translates between them.
 */
export function assetKey(filename: string): string | null {
  const m = /^(GTM-[0-9]{8}-[0-9]{6})_(visual|meme|video)\.(png|mp4)$/.exec(
    filename.replace(/^.*[\\/]/, ''),
  );
  return m ? `assets/${m[1]}/${m[2]}.${m[3]}` : null;
}

/** Run ids, newest first. Runs are listed by their folder, not by object. */
export async function runIds(limit = 25): Promise<string[]> {
  const { prefixes } = await list('gtm_runs/', '/');
  return prefixes
    .map((p) => p.replace('gtm_runs/', '').replace(/\/$/, ''))
    .filter((n) => n.startsWith('GTM-'))
    .sort()
    .reverse()
    .slice(0, limit);
}
