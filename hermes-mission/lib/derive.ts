/**
 * Pure derivations and formatters, lifted verbatim from the original component
 * class. Every number shown in the UI is computed here from the source records —
 * nothing is hardcoded.
 */
import { INK, INK2, MONO, OK, OK_SOFT, BAD, BAD_SOFT } from "./colors";
import type {
  Classified,
  DraftPayload,
  GatePayload,
  NostrEvent,
  ParseResult,
  ResearchPayload,
  Ruling,
  Run,
  Stepps,
  Tier,
} from "./types";
import type { CSSProperties } from "react";

export const STRATS = [
  "strategist-capital-efficiency",
  "strategist-risk-relief",
  "strategist-agentic-credit",
] as const;

export const ARC_OF: Record<string, string> = {
  "strategist-capital-efficiency": "capital-efficiency",
  "strategist-risk-relief": "risk-relief",
  "strategist-agentic-credit": "agentic-credit",
};

export const ARC_ORDER = [
  "capital-efficiency",
  "risk-relief",
  "agentic-credit",
] as const;

/* ------------------------------------------------------------------- pill */

export interface PillOpts {
  pad?: string;
  size?: string;
}

export const pill = (
  color: string,
  bg: string,
  opts?: PillOpts,
): CSSProperties => ({
  display: "inline-flex",
  alignItems: "center",
  gap: "6px",
  padding: (opts && opts.pad) || "5px 12px",
  borderRadius: "999px",
  fontSize: (opts && opts.size) || "12px",
  fontWeight: 600,
  lineHeight: "18px",
  color,
  background: bg,
  whiteSpace: "nowrap",
});

/* ------------------------------------------------------------- formatters */

export const local = (u: number): string =>
  new Date(u * 1000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });

export const localDate = (u: number): string => {
  const dt = new Date(u * 1000);
  return (
    dt.toLocaleDateString([], { month: "short", day: "numeric" }) +
    " " +
    dt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false })
  );
};

export const utc = (u: number): string =>
  new Date(u * 1000).toISOString().replace(".000", "") + " (UTC)";

export const dur = (sec: number | null | undefined): string => {
  if (sec == null) return "—";
  const s = Math.max(0, Math.round(sec));
  if (s < 60) return s + "s";
  const m = Math.floor(s / 60),
    r = s % 60;
  if (m < 60) return m + "m " + String(r).padStart(2, "0") + "s";
  return Math.floor(m / 60) + "h " + String(m % 60).padStart(2, "0") + "m";
};

export const usd = (n: number | null | undefined, dp?: number): string =>
  "$" + (n ?? 0).toFixed(dp ?? 2);

export const int = (n: number | null | undefined): string =>
  (n ?? 0).toLocaleString("en-US");

/* ------------------------------------------------------------------- cost */

export const runCost = (run: Run): number =>
  run.calls.reduce((a, c) => a + c.cost_usd, 0);

/* ------------------------------------------------- defensive parse/classify */

export function parse(text: string | null | undefined): ParseResult {
  const t = (text || "").trim();
  if (!t.startsWith("{") && !t.startsWith("[")) return { kind: "prose", value: null };
  try {
    return { kind: "json", value: JSON.parse(t) };
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return {
      kind: "broken",
      value: null,
      error: String(message || e).replace(/^JSON\.parse: /, "").slice(0, 90),
    };
  }
}

/** Narrowing helper — the parsed value is `unknown` until a field proves it. */
function has(v: unknown, key: string): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && key in v;
}

export function classify(msg: NostrEvent): Classified {
  const p = parse(msg.content);
  if (p.kind === "broken") return { type: "broken", error: p.error };
  if (p.kind === "prose")
    return { type: /^ERROR |outcome="error"/.test(msg.content) ? "error" : "prose" };
  const v = p.value;
  if (has(v, "trends")) return { type: "research", value: v as unknown as ResearchPayload };
  if (has(v, "arc") && has(v, "posts"))
    return { type: "draft", value: v as unknown as DraftPayload };
  if (has(v, "verdict")) return { type: "ruling", value: v as unknown as Ruling };
  if (has(v, "gate")) return { type: "gate", value: v as unknown as GatePayload };
  return { type: "json", value: v };
}

/* ---------------------------------------------------------------- threading */

export const parentOf = (msg: NostrEvent): string | null => {
  const t = (msg.tags || []).find((x) => x[0] === "e");
  return t ? t[1] : null;
};

export interface CrossReplies {
  n: number;
  pairs: number;
  matrix: Record<string, Record<string, number>>;
}

/**
 * Cross-replies and the debate matrix, computed from `e` tags at render time.
 * A strategist who addresses another in prose without a reply tag is not counted —
 * the matrix undercounts rather than guesses.
 */
export function crossReplies(
  run: Run,
  agentOf: (m: NostrEvent) => string,
): CrossReplies {
  const byId: Record<string, NostrEvent> = {};
  run.messages.forEach((m) => (byId[m.id] = m));
  let n = 0;
  const pairs = new Set<string>();
  const matrix: Record<string, Record<string, number>> = {};
  STRATS.forEach((a) => {
    matrix[a] = {};
    STRATS.forEach((b) => (matrix[a][b] = 0));
  });
  run.messages.forEach((m) => {
    const from = agentOf(m),
      pid = parentOf(m);
    if (!pid || !STRATS.includes(from as (typeof STRATS)[number])) return;
    const parent = byId[pid];
    if (!parent) return;
    const to = agentOf(parent);
    if (!STRATS.includes(to as (typeof STRATS)[number])) return;
    matrix[from][to] += 1;
    if (from !== to) {
      n += 1;
      pairs.add([from, to].sort().join("|"));
    }
  });
  return { n, pairs: pairs.size, matrix };
}

/* ------------------------------------------------------------------ stepps */

export interface SteppsRow {
  label: string;
  v: string;
  pct: string;
}

export function steppsList(obj: Stepps, max?: number): SteppsRow[] {
  const L: Record<keyof Stepps, string> = {
    social_currency: "Social currency",
    triggers: "Triggers",
    emotion: "Emotion",
    public: "Public",
    practical_value: "Practical value",
    stories: "Stories",
  };
  return (Object.keys(L) as (keyof Stepps)[]).map((k) => ({
    label: L[k],
    v: String(obj[k] ?? 0),
    pct: ((obj[k] ?? 0) / (max || 10)) * 100 + "%",
  }));
}

/* -------------------------------------------------------------- claim tiers */

export function tierStyle(tier: Tier): CSSProperties {
  const c = tier === "A" ? OK : tier === "B" ? "#595959" : BAD;
  const bg = tier === "A" ? OK_SOFT : tier === "B" ? "#F4F4F4" : BAD_SOFT;
  return {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    width: "22px",
    height: "22px",
    borderRadius: "8px",
    fontFamily: MONO,
    fontSize: "11px",
    fontWeight: 600,
    background: bg,
    color: c,
  };
}

/* --------------------------------------------------------------------- misc */

export const tint = (hex: string | null | undefined, aa?: string): string =>
  (hex || "#000000") + (aa || "1A");

export function rulingOf(run: Run): Ruling | null {
  if (run.ruling) return run.ruling;
  for (const m of run.messages) {
    const c = classify(m);
    if (c.type === "ruling") return c.value;
  }
  return null;
}

export const chipStyle = (bg?: string, color?: string): CSSProperties => ({
  fontFamily: MONO,
  fontSize: "11px",
  fontWeight: 500,
  padding: "4px 11px",
  borderRadius: "999px",
  background: bg || "#F4F4F4",
  color: color || INK2,
  whiteSpace: "nowrap",
});

export { INK, INK2 };
