"use client";

import { MONO } from "@/lib/colors";
import { StatTile, LABEL_06_949494_10 } from "../StatTile";
import type { MissionVM } from "@/lib/viewmodel";

const CARD = {
  background: "#FFFFFF",
  border: "1px solid #E5E7EB",
  borderRadius: "20px",
  padding: "22px 24px",
} as const;

const CARD_LABEL = {
  fontFamily: MONO,
  fontSize: "12px",
  fontWeight: 600,
  letterSpacing: "0.08em",
  textTransform: "uppercase" as const,
  color: "#777777",
};

const ROW = {
  display: "grid",
  gridTemplateColumns: "1fr 66px 1fr",
  gap: "12px",
  alignItems: "center",
  padding: "12px 0",
  borderBottom: "1px solid #F4F4F4",
} as const;

const COST_CELL = {
  fontFamily: MONO,
  fontSize: "13px",
  textAlign: "right" as const,
  fontVariantNumeric: "tabular-nums" as const,
  color: "#1F1F1F",
};

function Bar({ pct, color }: { pct: string; color: string }) {
  return (
    <span
      style={{
        height: "6px",
        background: "#F4F4F4",
        borderRadius: "999px",
        overflow: "hidden",
        display: "block",
      }}
    >
      <span
        style={{
          display: "block",
          height: "100%",
          width: pct,
          borderRadius: "999px",
          background: color,
        }}
      />
    </span>
  );
}

export function Cost({ vm }: { vm: MissionVM }) {
  return (
    <section
      style={{
        padding: "24px 32px 80px",
        maxWidth: "1560px",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
      }}
    >
      <div
        style={{
          background: "#111111",
          borderRadius: "20px",
          padding: "28px 32px",
          display: "flex",
          alignItems: "flex-end",
          gap: "28px 56px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <div
            style={{
              fontFamily: MONO,
              fontSize: "10px",
              fontWeight: 600,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "#777777",
            }}
          >
            Spent this cap window
          </div>
          <div
            style={{
              fontFamily: MONO,
              fontSize: "56px",
              lineHeight: "64px",
              fontWeight: 600,
              marginTop: "8px",
              fontVariantNumeric: "tabular-nums",
              letterSpacing: "-0.03em",
              color: "#FFFFFF",
            }}
          >
            {vm.spentText}
          </div>
          <div style={{ fontSize: "14px", color: "#949494", marginTop: "4px" }}>
            {vm.costCapLine}
          </div>
        </div>
        <div style={{ flex: "1 1 320px", maxWidth: "560px", paddingBottom: "10px" }}>
          <div
            style={{
              height: "10px",
              background: "#2C2C2C",
              borderRadius: "999px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: vm.capPct,
                borderRadius: "999px",
                backgroundImage: vm.capBar,
              }}
            />
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginTop: "10px",
              fontFamily: MONO,
              fontSize: "12px",
              color: "#A9A9A9",
            }}
          >
            <span>{vm.capNote}</span>
            <span>
              {vm.remainingText} remaining of {vm.capText}
            </span>
          </div>
        </div>
        <div style={{ textAlign: "right", paddingBottom: "10px" }}>
          <div
            style={{
              fontFamily: MONO,
              fontSize: "10px",
              fontWeight: 600,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "#777777",
            }}
          >
            Window opened
          </div>
          <div
            style={{
              fontFamily: MONO,
              fontSize: "14px",
              marginTop: "6px",
              color: "#DFDFDF",
            }}
          >
            {vm.ledgerStarted}
          </div>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "20px",
          alignItems: "start",
        }}
      >
        <div style={CARD}>
          <div style={CARD_LABEL}>By run</div>
          {vm.costByRun.map((r) => (
            <div key={r.label} style={ROW}>
              <span style={{ fontFamily: MONO, fontSize: "13px", color: "#1F1F1F" }}>
                {r.label}
              </span>
              <span style={COST_CELL}>{r.cost}</span>
              <Bar pct={r.pct} color={r.color} />
            </div>
          ))}
        </div>
        <div style={CARD}>
          <div style={CARD_LABEL}>By agent</div>
          {vm.costByAgent.map((r) => (
            <div key={r.label} style={ROW}>
              <span
                style={{
                  fontFamily: MONO,
                  fontSize: "12px",
                  fontWeight: 500,
                  color: r.color,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {r.label}
              </span>
              <span style={COST_CELL}>{r.cost}</span>
              <Bar pct={r.pct} color={r.color} />
            </div>
          ))}
        </div>
        <div style={CARD}>
          <div style={CARD_LABEL}>By stage</div>
          {vm.costByStage.map((r) => (
            <div key={r.label} style={ROW}>
              <span style={{ fontFamily: MONO, fontSize: "13px", color: "#1F1F1F" }}>
                {r.label}
              </span>
              <span style={COST_CELL}>{r.cost}</span>
              <Bar pct={r.pct} color={r.color} />
            </div>
          ))}
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
          gap: "20px",
          alignItems: "start",
        }}
      >
        <div style={CARD}>
          <div style={CARD_LABEL}>Input tokens — cached vs fresh</div>
          <div
            style={{
              display: "flex",
              height: "40px",
              marginTop: "18px",
              borderRadius: "12px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: vm.cachedPct,
                background: "#DFDFDF",
                display: "flex",
                alignItems: "center",
                gap: "6px",
                paddingLeft: "14px",
                fontFamily: MONO,
                fontSize: "12px",
                fontWeight: 500,
                color: "#1F1F1F",
                whiteSpace: "nowrap",
                overflow: "hidden",
              }}
            >
              <span>cached</span>
              <span>{vm.cachedPct}</span>
            </div>
            <div
              style={{
                flex: "1 1 auto",
                background: "#703AE6",
                display: "flex",
                alignItems: "center",
                paddingLeft: "14px",
                fontFamily: MONO,
                fontSize: "12px",
                fontWeight: 500,
                color: "#FFFFFF",
              }}
            >
              fresh
            </div>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "110px 1fr",
              gap: "10px 20px",
              marginTop: "18px",
              fontSize: "13px",
              alignItems: "baseline",
            }}
          >
            <div
              style={{
                fontFamily: MONO,
                fontSize: "11px",
                color: "#949494",
                whiteSpace: "nowrap",
              }}
            >
              cached input
            </div>
            <div
              style={{
                fontFamily: MONO,
                fontVariantNumeric: "tabular-nums",
                color: "#1F1F1F",
              }}
            >
              {vm.cachedTokens} tok · {vm.cachedCost}
            </div>
            <div
              style={{
                fontFamily: MONO,
                fontSize: "11px",
                color: "#949494",
                whiteSpace: "nowrap",
              }}
            >
              fresh input
            </div>
            <div
              style={{
                fontFamily: MONO,
                fontVariantNumeric: "tabular-nums",
                color: "#1F1F1F",
              }}
            >
              {vm.freshTokens} tok · {vm.freshCost}
            </div>
            <div
              style={{
                fontFamily: MONO,
                fontSize: "11px",
                color: "#949494",
                whiteSpace: "nowrap",
              }}
            >
              output
            </div>
            <div
              style={{
                fontFamily: MONO,
                fontVariantNumeric: "tabular-nums",
                color: "#1F1F1F",
              }}
            >
              {vm.outputTokens} tok · {vm.outputCost}
            </div>
          </div>
          <p
            style={{
              margin: "18px 0 0",
              fontSize: "13px",
              lineHeight: "21px",
              color: "#4B5563",
              maxWidth: "58ch",
            }}
          >
            Cached input is {vm.cachedPct} of all input tokens and is billed at a quarter of the
            fresh rate. A single “input tokens” number would overstate the bill by roughly{" "}
            {vm.cachedOverstate}.
          </p>
        </div>
        <div style={CARD}>
          <div style={CARD_LABEL}>Calls</div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "12px",
              marginTop: "18px",
            }}
          >
            {[
              { label: "Total calls", value: vm.totalCalls },
              { label: "Mean / call", value: vm.meanCall },
              { label: "Rewrites", value: vm.rewrites },
            ].map((t) => (
              <StatTile
                key={t.label}
                label={t.label}
                value={t.value}
                container={{
                  background: "#F7F7F7",
                  borderRadius: "12px",
                  padding: "16px",
                }}
                labelStyle={LABEL_06_949494_10}
                valueStyle={{
                  fontSize: "22px",
                  fontWeight: 500,
                  marginTop: "6px",
                  fontVariantNumeric: "tabular-nums",
                }}
              />
            ))}
          </div>
          <p
            style={{
              margin: "18px 0 0",
              fontSize: "13px",
              lineHeight: "21px",
              color: "#4B5563",
              maxWidth: "58ch",
            }}
          >
            {vm.rewriteNote}
          </p>
        </div>
      </div>
    </section>
  );
}
