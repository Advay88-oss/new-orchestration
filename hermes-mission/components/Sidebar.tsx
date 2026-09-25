"use client";

import React from "react";
import { HoverButton } from "./Hover";
import type { MissionVM } from "@/lib/viewmodel";
import { AGENT_COUNT } from "@/lib/agents";

interface SidebarProps {
  vm: MissionVM;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export function Sidebar({ vm, mobileOpen = false, onCloseMobile }: SidebarProps) {
  // null while unknown, so the rail says "checking…" rather than asserting
  // either state before it has an answer.
  const [daemon, setDaemon] = React.useState<boolean | null>(null);
  React.useEffect(() => {
    const check = () =>
      fetch("/api/daemon", { cache: "no-store" })
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
        .then((d) => setDaemon(Boolean(d.running)))
        // A 501 is the deployed dashboard saying the pipeline is not here,
        // which is a real "not running" from this page's point of view.
        .catch(() => setDaemon(false));
    check();
    const t = setInterval(check, 15000);
    return () => clearInterval(t);
  }, []);

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
                background: "#703AE6",
                flex: "0 0 32px",
                }}
            />
            <div>
              <div
                style={{
                  fontSize: "16px",
                  lineHeight: "22px",
                  fontWeight: 600,
                  color: "var(--vn-ink)",
                  letterSpacing: "-0.01em",
                }}
              >
                Mission Control
              </div>
              {/* Was mono, uppercase, letter-spaced and terminal green —
                  four devices on a six-word subtitle, under a heading that
                  needed none of them. "System 2" also named nothing a reader
                  of this page can see. */}
              <div
                style={{
                  fontSize: "11px",
                  lineHeight: "16px",
                  fontWeight: 500,
                  color: "var(--vn-ink-faint)",
                }}
              >
                {AGENT_COUNT}-agent GTM OS
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
          <div style={{ fontFamily: "var(--font-jetbrains-mono), monospace", fontSize: "10px", fontWeight: 700, color: "#7B7590", textTransform: "uppercase" }}>
            AUTONOMOUS DAEMON
          </div>
          {/* Checked, not asserted. This was a green dot and the literal
              "Active · 30m cycle" on every page — while no scheduled task
              existed and nothing had ticked the scheduler in 17 hours. The
              Runs view already polls /api/daemon; the rail now does too. */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "6px" }}>
            <span style={{ width: "7px", height: "7px", borderRadius: "999px",
                           background: daemon ? "#4ADE9B" : "#7B7590" }} />
            <span style={{ fontSize: "12px", fontWeight: 600,
                           color: daemon ? "#FFFFFF" : "#7B7590" }}>
              {daemon === null ? "checking…" : daemon ? "Active · 30m cycle" : "Not scheduled"}
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
        // Geometry lives in globals.css so the fixed rail and the matching
        // gutter on <main> are declared together and cannot drift apart.
        //
        // Sticky was wrong twice over: sticky only on the vertical axis let
        // the rail slide off the left edge whenever the page scrolled
        // sideways, and making it sticky horizontally instead parked it on
        // top of the content. Fixed + a reserved gutter makes overlap
        // structurally impossible, whatever the scroll position.
        style={{
          background: "#0C0716",
          borderRight: "1px solid rgba(255, 255, 255, 0.08)",
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
