"use client";

import type { CSSProperties, ReactNode } from "react";

/**
 * A pill's style is computed in the viewmodel by the same `pill()` helper the
 * original used; this only renders it.
 */
export function Pill({ style, children }: { style: CSSProperties; children: ReactNode }) {
  return <span style={style}>{children}</span>;
}
