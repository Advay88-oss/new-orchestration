"use client";

import { useEffect, useState } from "react";

export interface Viewer {
  owner: boolean;
  previewing: boolean;
  since: string | null;
}

let cached: Promise<Viewer> | null = null;

/** Owner or visitor (lib/viewer.ts). Fetched once per page load. */
export function useViewer(): Viewer | null {
  const [v, setV] = useState<Viewer | null>(null);
  useEffect(() => {
    cached ??= fetch("/api/viewer", { cache: "no-store" })
      .then((r) => r.json())
      .catch(() => ({ owner: false, previewing: false, since: null }));
    cached.then(setV);
  }, []);
  return v;
}

export function sinceLabel(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleString(undefined, {
    day: "numeric", month: "short", hour: "numeric", minute: "2-digit",
  });
}
