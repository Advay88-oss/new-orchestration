"use client";

/**
 * Which company a run, idea or reference belongs to. The engine serves more
 * than one tenant (Vanna, Morpho, ...) and every view listed their work mixed
 * together. The tone is picked from the name, so each company keeps one
 * colour everywhere.
 */
import React from "react";
import { MONO } from "@/lib/colors";

const TONES = ["var(--vn-accent-ink)", "var(--vn-ok)", "var(--vn-warn)", "var(--vn-info, #3b82f6)", "var(--vn-bad)"];

export function companyName(t: string | null | undefined): string {
  const s = String(t || "").trim();
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : "—";
}

export function companyTone(t: string | null | undefined): string {
  const s = String(t || "").toLowerCase();
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return TONES[h % TONES.length];
}

export function CompanyChip({ company, size = "sm" }: { company?: string | null; size?: "sm" | "md" }) {
  if (!company) return null;
  const tone = companyTone(company);
  return (
    <span
      title={"Company: " + companyName(company)}
      style={{
        display: "inline-flex", alignItems: "center", gap: 5, whiteSpace: "nowrap",
        fontFamily: MONO, fontSize: size === "md" ? 11.5 : 10.5, fontWeight: 700, letterSpacing: 0.4,
        color: tone, border: "1px solid color-mix(in srgb, " + tone + " 40%, transparent)",
        background: "color-mix(in srgb, " + tone + " 10%, transparent)",
        borderRadius: 999, padding: size === "md" ? "3px 10px" : "1px 8px",
      }}
    >
      <span style={{ width: 6, height: 6, borderRadius: 999, background: tone }} />
      {companyName(company).toUpperCase()}
    </span>
  );
}

/** A row of filter pills, one per company present, plus "All". */
export function CompanyFilter({ companies, value, onChange }: {
  companies: string[]; value: string; onChange: (v: string) => void;
}) {
  const list = [...new Set(companies.filter(Boolean))].sort();
  if (list.length < 2) return null;
  const pill = (id: string, label: React.ReactNode) => {
    const on = value === id;
    return (
      <button key={id} onClick={() => onChange(id)}
        style={{
          background: on ? "var(--vn-accent-soft)" : "var(--vn-hover)",
          border: "1px solid " + (on ? "var(--vn-accent)" : "var(--vn-line-strong)"),
          color: on ? "var(--vn-ink)" : "var(--vn-ink-muted)", padding: "5px 11px", borderRadius: 8,
          cursor: "pointer", fontFamily: MONO, fontSize: 11.5, fontWeight: 600,
        }}>
        {label}
      </button>
    );
  };
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
      <span style={{ fontFamily: MONO, fontSize: 10.5, color: "var(--vn-ink-faint)", marginRight: 2 }}>COMPANY</span>
      {pill("all", "All")}
      {list.map((c) => pill(c, companyName(c)))}
    </div>
  );
}
