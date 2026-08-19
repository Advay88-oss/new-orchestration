"use client";

import { MONO } from "@/lib/colors";
import { HoverDiv } from "../Hover";
import type { MissionVM } from "@/lib/viewmodel";

const GRID =
  "minmax(0,2.3fr) minmax(0,1.3fr) minmax(0,1.2fr) minmax(0,1.4fr) minmax(0,0.9fr)";

export function Runs({ vm }: { vm: MissionVM }) {
  return (
    <section style={{ padding: "24px 32px 64px", maxWidth: "1560px" }}>
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: "14px",
          padding: "16px 20px",
          background: "#F1EBFD",
          borderRadius: "16px",
          maxWidth: "104ch",
          marginBottom: "24px",
        }}
      >
        <span
          style={{
            fontFamily: MONO,
            fontSize: "10px",
            lineHeight: "15px",
            fontWeight: 600,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "#FFFFFF",
            background: "#703AE6",
            padding: "3px 8px",
            borderRadius: "999px",
            flex: "0 0 auto",
          }}
        >
          Inferred
        </span>
        <p style={{ margin: 0, fontSize: "14px", lineHeight: "21px", color: "#3E207F" }}>
          Runs are not delimited in the data — there is no{" "}
          <code style={{ fontFamily: MONO, fontSize: "13px" }}>run_id</code>. Every boundary
          below is derived client-side from the conductor&apos;s run-open / run-close messages
          and is shown as an inference, with its evidence, on each run.{" "}
          <a href="#" onClick={vm.goNotes}>
            See the backend change that would fix this →
          </a>
        </p>
      </div>

      <div
        style={{
          background: "#FFFFFF",
          border: "1px solid #E5E7EB",
          borderRadius: "20px",
          overflow: "hidden",
          boxShadow:
            "0px 7px 15px rgba(17,17,17,0.03), 0px 28px 28px rgba(17,17,17,0.03)",
        }}
      >
        <div style={{ overflowX: "auto", minWidth: 0 }}>
          <div
            style={{
              minWidth: "860px",
              display: "grid",
              gridTemplateColumns: GRID,
              gap: "0 20px",
              padding: "14px 24px",
              background: "#111111",
              fontFamily: MONO,
              fontSize: "10px",
              lineHeight: "15px",
              fontWeight: 600,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "#949494",
            }}
          >
            <div>Run</div>
            <div>Trigger</div>
            <div>Outcome</div>
            <div>Debate</div>
            <div style={{ textAlign: "right" }}>Duration / cost</div>
          </div>
          {vm.runRows.map((r) => (
            <HoverDiv
              key={r.key}
              onClick={r.open}
              style={{
                display: "grid",
                minWidth: "860px",
                gridTemplateColumns: GRID,
                gap: "0 20px",
                padding: "18px 24px",
                borderBottom: "1px solid #F4F4F4",
                cursor: "pointer",
                alignItems: "center",
              }}
              hoverStyle={{ background: "#FBFAFE" }}
            >
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    flexWrap: "wrap",
                  }}
                >
                  <span
                    style={{
                      fontFamily: MONO,
                      fontSize: "14px",
                      fontWeight: 600,
                      color: "#1F1F1F",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {r.label}
                  </span>
                  <span style={r.boundaryStyle}>{r.boundaryLabel}</span>
                  <span
                    title={r.startedUtc}
                    style={{
                      fontFamily: MONO,
                      fontSize: "11px",
                      color: "#949494",
                      fontVariantNumeric: "tabular-nums",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {r.startedLocal}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: "12px",
                    lineHeight: "18px",
                    color: "#777777",
                    marginTop: "5px",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {r.headline}
                </div>
              </div>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: "13px", lineHeight: "19px", color: "#4B5563" }}>
                  {r.trigger}
                </div>
                <div
                  style={{
                    fontSize: "12px",
                    lineHeight: "18px",
                    fontWeight: 600,
                    color: r.bucketColor,
                    marginTop: "4px",
                  }}
                >
                  {r.bucket}
                </div>
              </div>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span
                    style={{
                      width: "8px",
                      height: "8px",
                      borderRadius: "999px",
                      background: r.outcomeColor,
                      flex: "0 0 8px",
                    }}
                  />
                  <span
                    style={{ fontSize: "14px", fontWeight: 600, color: r.outcomeColor }}
                  >
                    {r.outcomeLabel}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: "12px",
                    lineHeight: "18px",
                    color: "#949494",
                    marginTop: "3px",
                    marginLeft: "16px",
                  }}
                >
                  {r.outcomeNote}
                </div>
              </div>
              <div>
                <div
                  style={{
                    fontSize: "13px",
                    lineHeight: "19px",
                    color: r.debateColor,
                    fontWeight: 500,
                  }}
                >
                  {r.debateLabel}
                </div>
                <div style={{ display: "flex", gap: "3px", marginTop: "7px" }}>
                  {r.stageDots.map((d) => (
                    <span key={d.id} title={d.title} style={d.style} />
                  ))}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div
                  style={{
                    fontFamily: MONO,
                    fontSize: "13px",
                    fontVariantNumeric: "tabular-nums",
                    color: "#1F1F1F",
                  }}
                >
                  {r.duration}
                </div>
                <div
                  style={{
                    fontFamily: MONO,
                    fontSize: "12px",
                    fontVariantNumeric: "tabular-nums",
                    color: "#949494",
                    marginTop: "4px",
                  }}
                >
                  {r.cost}
                </div>
              </div>
            </HoverDiv>
          ))}
        </div>
      </div>

      <div
        style={{
          marginTop: "16px",
          fontSize: "12px",
          lineHeight: "18px",
          color: "#949494",
          fontFamily: MONO,
        }}
      >
        {vm.runsFootnote}
      </div>
    </section>
  );
}
