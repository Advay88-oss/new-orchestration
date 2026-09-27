"use client";

/**
 * The page a client opens from an invite: connect their Notion so the agents
 * write from their latest facts. No login — the invite names the company,
 * expires in 7 days and works once (pipeline/brand_brain/notion_oauth.py).
 */
import React, { useEffect, useState } from "react";

type State =
  | { kind: "loading" }
  | { kind: "ready"; company: string; configured: boolean }
  | { kind: "done"; company: string }
  | { kind: "error"; message: string };

export default function ConnectNotion() {
  const [st, setSt] = useState<State>({ kind: "loading" });
  const [invite, setInvite] = useState("");

  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    if (q.get("done")) return setSt({ kind: "done", company: q.get("company") || "" });
    if (q.get("error")) return setSt({ kind: "error", message: q.get("error") || "" });
    const inv = q.get("invite") || "";
    setInvite(inv);
    if (!inv) return setSt({ kind: "error", message: "This page needs an invite link." });
    fetch("/api/connect/notion/check", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ invite: inv }),
    })
      .then((r) => r.json())
      .then((d) => setSt(d.ok ? { kind: "ready", company: d.company, configured: d.configured }
                               : { kind: "error", message: d.error || "This invite link is not valid." }))
      .catch(() => setSt({ kind: "error", message: "Could not reach the dashboard. Try again in a minute." }));
  }, []);

  return (
    <main style={{ minHeight: "100dvh", display: "flex", alignItems: "center", justifyContent: "center",
                   padding: "48px 16px", background: "var(--vn-bg)" }}>
      <div className="vanna-card" style={{ width: "100%", maxWidth: 520, padding: 36 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 28 }}>
          <span style={{ width: 28, height: 28, borderRadius: 6, background: "var(--vn-cta)", color: "var(--vn-on-accent)",
                         display: "flex", alignItems: "center", justifyContent: "center",
                         fontFamily: "var(--font-display)", fontSize: 18 }}>V</span>
          <span style={{ fontSize: 14, fontWeight: 600 }}>Mission Control</span>
        </div>

        {st.kind === "loading" && <p style={{ color: "var(--vn-ink-muted)" }}>Checking your invite…</p>}

        {st.kind === "ready" && (
          <>
            <h1 style={{ marginBottom: 12 }}>Connect {st.company}&rsquo;s Notion</h1>
            <p>
              The content agents write from what your company has written down. Connecting Notion lets them read
              the pages you choose, so posts use your latest launches, figures and wording.
            </p>
            <ul style={{ color: "var(--vn-ink-body)", fontSize: 14, lineHeight: 1.7, paddingLeft: 18, margin: "8px 0 24px" }}>
              <li>You pick the pages on Notion&rsquo;s own screen. Nothing else is shared.</li>
              <li>Read only: nothing is ever written to your Notion.</li>
              <li>You can remove access any time from Notion&rsquo;s Connections settings.</li>
            </ul>
            {st.configured ? (
              <a href={"/api/connect/notion/start?invite=" + encodeURIComponent(invite)}
                 style={{ display: "inline-block", background: "var(--vn-cta)", color: "var(--vn-on-accent)",
                          borderRadius: 6, padding: "11px 20px", fontSize: 14, fontWeight: 500, textDecoration: "none" }}>
                Connect Notion
              </a>
            ) : (
              <p style={{ color: "var(--vn-warn)" }}>Notion connections are not switched on yet. Please check back soon.</p>
            )}
          </>
        )}

        {st.kind === "done" && (
          <>
            <h1 style={{ marginBottom: 12 }}>Notion is connected</h1>
            <p>
              Thank you{st.company ? ", " + st.company : ""}. The pages you shared will be read at the next content run,
              and changes you make in Notion reach the agents from then on. You can close this page.
            </p>
          </>
        )}

        {st.kind === "error" && (
          <>
            <h1 style={{ marginBottom: 12 }}>This link didn&rsquo;t work</h1>
            <p>{st.message}</p>
            <p style={{ fontSize: 13, color: "var(--vn-ink-muted)" }}>Ask the person who sent it for a new invite.</p>
          </>
        )}
      </div>
    </main>
  );
}
