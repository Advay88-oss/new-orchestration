import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { pythonPath } from '@/lib/python';
import { listGtmRunIds, gtmRunSummary } from '@/lib/gtm';
import { cloudMode, companyAccess } from '@/lib/local-only';
import { runPipelineJob } from '@/lib/cloudrun';
import { allow } from '@/lib/ratelimit';

export const dynamic = 'force-dynamic';

const REPO_ROOT = path.resolve(process.cwd(), '..');
const RUNS_DIR = path.join(REPO_ROOT, 'pipeline', 'state', 'gtm_runs');
const CONTEXT_FILE = path.join(REPO_ROOT, 'pipeline', 'state', 'brief_context.json');

type Source = { title: string; url: string | null; excerpt: string; publisher: string };

function httpUrl(value: unknown): string | null {
  const s = String(value || '').trim();
  return /^https?:\/\//i.test(s) ? s : null;
}

function looksLikePath(value: string): boolean {
  return /^[A-Za-z]:[\\/]/.test(value) || value.startsWith('/') || value.includes('\\');
}

/** The archive row the run named, read only from inside this repo. */
function archiveExcerpt(sourcePath: string, headline: string): string {
  if (!sourcePath || sourcePath.includes('..')) return '';
  const resolved = path.resolve(sourcePath);
  const root = path.resolve(REPO_ROOT);
  const prefix = root.endsWith(path.sep) ? root : root + path.sep;
  const inside = process.platform === 'win32'
    ? resolved.toLowerCase().startsWith(prefix.toLowerCase())
    : resolved.startsWith(prefix);
  if (!inside || !resolved.endsWith('opportunities.jsonl')) return '';
  let text = '';
  try { text = fs.readFileSync(resolved, 'utf-8'); } catch { return ''; }
  for (const line of text.split('\n')) {
    if (!line.trim()) continue;
    try {
      const row = JSON.parse(line);
      if (row.title === headline && row.description) return String(row.description).slice(0, 600);
    } catch { /* a bad line is skipped */ }
  }
  return '';
}

function chosenSource(summary: any, runId: string): Source {
  const title = String(summary?.signal || '').trim();
  const raw = String(summary?.signal_source || '');
  const url = httpUrl(summary?.signal_url) || httpUrl(raw);
  let excerpt = String(summary?.signal_excerpt || '').trim();
  let publisher = String(summary?.signal_publisher || '').trim();
  if (looksLikePath(publisher)) publisher = '';
  if (!excerpt || !url) {
    try {
      const harvest = JSON.parse(fs.readFileSync(path.join(RUNS_DIR, runId, 'harvest.json'), 'utf-8'));
      const row = (harvest.signals || []).find((s: any) => s.headline === title);
      if (row) {
        if (!url && !excerpt) excerpt = archiveExcerpt(String(row.source || ''), title);
        if (!publisher) {
          const root = String(row.source_root || '');
          publisher = looksLikePath(root) ? '' : root;
        }
      }
    } catch { /* harvest is optional */ }
  }
  return {
    title: title || 'No source was recorded for this run',
    url,
    excerpt: excerpt || title,
    publisher,
  };
}

function carriedSources(summary: any): Source[] {
  const rows = Array.isArray(summary?.brief_sources) ? summary.brief_sources : [];
  return rows.slice(0, 6).map((s: any) => ({
    title: String(s.title || '').slice(0, 300),
    url: httpUrl(s.url),
    excerpt: String(s.excerpt || '').slice(0, 600),
    publisher: String(s.publisher || '').slice(0, 120),
  })).filter((s: Source) => s.title);
}

function isFounderDirective(summary: any): boolean {
  const src = String(summary?.signal_source || '');
  return src === 'founder-directive' || src === 'FOUNDER_DIRECTIVE';
}

function postText(post: any): string {
  if (!post) return '';
  const hook = String(post.hook || '').trim();
  const copy = String(post.copy || '').trim();
  if (hook && copy && !copy.startsWith(hook)) return hook + '\n\n' + copy;
  return copy || hook;
}

export async function GET(req: Request) {
  const asked = new URL(req.url).searchParams.get('runId');
  const access = companyAccess('the post brief');
  if (access instanceof NextResponse) return access;
  const ids = await listGtmRunIds(12);
  let runId = asked && ids.includes(asked) ? asked : '';
  let summary: any = runId ? await gtmRunSummary(runId) : null;
  if (!asked) {
    for (const id of ids) {
      const s = await gtmRunSummary(id);
      if (!s) { runId = id; summary = null; break; }
      const ready = ['x', 'linkedin', 'reddit'].some((k) => postText((s.posts || {})[k]));
      if (ready) { runId = id; summary = s; break; }
    }
  }
  if (!runId) {
    return NextResponse.json({ ok: true, runId: null, status: 'empty', posts: {}, sources: [] });
  }
  if (!summary) {
    return NextResponse.json({ ok: true, runId, status: 'running', posts: {}, sources: [], platforms: [] });
  }
  const posts = summary.posts || {};
  const platforms = ['x', 'linkedin', 'reddit'].filter((k) => postText(posts[k]));
  const chosen = chosenSource(summary, runId);
  const sources: Source[] = [];
  if (!isFounderDirective(summary)) sources.push(chosen);
  for (const extra of carriedSources(summary)) {
    if (!sources.some((s) => s.title === extra.title && s.url === extra.url)) sources.push(extra);
  }
  if (!sources.length) {
    sources.push({
      title: 'No scraped source was recorded for this post',
      url: null,
      excerpt: '',
      publisher: '',
    });
  }
  return NextResponse.json({
    ok: true,
    runId,
    status: summary.status || 'finished',
    platforms,
    posts: Object.fromEntries(platforms.map((k) => [k, postText(posts[k])])),
    sources: sources.filter((s) => s.title),
    runs: ids.slice(0, 8),
  });
}

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const request = String(body.request || '').trim().slice(0, 2000);
  if (!request) return NextResponse.json({ ok: false, error: 'write what the next post should do' }, { status: 400 });
  const access = companyAccess('requesting a post', null, { write: true });
  if (access instanceof NextResponse) return access;
  const tenant = access.tenant || process.env.BRAIN_TENANT || 'vanna';
  if (!allow('launch', 6, 3_600_000)) {
    return NextResponse.json({ ok: false, error: 'too many launches: the limit is 6 an hour' }, { status: 429 });
  }

  const current = await GET(new Request('http://local/api/brief'));
  const brief = await current.json().catch(() => ({}));
  const sources = (Array.isArray(brief.sources) ? brief.sources : []).slice(0, 4);
  const context = sources.map((s: Source, i: number) =>
    `[${i + 1}] ${s.title}${s.url ? ' ' + s.url : ''}${s.excerpt ? '\n' + s.excerpt : ''}`).join('\n');
  const directive = (context
    ? request + '\n\nStay with this scraped source. Do not switch the subject:\n' + context
    : request).slice(0, 4000);
  const packed = JSON.stringify({ at: new Date().toISOString(), request, sources });

  fs.mkdirSync(path.dirname(CONTEXT_FILE), { recursive: true });
  fs.writeFileSync(CONTEXT_FILE, packed);

  if (cloudMode()) {
    const r = await runPipelineJob(
      ['cycle', '--directive', directive, '--no-video'],
      { BRAIN_TENANT: tenant, BRIEF_SOURCES_JSON: packed },
    );
    if (!r.ok) {
      try { fs.unlinkSync(CONTEXT_FILE); } catch { /* already gone */ }
      return NextResponse.json({ ok: false, error: r.error || 'the pipeline job did not start' }, { status: 502 });
    }
    return NextResponse.json({
      ok: true,
      started: true,
      execution: r.execution,
      note: 'The existing pipeline is writing the next post. This page follows that run.',
    });
  }

  const py = pythonPath();
  if (!py) {
    try { fs.unlinkSync(CONTEXT_FILE); } catch { /* already gone */ }
    return NextResponse.json({ ok: false, error: 'no python interpreter for the pipeline' }, { status: 503 });
  }
  const logFile = path.join(RUNS_DIR, 'last_launch.log');
  fs.mkdirSync(RUNS_DIR, { recursive: true });
  const out = fs.openSync(logFile, 'a');
  const child = spawn(py, ['-m', 'pipeline.gtm_os.autonomous_cycle', '--directive', directive, '--no-video'], {
    cwd: REPO_ROOT,
    env: {
      ...process.env,
      PYTHONPATH: REPO_ROOT,
      PYTHONIOENCODING: 'utf-8',
      BRAIN_TENANT: tenant,
      BRIEF_SOURCES_JSON: packed,
    },
    detached: true,
    stdio: ['ignore', out, out],
  });
  child.unref();
  return NextResponse.json({
    ok: true,
    started: true,
    pid: child.pid,
    note: 'The existing pipeline is writing the next post. This page follows that run.',
  });
}
