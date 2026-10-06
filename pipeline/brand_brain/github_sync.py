"""Vanna GitHub Ingestion & Sync — Phase 3 Brand Brain Knowledge Source.

Syncs Vanna's GitHub repositories (Vanna_docs, mercury-stellar-backend,
Protocol_V1_Solana, etc.) into the Brand Brain:
  1. Tree Discovery: Fetches repository file trees via GitHub REST API.
  2. Content Fetch: Retrieves documentation, contract interfaces, and specs.
  3. Heading-Aware Chunking: Splits files into structured ~500-token chunks.
  4. Vector Embeddings: Embeds chunks via `gemini-embedding-2` (768-d).
  5. Storage & Deduplication: Upserts into PostgreSQL `chunks` (source: 'github', authority: 2).
  6. Commits: the last 30 days of commits on every branch of every repo the
     org pushed to, kept in brain meta `github:commits` (sync_commits). They
     stay out of `whats_new`: a commit message is not a launch.

Usage:
    python -m pipeline.brand_brain.github_sync sync [--org vannafinance] [--tenant vanna]
    python -m pipeline.brand_brain.github_sync commits [--tenant vanna] [--days 30]
    python -m pipeline.brand_brain.github_sync latest [--tenant vanna] [--repo X] [--limit 20]
    python -m pipeline.brand_brain.github_sync status [--tenant vanna]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from pipeline.brand_brain.chunking import chunk_markdown
from pipeline.brand_brain.client import Brain
from pipeline.brand_brain import store as S

AGENT = "BRAIN_github"
DEFAULT_ORG = "vannafinance"
DEFAULT_TENANT = "vanna"

# Prose that explains the product. Source files, tests, licenses and
# internal notes are not brand knowledge.
_DOC_EXTENSIONS = {".md", ".mdx"}

# Target high-value repos for Vanna
DEFAULT_REPOS = [
    "Vanna_docs",
    "Solana_Docs",
    "mercury-stellar-backend",
    "Protocol_V1_Solana",
    "vanna_homepage",
    "Zonymous",
]

# The pages a post is allowed to lean on. The marketing site stays searchable
# and is not re-fetched on the clock.
PRODUCT_REPOS = [
    "Vanna_docs",
    "Solana_Docs",
    "mercury-stellar-backend",
    "Protocol_V1_Solana",
    "Zonymous",
]
DOCS_KEY = "github:docs_synced_at"
DOC_REFRESH_HOURS = 6

def _token() -> Optional[str]:
    """GitHub token from environment or pipeline/.env (optional; raises rate limit to 5000/hr)."""
    return os.environ.get("GITHUB_TOKEN") or S._env_file("GITHUB_TOKEN")


def _http_get(url: str, timeout: int = 15) -> bytes:
    """HTTP GET with optional GitHub Token auth and standard headers."""
    headers = {"User-Agent": "Vanna-GTM-Scout/1.0"}
    tok = _token()
    if tok and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {tok}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def relevant_github_path(path: str) -> bool:
    """A file the brain should keep: written to explain the product.

    READMEs, PRDs, and the learn / guides / docs / contract pages. Not the
    Rust or Solidity source, tests, toolchains, licenses, coming-soon stubs,
    or internal review notes.
    """
    p = path.replace("\\", "/").lower()
    name = p.rsplit("/", 1)[-1]
    if Path(name).suffix.lower() not in _DOC_EXTENSIONS:
        return False
    if any(part in p for part in ("/tests/", "/test/", "node_modules/", "target/", "vendor/", ".git/")):
        return False
    if name in {"agents.md", "source_review.md", "docs-review.md", "redundancy-report.md"}:
        return False
    if "coming-soon" in name or "/snippets/" in p or "/icons/" in p:
        return False
    if any(s in p for s in ("deploy.md", "dns-migration", "/migrations/")):
        return False
    return True


def list_repo_files(org: str, repo: str) -> list[dict[str, str]]:
    """Retrieves file tree using git trees API (trying main branch, then master)."""
    for branch in ("main", "master"):
        url = f"https://api.github.com/repos/{org}/{repo}/git/trees/{branch}?recursive=1"
        try:
            data = json.loads(_http_get(url).decode("utf-8"))
            tree = data.get("tree", [])
            out = []
            for item in tree:
                if item.get("type") != "blob":
                    continue
                path = item.get("path", "")
                if not relevant_github_path(path):
                    continue
                out.append({
                        "path": path,
                        "branch": branch,
                        "raw_url": f"https://raw.githubusercontent.com/{org}/{repo}/{branch}/{path}",
                        "html_url": f"https://github.com/{org}/{repo}/blob/{branch}/{path}",
                        "size": item.get("size", 0)
                    })
            if out:
                def rank(item: dict) -> tuple:
                    path = item["path"].lower()
                    return (
                        0 if path.endswith("readme.md") or path.endswith("prd.md") else 1,
                        0 if "/learn/" in path or "/guides/" in path else 1,
                        path,
                    )
                out.sort(key=rank)
                return out
        except Exception:
            continue
    return []


def fetch_file_content(raw_url: str) -> Optional[str]:
    """Fetches raw text content of a file."""
    try:
        raw = _http_get(raw_url, timeout=12)
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return None


def format_code_as_markdown(repo: str, file_path: str, content: str) -> str:
    """Wraps source code / config in markdown with architectural context."""
    ext = Path(file_path).suffix.lower()
    lang = "rust" if ext == ".rs" else "solidity" if ext == ".sol" else "toml" if ext == ".toml" else ""
    return f"# Repository: {repo}\n## File: {file_path}\n\n```{lang}\n{content.strip()}\n```\n"


def sync_repository(
    org: str,
    repo: str,
    brain: Brain,
    limit_files: int = 40,
    verbose: bool = True
) -> dict[str, int]:
    """Syncs one repository into the brand brain."""
    files = list_repo_files(org, repo)
    if verbose:
        print(f"[{repo}] Discovered {len(files)} relevant files (processing up to {limit_files})...")

    stats = {"pages": 0, "fresh": 0, "reused": 0, "bytes": 0}

    for item in files[:limit_files]:
        path = item["path"]
        raw_url = item["raw_url"]
        html_url = item["html_url"]
        
        content = fetch_file_content(raw_url)
        if not content or len(content.strip()) < 30:
            continue

        stats["bytes"] += len(content)
        ext = Path(path).suffix.lower()
        
        # If it's markdown, chunk directly; otherwise format as code block
        if ext in _DOC_EXTENSIONS:
            md_text = content
        else:
            md_text = format_code_as_markdown(repo, path, content)

        chunks = chunk_markdown(
            md_text,
            title=f"GitHub: {repo}/{path}",
            company=brain.tenant,
            source_label=f"GitHub {repo}",
        )
        if not chunks:
            continue

        page_id = f"github:{repo}/{path}"
        try:
            res = brain.upsert_page(
                page_id=page_id,
                chunks=chunks,
                source="github",
                authority=2,  # Verified protocol code/documentation
                url=html_url,
                embed=True
            )
            stats["pages"] += 1
            stats["fresh"] += res.get("added_or_changed", 0)
            stats["reused"] += res.get("unchanged", 0)
            if verbose and res.get("added_or_changed", 0) > 0:
                print(f"  ✓ Indexed: {repo}/{path} ({len(chunks)} chunks, {res.get('added_or_changed')} new embedded)")
        except Exception as e:
            if verbose:
                print(f"  ✕ Failed {repo}/{path}: {e}")

    return stats


def sync_github(
    org: str = DEFAULT_ORG,
    tenant: str = DEFAULT_TENANT,
    repos: Optional[list[str]] = None,
    limit_per_repo: int = 120
) -> dict[str, Any]:
    """Full sync across Vanna's GitHub repositories."""
    target_repos = repos or DEFAULT_REPOS
    brain = Brain(tenant)

    print(f"============================================================")
    print(f" 🐙 GITHUB KNOWLEDGE SYNC — ORG: [{org}] -> TENANT: [{tenant}]")
    print(f"============================================================")

    total_stats = {"repos": len(target_repos), "pages": 0, "fresh_chunks": 0, "reused_chunks": 0}

    for r in target_repos:
        res = sync_repository(org, r, brain, limit_files=limit_per_repo)
        total_stats["pages"] += res["pages"]
        total_stats["fresh_chunks"] += res["fresh"]
        total_stats["reused_chunks"] += res["reused"]

    print(f"\n============================================================")
    print(f" ✅ GITHUB SYNC COMPLETED!")
    print(f"    Total Repos Synced: {total_stats['repos']}")
    print(f"    Total Files/Pages:  {total_stats['pages']}")
    print(f"    New Chunks Embedded: {total_stats['fresh_chunks']}")
    print(f"    Reused Chunks:       {total_stats['reused_chunks']}")
    print(f"============================================================\n")

    return total_stats


def refresh_product_docs(org: str = DEFAULT_ORG, tenant: str = DEFAULT_TENANT,
                         force: bool = False, verbose: bool = True) -> dict[str, Any]:
    """Re-read the product repos into the live brain.

    Unchanged pages are kept as they are, so a repeat does not re-embed them.
    The clock calls this every six hours. Commits stay on their own hourly pass.
    """
    brain = Brain(tenant)
    last = brain.meta(DOCS_KEY) or ""
    if not force and last:
        try:
            at = datetime.fromisoformat(last)
        except ValueError:
            at = None
        if at and datetime.now(timezone.utc) - at < timedelta(hours=DOC_REFRESH_HOURS):
            return {"ok": True, "skipped": True, "synced_at": last}
    stats = sync_github(org=org, tenant=tenant, repos=PRODUCT_REPOS, limit_per_repo=200)
    stamped = datetime.now(timezone.utc).isoformat(timespec="seconds")
    brain.meta(DOCS_KEY, stamped)
    stats["skipped"] = False
    stats["synced_at"] = stamped
    return stats


COMMITS_KEY = "github:commits"
MAX_COMMITS = 1500


def _api(path: str) -> Any:
    return json.loads(_http_get("https://api.github.com" + path, timeout=20).decode("utf-8"))


def sync_commits(org: str = DEFAULT_ORG, tenant: str = DEFAULT_TENANT, days: int = 30,
                 verbose: bool = True) -> dict[str, Any]:
    """Commits from the last `days` on every branch of every public repo the
    org pushed to in that window. A branch whose head has not moved since the
    last sync is not fetched again, so an unauthenticated run (60 calls/hour)
    still covers the org; on a rate limit the run stops and keeps what it has,
    and the next one carries on."""
    brain = Brain(tenant)
    try:
        prev = json.loads(brain.meta(COMMITS_KEY) or "{}")
    except ValueError:
        prev = {}
    heads: dict[str, dict[str, str]] = prev.get("heads", {})
    by_sha: dict[str, dict] = {c["sha"]: c for c in prev.get("commits", [])}
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    since = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    errors: list[str] = []
    calls = 0

    def get(path: str) -> Any:
        nonlocal calls
        calls += 1
        return _api(path)

    try:
        repos = get(f"/orgs/{org}/repos?per_page=100&sort=pushed")
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"GitHub {e.code} listing {org} repos"}
    active = [r for r in repos if not r.get("private") and str(r.get("pushed_at") or "") >= since]

    # Every repo's default branch goes before any feature branch, so a rate
    # limit costs the long tail of branches, never a whole repo.
    stopped = False
    queue: list[tuple[int, str, str, str]] = []
    for r in active:
        name = r["name"]
        try:
            branches = get(f"/repos/{org}/{name}/branches?per_page=100")
        except urllib.error.HTTPError as e:
            errors.append(f"{name}: GitHub {e.code} on branches")
            if e.code in (403, 429):
                stopped = True
                break
            continue
        default = r.get("default_branch") or "main"
        for b in branches:
            queue.append((b["name"] != default, name, b["name"], b.get("commit", {}).get("sha", "")))
    queue.sort(key=lambda q: q[0])

    for _, name, branch, head in ([] if stopped else queue):
        seen = heads.setdefault(name, {})
        if seen.get(branch) == head:
            continue
        if head in by_sha:
            # The head is already known from another branch: its history is too.
            if branch not in by_sha[head]["branches"]:
                by_sha[head]["branches"].append(branch)
            seen[branch] = head
            continue
        q = urllib.parse.quote(branch, safe="")
        try:
            rows = get(f"/repos/{org}/{name}/commits?sha={q}&since={since}&per_page=100")
        except urllib.error.HTTPError as e:
            errors.append(f"{name}@{branch}: GitHub {e.code}")
            if e.code in (403, 429):
                stopped = True
                break
            continue
        for c in rows:
            cm = c.get("commit", {})
            author = cm.get("author") or {}
            row = by_sha.get(c["sha"]) or {
                "sha": c["sha"], "short": c["sha"][:7], "repo": name,
                "author": author.get("name") or "",
                "login": (c.get("author") or {}).get("login") or "",
                "date": author.get("date") or "",
                "message": (cm.get("message") or "").split("\n", 1)[0][:200],
                "url": c.get("html_url") or "", "branches": []}
            if branch not in row["branches"]:
                row["branches"].append(branch)
            by_sha[c["sha"]] = row
        seen[branch] = head
        if verbose:
            print(f"  [{name}@{branch}] {len(rows)} commits")
    if stopped:
        errors.append("GitHub rate limit reached; the next run continues (GITHUB_TOKEN in pipeline/.env lifts it)")

    commits = sorted((c for c in by_sha.values() if c["date"] >= since),
                     key=lambda c: c["date"], reverse=True)[:MAX_COMMITS]
    out = {"synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "org": org,
           "days": days, "heads": heads, "commits": commits, "errors": errors,
           "repos": [{"repo": r["name"], "pushed_at": r.get("pushed_at"), "url": r.get("html_url")}
                     for r in active]}
    brain.meta(COMMITS_KEY, json.dumps(out))
    if verbose:
        print(f"commits: {len(commits)} kept from {len(active)} repos, {calls} API calls"
              + (f"; {len(errors)} errors" if errors else ""))
    return {"ok": not stopped, "commits": len(commits), "repos": len(active), "calls": calls,
            "errors": errors}


# Product pages pasted into every post prompt. Build steps, env files and the
# marketing site stay searchable and are not repeated on every run.
_BRIEF_PAGES: list[tuple[str, tuple[str, ...]]] = [
    ("github:Protocol_V1_Solana/README.md", (
        "lending and margin protocol for stock tokens",
        "credit lps supply",
        "**perps**",
    )),
    ("github:Solana_Docs/developers/deployed-contracts.mdx", ("tslax",)),
    ("github:Solana_Docs/guides/earn/overview.mdx", ("kamino's xstocks",)),
    ("github:Vanna_docs/guides/how-vanna-works.mdx", ("two connected sides",)),
    ("github:Vanna_docs/learn/overview.mdx", ("connects liquidity providers",)),
    ("github:Vanna_docs/learn/protocol-architecture.mdx", ("core accounting contracts",)),
    ("github:mercury-stellar-backend/README.md", ("stellar-side frontend",)),
    ("github:mercury-stellar-backend/PRD.md", ("defi protocol web app",)),
]


def product_brief(tenant: str = DEFAULT_TENANT, chars: int = 700) -> str:
    """The product pages, for the agents' prompt.

    Each excerpt stays tied to the GitHub page it came from, so a Solana
    page and a Stellar page are not blended into one description.
    """
    brain = Brain(tenant)
    blocks: list[str] = []
    with brain._db() as con:
        for page_id, needles in _BRIEF_PAGES:
            rows = con.execute(
                "SELECT section, url, text FROM chunks WHERE page_id=? AND deleted=0 "
                "AND content_type!='section'", (page_id,)).fetchall()
            used: set[str] = set()
            for needle in needles:
                nd = needle.lower()
                for r in rows:
                    text = " ".join((r["text"] or "").split())
                    if len(text) < 80 or text in used or nd not in text.lower():
                        continue
                    used.add(text)
                    label = page_id.split(":", 1)[-1]
                    blocks.append("[" + label + " · " + str(r["section"] or "")[:90]
                                  + (" · " + r["url"] if r["url"] else "") + "]\n  " + text[:chars])
                    break
    if not blocks:
        return ""
    return ("GITHUB PRODUCT PAGES — how the product is written in the repos. "
            "A post may describe a mechanism only when that page states it, and the post "
            "stays on that page's deployment. The only numbers are the true figures.\n\n"
            + "\n\n".join(blocks))


def embed_missing(tenant: str = DEFAULT_TENANT) -> dict[str, int]:
    """Embed GitHub chunks that were stored without a vector, so search can find them."""
    from pipeline.brand_brain.embed import texts, to_blob
    brain = Brain(tenant)
    with brain._db() as con:
        rows = con.execute(
            "SELECT id, prefix, text FROM chunks WHERE source='github' AND deleted=0 "
            "AND embedding IS NULL AND content_type!='section'").fetchall()
    if not rows:
        return {"embedded": 0}
    vecs = texts([(r["prefix"] or "") + "\n" + (r["text"] or "") for r in rows])
    with brain._db() as con:
        for r, v in zip(rows, vecs):
            con.execute("UPDATE chunks SET embedding=? WHERE id=?", (to_blob(v), r["id"]))
    return {"embedded": len(rows)}


def recent_commits(tenant: str = DEFAULT_TENANT, repo: Optional[str] = None,
                   since: Optional[str] = None, limit: int = 20) -> dict[str, Any]:
    """The newest synced commits, optionally for one repo or after `since`."""
    try:
        data = json.loads(Brain(tenant).meta(COMMITS_KEY) or "{}")
    except ValueError:
        data = {}
    rows = data.get("commits", [])
    if repo:
        rows = [c for c in rows if c["repo"].lower() == repo.lower()]
    if since:
        rows = [c for c in rows if c["date"] > since]
    return {"synced_at": data.get("synced_at"), "window_days": data.get("days"),
            "errors": data.get("errors", []), "commits": rows[:max(1, min(limit, 100))]}


def prune_irrelevant(tenant: str = DEFAULT_TENANT) -> dict[str, int]:
    """Mark GitHub pages already stored that do not explain the product as deleted.

    Source files, tests and internal notes then drop out of search. The prose
    pages stay.
    """
    from pipeline.brand_brain.client import _now
    brain = Brain(tenant)
    kept = dropped = 0
    with brain._db() as con:
        rows = con.execute(
            "SELECT DISTINCT page_id FROM chunks WHERE source='github' AND deleted=0").fetchall()
        for r in rows:
            page_id = r["page_id"]
            path = page_id.split(":", 1)[-1]
            if relevant_github_path(path):
                kept += 1
                continue
            con.execute("UPDATE chunks SET deleted=1, updated_at=? WHERE page_id=? AND deleted=0",
                        (_now(), page_id))
            dropped += 1
    return {"kept": kept, "dropped": dropped}


def status(tenant: str = DEFAULT_TENANT) -> None:
    """Prints GitHub chunks stored for the given tenant."""
    is_pg = S.backend() == "pg"
    where_tenant = "tenant_id=? AND " if is_pg else ""
    params = (tenant,) if is_pg else ()

    with S.connect(tenant) as con:
        total = con.execute(f"SELECT COUNT(*) FROM chunks WHERE {where_tenant}source='github' AND deleted=0", params).fetchone()[0]
        embedded = con.execute(f"SELECT COUNT(*) FROM chunks WHERE {where_tenant}source='github' AND deleted=0 AND embedding IS NOT NULL", params).fetchone()[0]
        pages = con.execute(f"SELECT COUNT(DISTINCT page_id) FROM chunks WHERE {where_tenant}source='github' AND deleted=0", params).fetchone()[0]
        recent = con.execute(f"SELECT page_id, substring(text, 1, 80) FROM chunks WHERE {where_tenant}source='github' AND deleted=0 LIMIT 3", params).fetchall()

    print(f"=== GITHUB KNOWLEDGE STATUS: [{tenant.upper()}] ===")
    print(f"  Indexed GitHub Files:  {pages}")
    print(f"  Total Chunks:          {total}")
    print(f"  Embedded (vector 768): {embedded}")
    if recent:
        print(f"  Sample Snippets:")
        for r in recent:
            print(f"    - [{r[0]}]: {r[1]}...")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Vanna GitHub Brand Brain Ingestion")
    sub = parser.add_subparsers(dest="command")

    p_sync = sub.add_parser("sync", help="Sync repositories into Brand Brain")
    p_sync.add_argument("--org", default=DEFAULT_ORG, help="GitHub org name")
    p_sync.add_argument("--tenant", default=DEFAULT_TENANT, help="Brand Brain tenant")
    p_sync.add_argument("--repo", action="append", help="Specific repo(s) to sync")
    p_sync.add_argument("--limit", type=int, default=30, help="Max files per repo")

    p_status = sub.add_parser("status", help="Check indexed GitHub knowledge")
    p_status.add_argument("--tenant", default=DEFAULT_TENANT, help="Brand Brain tenant")

    p_commits = sub.add_parser("commits", help="Sync the last N days of commits on every branch")
    p_commits.add_argument("--org", default=DEFAULT_ORG)
    p_commits.add_argument("--tenant", default=DEFAULT_TENANT)
    p_commits.add_argument("--days", type=int, default=30)

    p_latest = sub.add_parser("latest", help="Print the newest synced commits")
    p_latest.add_argument("--tenant", default=DEFAULT_TENANT)
    p_latest.add_argument("--repo")
    p_latest.add_argument("--limit", type=int, default=20)

    args = parser.parse_args(argv)

    if args.command == "status":
        status(args.tenant)
        return 0

    if args.command == "commits":
        res = sync_commits(org=args.org, tenant=args.tenant, days=args.days)
        return 0 if res.get("commits") is not None else 1

    if args.command == "latest":
        res = recent_commits(args.tenant, repo=args.repo, limit=args.limit)
        print(f"synced {res['synced_at']}")
        for c in res["commits"]:
            print(f"{c['date']}  {c['repo']:<24} {c['short']}  {c['author']:<18} {c['message']}"
                  f"  [{', '.join(c['branches'])}]")
        for e in res["errors"]:
            print("! " + e)
        return 0

    if args.command == "sync":
        sync_github(org=args.org, tenant=args.tenant, repos=args.repo, limit_per_repo=args.limit)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
