"use client";

import React, { useEffect, useRef, useState } from "react";
import type { MissionVM } from "@/lib/viewmodel";
import { useViewer } from "@/lib/useViewer";
import { useTheme } from "@/lib/theme";
import { companyHue, useTenant } from "@/lib/tenant";
import { autopilotSummary, useAutopilot } from "./AutopilotPanel";
import {
  HeraldMark, IconBookmark, IconChat, IconChevronRight, IconChevrons, IconClose, IconCompass, IconEdit,
  IconImage, IconMegaphone, IconMoon, IconPulse, IconSearch, IconShare, IconSun,
} from "./icons";

interface SidebarProps {
  vm: MissionVM;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
  onAutopilot: () => void;
  onSearch: () => void;
  onNewChat: () => void;
}

const SECTIONS: { label: string; items: { id: string; label: string; icon: (p: { size?: number }) => React.ReactElement }[] }[] = [
  { label: "Create", items: [
    { id: "assistant", label: "Assistant", icon: IconChat },
    { id: "runs", label: "Posts", icon: IconImage },
  ] },
  { label: "Research", items: [
    { id: "research", label: "Signals", icon: IconPulse },
    { id: "references", label: "References", icon: IconBookmark },
    { id: "vanna_plays", label: "Inspiration", icon: IconCompass },
    { id: "campaigns", label: "Campaigns", icon: IconMegaphone },
  ] },
];

export function Badge({ id, name, size = 34 }: { id: string; name: string; size?: number }) {
  return (
    <span style={{ width: size, height: size, flex: `0 0 ${size}px`, borderRadius: size > 26 ? 9 : 6, background: companyHue(id),
                   color: "#fff", display: "inline-flex", alignItems: "center", justifyContent: "center",
                   fontSize: size > 26 ? 14 : 11, fontWeight: 600 }}>
      {(name || id || "?").charAt(0).toUpperCase()}
    </span>
  );
}

function OwnerName({ role }: { role: string }) {
  const [name, setName] = useState("");
  const [edit, setEdit] = useState(false);
  useEffect(() => { try { setName(localStorage.getItem("vn_owner_name") || ""); } catch { /* */ } }, []);
  const save = (v: string) => {
    const clean = v.trim().slice(0, 40);
    setName(clean);
    setEdit(false);
    try { if (clean) localStorage.setItem("vn_owner_name", clean); else localStorage.removeItem("vn_owner_name"); } catch { /* */ }
    window.dispatchEvent(new CustomEvent("vn:owner-name", { detail: clean }));
  };
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
      <span style={{ width: 32, height: 32, flex: "0 0 32px", borderRadius: 999, background: "var(--vn-ink)", color: "var(--vn-bg)",
                     display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 600 }}>
        {(name || role || " ").charAt(0).toUpperCase()}
      </span>
      <div style={{ minWidth: 0 }}>
        {edit ? (
          <input autoFocus defaultValue={name} placeholder="Your name" aria-label="Your name"
                 onBlur={(e) => save(e.target.value)}
                 onKeyDown={(e) => { if (e.key === "Enter") save((e.target as HTMLInputElement).value); if (e.key === "Escape") setEdit(false); }}
                 style={{ width: 120, fontSize: 13.5, border: "1px solid var(--vn-line-strong)", borderRadius: 6, padding: "2px 6px", background: "var(--vn-surface)" }} />
        ) : (
          <button onClick={() => setEdit(true)} title="Set your name"
                  style={{ display: "block", border: "none", background: "transparent", padding: 0, fontSize: 14, fontWeight: 550,
                           color: "var(--vn-ink)", cursor: "pointer", textAlign: "left" }}>
            {name || "Add your name"}
          </button>
        )}
        <div style={{ fontSize: 12, color: "var(--vn-ink-muted)", textTransform: "capitalize" }}>{role}</div>
      </div>
    </div>
  );
}

export function Sidebar({ vm, mobileOpen = false, onCloseMobile, onAutopilot, onSearch, onNewChat }: SidebarProps) {
  const viewer = useViewer();
  const [theme, setTheme] = useTheme();
  const [company, companies, pickCompany] = useTenant();
  const [menu, setMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const owner = Boolean(viewer?.owner);
  const role = !viewer ? "" : viewer.client ? "client" : owner ? "owner" : "visitor";
  const { clock, daemon } = useAutopilot(15000, owner);
  const auto = autopilotSummary(clock, daemon);
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const read = () => setDark(theme === "dark" || (theme === "system" && mq.matches));
    read();
    mq.addEventListener("change", read);
    return () => mq.removeEventListener("change", read);
  }, [theme]);

  useEffect(() => {
    if (!menu) return;
    const off = (e: MouseEvent) => { if (!menuRef.current?.contains(e.target as Node)) setMenu(false); };
    window.addEventListener("mousedown", off);
    return () => window.removeEventListener("mousedown", off);
  }, [menu]);

  const shown = new Set(vm.nav.map((n) => n.id));
  const navOf = (id: string) => vm.nav.find((n) => n.id === id);
  const go = (id: string) => { navOf(id)?.go(); onCloseMobile?.(); };

  const content = (
    <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", background: "var(--vn-sunken)", padding: "18px 14px 14px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 6px 16px" }}>
        <a href="/" style={{ display: "flex", alignItems: "center", gap: 10, color: "var(--vn-ink)", textDecoration: "none" }}>
          <HeraldMark size={26} />
          <span style={{ fontSize: 18, fontWeight: 600, letterSpacing: "-0.02em" }}>Herald</span>
        </a>
        {onCloseMobile && (
          <button className="hd-icon-btn mobile-only" onClick={onCloseMobile} aria-label="Close menu"><IconClose /></button>
        )}
      </div>

      {/* Company switcher */}
      <div ref={menuRef} style={{ position: "relative" }}>
        <button onClick={() => companies.length > 1 && setMenu((m) => !m)} aria-haspopup="listbox" aria-expanded={menu}
                style={{ width: "100%", display: "flex", alignItems: "center", gap: 10, padding: "8px 10px", borderRadius: 12,
                         border: "1px solid var(--vn-line)", background: "var(--vn-surface)", boxShadow: "var(--vn-shadow)",
                         cursor: companies.length > 1 ? "pointer" : "default", textAlign: "left" }}>
          {company ? <Badge id={company.id} name={company.name} /> : <span className="vn-skel" style={{ width: 34, height: 34, borderRadius: 9 }} />}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14.5, fontWeight: 600, color: "var(--vn-ink)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {company?.name || "…"}
            </div>
            <div style={{ fontSize: 12, color: "var(--vn-ink-muted)", textTransform: "capitalize" }}>{role}</div>
          </div>
          {companies.length > 1 && <IconChevrons size={16} style={{ color: "var(--vn-ink-muted)" }} />}
        </button>
        {menu && (
          <div role="listbox" className="hd-pop"
               style={{ position: "absolute", top: "calc(100% + 6px)", left: 0, right: 0, zIndex: 50, background: "var(--vn-surface)",
                        border: "1px solid var(--vn-line)", borderRadius: 12, boxShadow: "var(--vn-shadow-lg)", padding: 6 }}>
            {companies.map((c) => (
              <button key={c.id} role="option" aria-selected={c.id === company?.id} className="hd-nav-item"
                      onClick={() => { pickCompany(c.id); setMenu(false); }}
                      style={{ fontWeight: c.id === company?.id ? 600 : 450 }}>
                <Badge id={c.id} name={c.name} size={22} />
                {c.name}
              </button>
            ))}
          </div>
        )}
      </div>

      <nav aria-label="Main" style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 2 }}>
        {shown.has("assistant") && (
          <button className="hd-nav-item" onClick={() => { onNewChat(); onCloseMobile?.(); }}><IconEdit />New chat</button>
        )}
        <button className="hd-nav-item" onClick={() => { onSearch(); onCloseMobile?.(); }}>
          <IconSearch />Search
          <kbd style={{ marginLeft: "auto", fontSize: 11, color: "var(--vn-ink-muted)", background: "var(--vn-surface)" }}>⌘K</kbd>
        </button>
        {SECTIONS.map((sec) => {
          const items = sec.items.filter((it) => shown.has(it.id));
          if (!items.length) return null;
          return (
            <React.Fragment key={sec.label}>
              <div className="hd-section-label">{sec.label}</div>
              {items.map((it) => {
                const n = navOf(it.id)!;
                const Icon = it.icon;
                return (
                  <button key={it.id} className="hd-nav-item" aria-current={n.on ? "page" : undefined} onClick={() => go(it.id)}>
                    <Icon />
                    {it.label}
                    {n.count ? <span style={{ marginLeft: "auto", fontSize: 12.5, color: "var(--vn-ink-muted)", fontVariantNumeric: "tabular-nums" }}>{n.count}</span> : null}
                  </button>
                );
              })}
            </React.Fragment>
          );
        })}
      </nav>

      <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: 6, paddingTop: 16 }}>
        {owner && (
          <button onClick={() => { onAutopilot(); onCloseMobile?.(); }}
                  style={{ display: "flex", alignItems: "center", gap: 10, width: "100%", padding: "11px 12px", borderRadius: 12,
                           border: "1px solid var(--vn-line)", background: "var(--vn-surface)", boxShadow: "var(--vn-shadow)",
                           cursor: "pointer", textAlign: "left" }}>
            <span className="hd-dot" style={{ background: auto.on ? "var(--vn-ok)" : "var(--vn-ink-faint)",
                                              boxShadow: auto.on ? "0 0 0 3px var(--vn-ok-soft)" : "none" }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13.5, fontWeight: 550, color: "var(--vn-ink)" }}>{clock || daemon ? auto.title : "Autopilot"}</div>
              <div style={{ fontSize: 12, color: "var(--vn-ink-muted)" }}>{clock || daemon ? auto.sub : "Checking…"}</div>
            </div>
            <IconChevronRight size={16} style={{ color: "var(--vn-ink-muted)" }} />
          </button>
        )}
        <a className="hd-nav-item" href="/brief" target="_blank" rel="noreferrer" style={{ textDecoration: "none" }}>
          <IconShare />Share page
        </a>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, padding: "8px 4px 0" }}>
          <OwnerName role={role} />
          <div role="radiogroup" aria-label="Theme" style={{ display: "flex", background: "var(--vn-raised)", borderRadius: 9, padding: 3, gap: 2 }}>
            {([["light", IconSun], ["dark", IconMoon]] as const).map(([t, Icon]) => {
              const on = (t === "dark") === dark;
              return (
                <button key={t} role="radio" aria-checked={on} aria-label={t === "light" ? "Light" : "Dark"} onClick={() => setTheme(t)}
                        style={{ width: 30, height: 26, border: "none", borderRadius: 7, display: "inline-flex", alignItems: "center", justifyContent: "center",
                                 background: on ? "var(--vn-surface)" : "transparent", boxShadow: on ? "var(--vn-shadow)" : "none",
                                 color: on ? "var(--vn-ink)" : "var(--vn-ink-muted)", cursor: "pointer" }}>
                  <Icon size={15} />
                </button>
              );
            })}
          </div>
        </div>
        {viewer && !owner && (
          <div style={{ fontSize: 11.5, color: "var(--vn-ink-faint)", padding: "6px 4px 0", lineHeight: 1.45 }}>
            {viewer.previewing ? <>Previewing the visitor view · <a href="?as=owner">back to owner</a></>
              : viewer.client ? <>This link shows {company?.name || viewer.client} only.</>
              : <>View only. You see posts made since your first visit.</>}
          </div>
        )}
        {owner && (
          <div style={{ fontSize: 11.5, color: "var(--vn-ink-faint)", padding: "4px 4px 0" }}>
            <a href="?as=visitor" style={{ color: "var(--vn-ink-faint)", fontWeight: 450 }}>See what visitors see</a>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <>
      <aside className="desktop-sidebar-pin" style={{ background: "var(--vn-sunken)", borderRight: "1px solid var(--vn-line)" }}>
        {content}
      </aside>
      {mobileOpen && (
        <div style={{ position: "fixed", inset: 0, zIndex: 100, display: "flex", background: "var(--vn-overlay)" }} onClick={onCloseMobile}>
          <div style={{ width: 288, maxWidth: "86vw", height: "100dvh", boxShadow: "var(--vn-shadow-lg)" }} onClick={(e) => e.stopPropagation()}>
            {content}
          </div>
        </div>
      )}
    </>
  );
}
