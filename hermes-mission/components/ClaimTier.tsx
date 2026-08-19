"use client";

import type { CSSProperties } from "react";

/** The 22×22 tier badge. A / B / C, coloured by `tierStyle()` in the viewmodel. */
export function ClaimTier({ tier, style }: { tier: string; style: CSSProperties }) {
  return <span style={style}>{tier}</span>;
}
