"use client";

import type { MissionVM } from "@/lib/viewmodel";

export function PageHeader({ vm }: { vm: MissionVM }) {
  return (
    <header
      className="app-header"
      style={{
        borderBottom: "1px solid var(--vn-line)",
        background: "var(--vn-header-bg)",
        padding: "24px 0 20px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "24px",
        position: "sticky",
        top: 0,
        zIndex: 5,
        flexWrap: "wrap",
        backdropFilter: "blur(12px)",
      }}
    >
      <div style={{ minWidth: "260px", flex: "1 1 360px" }}>
        <h1
          style={{
            margin: 0,
            fontSize: "30px",
            lineHeight: "36px",
            fontWeight: 400,
            letterSpacing: "-0.02em",
            color: "var(--vn-ink)",
          }}
        >
          {vm.pageTitle}
        </h1>
        <div
          style={{
            fontSize: "13px",
            lineHeight: "20px",
            color: "var(--vn-ink-muted)",
            maxWidth: "78ch",
            marginTop: "2px",
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
          marginLeft: "auto",
        }}
      >
        {/* The Session Spend / Cap card lived here. Every model that runs
            is unpriced, so it could only ever read "unpriced / $10.00" on
            every page. Usage that IS measured — calls and tokens — is on
            each row of the agent history, beside the run that spent it. */}
      </div>
    </header>
  );
}
