"use client";

import React from "react";
import { HoverButton } from "./Hover";
import type { MissionVM } from "@/lib/viewmodel";

interface SidebarProps {
  vm: MissionVM;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export function Sidebar({ vm, mobileOpen = false, onCloseMobile }: SidebarProps) {
  const sidebarContent = (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        background: "#0C0716",
        padding: "24px 16px",
      }}
    >
      <div>
        {/* Brand Lockup */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 8px 24px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "10px",
                backgroundImage: "linear-gradient(135deg, #FC5457 10%, #703AE6 80%)",
                flex: "0 0 32px",
                boxShadow: "0 4px 12px rgba(112, 58, 230, 0.4)"
              }}
            />
            <div>
              <div
                style={{
                  fontSize: "16px",
                  lineHeight: "22px",
                  fontWeight: 700,
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
                  lineHeight: "14px",
                  fontWeight: 600,
                  letterSpacing: "0.06em",
                  color: "#38EF7D",
                  textTransform: "uppercase",
                }}
              >
                System 2: 13-Agent GTM OS
              </div>
            </div>
          </div>

          {/* Mobile Close Button */}
          {onCloseMobile && (
            <button
              onClick={onCloseMobile}
              className="mobile-only"
              style={{
                background: "rgba(255,255,255,0.08)",
                border: "none",
                color: "#FFFFFF",
                borderRadius: "8px",
                padding: "6px 10px",
                fontSize: "14px",
                cursor: "pointer",
              }}
            >
              ✕
            </button>
          )}
        </div>

        {/* Navigation List */}
        <nav style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          {vm.nav.map((n) => (
            <HoverButton
              key={n.id}
              onClick={() => {
                n.go();
                if (onCloseMobile) onCloseMobile();
              }}
              style={n.style}
              hoverStyle={{ background: "#1E1E28", color: "#FFFFFF" }}
            >
              <span style={{ display: "flex", alignItems: "center", gap: "10px", whiteSpace: "nowrap" }}>
                <span style={n.dot} />
                {n.label}
              </span>
              <span
                style={{
                  fontFamily: "var(--font-jetbrains-mono), monospace",
                  fontSize: "10px",
                  fontWeight: 500,
                  color: "#7E7598",
                }}
              >
                {n.count}
              </span>
            </HoverButton>
          ))}
        </nav>
      </div>

      {/* Footer Info Cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "auto", paddingTop: "20px" }}>
        <div style={{ background: "#130B22", borderRadius: "12px", padding: "14px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
          <div style={{ fontFamily: "var(--font-jetbrains-mono), monospace", fontSize: "10px", fontWeight: 700, color: "#8E85A8", textTransform: "uppercase" }}>
            AUTONOMOUS DAEMON
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "6px" }}>
            <span style={{ width: "7px", height: "7px", borderRadius: "999px", background: "#38EF7D" }} />
            <span style={{ fontSize: "12px", fontWeight: 600, color: "#FFFFFF" }}>Active · 30m cycle</span>
          </div>
        </div>

        <div style={{ background: "#130B22", borderRadius: "12px", padding: "14px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontFamily: "var(--font-jetbrains-mono), monospace", fontSize: "10px", color: "#8E85A8" }}>SPEND CAP</span>
            <span style={{ fontFamily: "var(--font-jetbrains-mono), monospace", fontSize: "11px", color: "#38EF7D", fontWeight: 700 }}>
              {vm.spentText} / {vm.capText}
            </span>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Pinned Sidebar */}
      <aside
        className="desktop-sidebar-pin"
        style={{
          width: "240px",
          flex: "0 0 240px",
          background: "#0C0716",
          borderRight: "1px solid rgba(255, 255, 255, 0.08)",
          position: "sticky",
          top: 0,
          height: "100vh",
        }}
      >
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 100,
            display: "flex",
            background: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(8px)",
          }}
          onClick={onCloseMobile}
        >
          <div
            style={{
              width: "280px",
              maxWidth: "80vw",
              height: "100vh",
              boxShadow: "0 0 40px rgba(0,0,0,0.9)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
