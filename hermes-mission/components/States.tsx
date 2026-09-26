"use client";

/**
 * Loading, empty and error states, shared by every view so they look like
 * one product. A skeleton takes the shape of what is coming; an empty state
 * says why there is nothing and what makes something appear.
 */
import React from "react";

export function Skeleton({ w = "100%", h = 12, r = 6, style }: {
  w?: number | string; h?: number | string; r?: number; style?: React.CSSProperties;
}) {
  return <span className="vn-skel" style={{ width: w, height: h, borderRadius: r, ...style }} aria-hidden />;
}

/** A card-shaped placeholder: a title bar and a few lines of text. */
export function SkeletonCard({ lines = 3, media = false }: { lines?: number; media?: boolean }) {
  return (
    <div className="vanna-card" style={{ display: "flex", gap: 20 }}>
      {media && <Skeleton w={96} h={96} r={8} style={{ flex: "0 0 96px" }} />}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 10 }}>
        <Skeleton w="38%" h={16} />
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton key={i} w={i === lines - 1 ? "62%" : "100%"} />
        ))}
      </div>
    </div>
  );
}

/** A whole view loading: a header placeholder and a stack of cards. */
export function ViewSkeleton({ cards = 3, media = false, label = "Loading" }: {
  cards?: number; media?: boolean; label?: string;
}) {
  return (
    <section className="vanna-section" aria-busy="true" aria-label={label}>
      <div className="vanna-card" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <Skeleton w={220} h={22} />
        <Skeleton w="54%" />
      </div>
      {Array.from({ length: cards }).map((_, i) => <SkeletonCard key={i} media={media} />)}
    </section>
  );
}

/** Table rows while a list loads. */
export function SkeletonRows({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column" }} aria-busy="true">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} style={{ display: "grid", gridTemplateColumns: `2fr repeat(${cols - 1}, 1fr)`, gap: 24,
                              padding: "16px 20px", borderTop: i ? "1px solid var(--vn-line)" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <Skeleton w="70%" h={14} /><Skeleton w="40%" h={10} />
          </div>
          {Array.from({ length: cols - 1 }).map((_, j) => <Skeleton key={j} w="60%" h={12} style={{ alignSelf: "center" }} />)}
        </div>
      ))}
    </div>
  );
}

const ICONS: Record<string, React.ReactNode> = {
  runs: <><rect x="4" y="5" width="16" height="14" rx="2" /><path d="M4 10h16M9 15h6" /></>,
  signal: <><path d="M4 18c3-8 5-12 8-12s5 4 8 12" /><circle cx="12" cy="6" r="1.5" /></>,
  idea: <><path d="M9 18h6M10 21h4" /><path d="M12 3a6 6 0 0 0-3.6 10.8c.6.5 1 1.2 1 2V16h5.2v-.2c0-.8.4-1.5 1-2A6 6 0 0 0 12 3z" /></>,
  trace: <><path d="M3 12h4l2-5 4 10 2-5h6" /></>,
  search: <><circle cx="11" cy="11" r="6" /><path d="M20 20l-4.5-4.5" /></>,
  error: <><circle cx="12" cy="12" r="8" /><path d="M12 8v5M12 16h.01" /></>,
};

/** Nothing to show yet: a line icon, what is missing, and what brings it in. */
export function EmptyState({ icon = "runs", title, body, action, compact = false }: {
  icon?: keyof typeof ICONS; title: string; body?: React.ReactNode; action?: React.ReactNode; compact?: boolean;
}) {
  return (
    <div className={compact ? undefined : "vanna-card"} role="status"
         style={{ display: "flex", gap: 16, alignItems: "flex-start", padding: compact ? "24px 20px" : "32px" }}>
      <span style={{ flex: "0 0 40px", width: 40, height: 40, borderRadius: 8, background: "var(--vn-sunken)",
                     border: "1px solid var(--vn-line)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={icon === "error" ? "var(--vn-bad)" : "var(--vn-ink-muted)"}
             strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          {ICONS[icon]}
        </svg>
      </span>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: "var(--vn-ink)" }}>{title}</div>
        {body && <div style={{ fontSize: 13.5, color: "var(--vn-ink-muted)", marginTop: 4, maxWidth: "62ch", lineHeight: 1.55 }}>{body}</div>}
        {action && <div style={{ marginTop: 14 }}>{action}</div>}
      </div>
    </div>
  );
}

export function ErrorState({ title = "This view could not load", detail, onRetry }: {
  title?: string; detail?: string; onRetry?: () => void;
}) {
  return (
    <EmptyState icon="error" title={title} body={detail}
      action={onRetry && (
        <button onClick={onRetry} style={{ background: "var(--vn-cta)", color: "var(--vn-on-accent)", border: "none",
                                           borderRadius: 6, padding: "8px 14px", fontSize: 13, fontWeight: 500 }}>
          Try again
        </button>
      )} />
  );
}
