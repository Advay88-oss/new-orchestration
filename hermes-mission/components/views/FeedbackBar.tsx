"use client";

/**
 * The founder's decision on a run — the learning loop's reward.
 *
 * Approve / Revise / Kill write to `feedback.json` and the ledger through the
 * same recorder the Telegram listener uses. Nothing here publishes: approve
 * records that the run was good, it does not send it anywhere.
 */

import React, { useCallback, useEffect, useState } from "react";
import { MONO } from "@/lib/colors";

const DIM = "#7B7590";
const TONE: Record<string, string> = { approve: "#4ADE9B", revise: "#F5A524", kill: "#F0666B" };
const LABEL: Record<string, string> = { approve: "Approved", revise: "Revise", kill: "Killed" };

export function FeedbackBar({ runId }: { runId: string }) {
  const [fb, setFb] = useState<any>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!/^GTM-/.test(runId)) return;
    fetch(`/api/gtm/feedback?runId=${encodeURIComponent(runId)}`, { cache: "no-store" })
      .then((r) => r.json())
      .then((j) => setFb(j.feedback ?? null))
      .catch(() => {});
  }, [runId]);

  useEffect(() => { load(); }, [load]);

  if (!/^GTM-/.test(runId)) return null;

  const send = async (verdict: string) => {
    setBusy(verdict);
    setErr(null);
    try {
      const r = await fetch("/api/gtm/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ runId, verdict, note }),
      });
      const j = await r.json();
      if (!j.success) throw new Error(j.error || `HTTP ${r.status}`);
      setNote("");
      load();
    } catch (e: any) {
      setErr(String(e.message || e));
    } finally {
      setBusy(null);
    }
  };

  const latest = fb?.latest;
  return (
    <div style={{ background: "#0C0716", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, padding: "14px 18px", display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <span style={{ fontFamily: MONO, fontSize: 11, color: "#A98CFF", fontWeight: 700 }}>
          YOUR DECISION · TEACHES THE AGENTS
        </span>
        {latest ? (
          <span style={{ fontFamily: MONO, fontSize: 11, color: TONE[latest.verdict], border: `1px solid ${TONE[latest.verdict]}55`, borderRadius: 6, padding: "2px 8px", fontWeight: 700 }}>
            {LABEL[latest.verdict].toUpperCase()} · {latest.source} · {new Date(latest.at).toLocaleString()}
          </span>
        ) : (
          <span style={{ fontFamily: MONO, fontSize: 11, color: DIM }}>no decision yet</span>
        )}
      </div>
      {latest?.note && (
        <div style={{ fontSize: 13, color: "#CFC8E0" }}>Note: {latest.note}</div>
      )}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="What worked or what should change (optional; used for learning)"
          style={{ flex: "1 1 260px", minWidth: 0, background: "#080310", color: "#FFFFFF", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, padding: "8px 10px", fontSize: 13 }}
        />
        {(["approve", "revise", "kill"] as const).map((v) => (
          <button
            key={v}
            disabled={busy !== null}
            onClick={() => send(v)}
            style={{ background: `${TONE[v]}1A`, border: `1px solid ${TONE[v]}88`, color: TONE[v], borderRadius: 8, padding: "8px 14px", fontFamily: MONO, fontSize: 12, fontWeight: 700, cursor: busy ? "wait" : "pointer" }}
          >
            {busy === v ? "…" : v === "approve" ? "✓ Approve" : v === "revise" ? "✎ Revise" : "✕ Kill"}
          </button>
        ))}
      </div>
      <div style={{ fontSize: 11, color: DIM }}>
        Recording a decision never publishes. {fb?.history?.length > 1 && `${fb.history.length} decisions recorded on this run.`}
      </div>
      {err && <div style={{ fontSize: 12, color: "#F0666B" }}>{err}</div>}
    </div>
  );
}
