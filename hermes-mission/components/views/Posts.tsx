"use client";

import { MONO } from "@/lib/colors";
import { ClaimTier } from "../ClaimTier";
import { HoverButton } from "../Hover";
import { StatTile, LABEL_08_949494 } from "../StatTile";
import type { MissionVM } from "@/lib/viewmodel";

export function Posts({ vm }: { vm: MissionVM }) {
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
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "16px",
        }}
      >
        {vm.postStats.map((s) => (
          <StatTile
            key={s.label}
            label={s.label}
            value={s.value}
            container={{
              background: "#FFFFFF",
              border: "1px solid #E5E7EB",
              borderRadius: "16px",
              padding: "18px 20px",
            }}
            labelStyle={LABEL_08_949494}
            valueStyle={{
              fontSize: "30px",
              fontWeight: 600,
              marginTop: "8px",
              color: s.color,
              fontVariantNumeric: "tabular-nums",
            }}
          />
        ))}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
        {vm.postFilters.map((f) => (
          <HoverButton
            key={f.label}
            onClick={f.set}
            style={f.style}
            hoverStyle={{ borderColor: "#703AE6" }}
          >
            {f.label}
          </HoverButton>
        ))}
      </div>

      {vm.postRows.map((p) => (
        <div
          key={p.key}
          style={{
            background: "#FFFFFF",
            border: "1px solid #E5E7EB",
            borderRadius: "20px",
            padding: "24px 28px",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
            gap: "24px 40px",
            alignItems: "start",
          }}
        >
          <div style={{ minWidth: 0 }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                flexWrap: "wrap",
              }}
            >
              <span style={{ fontSize: "14px", fontWeight: 600, color: p.hue }}>{p.arc}</span>
              <span
                style={{
                  fontFamily: MONO,
                  fontSize: "11px",
                  color: "#949494",
                  whiteSpace: "nowrap",
                }}
              >
                {p.platform} · {p.template} · {p.persona}
              </span>
              <span style={p.statusPill}>{p.status}</span>
            </div>
            <div
              style={{
                fontSize: "19px",
                lineHeight: "29px",
                fontWeight: 600,
                marginTop: "14px",
                color: "#1F1F1F",
                letterSpacing: "-0.01em",
                maxWidth: "56ch",
              }}
            >
              “{p.hook}…”
            </div>
            <div
              style={{
                fontSize: "15px",
                lineHeight: "26px",
                marginTop: "12px",
                color: "#4B5563",
                whiteSpace: "pre-wrap",
                maxWidth: "66ch",
              }}
            >
              {p.body}
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                marginTop: "12px",
                flexWrap: "wrap",
              }}
            >
              {p.canExpand && (
                <HoverButton
                  onClick={p.toggle}
                  style={{
                    background: "#F1EBFD",
                    border: "none",
                    borderRadius: "8px",
                    padding: "7px 14px",
                    cursor: "pointer",
                    fontSize: "12px",
                    fontWeight: 600,
                    color: "#703AE6",
                    whiteSpace: "nowrap",
                  }}
                  hoverStyle={{ background: "#D3C2F7" }}
                >
                  {p.expandLabel}
                </HoverButton>
              )}
              {p.hasThread && (
                <span
                  style={{
                    fontFamily: MONO,
                    fontSize: "12px",
                    color: "#949494",
                    whiteSpace: "nowrap",
                  }}
                >
                  + {p.threadCount} thread posts
                </span>
              )}
              <span
                style={{
                  fontFamily: MONO,
                  fontSize: "12px",
                  color: "#949494",
                  whiteSpace: "nowrap",
                }}
              >
                {p.finalNote}
              </span>
            </div>
            {p.hasThread && (
              <div
                style={{
                  marginTop: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px",
                  maxWidth: "66ch",
                }}
              >
                {p.thread.map((t, i) => (
                  <div
                    key={i}
                    style={{
                      fontSize: "14px",
                      lineHeight: "23px",
                      color: "#4B5563",
                      paddingLeft: "16px",
                      borderLeft: "2px solid #E5E7EB",
                    }}
                  >
                    {t}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div style={{ minWidth: 0 }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "12px",
                paddingBottom: "14px",
                borderBottom: "1px solid #F4F4F4",
              }}
            >
              <HoverButton
                onClick={p.openRun}
                style={{
                  background: "none",
                  border: "none",
                  padding: 0,
                  cursor: "pointer",
                  fontFamily: MONO,
                  fontSize: "13px",
                  fontWeight: 600,
                  color: "#703AE6",
                }}
                hoverStyle={{ color: "#5029A3" }}
              >
                {p.runLabel} →
              </HoverButton>
              <span
                style={{
                  fontFamily: MONO,
                  fontSize: "26px",
                  fontWeight: 600,
                  color: p.scoreColor,
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                {p.score}
              </span>
            </div>
            <div
              style={{
                fontSize: "13px",
                lineHeight: "21px",
                color: "#4B5563",
                marginTop: "14px",
              }}
            >
              {p.note}
            </div>
            <div
              style={{
                fontFamily: MONO,
                fontSize: "10px",
                fontWeight: 600,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color: "#949494",
                marginTop: "20px",
              }}
            >
              Claims
            </div>
            <div
              style={{
                marginTop: "10px",
                display: "flex",
                flexDirection: "column",
                gap: "9px",
              }}
            >
              {p.claims.map((c, i) => (
                <div
                  key={i}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "22px minmax(0,1fr)",
                    gap: "10px",
                    alignItems: "start",
                  }}
                >
                  <ClaimTier tier={c.tier} style={c.tierStyle} />
                  <div style={{ fontSize: "13px", lineHeight: "20px", color: "#1F1F1F" }}>
                    {c.text}
                  </div>
                </div>
              ))}
            </div>
            <div
              style={{ display: "flex", gap: "8px", marginTop: "18px", flexWrap: "wrap" }}
            >
              <span
                style={{
                  fontFamily: MONO,
                  fontSize: "11px",
                  padding: "4px 11px",
                  background: "#F4F4F4",
                  borderRadius: "999px",
                  color: "#4B5563",
                  whiteSpace: "nowrap",
                }}
              >
                {p.visual}
              </span>
              <span
                style={{
                  fontFamily: MONO,
                  fontSize: "11px",
                  padding: "4px 11px",
                  background: "#F4F4F4",
                  borderRadius: "999px",
                  color: "#4B5563",
                  whiteSpace: "nowrap",
                }}
              >
                {p.when}
              </span>
            </div>
            <div
              style={{
                fontSize: "12px",
                lineHeight: "18px",
                color: "#949494",
                marginTop: "12px",
              }}
            >
              {p.disclaimer}
            </div>
          </div>
        </div>
      ))}
    </section>
  );
}
