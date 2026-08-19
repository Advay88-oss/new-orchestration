"use client";

import { MONO } from "@/lib/colors";
import { StatTile, LABEL_06_949494_9 } from "../StatTile";
import type { MissionVM } from "@/lib/viewmodel";

const TILE = { background: "#F7F7F7", borderRadius: "12px", padding: "12px" } as const;
const TILE_VALUE = {
  fontSize: "16px",
  fontWeight: 500,
  marginTop: "5px",
  fontVariantNumeric: "tabular-nums" as const,
};

export function Agents({ vm }: { vm: MissionVM }) {
  return (
    <section
      style={{
        padding: "24px 32px 80px",
        maxWidth: "1560px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
      }}
    >
      {vm.agentRows.map((a) => (
        <div
          key={a.id}
          style={{
            background: "#FFFFFF",
            border: "1px solid #E5E7EB",
            borderRadius: "20px",
            padding: "22px 26px",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "24px 40px",
            alignItems: "start",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "999px",
                  background: a.statusColor,
                  flex: "0 0 8px",
                }}
              />
              <span
                style={{
                  fontFamily: MONO,
                  fontSize: "14px",
                  fontWeight: 600,
                  color: a.hue,
                  wordBreak: "break-word",
                }}
              >
                {a.id}
              </span>
            </div>
            {a.hasArc && (
              <div
                style={{
                  fontSize: "15px",
                  lineHeight: "24px",
                  marginTop: "12px",
                  color: a.arcColor,
                  fontWeight: 500,
                  fontStyle: "italic",
                  maxWidth: "36ch",
                }}
              >
                {a.arcline}
              </div>
            )}
            <div
              style={{
                fontSize: "13px",
                color: "#777777",
                marginTop: "10px",
                maxWidth: "36ch",
                lineHeight: "20px",
              }}
            >
              {a.role}
            </div>
          </div>
          <div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                flexWrap: "wrap",
              }}
            >
              <span style={a.statusPill}>{a.statusLabel}</span>
              <span style={{ fontSize: "14px", color: "#1F1F1F" }}>{a.working}</span>
            </div>
            <div
              style={{
                fontFamily: MONO,
                fontSize: "12px",
                color: "#777777",
                marginTop: "14px",
                lineHeight: "20px",
                maxWidth: "64ch",
                wordBreak: "break-word",
                background: "#F7F7F7",
                borderRadius: "10px",
                padding: "10px 14px",
              }}
            >
              {a.log}
            </div>
            <div
              style={{
                fontSize: "13px",
                color: "#949494",
                marginTop: "12px",
                maxWidth: "64ch",
                lineHeight: "20px",
              }}
            >
              {a.distinct}
            </div>
          </div>
          <div
            style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px" }}
          >
            <StatTile
              label="Turns"
              value={a.turns}
              container={TILE}
              labelStyle={LABEL_06_949494_9}
              valueStyle={TILE_VALUE}
            />
            <StatTile
              label="Calls"
              value={a.calls}
              container={TILE}
              labelStyle={LABEL_06_949494_9}
              valueStyle={TILE_VALUE}
            />
            <StatTile
              label="Tokens"
              value={a.tokens}
              container={TILE}
              labelStyle={LABEL_06_949494_9}
              valueStyle={TILE_VALUE}
              sub={`${a.cachedPct} cached`}
              subStyle={{ fontSize: "10px", color: "#949494", marginTop: "2px" }}
            />
            <StatTile
              label="Cost"
              value={a.cost}
              container={TILE}
              labelStyle={LABEL_06_949494_9}
              valueStyle={TILE_VALUE}
            />
          </div>
        </div>
      ))}
      <div
        style={{
          fontSize: "12px",
          lineHeight: "18px",
          color: "#949494",
          maxWidth: "88ch",
          marginTop: "4px",
        }}
      >
        Turns and cost are attributed to the run currently open in Run detail (
        {vm.agentScopeLabel}). Status is read from each agent&apos;s process log — an agent with
        no recent line reads <em>idle</em>, never <em>errored</em>.
      </div>
    </section>
  );
}
