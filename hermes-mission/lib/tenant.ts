"use client";

/**
 * The company the page is working on. The sidebar switcher sets it, the
 * Assistant and the breadcrumb read it. Kept in localStorage under the key the
 * Assistant already used, and announced with a window event so every part of
 * the page follows a switch at once.
 */
import { useCallback, useEffect, useState } from "react";

const KEY = "vn_assistant_tenant";
const EVENT = "vn:tenant";

export type Company = { id: string; name: string };

let listing: Promise<{ tenants: string[]; names: Record<string, string> }> | null = null;
const brains = new Map<string, Promise<any>>();

/** One company's brain summary (/api/gtm/brain), fetched once per page load. */
export function brainOf(tenant: string): Promise<any> {
  if (!brains.has(tenant)) {
    brains.set(tenant, fetch("/api/gtm/brain?tenant=" + encodeURIComponent(tenant), { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null)).catch(() => null));
  }
  return brains.get(tenant)!;
}

function loadCompanies() {
  listing ??= fetch("/api/gtm/brain", { cache: "no-store" })
    .then((r) => r.json())
    .then(async (d) => {
      const tenants: string[] = Array.isArray(d.tenants) ? d.tenants : [];
      const names: Record<string, string> = {};
      if (d.tenant) {
        brains.set(d.tenant, Promise.resolve(d));
        if (d.profile?.company?.name) names[d.tenant] = d.profile.company.name;
      }
      await Promise.all(tenants.filter((t) => !names[t]).map((t) =>
        brainOf(t).then((x) => { if (x?.profile?.company?.name) names[t] = x.profile.company.name; })));
      return { tenants, names };
    })
    .catch(() => ({ tenants: [], names: {} }));
  return listing;
}

export function readTenant(): string {
  try { return localStorage.getItem(KEY) || ""; } catch { return ""; }
}

export function setTenant(t: string) {
  try { localStorage.setItem(KEY, t); } catch { /* private mode */ }
  window.dispatchEvent(new CustomEvent(EVENT, { detail: t }));
}

/** [current company, every company, switch]. */
export function useTenant(): [Company | null, Company[], (t: string) => void] {
  const [all, setAll] = useState<Company[]>([]);
  const [cur, setCur] = useState<string>("");

  useEffect(() => {
    let alive = true;
    loadCompanies().then(({ tenants, names }) => {
      if (!alive) return;
      setAll(tenants.map((t) => ({ id: t, name: names[t] || t.charAt(0).toUpperCase() + t.slice(1) })));
      const saved = readTenant();
      setCur(tenants.includes(saved) ? saved : tenants[0] || "");
    });
    const on = (e: Event) => setCur(String((e as CustomEvent).detail || ""));
    window.addEventListener(EVENT, on);
    return () => { alive = false; window.removeEventListener(EVENT, on); };
  }, []);

  const pick = useCallback((t: string) => { setCur(t); setTenant(t); }, []);
  const company = all.find((c) => c.id === cur) || (cur ? { id: cur, name: cur } : null);
  return [company, all, pick];
}

/** A stable colour per company for its initial badge. */
export function companyHue(id: string): string {
  const hues = ["#2F6B57", "#8A5A2B", "#2E5E8C", "#7A3E6B", "#5B6B2F", "#8C3B3B"];
  let h = 0;
  for (const ch of id) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return id === "vanna" ? hues[0] : hues[h % hues.length];
}
