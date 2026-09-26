import fs from 'fs';
import path from 'path';
import { REPO_ROOT } from '@/lib/v2';

export const dynamic = 'force-dynamic';

/** One image from a tenant's visual memory. Only files inside the brand
 *  brain's own tenant folders are served. */
export async function GET(req: Request) {
  const rel = new URL(req.url).searchParams.get('path') || '';
  const root = path.resolve(REPO_ROOT, 'pipeline', 'brain');
  const file = path.resolve(REPO_ROOT, rel);
  if (!file.startsWith(root + path.sep) || !/\.(png|jpe?g|webp)$/i.test(file) || !fs.existsSync(file)) {
    return new Response('not found', { status: 404 });
  }
  const type = /\.png$/i.test(file) ? 'image/png' : /\.webp$/i.test(file) ? 'image/webp' : 'image/jpeg';
  return new Response(fs.readFileSync(file), {
    headers: { 'Content-Type': type, 'Cache-Control': 'public, max-age=3600' },
  });
}
