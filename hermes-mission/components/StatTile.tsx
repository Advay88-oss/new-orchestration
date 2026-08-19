"use client";

import { MONO } from "@/lib/colors";
import type { CSSProperties, ReactNode } from "react";

/**
 * The label-over-number tile. The original used six metric variants of it, so the
 * three style slots are passed in rather than guessed from a variant name.
 */
interface Props {
  label: string;
  value: ReactNode;
  container: CSSProperties;
  labelStyle: CSSProperties;
  valueStyle: CSSProperties;
  sub?: string;
  subStyle?: CSSProperties;
}

export function StatTile({
  label,
  value,
  container,
  labelStyle,
  valueStyle,
  sub,
  subStyle,
}: Props) {
  return (
    <div style={container}>
      <div style={{ fontFamily: MONO, ...labelStyle }}>{label}</div>
      <div style={{ fontFamily: MONO, ...valueStyle }}>{value}</div>
      {sub !== undefined && <div style={{ fontFamily: MONO, ...subStyle }}>{sub}</div>}
    </div>
  );
}

/* Label style presets, each lifted from a specific call site in the original. */
export const LABEL_08_949494: CSSProperties = {
  fontSize: "10px",
  fontWeight: 600,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  color: "#949494",
};
export const LABEL_08_777777: CSSProperties = {
  fontSize: "10px",
  fontWeight: 600,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  color: "#777777",
};
export const LABEL_06_949494_9: CSSProperties = {
  fontSize: "9px",
  fontWeight: 600,
  letterSpacing: "0.06em",
  textTransform: "uppercase",
  color: "#949494",
};
export const LABEL_06_949494_10: CSSProperties = {
  fontSize: "10px",
  fontWeight: 600,
  letterSpacing: "0.06em",
  textTransform: "uppercase",
  color: "#949494",
};
