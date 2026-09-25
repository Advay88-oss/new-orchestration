"""Filling a tenant's brain from a sources spec — no company-specific code.

A tenant is onboarded from `seeds/<tenant>.sources.json`: which markdown
directories and files are its knowledge (each with a source name and an
authority), which images are its visual memory, and which social handles are
its competitors. Vanna is tenant #1 this way; a second company is a second
spec file (or, from Phase 2, a website analysis the founder approves).

    python -m pipeline.brand_brain init vanna        # profile draft + everything below
    python -m pipeline.brand_brain ingest vanna      # knowledge only, incremental
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pipeline.brand_brain import embed as E
from pipeline.brand_brain.chunking import chunk_markdown
from pipeline.brand_brain.client import Brain

REPO = Path(__file__).resolve().parents[2]
SEEDS = Path(__file__).resolve().parent / "seeds"
AGENT = "BRAIN_onboarding"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def spec(tenant: str) -> dict:
    return json.loads((SEEDS / (tenant + ".sources.json")).read_text(encoding="utf-8"))


def _mtime(p: Path) -> str:
    return datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat()


def _title(md: str, fallback: str) -> str:
    for line in md.splitlines():
        if line.startswith("# "):
            return line[2:].strip()[:160]
    return fallback


# -------------------------------------------------------------------- knowledge

def _markdown_items(src: dict) -> list[tuple[str, str, str, Optional[str], str]]:
    """(page_id, title, text, url, updated_at) for one knowledge source."""
    kind, path = src["kind"], REPO / src["path"]
    items = []
    if kind in ("markdown_dir", "markdown_glob"):
        for f in sorted(path.glob(src.get("glob", "*.md"))):
            if f.name in set(src.get("exclude", [])) or f.name.startswith("."):
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            url = None
            if src.get("url_template"):
                url = src["url_template"].format(path=f.stem.replace(src.get("path_sep", "__"), "/"))
            items.append((src["source"] + ":" + f.stem, _title(text, f.stem.replace("__", " / ")),
                          text, url, _mtime(f)))
    elif kind == "markdown_file":
        f = path
        if f.exists():
            text = f.read_text(encoding="utf-8", errors="replace")
            items.append((src["source"] + ":" + f.stem, _title(text, f.stem), text, None, _mtime(f)))
    elif kind == "git_markdown":
        # Tracked in git, deleted from disk: read the committed copy.
        names = subprocess.run(["git", "ls-files", src["path"]], cwd=REPO, capture_output=True,
                               text=True).stdout.split()
        for n in names:
            if not n.endswith(".md"):
                continue
            text = subprocess.run(["git", "show", "HEAD:" + n], cwd=REPO, capture_output=True,
                                  text=True, encoding="utf-8").stdout
            when = subprocess.run(["git", "log", "-1", "--format=%cI", "--", n], cwd=REPO,
                                  capture_output=True, text=True).stdout.strip()
            items.append((src["source"] + ":" + Path(n).stem, _title(text, Path(n).stem), text, None, when))
    return items


def ingest_knowledge(tenant: str, *, embed: bool = True) -> dict[str, Any]:
    s = spec(tenant)
    brain = Brain(tenant, create=True)
    report: dict[str, Any] = {}
    for src in s["knowledge"]:
        totals = {"pages": 0, "added_or_changed": 0, "tombstoned": 0, "unchanged": 0}
        for page_id, title, text, url, updated in _markdown_items(src):
            chunks = chunk_markdown(text, title=title, company=s["company"], source_label=src["label"],
                                    content_type=src.get("content_type", "doc"))
            r = brain.upsert_page(page_id, chunks, source=src["source"], authority=src["authority"],
                                  url=url, updated_at=updated, embed=embed)
            totals["pages"] += 1
            for k in ("added_or_changed", "tombstoned", "unchanged"):
                totals[k] += r[k]
        report[src["source"] + ":" + src["path"]] = totals
    brain.meta("last_ingest", _now())
    return report


# ----------------------------------------------------------------------- images

def _still(mp4: Path, out: Path) -> Optional[Path]:
    exe = shutil.which("ffmpeg") or "ffmpeg"
    try:
        subprocess.run([exe, "-y", "-loglevel", "error", "-sseof", "-1", "-i", str(mp4),
                        "-frames:v", "1", "-vf", "scale=1280:-1", str(out)], check=True, timeout=60)
        return out
    except Exception:                               # noqa: BLE001 — boundary
        return None


def _image_items(tenant: str, src: dict) -> list[dict]:
    kind, path = src["kind"], REPO / src["path"]
    items = []
    if kind == "exemplar_index" and path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            f = REPO / src["dir"] / r["file"]
            if f.exists():
                items.append({"file": f, "score": r.get("score"), "note": r.get("note") or "",
                              "brief": r.get("brief") or ""})
    elif kind == "video_index" and path.exists():
        from pipeline.brand_brain.store import tenant_dir
        stills = tenant_dir(tenant) / "stills"
        stills.mkdir(parents=True, exist_ok=True)
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            mp4 = REPO / src["dir"] / r["file"]
            st = _still(mp4, stills / (Path(r["file"]).stem + "_last.png")) if mp4.exists() else None
            if st:
                items.append({"file": st, "score": r.get("score"), "note": r.get("note") or "",
                              "video": mp4.relative_to(REPO).as_posix()})
    elif kind == "image_glob":
        items = [{"file": f, "score": None, "note": ""} for f in sorted(path.glob(src["glob"]))]
    elif kind == "image_file" and path.exists():
        items = [{"file": path, "score": None, "note": ""}]
    for it in items:
        it["kind"] = src["image_kind"]
    return items


def _describe(f: Path) -> dict:
    from pipeline.gtm_os import agent_runtime as R
    try:
        out = R.brain_vision(
            "Describe this brand image for a visual reference library. Return JSON: "
            '{"caption": str (2 sentences: what it shows and how it is composed), '
            '"style_tags": [str] (5-8 short tags: layout, palette, elements, mood)}',
            [f], agent=AGENT, system="You catalogue brand design references precisely and briefly.",
            role="reasoning", temperature=0.1, max_output_tokens=1024)
        return {"caption": str(out.get("caption") or "")[:600],
                "style_tags": [str(t)[:40] for t in (out.get("style_tags") or [])][:8]}
    except Exception:                               # noqa: BLE001 — boundary
        return {"caption": "", "style_tags": []}


def ingest_images(tenant: str) -> dict[str, int]:
    s = spec(tenant)
    brain = Brain(tenant, create=True)
    items = [it for src in s["images"] for it in _image_items(tenant, src)]
    todo = []
    # The brain keeps its own copy of every image, so it is self-contained:
    # the design references, for one, are not shipped in the container image.
    from pipeline.brand_brain.store import tenant_dir
    img_dir = tenant_dir(tenant) / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    for it in items:
        it["id"] = hashlib.sha1(it["file"].read_bytes()).hexdigest()[:12]
        own = img_dir / (it["id"] + it["file"].suffix.lower())
        if not own.exists():
            shutil.copyfile(it["file"], own)
        it["file"] = own
        if brain.has_image(it["id"]):
            # Known image: refresh score and note only (the founder may re-rate).
            brain.add_image(it["id"], it["file"].relative_to(REPO).as_posix(), kind=it["kind"],
                            score=it.get("score"), note=it.get("note", ""), source=it.get("video", ""))
        else:
            todo.append(it)

    def work(it):
        d = _describe(it["file"])
        try:
            v = E.image(it["file"])
        except Exception:                           # noqa: BLE001 — caption still searchable later
            v = None
        return it, d, v

    with ThreadPoolExecutor(max_workers=6) as pool:
        for it, d, v in pool.map(work, todo):
            brain.add_image(it["id"], it["file"].relative_to(REPO).as_posix(), kind=it["kind"],
                            caption=d["caption"], style_tags=d["style_tags"], score=it.get("score"),
                            note=it.get("note", ""), source=it.get("video", ""), vector=v)
    return {"images": len(items), "new": len(todo)}


# ---------------------------------------------------------- competitor patterns

def build_competitor_patterns(tenant: str, *, max_runs: int = 40) -> dict[str, int]:
    """Summaries of how competitors post, from scraped posts. Their text is
    read here and never stored: only the pattern summary enters the brain."""
    from pipeline.gtm_os import agent_runtime as R
    s = spec(tenant)
    handles = {k.lower(): v for k, v in (s.get("competitor_handles") or {}).items()}
    names = sorted(set(handles.values()))
    posts: dict[str, set[str]] = {}
    runs = sorted((REPO / "pipeline" / "state" / "gtm_runs").glob("GTM-*"))[-max_runs:]
    for d in runs:
        try:
            h = json.loads((d / "harvest.json").read_text(encoding="utf-8"))
        except Exception:                           # noqa: BLE001 — no harvest
            continue
        for sig in h.get("signals") or []:
            sid = str(sig.get("signal_id", ""))
            head = str(sig.get("headline", ""))[:280]
            if sid.upper().startswith("SIG-TWITTER-"):
                handle = sid.split("-")[2].lower()
                if handle in handles:
                    posts.setdefault(handles[handle], set()).add(head)
                continue
            # Since X is no longer scraped: news, community and channel items
            # that name a competitor, which is how they are seen publicly.
            low = head.lower()
            for name in names:
                if re.search(r"\b" + re.escape(name.lower()) + r"\b", low):
                    posts.setdefault(name, set()).add(head)
    brain = Brain(tenant, create=True)
    n = 0
    for comp, texts in posts.items():
        sample = sorted(texts)[:40]
        try:
            out = R.brain_json(
                "These are recent public posts by or news items about " + comp + ", a competitor. Describe HOW they "
                "post and are covered — formats, hook types, recurring topics, length, tone, calls to action — as "
                "patterns another brand could learn from. Do NOT quote or closely paraphrase any "
                "post, and do not include product claims or figures.\n\n"
                + "\n".join("- " + t for t in sample)
                + '\n\nReturn JSON: {"patterns": [{"topic": str, "pattern": str (one sentence)}]} '
                  "with 3-5 patterns.",
                agent=AGENT, system="You summarise social media strategy without copying content.",
                role="reasoning", temperature=0.2, max_output_tokens=2048)
        except Exception:                           # noqa: BLE001 — boundary
            continue
        for i, p in enumerate((out.get("patterns") or [])[:5]):
            brain.set_competitor_pattern(tenant + ":" + comp.lower().replace(" ", "_") + ":" + str(i),
                                         competitor=comp, topic=str(p.get("topic") or "")[:80],
                                         pattern=str(p.get("pattern") or "")[:400],
                                         evidence_n=len(sample))
            n += 1
    return {"competitors": len(posts), "patterns": n}


# --------------------------------------------------------------------- profile

def seed_profile(tenant: str) -> int:
    """The tenant's first profile, as a DRAFT the founder reviews and approves."""
    s = spec(tenant)
    brain = Brain(tenant, create=True)
    if brain.profile_versions():
        return 0
    prof = json.loads((REPO / s["profile_seed"]).read_text(encoding="utf-8"))
    return brain.save_profile(prof, status="draft", source="seed: " + s["profile_seed"],
                              note="Consolidated from the constants the agents used before the brain.")


def init(tenant: str) -> dict[str, Any]:
    return {"profile_version": seed_profile(tenant),
            "knowledge": ingest_knowledge(tenant),
            "images": ingest_images(tenant),
            "competitors": build_competitor_patterns(tenant),
            "stats": Brain(tenant).stats()}


def remember_image(path: Path, *, kind: str, score: Optional[float] = None, note: str = "",
                   source: str = "", tenant: Optional[str] = None) -> Optional[str]:
    """Put one new image into the brain's visual memory as soon as it is
    rated, so the next run's `get_visual_refs` can return it. Never raises."""
    from pipeline.brand_brain.client import current_tenant
    try:
        t = tenant or current_tenant()
        brain = Brain(t, create=True)
        path = Path(path)
        iid = hashlib.sha1(path.read_bytes()).hexdigest()[:12]
        rel = path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else path.as_posix()
        if brain.has_image(iid):
            brain.add_image(iid, rel, kind=kind, score=score, note=note, source=source)
            return iid
        d = _describe(path)
        try:
            v = E.image(path)
        except Exception:                           # noqa: BLE001 — caption only
            v = None
        brain.add_image(iid, rel, kind=kind, caption=d["caption"], style_tags=d["style_tags"],
                        score=score, note=note, source=source, vector=v)
        return iid
    except Exception:                               # noqa: BLE001 — boundary
        return None


def index_profile(tenant: str) -> dict[str, int]:
    """The profile's own facts as searchable knowledge (source 'profile',
    authority 1), so the reviewer can find a figure or a URL the profile
    states even when no document repeats it. Re-run whenever the profile
    changes; unchanged facts are not re-embedded."""
    from pipeline.brand_brain.chunking import Chunk
    brain = Brain(tenant)
    p = brain.get_brand_profile()
    if not p:
        return {"added_or_changed": 0}
    name = (p.get("company") or {}).get("name", tenant)
    pre = "From " + name + "'s approved brand profile."
    facts: list[tuple[str, str]] = []
    c = p.get("company") or {}
    for k in ("what_it_is", "deployment", "stage", "website", "docs_url", "app_url"):
        if c.get(k):
            facts.append(("company", k.replace("_", " ") + ": " + str(c[k])))
    for k, v in ((p.get("visual") or {}).get("anchors") or {}).items():
        facts.append(("product anchors", k + ": " + v))
    for f in (p.get("claims") or {}).get("true_figures") or []:
        facts.append(("true figures", f["value"] + " — " + f.get("meaning", "")))
    for a in (p.get("claims") or {}).get("approved") or []:
        facts.append(("approved claims", a))
    for n, r in (p.get("partners") or {}).items():
        facts.append(("confirmed partners", n + " — " + r))
    if (p.get("voice") or {}).get("cta"):
        facts.append(("call to action", p["voice"]["cta"]))
    chunks = [Chunk(text=t, title="Brand profile", section=s, content_type="fact", prefix=pre)
              for s, t in facts]
    r = brain.upsert_page("profile:facts", chunks, source="profile", authority=1)
    return r
