"use client";

import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

type Detail = NonNullable<MissionVM["d"]>;

/** The 3×3 who-replied-to-whom grid. Rows reply to columns. */
export function DebateMatrix({
  cols,
  rows,
}: {
  cols: Detail["matrixCols"];
  rows: Detail["matrixRows"];
}) {
  return (
    <div
      style={{
        flex: "0 0 auto",
        background: "#FFFFFF",
        borderRadius: "16px",
        padding: "18px 20px",
      }}
    >
      <div
        style={{
          fontFamily: MONO,
          fontSize: "10px",
          fontWeight: 600,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "#949494",
          marginBottom: "12px",
        }}
      >
        Who replied to whom
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "auto repeat(3, 38px)",
          gap: "5px",
          alignItems: "center",
        }}
      >
        <div />
        {cols.map((c) => (
          <div
            key={c.full}
            title={c.full}
            style={{
              fontFamily: MONO,
              fontSize: "11px",
              fontWeight: 600,
              textAlign: "center",
              color: c.hue,
            }}
          >
            {c.short}
          </div>
        ))}
        {rows.map((row) => (
          <div key={row.full} style={{ display: "contents" }}>
            <div
              title={row.full}
              style={{
                fontFamily: MONO,
                fontSize: "11px",
                fontWeight: 600,
                textAlign: "right",
                paddingRight: "8px",
                color: row.hue,
              }}
            >
              {row.short}
            </div>
            {row.cells.map((cell) => (
              <div key={cell.key} title={cell.title} style={cell.style}>
                {cell.text}
              </div>
            ))}
          </div>
        ))}
      </div>
      <div
        style={{
          fontSize: "11px",
          lineHeight: "16px",
          color: "#949494",
          marginTop: "12px",
          maxWidth: "24ch",
        }}
      >
        Rows reply to columns. Diagonal is self-continuation.
      </div>
    </div>
  );
}
