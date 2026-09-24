"use client";

import { MONO } from "@/lib/colors";
import { HoverButton } from "./Hover";
import type { MissionVM } from "@/lib/viewmodel";

type MessageVM = NonNullable<MissionVM["d"]>["messages"][number];

/**
 * The thread renders in two places. They are byte-identical apart from three
 * values the original varied between them, passed in here rather than guessed.
 */
interface Props {
  messages: MessageVM[];
  /** "18px 0" in Live debate, "20px 0" in Run detail. */
  articlePadding: string;
  /** Live debate wraps the parse-failure header; Run detail does not. */
  wrapParseHeader: boolean;
  /** Live debate's expand button carries white-space:nowrap; Run detail's does not. */
  nowrapExpand: boolean;
}

export function MessageThread({
  messages,
  articlePadding,
  wrapParseHeader,
  nowrapExpand,
}: Props) {
  return (
    <>
      {messages.map((m) => (
        <article
          key={m.id}
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(120px,150px) minmax(0,1fr)",
            gap: "0 20px",
            padding: articlePadding,
            borderBottom: "1px solid #F4F4F4",
          }}
        >
          <div style={{ textAlign: "right" }}>
            <div
              style={{
                fontSize: "13px",
                lineHeight: "19px",
                fontWeight: 600,
                color: m.hue,
                wordBreak: "break-word",
              }}
            >
              {m.agentLabel}
            </div>
            <div
              title={m.utc}
              style={{
                fontFamily: MONO,
                fontSize: "12px",
                color: "#949494",
                marginTop: "5px",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {m.local}
            </div>
            <div
              style={{
                display: "inline-block",
                marginTop: "7px",
                fontFamily: MONO,
                fontSize: "10px",
                fontWeight: 600,
                letterSpacing: "0.06em",
                textTransform: "uppercase",
                color: "#777777",
                background: "#F4F4F4",
                padding: "2px 8px",
                borderRadius: "999px",
              }}
            >
              {m.kindLabel}
            </div>
          </div>

          <div
            style={{
              minWidth: 0,
              borderLeft: `${m.railWidth} solid ${m.railColor}`,
              paddingLeft: "20px",
            }}
          >
            {m.hasParent && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  marginBottom: "12px",
                  padding: "7px 12px",
                  background: "#F7F7F7",
                  borderRadius: "999px",
                  maxWidth: "74ch",
                }}
              >
                <span
                  style={{
                    fontFamily: MONO,
                    fontSize: "11px",
                    fontWeight: 600,
                    color: m.parentHue,
                    flex: "0 0 auto",
                    whiteSpace: "nowrap",
                  }}
                >
                  ↳ {m.parentAgent}
                </span>
                <span
                  style={{
                    fontSize: "12px",
                    color: "#777777",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {m.parentSnippet}
                </span>
              </div>
            )}

            {m.isProse && (
              <div
                style={{
                  fontSize: "15px",
                  lineHeight: "26px",
                  maxWidth: "70ch",
                  color: "#1F1F1F",
                  whiteSpace: "pre-wrap",
                }}
              >
                {m.body}
              </div>
            )}

            {m.isPayload && (
              <div style={{ maxWidth: "78ch" }}>
                <div style={{ fontSize: "14px", lineHeight: "22px", color: "#1F1F1F" }}>
                  {m.summary}
                </div>
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "8px",
                    marginTop: "12px",
                  }}
                >
                  {m.chips.map((ch, i) => (
                    <span key={i} style={ch.style}>
                      {ch.text}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {m.parseFailed && (
              <div style={{ maxWidth: "78ch" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    ...(wrapParseHeader ? { flexWrap: "wrap" as const } : {}),
                  }}
                >
                  <span
                    style={{
                      fontFamily: MONO,
                      fontSize: "10px",
                      fontWeight: 600,
                      letterSpacing: "0.06em",
                      textTransform: "uppercase",
                      color: "#FFFFFF",
                      background: "#F0666B",
                      padding: "3px 8px",
                      borderRadius: "999px",
                    }}
                  >
                    Parse failed
                  </span>
                  <span style={{ fontSize: "13px", color: "#4B5563" }}>{m.parseError}</span>
                </div>
                <pre
                  style={{
                    margin: "12px 0 0",
                    padding: "14px 16px",
                    background: "#FEEEEE",
                    borderRadius: "12px",
                    fontFamily: MONO,
                    fontSize: "12px",
                    lineHeight: "20px",
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    color: "#8B2E30",
                    maxHeight: "220px",
                    overflow: "auto",
                  }}
                >
                  {m.raw}
                </pre>
                <div
                  style={{
                    fontSize: "12px",
                    lineHeight: "18px",
                    color: "#777777",
                    marginTop: "8px",
                  }}
                >
                  Message kept and shown raw. Nothing was dropped.
                </div>
              </div>
            )}

            {m.canExpand && (
              <HoverButton
                onClick={m.toggle}
                style={{
                  marginTop: "12px",
                  background: "#F1EBFD",
                  border: "none",
                  borderRadius: "8px",
                  padding: "6px 12px",
                  cursor: "pointer",
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "#703AE6",
                  ...(nowrapExpand ? { whiteSpace: "nowrap" as const } : {}),
                }}
                hoverStyle={{ background: "#D3C2F7" }}
              >
                {m.toggleLabel}
              </HoverButton>
            )}
          </div>
        </article>
      ))}
    </>
  );
}
