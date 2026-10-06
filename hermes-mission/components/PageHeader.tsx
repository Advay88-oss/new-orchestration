"use client";

import React, { useEffect, useState } from "react";
import type { MissionVM } from "@/lib/viewmodel";
import { brainOf, useTenant } from "@/lib/tenant";
import { IconChevronRight, IconMenu, IconSearch } from "./icons";

/** How fresh the company's brain is, from its last ingest. */
function useKnowledge(tenant: string | undefined) {
  const [last, setLast] = useState<string | null | undefined>(undefined);
  useEffect(() => {
    if (!tenant) return;
    let alive = true;
    setLast(undefined);
    brainOf(tenant).then((d) => { if (alive) setLast(d?.stats?.last_ingest || null); });
    return () => { alive = false; };
  }, [tenant]);
  return last;
}

function knowledgeLabel(iso: string): { fresh: boolean; text: string } {
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return { fresh: false, text: "Knowledge" };
  const hours = (Date.now() - t) / 3_600_000;
  if (hours < 24) return { fresh: true, text: "Knowledge up to date" };
  return { fresh: false, text: "Knowledge from " + new Date(t).toLocaleDateString(undefined, { day: "numeric", month: "short" }) };
}

export function PageHeader({ vm, onSearch, onMenu, title }: {
  vm: MissionVM; onSearch: () => void; onMenu: () => void; title?: string;
}) {
  const [company] = useTenant();
  const last = useKnowledge(company?.id);
  const k = last ? knowledgeLabel(last) : null;
  return (
    <header className="hd-topbar">
      <div className="hd-crumbs">
        <button className="hd-icon-btn mobile-only" onClick={onMenu} aria-label="Open menu" style={{ marginRight: 2 }}><IconMenu /></button>
        <span style={{ whiteSpace: "nowrap" }}>{company?.name || "…"}</span>
        <IconChevronRight size={14} style={{ color: "var(--vn-ink-faint)" }} />
        <b style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{title || vm.pageTitle}</b>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {k && (
          <span className="hd-pill" title={"Last ingest " + new Date(last as string).toLocaleString()}
                style={{ border: "1px solid var(--vn-line)", background: "var(--vn-surface)", color: "var(--vn-ink-body)", padding: "5px 12px", fontSize: 13, whiteSpace: "nowrap" }}>
            <span className="hd-dot" style={{ background: k.fresh ? "var(--vn-ok)" : "var(--vn-warn)" }} />
            <span className="hd-know-text">{k.text}</span>
          </span>
        )}
        <button className="hd-icon-btn" onClick={onSearch} aria-label="Search (Ctrl K)"><IconSearch /></button>
      </div>
    </header>
  );
}
