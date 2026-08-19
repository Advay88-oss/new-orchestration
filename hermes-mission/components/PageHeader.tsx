"use client";

import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

export function PageHeader({ vm }: { vm: MissionVM }) {
  return (
    <header
      style={{
        borderBottom: "1px solid #E5E7EB",
        background: "#FFFFFF",
        padding: "24px 32px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "32px",
        position: "sticky",
        top: 0,
        zIndex: 5,
        flexWrap: "wrap",
      }}
    >
      <div style={{ minWidth: "280px", flex: "1 1 380px" }}>
        <h1
          style={{
            margin: 0,
            fontSize: "24px",
            lineHeight: "36px",
            fontWeight: 600,
            letterSpacing: "-0.02em",
            color: "#1F1F1F",
          }}
        >
          {vm.pageTitle}
        </h1>
        <div
          style={{
            fontSize: "14px",
            lineHeight: "21px",
            color: "#4B5563",
            maxWidth: "78ch",
          }}
        >
          {vm.pageSub}
        </div>
      </div>
      <div
        style={{
          flex: "0 0 auto",
          display: "flex",
          alignItems: "center",
          gap: "16px",
          border: "1px solid #E5E7EB",
          borderRadius: "16px",
          padding: "12px 16px",
          marginLeft: "auto",
        }}
      >
        <div>
          <div
            style={{
              fontFamily: MONO,
              fontSize: "10px",
              lineHeight: "15px",
              fontWeight: 600,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "#949494",
              whiteSpace: "nowrap",
            }}
          >
            Spend / cap
          </div>
          <div
            style={{
              fontFamily: MONO,
              fontSize: "18px",
              fontWeight: 500,
              fontVariantNumeric: "tabular-nums",
              marginTop: "4px",
              color: vm.capColor,
              whiteSpace: "nowrap",
            }}
          >
            {vm.spentText}
            <span style={{ color: "#A9A9A9", fontSize: "14px" }}> / {vm.capText}</span>
          </div>
        </div>
        <div style={{ width: "140px" }}>
          <div
            style={{
              height: "6px",
              background: "#F4F4F4",
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
              marginTop: "6px",
              fontSize: "12px",
              lineHeight: "18px",
              color: "#777777",
              textAlign: "right",
            }}
          >
            {vm.capNote}
          </div>
        </div>
      </div>
    </header>
  );
}
