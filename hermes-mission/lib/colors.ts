/**
 * Palette, verbatim from the original component. These are the exact strings the
 * source used as `const INK = "#1F1F1F"` etc. — re-exported, never re-derived.
 */

export const INK = "#1F1F1F";
export const INK2 = "#4B5563";
export const INK3 = "#777777";
export const MUTED = "#949494";

export const ACCENT = "#703AE6";
export const ACCENT_SOFT = "#F1EBFD";
export const ACCENT_DEEP = "#3E207F";

export const OK = "#24A0A9";
export const OK_SOFT = "#EBFCFD";

export const BAD = "#E54C4F";
export const BAD_SOFT = "#FEEEEE";

export const WARN = "#E8006F";
export const WARN_SOFT = "#FFE6F2";

export const NEUTRAL = "#777777";

export const GRADIENT = "linear-gradient(135deg, #FC5457 10%, #703AE6 80%)";

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
