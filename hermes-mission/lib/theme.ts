"use client";

/**
 * Light / dark / system. The choice is a per-browser convenience kept in
 * localStorage; "system" follows the OS (the CSS media query in
 * globals.css). app/layout.tsx applies a saved choice before first paint, so
 * a reload never flashes the other theme.
 */
import { useCallback, useEffect, useState } from "react";

export type Theme = "system" | "light" | "dark";
const KEY = "vn_theme";

export function applyTheme(t: Theme) {
  const el = document.documentElement;
  if (t === "system") delete el.dataset.theme;
  else el.dataset.theme = t;
}

export function useTheme(): [Theme, (t: Theme) => void] {
  const [theme, setTheme] = useState<Theme>("system");
  useEffect(() => {
    try {
      const t = localStorage.getItem(KEY);
      if (t === "light" || t === "dark") setTheme(t);
    } catch { /* private mode: system */ }
  }, []);
  const set = useCallback((t: Theme) => {
    setTheme(t);
    applyTheme(t);
    try { if (t === "system") localStorage.removeItem(KEY); else localStorage.setItem(KEY, t); } catch { /* */ }
  }, []);
  return [theme, set];
}

/** Runs before React: the saved theme on <html>, so nothing flashes. */
export const THEME_BOOT =
  "try{var t=localStorage.getItem('" + KEY + "');if(t==='light'||t==='dark')document.documentElement.dataset.theme=t}catch(e){}";
