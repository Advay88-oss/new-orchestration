/**
 * Palette, verbatim from the original component. These are the exact strings the
 * source used as `const INK = "#1F1F1F"` etc. — re-exported, never re-derived.
 */

export const INK = "var(--vn-ink)";
export const INK2 = "var(--vn-ink-body)";
export const INK3 = "var(--vn-ink-muted)";
export const MUTED = "var(--vn-ink-faint)";

export const ACCENT = "var(--vn-accent)";
export const ACCENT_SOFT = "var(--vn-accent-soft)";
export const ACCENT_DEEP = "var(--vn-accent-ink)";

export const OK = "var(--vn-ok)";
export const OK_SOFT = "var(--vn-ok-soft)";

export const BAD = "var(--vn-bad)";
export const BAD_SOFT = "var(--vn-bad-soft)";

export const WARN = "var(--vn-warn)";
export const WARN_SOFT = "var(--vn-warn-soft)";

export const NEUTRAL = "var(--vn-ink-muted)";

export const GRADIENT = "var(--vn-accent)";

/**
 * The original wrote this literally as `'JetBrains Mono', monospace`. next/font
 * hashes the family name at build time, so the literal no longer resolves — the
 * variable set in app/layout.tsx points at the same Google font, same weights.
 * Rendered output is unchanged; only the string differs.
 */
export const MONO = "var(--font-jetbrains-mono), monospace";

/** Default arc palette — also the default value of the `arcPalette` prop. */
export const DEFAULT_ARC_PALETTE: readonly [string, string, string] = [
  "#703AE6",
  "#24A0A9",
  "#FF007A",
];
