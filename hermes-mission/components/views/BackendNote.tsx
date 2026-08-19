"use client";

import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

const CARD = {
  background: "#FFFFFF",
  border: "1px solid #E5E7EB",
  borderRadius: "20px",
  padding: "32px 36px",
} as const;

const H2 = {
  margin: 0,
  fontSize: "24px",
  lineHeight: "36px",
  fontWeight: 600,
  letterSpacing: "-0.02em",
} as const;

const PROSE = {
  fontSize: "16px",
  lineHeight: "26px",
  color: "#4B5563",
  maxWidth: "72ch",
} as const;

export function BackendNote({ vm }: { vm: MissionVM }) {
  return (
    <section style={{ padding: "24px 32px 96px", maxWidth: "1000px" }}>
      <div style={CARD}>
        <h2 style={H2}>The run-id decision</h2>
        <p style={{ margin: "12px 0 0", ...PROSE }}>
          Run boundaries are{" "}
          <strong style={{ fontWeight: 600, color: "#1F1F1F" }}>derived client-side</strong>{" "}
          from the conductor&apos;s run-open and run-close messages, and every surface that
          shows a run says so. Nothing in the channel records a run identity, so the
          alternative — inventing one and presenting it as recorded — would make the dashboard
          the least reliable component in the system.
        </p>
        <p style={{ margin: "16px 0 0", ...PROSE }}>
          The inference is honest about its own quality. A run with both an open and a close
          message reads <em>inferred</em>; a run with an open and no close reads{" "}
          <em>inferred · weak</em>, and the detail view names what filled the gap. R-08-02 is
          the case that matters: the visual agent died, no close was ever posted, and its end is
          the last event before the next open — an assumption, labelled as one.
        </p>
        <p style={{ margin: "16px 0 0", ...PROSE }}>
          This should not stay client-side. The fix is one line in the conductor: stamp every
          event it dispatches with a run tag, and have agents echo it. Until that lands, this UI
          shows an inference; after it lands, the same views read the tag and the “inferred”
          chips disappear.
        </p>
        <pre
          style={{
            margin: "20px 0 0",
            padding: "18px 20px",
            background: "#111111",
            borderRadius: "16px",
            fontFamily: MONO,
            fontSize: "13px",
            lineHeight: "22px",
            color: "#BDA4F4",
            overflow: "auto",
          }}
        >
          {'"tags": [["h", "<channel-uuid>"], ["run", "2026-08-08T16:28:05Z-conductor"]]'}
        </pre>
      </div>

      <div style={{ ...CARD, marginTop: "20px" }}>
        <h2 style={H2}>Endpoints this frontend needs</h2>
        <p
          style={{
            margin: "8px 0 0",
            fontSize: "14px",
            lineHeight: "22px",
            color: "#777777",
            maxWidth: "72ch",
          }}
        >
          All read-only, all local, all returning JSON. Nothing here writes.
        </p>
        <div style={{ marginTop: "20px" }}>
          {vm.endpoints.map((e) => (
            <div
              key={e.route}
              style={{
                display: "grid",
                gridTemplateColumns: "minmax(240px,330px) minmax(0,1fr)",
                gap: "0 28px",
                padding: "16px 0",
                borderTop: "1px solid #F4F4F4",
                alignItems: "baseline",
              }}
            >
              <code
                style={{
                  fontFamily: MONO,
                  fontSize: "12px",
                  lineHeight: "20px",
                  color: "#5029A3",
                  wordBreak: "break-all",
                }}
              >
                {e.route}
              </code>
              <div style={{ fontSize: "14px", lineHeight: "22px", color: "#4B5563" }}>
                {e.why}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ ...CARD, marginTop: "20px" }}>
        <h2 style={H2}>What the current sources cannot answer</h2>
        <div style={{ marginTop: "16px" }}>
          {vm.gaps.map((g) => (
            <div key={g.title} style={{ padding: "16px 0", borderTop: "1px solid #F4F4F4" }}>
              <div
                style={{
                  fontSize: "16px",
                  lineHeight: "24px",
                  fontWeight: 600,
                  color: "#1F1F1F",
                }}
              >
                {g.title}
              </div>
              <div
                style={{
                  fontSize: "14px",
                  lineHeight: "22px",
                  color: "#4B5563",
                  marginTop: "6px",
                  maxWidth: "72ch",
                }}
              >
                {g.body}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div
        style={{
          background: "#F1EBFD",
          borderRadius: "20px",
          padding: "32px 36px",
          marginTop: "20px",
        }}
      >
        <h2 style={{ ...H2, color: "#2F1B61" }}>Rules this UI holds itself to</h2>
        <ul
          style={{
            margin: "14px 0 0",
            paddingLeft: "22px",
            fontSize: "15px",
            lineHeight: "30px",
            color: "#3E207F",
            maxWidth: "72ch",
          }}
        >
          <li>
            Null engagement renders as “no data”, never as 0. Zero is a measurement; absence is
            not.
          </li>
          <li>
            Stages never reached are hollow and grey. Failure is red. They are never the same
            shape.
          </li>
          <li>
            A running stage says how long it has been running. It never claims progress it
            cannot measure.
          </li>
          <li>
            Pubkeys are mapped to agent names and never rendered — not in the list, not in raw
            payloads.
          </li>
          <li>
            A message whose JSON will not parse is shown as raw text with the parser error.
            Never dropped.
          </li>
          <li>
            No metric is displayed that the four sources cannot produce. No efficiency score, no
            sentiment.
          </li>
        </ul>
      </div>
    </section>
  );
}
