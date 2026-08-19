"use client";

import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

type Detail = NonNullable<MissionVM["d"]>;

/**
 * The nine-card stage rail. Never-reached cards are dashed and grey; failed cards
 * are red. The two treatments are set in the viewmodel and never share a style.
 */
export function StageRail({ stages, note }: { stages: Detail["stages"]; note: string }) {
  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "1px solid #E5E7EB",
        borderRadius: "20px",
        padding: "24px 28px",
      }}
    >
      <div
        style={{
          fontFamily: MONO,
          fontSize: "12px",
          lineHeight: "18px",
          fontWeight: 600,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "#777777",
        }}
      >
        Stage rail
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
          gap: "12px",
          marginTop: "18px",
        }}
      >
        {stages.map((s) => (
          <div key={s.id} style={s.cardStyle}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={s.dotStyle} />
              <span
                style={{
                  fontSize: "13px",
                  lineHeight: "19px",
                  color: s.labelColor,
                  fontWeight: s.weight,
                }}
              >
                {s.label}
              </span>
            </div>
            <div
              style={{
                fontFamily: MONO,
                fontSize: "12px",
                marginTop: "8px",
                color: s.metaColor,
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {s.meta}
            </div>
          </div>
        ))}
      </div>
      <div
        style={{
          marginTop: "14px",
          fontSize: "12px",
          lineHeight: "18px",
          color: "#949494",
        }}
      >
        {note}
      </div>
    </div>
  );
}
