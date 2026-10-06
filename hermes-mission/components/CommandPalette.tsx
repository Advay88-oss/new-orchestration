"use client";

/**
 * ⌘K: jump to a page, an action, or a post by its line.
 */
import React, { useEffect, useMemo, useRef, useState } from "react";
import type { MissionVM } from "@/lib/viewmodel";
import { IconArrowRight, IconImage, IconSearch } from "./icons";

type Item = { id: string; label: string; hint: string; run: () => void; kind: "page" | "action" | "post" };

const PAGE_LABEL: Record<string, string> = {
  assistant: "Assistant", runs: "Posts", research: "Signals", references: "References",
  vanna_plays: "Inspiration", campaigns: "Campaigns",
};

export function CommandPalette({ vm, onClose, onAutopilot, onNewChat }: {
  vm: MissionVM; onClose: () => void; onAutopilot: () => void; onNewChat: () => void;
}) {
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => { input.current?.focus(); }, []);

  const items = useMemo<Item[]>(() => {
    const pages: Item[] = vm.nav.map((n) => ({ id: "p-" + n.id, label: PAGE_LABEL[n.id] || n.label, hint: "Page", kind: "page", run: n.go }));
    const owner = vm.nav.some((n) => n.id === "assistant");
    const actions: Item[] = owner ? [
      { id: "a-new", label: "New chat", hint: "Action", kind: "action", run: onNewChat },
      { id: "a-auto", label: "Autopilot: what runs on its own", hint: "Action", kind: "action", run: onAutopilot },
      { id: "a-share", label: "Open the share page", hint: "Action", kind: "action", run: () => window.open("/brief", "_blank") },
    ] : [];
    const posts: Item[] = ((vm as any).runRows || []).slice(0, 120).map((r: any) => ({
      id: "r-" + r.key,
      label: String(r.headline || r.label || r.key).replace(/\s*…$/, "").slice(0, 110),
      hint: r.startedLocal || r.key,
      kind: "post" as const,
      run: () => (vm as any).openRun(r.key),
    }));
    return [...pages, ...actions, ...posts];
  }, [vm, onAutopilot, onNewChat]);

  const shown = useMemo(() => {
    const words = q.toLowerCase().split(/\s+/).filter(Boolean);
    const hit = (it: Item) => words.every((w) => (it.label + " " + it.hint).toLowerCase().includes(w));
    const list = words.length ? items.filter(hit) : items.filter((i) => i.kind !== "post").concat(items.filter((i) => i.kind === "post").slice(0, 6));
    return list.slice(0, 40);
  }, [items, q]);

  useEffect(() => { setSel(0); }, [q]);

  const pick = (it?: Item) => { if (!it) return; onClose(); it.run(); };

  return (
    <div onMouseDown={onClose} style={{ position: "fixed", inset: 0, zIndex: 120, background: "var(--vn-overlay)", display: "flex", justifyContent: "center", alignItems: "flex-start", paddingTop: "12vh" }}>
      <div className="hd-pop" role="dialog" aria-label="Search" onMouseDown={(e) => e.stopPropagation()}
           style={{ width: "min(620px, calc(100vw - 32px))", background: "var(--vn-surface)", border: "1px solid var(--vn-line)", borderRadius: 16, boxShadow: "var(--vn-shadow-lg)", overflow: "hidden" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "14px 16px", borderBottom: "1px solid var(--vn-line)" }}>
          <IconSearch style={{ color: "var(--vn-ink-muted)" }} />
          <input ref={input} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search pages, actions and posts"
                 onKeyDown={(e) => {
                   if (e.key === "Escape") onClose();
                   else if (e.key === "ArrowDown") { e.preventDefault(); setSel((s) => Math.min(s + 1, shown.length - 1)); }
                   else if (e.key === "ArrowUp") { e.preventDefault(); setSel((s) => Math.max(s - 1, 0)); }
                   else if (e.key === "Enter") { e.preventDefault(); pick(shown[sel]); }
                 }}
                 style={{ flex: 1, border: "none", outline: "none", background: "transparent", fontSize: 15.5, color: "var(--vn-ink)" }} />
          <kbd>Esc</kbd>
        </div>
        <div style={{ maxHeight: "52vh", overflowY: "auto", padding: 6 }}>
          {shown.length === 0 && <div style={{ padding: "18px 12px", fontSize: 14, color: "var(--vn-ink-muted)" }}>Nothing matches “{q}”.</div>}
          {shown.map((it, i) => (
            <button key={it.id} onMouseEnter={() => setSel(i)} onClick={() => pick(it)}
                    style={{ width: "100%", display: "flex", alignItems: "center", gap: 10, padding: "9px 12px", borderRadius: 10, border: "none",
                             background: i === sel ? "var(--vn-raised)" : "transparent", cursor: "pointer", textAlign: "left", color: "var(--vn-ink)" }}>
              {it.kind === "post" ? <IconImage size={16} style={{ color: "var(--vn-ink-muted)" }} /> : <IconArrowRight size={16} style={{ color: "var(--vn-ink-muted)" }} />}
              <span style={{ flex: 1, fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{it.label}</span>
              <span style={{ fontSize: 12, color: "var(--vn-ink-faint)", whiteSpace: "nowrap" }}>{it.hint}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
