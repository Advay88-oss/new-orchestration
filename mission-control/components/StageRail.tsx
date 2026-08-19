'use client';

import { fmt } from '@/lib/data';
import type { Run, Stage, StageStatus } from '@/lib/types';

/** Four states, four readings. `never` and `skipped` are not failures, and a
 *  rail that styles them like one tells the operator a run broke when it simply
 *  stopped. */
type StatusStyle = { fill: string; ink: string; label: string };

const STATUS_STYLE: Record<StageStatus, StatusStyle> = {
  done: { fill: 'var(--accent)', ink: '#fff', label: 'completed' },
  active: { fill: 'var(--accent-tint)', ink: 'var(--accent-deep)', label: 'running now' },
  failed: { fill: '#fdecec', ink: 'var(--danger)', label: 'failed' },
  skipped: { fill: 'var(--bg-raised)', ink: 'var(--ink-4)', label: 'skipped' },
  not_reached: { fill: 'transparent', ink: 'var(--ink-4)', label: 'never reached' },
};

const UNKNOWN: StatusStyle = { fill: 'var(--bg-raised)', ink: 'var(--ink-4)', label: 'unknown' };

/** Never index the map directly. A status the UI has not seen before should
 *  render as "unknown", not take the whole page down — the dashboard's job is
 *  to show what is happening, including when the data surprises it. */
function styleFor(status: string): StatusStyle {
  return STATUS_STYLE[status as StageStatus] ?? UNKNOWN;
}

export function StageRail({ run, showDurations = true }: { run: Run; showDurations?: boolean }) {
  return (
    <div>
      <div style={{ display: 'flex', gap: 6, alignItems: 'stretch' }}>
        {run.stages.map((s) => (
          <StageChip key={s.id} stage={s} showDuration={showDurations} />
        ))}
      </div>
      <Legend />
    </div>
  );
}

function StageChip({ stage, showDuration }: { stage: Stage; showDuration: boolean }) {
  const st = styleFor(stage.status);
  const dashed = stage.status === 'not_reached';
  return (
    <div style={{ flex: 1, minWidth: 0 }}>
      <div
        title={`${stage.label} — ${st.label}`}
        style={{
          background: st.fill,
          color: st.ink,
          border: dashed ? '1px dashed var(--line-strong)' : '1px solid transparent',
          borderRadius: 'var(--r-sm)',
          padding: '7px 8px',
          fontSize: 10,
          fontWeight: 500,
          textAlign: 'center',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}
      >
        {stage.label}
      </div>
      {showDuration && (
        <div style={{ fontSize: 9, color: 'var(--ink-4)', textAlign: 'center', marginTop: 4 }}>
          {stage.started != null && stage.ended != null
            ? fmt.duration(stage.started, stage.ended)
            : stage.status === 'active'
              ? 'running'
              : '—'}
        </div>
      )}
    </div>
  );
}

function Legend() {
  return (
    <div style={{ display: 'flex', gap: 14, marginTop: 12, flexWrap: 'wrap' }}>
      {(Object.keys(STATUS_STYLE) as StageStatus[]).map((k) => (
        <span key={k} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 9, color: 'var(--ink-4)' }}>
          <span
            style={{
              width: 9,
              height: 9,
              borderRadius: 3,
              background: styleFor(k).fill,
              border: k === 'not_reached' ? '1px dashed var(--line-strong)' : '1px solid var(--line)',
              display: 'inline-block',
            }}
          />
          {styleFor(k).label}
        </span>
      ))}
    </div>
  );
}

/** Timeline where segment width is real elapsed time, so a run that sat nine
 *  minutes in ruling looks different from one that took forty seconds. */
export function StageTimeline({ run }: { run: Run }) {
  const spans = run.stages
    .filter((s) => s.started != null)
    .map((s) => ({ ...s, dur: Math.max(1, (s.ended ?? s.started!) - s.started!) }));
  const total = spans.reduce((sum, s) => sum + s.dur, 0) || 1;

  return (
    <div style={{ display: 'flex', height: 10, borderRadius: 'var(--r-pill)', overflow: 'hidden', background: 'var(--bg-raised)' }}>
      {spans.map((s) => (
        <div
          key={s.id}
          title={`${s.label} — ${fmt.duration(s.started!, s.ended)} (${styleFor(s.status).label})`}
          style={{
            width: `${(s.dur / total) * 100}%`,
            background: styleFor(s.status).fill,
            borderRight: '1px solid #fff',
          }}
        />
      ))}
    </div>
  );
}
