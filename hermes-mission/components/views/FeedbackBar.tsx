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

const DIM = "var(--vn-ink-muted)";
const TONE: Record<string, string> = { approve: "var(--vn-ok)", edit: "var(--vn-ok)", revise: "var(--vn-warn)", kill: "var(--vn-bad)" };
const LABEL: Record<string, string> = { approve: "Approved", edit: "Approved with edits", revise: "Revise", kill: "Killed" };

export function FeedbackBar({ runId, draft }: { runId: string; draft?: string }) {
  const [fb, setFb] = useState<any>(null);
  const [note, setNote] = useState("");
  const [editing, setEditing] = useState(false);
  const [edited, setEdited] = useState(draft ?? "");
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
        body: JSON.stringify({ runId, verdict, note, ...(verdict === "edit" ? { edited } : {}) }),
      });
      const j = await r.json();
      if (!j.success) throw new Error(j.error || `HTTP ${r.status}`);
      setNote("");
      setEditing(false);
      load();
    } catch (e: any) {
      setErr(String(e.message || e));
    } finally {
      setBusy(null);
    }
  };

  const latest = fb?.latest;
  return (
    <div style={{ background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 12, padding: "14px 18px", display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <span style={{ fontFamily: MONO, fontSize: 11, color: "var(--vn-accent-ink)", fontWeight: 700 }}>
          YOUR DECISION · TEACHES THE AGENTS
        </span>
        {latest ? (
          <span style={{ fontFamily: MONO, fontSize: 11, color: TONE[latest.verdict], border: `1px solid color-mix(in srgb, ${TONE[latest.verdict]} 33%, transparent)`, borderRadius: 6, padding: "2px 8px", fontWeight: 700 }}>
            {LABEL[latest.verdict].toUpperCase()} · {latest.source} · {new Date(latest.at).toLocaleString()}
          </span>
        ) : (
          <span style={{ fontFamily: MONO, fontSize: 11, color: DIM }}>no decision yet</span>
        )}
      </div>
      {latest?.note && (
        <div style={{ fontSize: 13, color: "var(--vn-ink-body)" }}>Note: {latest.note}</div>
      )}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="What worked or what should change (optional; used for learning)"
          style={{ flex: "1 1 260px", minWidth: 0, background: "var(--vn-sunken)", color: "var(--vn-ink)", border: "1px solid var(--vn-line-strong)", borderRadius: 8, padding: "8px 10px", fontSize: 13 }}
        />
        {(["approve", "revise", "kill"] as const).map((v) => (
          <button
            key={v}
            disabled={busy !== null}
            onClick={() => send(v)}
            style={{ background: `color-mix(in srgb, ${TONE[v]} 10%, transparent)`, border: `1px solid color-mix(in srgb, ${TONE[v]} 53%, transparent)`, color: TONE[v], borderRadius: 8, padding: "8px 14px", fontFamily: MONO, fontSize: 12, fontWeight: 700, cursor: busy ? "wait" : "pointer" }}
          >
            {busy === v ? "…" : v === "approve" ? "Approve" : v === "revise" ? "Revise" : "Kill"}
          </button>
        ))}
        {draft && (
          <button
            disabled={busy !== null}
            onClick={() => { setEdited(draft); setEditing((x) => !x); }}
            style={{ background: "transparent", border: `1px solid color-mix(in srgb, ${TONE.edit} 53%, transparent)`, color: TONE.edit, borderRadius: 8, padding: "8px 14px", fontFamily: MONO, fontSize: 12, fontWeight: 700, cursor: "pointer" }}
          >
            {editing ? "Close editor" : "Edit & approve"}
          </button>
        )}
      </div>
      {editing && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <textarea
            value={edited}
            onChange={(e) => setEdited(e.target.value)}
            style={{ minHeight: 180, background: "var(--vn-sunken)", color: "var(--vn-ink)", border: "1px solid var(--vn-line-strong)", borderRadius: 8, padding: 10, fontSize: 13, lineHeight: 1.5, fontFamily: "inherit" }}
          />
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button
              disabled={busy !== null || !edited.trim() || edited.trim() === (draft ?? "").trim()}
              onClick={() => send("edit")}
              style={{ background: `color-mix(in srgb, ${TONE.edit} 10%, transparent)`, border: `1px solid ${TONE.edit}`, color: TONE.edit, borderRadius: 8, padding: "8px 14px", fontFamily: MONO, fontSize: 12, fontWeight: 700, cursor: "pointer" }}
            >
              {busy === "edit" ? "…" : "Approve my edit"}
            </button>
            <span style={{ fontSize: 11, color: DIM }}>
              Your version is recorded as the approved one, and draft vs edit is kept as a preference example.
            </span>
          </div>
        </div>
      )}
      {latest && (latest.verdict === "approve" || latest.verdict === "edit") && <Posted runId={runId} />}
      <div style={{ fontSize: 11, color: DIM }}>
        Recording a decision never publishes. {fb?.history?.length > 1 && `${fb.history.length} decisions recorded on this run.`}
      </div>
      {err && <div style={{ fontSize: 12, color: "var(--vn-bad)" }}>{err}</div>}
    </div>
  );
}

/** After approval: where the founder posted it, so its engagement is read back. */
function Posted({ runId }: { runId: string }) {
  const [rec, setRec] = useState<any>(null);
  const [url, setUrl] = useState("");
  const [fmt, setFmt] = useState("auto");
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    fetch("/api/gtm/learning?published=" + encodeURIComponent(runId), { cache: "no-store" })
      .then((r) => r.json()).then((j) => setRec(j && j.url ? j : null)).catch(() => {});
  }, [runId]);
  useEffect(() => { load(); }, [load]);

  const save = async () => {
    setMsg(null);
    const r = await (await fetch("/api/gtm/learning", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "published", runId, url: url.trim(), format: fmt }),
    })).json();
    if (r.ok) { setUrl(""); load(); } else setMsg(r.error || "could not record it");
  };

  if (rec) {
    const reading = (rec.readings || []).slice(-1)[0];
    return (
      <div style={{ fontSize: 12.5, color: "var(--vn-ink-body)" }}>
        Posted: <a href={rec.url} target="_blank" rel="noopener noreferrer">{rec.url}</a>
        {rec.format ? " · " + rec.format : ""}
        {reading
          ? " · read at " + Math.round(reading.age_h) + "h: " + (reading.impressions ?? "?") + " impressions, "
            + (reading.likes ?? 0) + " likes, " + (reading.reposts ?? 0) + " reposts"
          : " · engagement is read 48 hours after it was recorded"}
      </div>
    );
  }
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
      <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="Posted it? Paste the X link"
             style={{ flex: "1 1 260px", minWidth: 0, background: "var(--vn-sunken)", color: "var(--vn-ink)",
                      border: "1px solid var(--vn-line-strong)", borderRadius: 8, padding: "8px 10px", fontSize: 13 }} />
      <select value={fmt} onChange={(e) => setFmt(e.target.value)}
              style={{ background: "var(--vn-sunken)", color: "var(--vn-ink)", border: "1px solid var(--vn-line-strong)",
                       borderRadius: 8, padding: "8px 10px", fontSize: 13 }}>
        <option value="auto">format: from the post</option>
        <option value="image">image</option>
        <option value="video">video</option>
        <option value="thread">thread</option>
        <option value="text">text only</option>
      </select>
      <button onClick={save} disabled={!/status\/\d+/.test(url)}
              style={{ background: "var(--vn-cta)", color: "var(--vn-on-accent)", border: "none", borderRadius: 6,
                       padding: "8px 14px", fontSize: 12.5, cursor: "pointer" }}>
        Record post
      </button>
      {msg && <span style={{ fontSize: 12, color: "var(--vn-bad)" }}>{msg}</span>}
    </div>
  );
}
