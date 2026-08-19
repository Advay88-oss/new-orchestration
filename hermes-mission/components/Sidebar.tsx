"use client";

import { HoverButton } from "./Hover";
import type { MissionVM } from "@/lib/viewmodel";

export function Sidebar({ vm }: { vm: MissionVM }) {
  return (
    <aside
      style={{
        width: "236px",
        flex: "0 0 236px",
        background: "#111111",
        display: "flex",
        flexDirection: "column",
        position: "sticky",
        top: 0,
        height: "100vh",
        padding: "24px 16px",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          padding: "0 8px 24px",
        }}
      >
        <div
          style={{
            width: "32px",
            height: "32px",
            borderRadius: "10px",
            backgroundImage: "linear-gradient(135deg, #FC5457 10%, #703AE6 80%)",
            flex: "0 0 32px",
          }}
        />
        <div>
          <div
            style={{
              fontSize: "16px",
              lineHeight: "24px",
              fontWeight: 600,
              color: "#FFFFFF",
              letterSpacing: "-0.01em",
            }}
          >
            Mission Control
          </div>
          <div
            style={{
              fontFamily: "var(--font-jetbrains-mono), monospace",
              fontSize: "10px",
              lineHeight: "15px",
              fontWeight: 500,
              letterSpacing: "0.06em",
              color: "#777777",
              textTransform: "uppercase",
            }}
          >
            7-agent pipeline
          </div>
        </div>
      </div>

      <nav style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {vm.nav.map((n) => (
          <HoverButton
            key={n.id}
            onClick={n.go}
            style={n.style}
            hoverStyle={{ background: "#1E1E1E", color: "#FFFFFF" }}
          >
            <span
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                whiteSpace: "nowrap",
              }}
            >
              <span style={n.dot} />
              {n.label}
            </span>
            <span
              style={{
                fontFamily: "var(--font-jetbrains-mono), monospace",
                fontSize: "10px",
                fontWeight: 500,
                color: "#595959",
              }}
            >
              {n.count}
            </span>
          </HoverButton>
        ))}
      </nav>

      <div
        style={{
          marginTop: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        <div style={{ background: "#1E1E1E", borderRadius: "16px", padding: "16px" }}>
          <div
            style={{
              fontFamily: "var(--font-jetbrains-mono), monospace",
              fontSize: "10px",
              lineHeight: "15px",
              fontWeight: 600,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: "#777777",
            }}
          >
            Source
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              marginTop: "10px",
            }}
          >
            <span
              style={{
                width: "7px",
                height: "7px",
                borderRadius: "999px",
                background: vm.relayDotColor,
                flex: "0 0 7px",
              }}
            />
            <span
              style={{
                fontFamily: "var(--font-jetbrains-mono), monospace",
                fontSize: "12px",
                color: "#DFDFDF",
              }}
            >
              {vm.relayLabel}
            </span>
          </div>
          <div
            style={{
              fontSize: "12px",
              lineHeight: "18px",
              color: "#949494",
              marginTop: "6px",
            }}
          >
            {vm.relayNote}
          </div>
          <HoverButton
            onClick={vm.tryRelay}
            style={{
              marginTop: "10px",
              background: "transparent",
              border: "1px solid #2C2C2C",
              borderRadius: "8px",
              padding: "6px 10px",
              fontSize: "12px",
              fontWeight: 600,
              color: "#BDA4F4",
              cursor: "pointer",
              width: "100%",
            }}
            hoverStyle={{ borderColor: "#703AE6", color: "#FFFFFF" }}
          >
            Retry relay
          </HoverButton>
        </div>

        <div style={{ background: "#1E1E1E", borderRadius: "16px", padding: "16px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div
              style={{
                fontFamily: "var(--font-jetbrains-mono), monospace",
                fontSize: "10px",
                lineHeight: "15px",
                fontWeight: 600,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color: "#777777",
              }}
            >
              Polling
            </div>
            <div
              style={{
                fontFamily: "var(--font-jetbrains-mono), monospace",
                fontSize: "11px",
                color: "#DFDFDF",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {vm.pollStatus}
            </div>
          </div>
          <div style={{ display: "flex", gap: "6px", marginTop: "12px" }}>
            <HoverButton
              onClick={vm.togglePause}
              style={{
                flex: "1 1 auto",
                background: "#2C2C2C",
                border: "none",
                borderRadius: "8px",
                padding: "7px 0",
                fontSize: "12px",
                fontWeight: 600,
                color: "#FFFFFF",
                cursor: "pointer",
              }}
              hoverStyle={{ background: "#703AE6" }}
            >
              {vm.pollButton}
            </HoverButton>
            {vm.intervals.map((iv) => (
              <HoverButton
                key={iv.label}
                onClick={iv.set}
                style={iv.style}
                hoverStyle={{ borderColor: "#703AE6" }}
              >
                {iv.label}
              </HoverButton>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
