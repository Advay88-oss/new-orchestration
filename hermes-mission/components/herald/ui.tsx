"use client";

/** Icons and small controls for the Herald app, drawn as in the design reference. */
import React from "react";

type I = { size?: number; style?: React.CSSProperties; className?: string };
const sv = (size: number, sw: number, extra: React.SVGProps<SVGSVGElement> = {}) => ({
  width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor",
  strokeWidth: sw, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, ...extra,
});

export const Mark = ({ size = 24, stroke = "var(--side)" }: { size?: number; stroke?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <rect x="2.5" y="2.5" width="19" height="19" rx="6" fill="currentColor" />
    <path d="M8 7.5v9M16 7.5v9M8 12h8" stroke={stroke} strokeWidth="2" strokeLinecap="round" />
  </svg>
);

export const IEdit = ({ size = 18 }: I) => <svg {...sv(size, 1.5)}><path d="M12 5H7a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-5" /><path d="M17.6 3.9a1.9 1.9 0 012.7 2.7L13 13.9l-3.6.9.9-3.6z" /></svg>;
export const ISearch = ({ size = 18, style }: I) => <svg {...sv(size, 1.5)} style={style}><circle cx="11" cy="11" r="6.5" /><path d="M16 16l4 4" /></svg>;
export const IChat = ({ size = 18 }: I) => <svg {...sv(size, 1.5)}><path d="M20 11.5a7.5 7.5 0 01-10.9 6.7L4.5 19.5l1.3-4.2A7.5 7.5 0 1120 11.5z" /></svg>;
export const IImage = ({ size = 18 }: I) => <svg {...sv(size, 1.5)}><rect x="4" y="4" width="16" height="16" rx="3" /><circle cx="9.5" cy="9.5" r="1.5" /><path d="M20 15.5l-4.5-4.5L6 20" /></svg>;
export const IPulse = ({ size = 18 }: I) => <svg {...sv(size, 1.5)}><path d="M3 12h3.5l2.5-6 4 12 2.5-6H21" /></svg>;
export const IBookmark = ({ size = 18 }: I) => <svg {...sv(size, 1.5)}><path d="M7 4h10a1 1 0 011 1v15l-6-3.5L6 20V5a1 1 0 011-1z" /></svg>;
export const ICompass = ({ size = 18 }: I) => <svg {...sv(size, 1.5)}><circle cx="12" cy="12" r="8.25" /><path d="M15.3 8.7l-1.9 4.7-4.7 1.9 1.9-4.7z" /></svg>;
export const IMegaphone = ({ size = 18 }: I) => <svg {...sv(size, 1.5)}><path d="M4 10v4a1 1 0 001 1h2l7 4V5L7 9H5a1 1 0 00-1 1z" /><path d="M17.5 9.5a3.5 3.5 0 010 5" /></svg>;
export const IChevR = ({ size = 16, style, className }: I) => <svg {...sv(size, 1.5)} style={style} className={className}><path d="M9 6l6 6-6 6" /></svg>;
export const IChevUD = ({ size = 16 }: I) => <svg {...sv(size, 1.5)} style={{ color: "var(--faint)" }}><path d="M8 10l4-4 4 4M8 14l4 4 4-4" /></svg>;
export const IShare = ({ size = 18 }: I) => <svg {...sv(size, 1.5)}><path d="M14 4h6v6" /><path d="M20 4l-8 8" /><path d="M18 14v5a1 1 0 01-1 1H5a1 1 0 01-1-1V7a1 1 0 011-1h5" /></svg>;
export const ISun = () => <svg {...sv(15, 1.6)}><circle cx="12" cy="12" r="3.75" /><path d="M12 3v1.5M12 19.5V21M4.6 4.6l1.1 1.1M18.3 18.3l1.1 1.1M3 12h1.5M19.5 12H21M4.6 19.4l1.1-1.1M18.3 5.7l1.1-1.1" /></svg>;
export const IMoon = () => <svg {...sv(15, 1.6)}><path d="M19.5 14.2A7.5 7.5 0 019.8 4.5a7.5 7.5 0 109.7 9.7z" /></svg>;
export const IMenu = () => <svg {...sv(19, 1.5)}><path d="M4 7h16M4 12h16M4 17h10" /></svg>;
export const ISend = () => <svg {...sv(16, 2)}><path d="M12 19V5M6 11l6-6 6 6" /></svg>;
export const IStop = () => <svg {...sv(14, 2)}><rect x="7" y="7" width="10" height="10" rx="2" /></svg>;
export const ICheck = ({ size = 16, className, style }: I) => <svg {...sv(size, 1.8)} className={className} style={style}><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>;
export const IPlus = ({ size = 14 }: I) => <svg {...sv(size, 1.8)}><path d="M12 5v14M5 12h14" /></svg>;
export const IBack = () => <svg {...sv(15, 1.7)}><path d="M15 6l-6 6 6 6" /></svg>;
export const ILock = () => <svg {...sv(14, 1.6)}><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 018 0v3" /></svg>;
export const IVideo = () => <svg {...sv(15, 1.5)}><rect x="3.5" y="6" width="12" height="12" rx="2" /><path d="M15.5 10.5l5-3v9l-5-3" /></svg>;
export const ICopy = () => <svg {...sv(14, 1.5)}><rect x="8" y="8" width="11" height="12" rx="2" /><path d="M5 15V6a2 2 0 012-2h7" /></svg>;
export const IAlert = () => <svg {...sv(18, 1.6)} className="bad-c" style={{ flex: "none", marginTop: 1 }}><circle cx="12" cy="12" r="8.5" /><path d="M12 8v4.5M12 15.8h.01" /></svg>;
export const IOk = () => <svg {...sv(16, 1.8)} className="ok-c" style={{ flex: "none", marginTop: 2 }}><circle cx="12" cy="12" r="8.5" /><path d="M8.5 12.3l2.4 2.4 4.6-5" /></svg>;
export const IBad = () => <svg {...sv(16, 1.8)} className="bad-c" style={{ flex: "none", marginTop: 2 }}><circle cx="12" cy="12" r="8.5" /><path d="M9.5 9.5l5 5M14.5 9.5l-5 5" /></svg>;
export const IRefresh = () => <svg {...sv(14, 1.6)}><path d="M19.5 12a7.5 7.5 0 11-2.2-5.3M19.5 4.5v4h-4" /></svg>;
export const IOut = () => <svg {...sv(13, 1.6)}><path d="M8 16L16 8M9 8h7v7" /></svg>;
export const ISpin = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" style={{ animation: "spin 1.6s linear infinite" }}>
    <circle cx="12" cy="12" r="8" stroke="currentColor" strokeOpacity=".25" strokeWidth="2.2" />
    <path d="M20 12a8 8 0 00-8-8" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
  </svg>
);
export const IClose = () => <svg {...sv(17, 1.6)}><path d="M6 6l12 12M18 6L6 18" /></svg>;

/** The design's segmented control: a sliding thumb under the chosen option. */
export function Seg<T extends string>({ value, options, onChange, label }: {
  value: T; options: { key: T; label: React.ReactNode; count?: number | string }[]; onChange: (k: T) => void; label: string;
}) {
  const i = Math.max(0, options.findIndex((o) => o.key === value));
  return (
    <div className="seg-wrap">
      <div className="seg" role="group" aria-label={label}>
        <span className="seg-thumb" style={{ width: `calc((100% - 6px) / ${options.length})`, transform: `translateX(${i * 100}%)` }} />
        {options.map((o) => (
          <button key={o.key} className={o.key === value ? "on" : ""} onClick={() => onChange(o.key)} aria-pressed={o.key === value}>
            {o.label}{o.count != null && <em>{o.count}</em>}
          </button>
        ))}
      </div>
    </div>
  );
}

export function Empty({ title, text, action }: { title: string; text: React.ReactNode; action?: React.ReactNode }) {
  return <div className="empty"><b>{title}</b><span>{text}</span>{action}</div>;
}

/** Loading rows that keep the page's shape while data arrives. */
export function Loading({ rows = 4 }: { rows?: number }) {
  return (
    <div className="card rows">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="row"><span className="skel" style={{ width: 36, height: 36 }} /><span className="skel" style={{ flex: 1, height: 14, width: "auto" }} /></div>
      ))}
    </div>
  );
}
