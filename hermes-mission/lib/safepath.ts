/**
 * Paths built from request input. Every route that turns a URL segment or a
 * query parameter into a file on disk goes through here, so `..`, `%2F`,
 * absolute paths and drive letters can never leave the folder it allows.
 */
import path from 'path';

/** `root` joined with `parts`, or null when the result is outside `root`. */
export function within(root: string, ...parts: string[]): string | null {
  const base = path.resolve(root);
  if (parts.some((p) => typeof p !== 'string' || p.includes('\0'))) return null;
  const full = path.resolve(base, ...parts);
  const rel = path.relative(base, full);
  if (!rel || rel.startsWith('..') || path.isAbsolute(rel)) return null;
  return full;
}

/** A single file name: no folders, no dots-only names, nothing hidden. */
export function bareName(name: string, maxLen = 160): string | null {
  const n = String(name || '');
  if (!n || n.length > maxLen) return null;
  if (n !== path.basename(n) || /[\\/:\0]/.test(n) || n.startsWith('.')) return null;
  return n;
}

export const MEDIA_TYPES: Record<string, string> = {
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.gif': 'image/gif', '.svg': 'image/svg+xml', '.mp4': 'video/mp4', '.webm': 'video/webm',
};

/** The media type for a file name, or null when it is not an image or video. */
export function mediaType(name: string): string | null {
  return MEDIA_TYPES[path.extname(name).toLowerCase()] ?? null;
}

export const RUN_ID = /^(GTM|RUN)[-_A-Za-z0-9]{4,80}$/;
