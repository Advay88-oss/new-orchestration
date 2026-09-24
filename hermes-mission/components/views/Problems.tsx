"use client";

/**
 * What has been going wrong, grouped by kind.
 *
 * Every agent already recorded its own failures with a reason. Nothing ever
 * put those reasons side by side, so a fault firing in four different agents
 * read as four unrelated bugs — and got fixed four separate times. The family
 * is the top level here for exactly that reason; the per-agent signature sits
 * underneath it, where it belongs.
 */

import React, { useEffect, useState } from "react";
import { MONO } from "@/lib/colors";
import type { MissionVM } from "@/lib/viewmodel";

type Problem = {
  agent: string;
  status: "degraded" | "failed";
  family: string;
  signature: string;
  count: number;
  runs: string[];
  lastSeen: string | null;
  sample: string;
};

export function Problems({ vm }: { vm: MissionVM }) {
  const [data, setData] = useState<{
    scanned: number;
    problems: Problem[];
    runsAffected: number;
    cleanRuns: number;
  } | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [onlyFailed, setOnlyFailed] = useState(false);

  useEffect(() => {
    const load = () =>
      fetch("/api/gtm/problems?limit=80", { cache: "no-store" })
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error("HTTP " + r.status))))
        .then((d) => {
          if (d.success === false) throw new Error(d.error || "unknown error");
          setData(d);
          setErr(null);
        })
        .catch((e) => setErr(String(e.message ?? e)));
    load();
    const t = setInterval(load, 20000);
    return () => clearInterval(t);
  }, []);

  if (err) {
    return (
      <section className="vanna-section">
        <div className="vanna-card" style={{ color: "var(--vn-bad)" }}>
          Could not read the stage journals: {err}
        </div>
      </section>
    );
  }
  if (!data) {
    return (
      <section className="vanna-section">
        <div className="vanna-card" style={{ color: "var(--vn-ink-muted)" }}>
          Reading stage journals…
        </div>
      </section>
    );
  }

  const shown = onlyFailed
    ? data.problems.filter((p) => p.status === "failed")
    : data.problems;

  // Family first. Ordered by how many occurrences it accounts for, not
  // alphabetically — the point of the page is what to fix next.
  const families = new Map<string, Problem[]>();
  for (const p of shown) {
    const arr = families.get(p.family) ?? [];
    arr.push(p);
    families.set(p.family, arr);
  }
  const ordered = [...families.entries()].sort(
    (a, b) =>
      b[1].reduce((n, p) => n + p.count, 0) - a[1].reduce((n, p) => n + p.count, 0),
  );

  const total = shown.reduce((n, p) => n + p.count, 0);

  return (
    <section className="vanna-section">
      <div className="vanna-banner">
        <div style={{ display: "flex", alignItems: "center", gap: "32px", flexWrap: "wrap" }}>
          <Stat label="Runs scanned" value={String(data.scanned)} />
          <Stat label="Clean" value={String(data.cleanRuns)}
                color={data.cleanRuns > 0 ? "#4ADE9B" : undefined} />
          <Stat label="With problems" value={String(data.runsAffected)}
                color={data.runsAffected > 0 ? "#E8B34C" : undefined} />
          <Stat label="Occurrences" value={String(total)} />
        </div>
        <button
          onClick={() => setOnlyFailed((v) => !v)}
          style={{
            background: onlyFailed ? "rgba(255,255,255,0.07)" : "transparent",
            border: "1px solid " + (onlyFailed ? "var(--vn-line-strong)" : "var(--vn-line)"),
            color: onlyFailed ? "var(--vn-ink)" : "var(--vn-ink-muted)",
            borderRadius: "8px", padding: "7px 14px", fontSize: "12px",
            fontWeight: 500, cursor: "pointer",
          }}
        >
          Failures only
        </button>
      </div>

      {ordered.length === 0 && (
        <div className="vanna-card" style={{ color: "var(--vn-ink-muted)" }}>
          Nothing recorded a problem across the last {data.scanned} runs.
        </div>
      )}

      {ordered.map(([fam, list]) => {
        const occurrences = list.reduce((n, p) => n + p.count, 0);
        const agents = new Set(list.map((p) => p.agent));
        const worst = list.some((p) => p.status === "failed");
        return (
          <div key={fam} className="vanna-card" style={{ padding: 0, overflow: "hidden" }}>
            <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--vn-line)" }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: "12px", flexWrap: "wrap" }}>
                <span style={{
                  fontFamily: MONO, fontSize: "22px", fontWeight: 600,
                  letterSpacing: "-0.02em",
                  color: worst ? "var(--vn-bad)" : "var(--vn-warn)",
                }}>
                  {occurrences}
                </span>
                <span style={{ fontSize: "15px", fontWeight: 600, color: "var(--vn-ink)" }}>
                  {fam}
                </span>
              </div>
              {/* The count of distinct agents is the whole reason this page
                  exists: one fault in four agents is one bug, not four. */}
              <div style={{ fontSize: "12px", color: "var(--vn-ink-muted)", marginTop: "5px" }}>
                across {agents.size} agent{agents.size === 1 ? "" : "s"}
                {agents.size > 1 ? " — " + [...agents].join(", ") : ""}
              </div>
            </div>

            {list
              .sort((a, b) => b.count - a.count)
              .map((p) => {
                const key = p.agent + p.signature;
                const isOpen = !!open[key];
                return (
                  <div key={key} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                    <button
                      onClick={() => setOpen((o) => ({ ...o, [key]: !o[key] }))}
                      style={{
                        width: "100%", textAlign: "left", background: "transparent",
                        border: "none", cursor: "pointer", padding: "14px 22px",
                        display: "flex", gap: "14px", alignItems: "flex-start",
                      }}
                    >
                      <span style={{
                        flex: "0 0 auto", fontFamily: MONO, fontSize: "11px",
                        fontWeight: 600, padding: "3px 8px", borderRadius: "5px",
                        color: p.status === "failed" ? "var(--vn-bad)" : "var(--vn-warn)",
                        background: p.status === "failed"
                          ? "rgba(240,102,107,0.12)" : "rgba(232,179,76,0.12)",
                      }}>
                        {p.status}
                      </span>
                      <span style={{ flex: "1 1 auto", minWidth: 0 }}>
                        <span style={{ display: "block", fontSize: "13px", color: "var(--vn-ink-body)" }}>
                          {p.signature}
                        </span>
                        <span style={{ display: "block", fontFamily: MONO, fontSize: "11px",
                                       color: "var(--vn-ink-faint)", marginTop: "4px" }}>
                          {p.agent}
                          {p.lastSeen ? " · last " + new Date(p.lastSeen).toLocaleString() : ""}
                        </span>
                      </span>
                      <span style={{ flex: "0 0 auto", fontFamily: MONO, fontSize: "13px",
                                     color: "var(--vn-ink-muted)" }}>
                        x{p.count}
                      </span>
                    </button>

                    {isOpen && (
                      <div style={{ padding: "0 22px 18px 22px" }}>
                        <div style={{
                          background: "var(--vn-sunken)", border: "1px solid var(--vn-line)",
                          borderRadius: "8px", padding: "12px 14px", fontFamily: MONO,
                          fontSize: "11.5px", color: "var(--vn-ink-body)",
                          whiteSpace: "pre-wrap", wordBreak: "break-word",
                        }}>
                          {p.sample || "no detail recorded"}
                        </div>
                        <div style={{ marginTop: "10px", display: "flex", gap: "8px",
                                      flexWrap: "wrap", alignItems: "center" }}>
                          <span style={{ fontSize: "11px", color: "var(--vn-ink-faint)" }}>
                            seen in
                          </span>
                          {p.runs.map((rid) => (
                            <button
                              key={rid}
                              onClick={() => vm.openRun(rid)}
                              style={{
                                background: "transparent", border: "1px solid var(--vn-line)",
                                borderRadius: "6px", padding: "3px 8px", cursor: "pointer",
                                fontFamily: MONO, fontSize: "11px",
                                color: "var(--vn-accent-light)",
                              }}
                            >
                              {rid}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
          </div>
        );
      })}
    </section>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div style={{ fontSize: "11px", color: "var(--vn-ink-faint)" }}>{label}</div>
      <div style={{
        fontFamily: MONO, fontSize: "27px", fontWeight: 600,
        letterSpacing: "-0.02em", color: color ?? "var(--vn-ink)",
      }}>
        {value}
      </div>
    </div>
  );
}
