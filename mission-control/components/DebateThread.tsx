'use client';

import { useMemo, useState } from 'react';
import { agentForPubkey, arcColour, arcOf, fmt, parentOf, parsePayload } from '@/lib/data';
import type { NostrMessage, Run } from '@/lib/types';
import { NoData, Pill } from './primitives';

/** The centrepiece. The question this view has to answer at a glance is not
 *  "what did each agent say" but "did they actually argue with each other" —
 *  so replies to a rival are marked, and the quoted parent is shown inline. */
export function DebateThread({ run }: { run: Run }) {
  const byId = useMemo(() => new Map(run.messages.map((m) => [m.id, m])), [run.messages]);
  const ordered = useMemo(
    () => [...run.messages].sort((a, b) => a.created_at - b.created_at),
    [run.messages],
  );

  if (!ordered.length) {
    return <NoData reason="no messages in this run" />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {ordered.map((m) => (
        <Message key={m.id} msg={m} parent={byId.get(parentOf(m) ?? '') ?? null} />
      ))}
      <div style={{ fontSize: 10, color: 'var(--ink-4)', textAlign: 'center', paddingTop: 4 }}>
        newest last · {ordered.length} messages
      </div>
    </div>
  );
}

function Message({ msg, parent }: { msg: NostrMessage; parent: NostrMessage | null }) {
  const agent = agentForPubkey(msg.pubkey);
  const arc = arcOf(agent);
  const colour = arcColour(arc);
  const parentAgent = parent ? agentForPubkey(parent.pubkey) : null;
  const isCross =
    !!parentAgent && agent.startsWith('strategist-') && parentAgent.startsWith('strategist-') && parentAgent !== agent;

  const payload = useMemo(() => {
    if (!msg.content.includes('{')) return null;
    return parsePayload(msg.content);
  }, [msg.content]);

  const long = msg.content.length > 900;
  const [expanded, setExpanded] = useState(false);
  const shown = long && !expanded ? msg.content.slice(0, 900) : msg.content;

  return (
    <article
      style={{
        border: '1px solid var(--line)',
        borderLeft: `3px solid ${colour}`,
        borderRadius: 'var(--r-md)',
        padding: '12px 14px',
        background: 'var(--bg)',
      }}
    >
      <header style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: parent ? 6 : 8, flexWrap: 'wrap' }}>
        <strong style={{ fontSize: 12, fontWeight: 600, color: colour }}>{agent}</strong>
        <span
          style={{ fontSize: 10, color: 'var(--ink-4)' }}
          title={fmt.utc(msg.created_at)}
        >
          {fmt.time(msg.created_at)}
        </span>
        {isCross && <Pill tone="accent">replies to rival</Pill>}
        {payload?.ok && <Pill tone="muted">structured payload</Pill>}
        {payload && !payload.ok && <Pill tone="danger">parse failed</Pill>}
      </header>

      {parent && parentAgent && (
        <div
          style={{
            fontSize: 10,
            color: 'var(--ink-3)',
            background: 'var(--bg-sunken)',
            borderRadius: 'var(--r-xs)',
            padding: '6px 8px',
            marginBottom: 8,
          }}
        >
          ↳ {parentAgent}: {parent.content.replace(/\s+/g, ' ').slice(0, 110)}
          {parent.content.length > 110 ? '…' : ''}
        </div>
      )}

      <div className="prose">{shown}</div>

      {payload && !payload.ok && (
        <div
          style={{
            marginTop: 8,
            fontSize: 10,
            color: 'var(--danger)',
            background: '#fdecec',
            borderRadius: 'var(--r-xs)',
            padding: '6px 8px',
          }}
        >
          {payload.error} — message kept and shown raw. Nothing was dropped.
        </div>
      )}

      {long && (
        <button
          onClick={() => setExpanded((v) => !v)}
          style={{
            marginTop: 8,
            fontSize: 10,
            color: 'var(--accent)',
            padding: 0,
          }}
        >
          {expanded ? 'collapse' : `show all ${msg.content.length.toLocaleString()} characters`}
        </button>
      )}
    </article>
  );
}
