import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { manifest, queueCounts, workerHealth, listRunIds, runView, REPO_ROOT } from '@/lib/v2';

export const dynamic = 'force-dynamic';

interface Subsystem {
  name: string;
  detail: string;
  status: 'ONLINE' | 'IDLE' | 'OFFLINE' | 'UNKNOWN';
  evidence: string;
}

function stat(p: string) {
  try {
    return fs.statSync(p);
  } catch {
    return null;
  }
}

function age(ts: number | null | undefined): string {
  if (!ts) return 'never';
  const s = Math.round(Date.now() / 1000 - ts);
  if (s < 90) return `${s}s ago`;
  if (s < 5400) return `${Math.round(s / 60)}m ago`;
  return `${Math.round(s / 3600)}h ago`;
}

/**
 * Health, checked rather than asserted.
 *
 * The Backend Topology view previously listed every subsystem as "ONLINE" from
 * a hardcoded array, next to a daemon status file that claimed RUNNING with a
 * pid that had been dead for a day. Every status below is derived from
 * something observable on disk right now.
 */
export async function GET() {
  const stages = manifest();
  const worker = workerHealth();
  const queue = queueCounts();
  const runIds = listRunIds(500);
  const latest = runIds[0] ? runView(runIds[0]) : null;

  const manifestStat = stat(path.join(REPO_ROOT, 'state', 'manifest.json'));
  const evidenceStat = stat(path.join(REPO_ROOT, 'state', 'evidence.jsonl'));
  const schedStat = stat(path.join(REPO_ROOT, 'pipeline', 'state', 'scheduler_state.json'));
  const mediaDir = path.join(REPO_ROOT, 'state', 'media');
  let mediaCount = 0;
  try {
    mediaCount = fs.readdirSync(mediaDir).length;
  } catch {
    mediaCount = 0;
  }

  const subsystems: Subsystem[] = [
    {
      name: 'Mission Control',
      detail: 'Next.js :3000',
      status: 'ONLINE',
      evidence: 'this response was served',
    },
    {
      name: 'Pipeline worker',
      detail: worker.pid ? `pid ${worker.pid}` : 'not started',
      status: worker.alive ? (worker.state === 'running' ? 'ONLINE' : 'IDLE') : 'OFFLINE',
      evidence: `heartbeat ${age(worker.ts)}${worker.alive ? '' : ' — stale, treat as not running'}`,
    },
    {
      name: 'Run journal',
      detail: `${runIds.length} run(s)`,
      status: runIds.length > 0 ? 'ONLINE' : 'IDLE',
      evidence: latest ? `latest ${latest.runId} (${latest.status}), ${age(latest.startedAt)}` : 'no runs recorded',
    },
    {
      name: 'Job queue',
      detail: `${queue.pending} pending / ${queue.claimed} claimed / ${queue.dead} dead`,
      status: queue.dead > 0 ? 'UNKNOWN' : queue.pending + queue.claimed > 0 ? 'ONLINE' : 'IDLE',
      evidence: queue.dead > 0 ? `${queue.dead} job(s) dead-lettered — inspect state/queue/dead` : 'no dead letters',
    },
    {
      name: 'Evidence store',
      detail: evidenceStat ? `${(evidenceStat.size / 1024).toFixed(1)} KB` : 'absent',
      status: evidenceStat ? 'ONLINE' : 'OFFLINE',
      evidence: evidenceStat ? `written ${age(evidenceStat.mtimeMs / 1000)}` : 'state/evidence.jsonl not found',
    },
    {
      name: 'Media outputs',
      detail: `${mediaCount} file(s)`,
      status: mediaCount > 0 ? 'ONLINE' : 'IDLE',
      evidence: mediaCount > 0 ? 'state/media populated' : 'no media generated yet',
    },
    {
      name: 'Scheduler',
      detail: schedStat ? 'state file present' : 'never run',
      status: schedStat && Date.now() / 1000 - schedStat.mtimeMs / 1000 < 86400 ? 'ONLINE' : 'IDLE',
      evidence: schedStat ? `last tick ${age(schedStat.mtimeMs / 1000)}` : 'pipeline/state/scheduler_state.json absent',
    },
    {
      name: 'Stage manifest',
      detail: `${stages.length} stages`,
      status: stages.length > 0 ? 'ONLINE' : 'OFFLINE',
      evidence: manifestStat ? `generated ${age(manifestStat.mtimeMs / 1000)}` : 'state/manifest.json missing',
    },
  ];

  return NextResponse.json({
    manifestLoaded: stages.length > 0,
    stages: stages.length,
    agents: stages.filter((s) => s.kind === 'AGENT').length,
    worker,
    queue,
    runs: runIds.length,
    latestRun: latest
      ? { runId: latest.runId, status: latest.status, agentsThatCalledModel: latest.agentsThatCalledModel, agentsDeclared: latest.agentsDeclared }
      : null,
    subsystems,
  });
}
