import type { CSSProperties, ReactNode } from 'react';

export function Section({
  title,
  note,
  right,
  children,
  style,
}: {
  title: string;
  note?: string;
  right?: ReactNode;
  children: ReactNode;
  style?: CSSProperties;
}) {
  return (
    <section
      style={{
        border: '1px solid var(--line)',
        borderRadius: 'var(--r-lg)',
        background: 'var(--bg)',
        padding: '18px 20px 20px',
        marginBottom: 16,
        ...style,
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          justifyContent: 'space-between',
          gap: 16,
          marginBottom: note ? 4 : 14,
        }}
      >
        <h2 style={{ fontSize: 13, fontWeight: 600, margin: 0, letterSpacing: '-0.01em' }}>
          {title}
        </h2>
        {right}
      </div>
      {note && (
        <p style={{ fontSize: 11, color: 'var(--ink-4)', margin: '0 0 14px', maxWidth: '80ch' }}>
          {note}
        </p>
      )}
      {children}
    </section>
  );
}

export function Pill({
  children,
  tone = 'neutral',
  colour,
}: {
  children: ReactNode;
  tone?: 'neutral' | 'accent' | 'danger' | 'muted';
  colour?: string;
}) {
  const tones: Record<string, CSSProperties> = {
    neutral: { background: 'var(--bg-raised)', color: 'var(--ink-2)' },
    accent: { background: 'var(--accent-tint)', color: 'var(--accent-deep)' },
    danger: { background: '#fdecec', color: 'var(--danger)' },
    muted: { background: 'transparent', color: 'var(--ink-4)', border: '1px solid var(--line)' },
  };
  return (
    <span
      style={{
        ...tones[tone],
        ...(colour ? { background: 'transparent', color: colour, border: `1px solid ${colour}33` } : {}),
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: '2px 9px',
        borderRadius: 'var(--r-pill)',
        fontSize: 10,
        fontWeight: 500,
        whiteSpace: 'nowrap',
      }}
    >
      {children}
    </span>
  );
}

/** "No data" is not zero, and the difference matters enough to have its own
 *  component so it is never accidentally rendered as a number. */
export function NoData({ reason }: { reason?: string }) {
  return (
    <span style={{ color: 'var(--ink-4)', fontSize: 11, fontStyle: 'normal' }}>
      no data{reason ? ` · ${reason}` : ''}
    </span>
  );
}

export function Metric({
  label,
  value,
  sub,
  colour,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  colour?: string;
}) {
  return (
    <div style={{ minWidth: 0 }}>
      <div style={{ fontSize: 10, color: 'var(--ink-4)', marginBottom: 3 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 600, color: colour ?? 'var(--ink)', lineHeight: 1.2 }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 10, color: 'var(--ink-3)', marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

export function Bar({
  segments,
  height = 8,
}: {
  segments: { value: number; colour: string; title?: string }[];
  height?: number;
}) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  return (
    <div
      style={{
        display: 'flex',
        height,
        borderRadius: 'var(--r-pill)',
        overflow: 'hidden',
        background: 'var(--bg-raised)',
      }}
    >
      {segments.map((s, i) => (
        <div
          key={i}
          title={s.title}
          style={{ width: `${(s.value / total) * 100}%`, background: s.colour }}
        />
      ))}
    </div>
  );
}
