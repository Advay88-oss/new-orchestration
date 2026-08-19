"use client";

import { MONO } from "@/lib/colors";
import type { SteppsRow } from "@/lib/derive";

/**
 * STEPPS bar list. Research and Drafts render the same rows at different metrics —
 * the original varied column widths, gap, bar height and fill between them.
 */
interface Props {
  rows: SteppsRow[];
  columns: string;
  gap: string;
  rowGap: string;
  barHeight: string;
  barColor: string;
  labelSize: string;
  labelColor: string;
  valueColor: string;
  /** "14px" under Research, "10px" under Drafts. */
  marginTop: string;
}

export function SteppsBars({
  rows,
  columns,
  gap,
  rowGap,
  barHeight,
  barColor,
  labelSize,
  labelColor,
  valueColor,
  marginTop,
}: Props) {
  return (
    <div style={{ marginTop, display: "flex", flexDirection: "column", gap: rowGap }}>
      {rows.map((sp) => (
        <div
          key={sp.label}
          style={{
            display: "grid",
            gridTemplateColumns: columns,
            gap,
            alignItems: "center",
          }}
        >
          <div style={{ fontSize: labelSize, color: labelColor }}>{sp.label}</div>
          <div
            style={{
              height: barHeight,
              background: "#DFDFDF",
              borderRadius: "999px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: sp.pct,
                borderRadius: "999px",
                background: barColor,
              }}
            />
          </div>
          <div
            style={{
              fontFamily: MONO,
              fontSize: "11px",
              textAlign: "right",
              color: valueColor,
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {sp.v}
          </div>
        </div>
      ))}
    </div>
  );
}
