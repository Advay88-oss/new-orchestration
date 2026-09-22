"""Quarantine the fabricated 'published' rows in the Brain DB.

`channel_dispatchers.py` used to invent a post id and canonical URL and return
`status="SUCCESS"` for every dispatch, including in LIVE mode. The worker then
wrote those receipts to `posts.jsonl` as published posts and seeded the
performance store from them.

The result: 306 rows claiming Vanna posted to x.com, reddit.com and linkedin.com
at URLs that do not exist, and performance records attached to them. A13 learns
pattern weights from that file, so the learning loop was being fed its own
fiction.

This moves them out rather than deleting them — they are evidence of what the
system did, and a future reader deserves to find them somewhere. They go to
`_quarantine/` next to the DB with the reason attached.

Identification is by the generators' own signatures, not by guesswork:

    x.com/vanna_finance/status/1835…          f"1835{int(time.time()) % 1e10}"
    …/comments/…/vanna_architecture/          a fixed slug on every Reddit post
    linkedin.com/feed/update/urn:li:share:72…  f"urn:li:share:{7240000000000000000 + …}"

Run with --apply to write. Without it, it reports and changes nothing.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DB = REPO_ROOT / "pipeline" / "brain" / "db"
QUARANTINE = DB / "_quarantine"

FAKE_URL = [
    re.compile(r"x\.com/vanna_finance/status/1835\d+"),
    re.compile(r"reddit\.com/r/[^/]+/comments/[^/]+/vanna_architecture/?$"),
    re.compile(r"linkedin\.com/feed/update/urn:li:share:72[0-9]{17}"),
]

REASON = ("Fabricated by channel_dispatchers.py before 2026-09-23: the "
          "dispatcher invented a post id and URL and returned SUCCESS without "
          "contacting any API. No such post exists.")


def _rows(p: Path) -> list[dict]:
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _write(p: Path, rows: list[dict]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, default=str) + "\n" for r in rows),
                 encoding="utf-8")


def is_fabricated(row: dict) -> bool:
    url = str(row.get("canonical_url") or row.get("url") or "")
    return any(p.search(url) for p in FAKE_URL)


def main(apply: bool) -> None:
    posts_p = DB / "posts.jsonl"
    posts = _rows(posts_p)
    bad = [r for r in posts if is_fabricated(r)]
    good = [r for r in posts if not is_fabricated(r)]
    bad_ids = {str(r.get("post_id") or r.get("id") or "") for r in bad} - {""}

    # Performance records seeded from those receipts, matched by post id.
    perf_targets = [DB / "performance.jsonl",
                    REPO_ROOT / "pipeline" / "state" / "performance_records.jsonl"]
    perf_moves: list[tuple[Path, list[dict], list[dict]]] = []
    for p in perf_targets:
        rows = _rows(p)
        pb = [r for r in rows
              if str(r.get("post_id") or r.get("content_id") or "") in bad_ids]
        pg = [r for r in rows if r not in pb]
        perf_moves.append((p, pb, pg))

    print("posts.jsonl              ", len(posts), "rows ->", len(bad), "fabricated")
    for p, pb, _ in perf_moves:
        print(p.name.ljust(26), len(_rows(p)), "rows ->", len(pb), "tied to fabricated posts")

    if not apply:
        print("\nDry run. Re-run with --apply to quarantine.")
        return

    stamp = datetime.now(timezone.utc).isoformat()
    QUARANTINE.mkdir(parents=True, exist_ok=True)

    for r in bad:
        r["_quarantined_at"] = stamp
        r["_quarantine_reason"] = REASON
    _write(QUARANTINE / "posts.fabricated.jsonl", bad)
    _write(posts_p, good)

    for p, pb, pg in perf_moves:
        if not pb:
            continue
        for r in pb:
            r["_quarantined_at"] = stamp
            r["_quarantine_reason"] = REASON
        _write(QUARANTINE / (p.stem + ".fabricated.jsonl"), pb)
        _write(p, pg)

    (QUARANTINE / "README.md").write_text(
        "# Quarantine\n\n"
        "Rows moved out of the Brain DB on " + stamp + ".\n\n"
        + REASON + "\n\n"
        "They are kept because they are evidence of what the system did, not "
        "because they are usable. Nothing should read from this directory.\n",
        encoding="utf-8")

    print("\nQuarantined to", QUARANTINE)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    main(ap.parse_args().apply)
