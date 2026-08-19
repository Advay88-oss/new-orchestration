"use client";

import { MONO } from "@/lib/colors";
import { HoverButton } from "../Hover";
import { MessageThread } from "../MessageThread";
import { StatTile, LABEL_08_777777 } from "../StatTile";
import type { MissionVM } from "@/lib/viewmodel";

const HERO_TILE = {
  background: "#1E1E1E",
  borderRadius: "14px",
  padding: "14px 20px",
  minWidth: "130px",
} as const;

const HERO_VALUE = {
  fontSize: "26px",
  fontWeight: 600,
  marginTop: "6px",
  color: "#FFFFFF",
  fontVariantNumeric: "tabular-nums",
} as const;

export function LiveDebate({ vm }: { vm: MissionVM }) {
  const live = vm.live;
  if (!live) return null;

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
      <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
        <span
          style={{
            fontFamily: MONO,
            fontSize: "11px",
            fontWeight: 600,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "#949494",
            marginRight: "4px",
            whiteSpace: "nowrap",
          }}
        >
          Watching
        </span>
        {live.picker.map((p) => (
          <HoverButton
            key={p.key}
            onClick={p.pick}
            style={p.style}
            hoverStyle={{ borderColor: "#703AE6" }}
          >
            {p.label}
          </HoverButton>
        ))}
      </div>

      <div
        style={{
          background: "#111111",
          borderRadius: "20px",
          padding: "26px 30px",
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: "40px",
          flexWrap: "wrap",
        }}
      >
        <div style={{ minWidth: "280px" }}>
          <div
            style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}
          >
            <span
              style={{
                fontFamily: MONO,
                fontSize: "20px",
                fontWeight: 600,
                color: "#FFFFFF",
              }}
            >
              {live.label}
            </span>
            <span style={live.outcomePill}>{live.outcomeLabel}</span>
          </div>
          <div
            style={{
              fontSize: "15px",
              lineHeight: "24px",
              color: "#DFDFDF",
              marginTop: "12px",
            }}
          >
            Current stage —{" "}
            <strong style={{ fontWeight: 600, color: "#FFFFFF" }}>{live.stageLabel}</strong>
          </div>
          <div
            style={{
              fontSize: "13px",
              lineHeight: "20px",
              color: "#949494",
              marginTop: "4px",
              maxWidth: "52ch",
            }}
          >
            {live.stageNote}
          </div>
          {live.hasQuiet && (
            <div
              style={{
                marginTop: "12px",
                padding: "10px 14px",
                background: "#2C2C2C",
                borderRadius: "10px",
                fontSize: "13px",
                lineHeight: "20px",
                color: "#FFB0D6",
                maxWidth: "52ch",
              }}
            >
              {live.quietNote}
            </div>
          )}
        </div>
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          <StatTile
            label="Cross-replies"
            value={live.crossReplies}
            container={HERO_TILE}
            labelStyle={LABEL_08_777777}
            valueStyle={HERO_VALUE}
          />
          <StatTile
            label="Pairs engaged"
            value={live.pairs}
            container={HERO_TILE}
            labelStyle={LABEL_08_777777}
            valueStyle={HERO_VALUE}
          />
          <StatTile
            label="Messages"
            value={live.msgCount}
            container={HERO_TILE}
            labelStyle={LABEL_08_777777}
            valueStyle={HERO_VALUE}
          />
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "16px",
        }}
      >
        {live.participants.map((p) => (
          <div
            key={p.id}
            style={{
              background: "#FFFFFF",
              border: "1px solid #E5E7EB",
              borderRadius: "16px",
              padding: "18px 20px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "10px",
              }}
            >
              <span
                style={{
                  fontFamily: MONO,
                  fontSize: "13px",
                  fontWeight: 600,
                  color: p.hue,
                  wordBreak: "break-word",
                }}
              >
                {p.id}
              </span>
              <span style={p.stateStyle}>{p.state}</span>
            </div>
            <div
              style={{
                fontSize: "14px",
                lineHeight: "22px",
                fontStyle: "italic",
                color: "#4B5563",
                marginTop: "10px",
              }}
            >
              {p.arcline}
            </div>
            <div
              style={{
                height: "4px",
                background: "#F4F4F4",
                borderRadius: "999px",
                marginTop: "14px",
                overflow: "hidden",
              }}
            >
              <div style={p.barStyle} />
            </div>
            <div
              style={{
                display: "flex",
                gap: "18px",
                marginTop: "10px",
                fontFamily: MONO,
                fontSize: "12px",
                color: "#777777",
              }}
            >
              <span>{p.turns} turns</span>
              <span>{p.replies} replies to rivals</span>
            </div>
          </div>
        ))}
      </div>

      <div
        style={{
          background: "#FFFFFF",
          border: "1px solid #E5E7EB",
          borderRadius: "20px",
          padding: "24px 28px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "14px", flexWrap: "wrap" }}>
          <span
            style={{
              fontSize: "20px",
              lineHeight: "30px",
              fontWeight: 600,
              letterSpacing: "-0.01em",
              color: live.verdictColor,
            }}
          >
            {live.verdict}
          </span>
          <span
            style={{
              fontFamily: MONO,
              fontSize: "12px",
              color: "#949494",
              whiteSpace: "nowrap",
            }}
          >
            newest last · {vm.pollStatus}
          </span>
        </div>
        <div style={{ marginTop: "12px" }}>
          <MessageThread
            messages={live.messages}
            articlePadding="18px 0"
            wrapParseHeader
            nowrapExpand
          />
        </div>
      </div>
    </section>
  );
}
