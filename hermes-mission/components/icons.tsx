/**
 * Line icons for the Herald shell: 1.6px strokes on a 24px grid, drawn in
 * currentColor so they take the text colour of whatever holds them.
 */
import React from "react";

type P = { size?: number; style?: React.CSSProperties };

function Svg({ size = 18, style, children }: P & { children: React.ReactNode }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={style}>
      {children}
    </svg>
  );
}

export const IconChat = (p: P) => <Svg {...p}><path d="M20 12a8 8 0 0 1-11.8 7L4 20l1-4.1A8 8 0 1 1 20 12Z" /></Svg>;
export const IconImage = (p: P) => <Svg {...p}><rect x="3.5" y="3.5" width="17" height="17" rx="3" /><circle cx="9" cy="9" r="1.6" /><path d="m20.5 15-4.6-4.6L6 20.5" /></Svg>;
export const IconPulse = (p: P) => <Svg {...p}><path d="M3 12h4l2.5-6 5 12 2.5-6h4" /></Svg>;
export const IconBookmark = (p: P) => <Svg {...p}><path d="M6.5 3.5h11v17L12 16.5l-5.5 4Z" /></Svg>;
export const IconCompass = (p: P) => <Svg {...p}><circle cx="12" cy="12" r="8.5" /><path d="m15.5 8.5-2 5-5 2 2-5Z" /></Svg>;
export const IconMegaphone = (p: P) => <Svg {...p}><path d="M4 10v4h3l7 4V6L7 10Z" /><path d="M17.5 9.5a3.5 3.5 0 0 1 0 5" /></Svg>;
export const IconEdit = (p: P) => <Svg {...p}><path d="M12.5 4.5H6a2 2 0 0 0-2 2V18a2 2 0 0 0 2 2h11.5a2 2 0 0 0 2-2v-6.5" /><path d="M18 3.5a2.1 2.1 0 0 1 3 3l-8 8-4 1 1-4Z" /></Svg>;
export const IconSearch = (p: P) => <Svg {...p}><circle cx="11" cy="11" r="6.5" /><path d="m20 20-4.2-4.2" /></Svg>;
export const IconChevrons = (p: P) => <Svg {...p}><path d="m8 9 4-4 4 4" /><path d="m8 15 4 4 4-4" /></Svg>;
export const IconChevronRight = (p: P) => <Svg {...p}><path d="m9.5 6 6 6-6 6" /></Svg>;
export const IconSun = (p: P) => <Svg {...p}><circle cx="12" cy="12" r="3.5" /><path d="M12 3v1.5M12 19.5V21M3 12h1.5M19.5 12H21M5.6 5.6l1.1 1.1M17.3 17.3l1.1 1.1M5.6 18.4l1.1-1.1M17.3 6.7l1.1-1.1" /></Svg>;
export const IconMoon = (p: P) => <Svg {...p}><path d="M19.5 14.5A7.5 7.5 0 0 1 9.5 4.5a7.5 7.5 0 1 0 10 10Z" /></Svg>;
export const IconShare = (p: P) => <Svg {...p}><path d="M14 4h6v6" /><path d="M20 4 11 13" /><path d="M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4" /></Svg>;
export const IconArrowUp = (p: P) => <Svg {...p}><path d="M12 19V5" /><path d="m6 11 6-6 6 6" /></Svg>;
export const IconClose = (p: P) => <Svg {...p}><path d="M6 6l12 12M18 6 6 18" /></Svg>;
export const IconMenu = (p: P) => <Svg {...p}><path d="M4 7h16M4 12h16M4 17h16" /></Svg>;
export const IconStop = (p: P) => <Svg {...p}><rect x="7" y="7" width="10" height="10" rx="2" /></Svg>;
export const IconCheck = (p: P) => <Svg {...p}><path d="m5 12.5 4.5 4.5L19 7.5" /></Svg>;
export const IconBolt = (p: P) => <Svg {...p}><path d="M13 3 5 13.5h6L10 21l8-10.5h-6Z" /></Svg>;
export const IconArrowRight = (p: P) => <Svg {...p}><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></Svg>;

/** The Herald mark: an H in a rounded square. `tone` picks ink or brand green. */
export function HeraldMark({ size = 24, tone = "ink" }: { size?: number; tone?: "ink" | "accent" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" style={{ flex: "0 0 auto", display: "block" }}>
      <rect width="24" height="24" rx="6.5" fill={tone === "accent" ? "var(--vn-accent)" : "var(--vn-ink)"} />
      <path d="M8 6.8v10.4M16 6.8v10.4M8 12h8" stroke={tone === "accent" ? "#fff" : "var(--vn-bg)"}
            strokeWidth="2.3" strokeLinecap="round" fill="none" />
    </svg>
  );
}
