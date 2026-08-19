"use client";

import { MONO } from "@/lib/colors";
import { HoverButton } from "../Hover";
import type { MissionVM } from "@/lib/viewmodel";

const LEGEND = [
  { label: "completed stage", swatch: { background: "#2C2C2C" } },
  { label: "running now", swatch: { background: "#703AE6" } },
  { label: "failed", swatch: { background: "#E54C4F" } },
  { label: "skipped", swatch: { background: "#DFDFDF" } },
  {
    label: "never reached",
    swatch: { border: "1px dashed #DFDFDF", boxSizing: "border-box" as const },
  },
];

export function Lifecycles({ vm }: { vm: MissionVM }) {
  return (
    <section
      style={{
        padding: "24px 32px 80px",
        maxWidth: "1400px",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
      }}
    >
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
            fontWeight: 600,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "#777777",
          }}
        >
          Where each run stopped
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(118px, 1fr))",
            gap: "10px",
            marginTop: "18px",
          }}
        >
          {vm.stageMeta.map((s) => (
            <div
              key={s.id}
              style={{
                background: "#F7F7F7",
                borderRadius: "12px",
                padding: "14px",
                minHeight: "104px",
              }}
            >
              <div
                style={{
                  fontSize: "12px",
                  lineHeight: "18px",
                  fontWeight: 600,
                  color: "#1F1F1F",
                }}
              >
                {s.label}
              </div>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "6px",
                  marginTop: "10px",
                }}
              >
                {s.chips.map((c) => (
                  <HoverButton
                    key={c.key}
                    onClick={c.open}
                    style={c.style}
                    hoverStyle={{ opacity: 0.8 }}
                  >
                    {c.label}
                  </HoverButton>
                ))}
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
          A run appears in the stage it is sitting in now, or the stage it died in. Completed
          runs sit under Human review.
        </div>
      </div>

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
            fontWeight: 600,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "#777777",
          }}
        >
          Lifecycle timelines
        </div>
        <div
          style={{ display: "flex", gap: "18px", flexWrap: "wrap", marginTop: "14px" }}
        >
          {LEGEND.map((l) => (
            <span
              key={l.label}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "7px",
                fontSize: "12px",
                color: "#777777",
              }}
            >
              <span
                style={{ width: "16px", height: "8px", borderRadius: "3px", ...l.swatch }}
              />
              {l.label}
            </span>
          ))}
        </div>
        <div style={{ marginTop: "8px" }}>
          {vm.lifecycles.map((l) => (
            <div key={l.key} style={{ padding: "20px 0", borderBottom: "1px solid #F4F4F4" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "20px",
                  flexWrap: "wrap",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    flexWrap: "wrap",
                  }}
                >
                  <span
                    style={{
                      fontFamily: MONO,
                      fontSize: "15px",
                      fontWeight: 600,
                      color: "#1F1F1F",
                    }}
                  >
                    {l.label}
                  </span>
                  <span style={l.outcomePill}>{l.outcomeLabel}</span>
                  <span
                    style={{
                      fontFamily: MONO,
                      fontSize: "12px",
                      color: "#949494",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {l.when} · {l.reached} · {l.duration} · {l.cost}
                  </span>
                </div>
                <div style={{ display: "flex", gap: "8px" }}>
                  <HoverButton
                    onClick={l.watch}
                    style={{
                      background: "#FFFFFF",
                      border: "1px solid #E5E7EB",
                      borderRadius: "999px",
                      padding: "6px 16px",
                      fontSize: "12px",
                      fontWeight: 600,
                      color: "#4B5563",
                      cursor: "pointer",
                      whiteSpace: "nowrap",
                    }}
                    hoverStyle={{ borderColor: "#703AE6", color: "#703AE6" }}
                  >
                    Watch debate
                  </HoverButton>
                  <HoverButton
                    onClick={l.open}
                    style={{
                      background: "#111111",
                      border: "none",
                      borderRadius: "999px",
                      padding: "7px 17px",
                      fontSize: "12px",
                      fontWeight: 600,
                      color: "#FFFFFF",
                      cursor: "pointer",
                      whiteSpace: "nowrap",
                    }}
                    hoverStyle={{ background: "#703AE6" }}
                  >
                    Open run
                  </HoverButton>
                </div>
              </div>
              <div style={{ display: "flex", gap: "3px", marginTop: "14px" }}>
                {l.segments.map((sg) => (
                  <div key={sg.id} title={sg.title} style={sg.style} />
                ))}
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
            maxWidth: "90ch",
          }}
        >
          Segment width is the real elapsed time of that stage, so a run that spent nine
          minutes in ruling looks different from one that spent forty seconds. Stage boundaries
          are derived from message timestamps — the same inference the run boundaries rest on.
        </div>
      </div>
    </section>
  );
}
