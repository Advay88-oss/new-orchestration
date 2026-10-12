"""Studio: the posters the visual agents made, and the jobs that make more from the chat.

Every finished poster lives in pipeline/state/studio as `studio-<id>.png` (full size, for download)
and `studio-<id>.jpg` (a preview for the grid), listed in index.json. Deployed, the same files sit
in the state bucket under studio/, which is what the dashboard serves.

A job is one request from the Assistant:
  revise  an image the owner uploaded (or a studio poster) + what they did not like -> the visual
          agent's director turns the feedback into exact changes, Nano Banana redraws, the judge
          checks the changes landed and no word or number slipped.
  create  a written request -> format_poster.run (the founder's format: phone, cards, real logo).
It runs in the background (one to four minutes) and writes jobs/<id>.json, which the chat polls.

    python -m pipeline.gtm_creative.studio import-exports      # the agent posters made so far
    python -m pipeline.gtm_creative.studio push                # files + index to the bucket
    python -m pipeline.gtm_creative.studio job <job_id>        # run one job (the Assistant starts it)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from PIL import Image

REPO = Path(__file__).resolve().parents[2]
STUDIO = REPO / "pipeline" / "state" / "studio"
INDEX = STUDIO / "index.json"
JOBS = STUDIO / "jobs"
PREFIX = "studio/"
JOB_ID = re.compile(r"^v_[a-z0-9]{10}$")
FILE = re.compile(r"^studio-[a-z0-9][a-z0-9-]{2,90}\.(png|jpg|jpeg|webp)$")
# Shapes the image model draws; anything else is drawn at the nearest one and cropped.
ASPECTS = {"1:1": 1.0, "4:5": 0.8, "3:4": 0.75, "2:3": 2 / 3, "9:16": 9 / 16, "5:4": 1.25, "4:3": 4 / 3,
           "3:2": 1.5, "16:9": 16 / 9, "21:9": 21 / 9, "4:1": 4.0}
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(s: str, n: int = 48) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(s).lower())).strip("-")[:n] or "poster"


def cloud() -> bool:
    return bool(os.environ.get("K_SERVICE") or os.environ.get("VANNA_CLOUD") == "1")


# ------------------------------------------------------------------ the index

def load() -> list[dict]:
    try:
        return json.loads(INDEX.read_text(encoding="utf-8")).get("items") or []
    except (OSError, ValueError):
        return []


def _save(items: list[dict]) -> None:
    STUDIO.mkdir(parents=True, exist_ok=True)
    tmp = INDEX.with_suffix(".tmp")
    tmp.write_text(json.dumps({"updated": _now(), "items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(INDEX)


def _preview(src: Path, dst: Path, long_side: int = 1200) -> None:
    with Image.open(src) as im:
        im = im.convert("RGB")
        k = long_side / max(im.size)
        if k < 1:
            im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        im.save(dst, quality=86, optimize=True)


def add(src: Path, *, title: str, collection: str, caption: Any = None, kind: str = "", parent: str = "",
        feedback: str = "", origin: str = "", tenant: str = "vanna", push: Optional[bool] = None,
        item_id: str = "") -> dict:
    """Copy a finished poster into the studio and list it; deployed, also into the bucket."""
    src = Path(src)
    digest = hashlib.sha1(src.read_bytes()).hexdigest()[:8]
    iid = item_id or (_slug(collection, 20) + "-" + _slug(title, 40) + "-" + digest)
    STUDIO.mkdir(parents=True, exist_ok=True)
    full, prev = "studio-" + iid + ".png", "studio-" + iid + ".jpg"
    with Image.open(src) as im:
        size = list(im.size)
        if src.suffix.lower() == ".png":
            shutil.copyfile(src, STUDIO / full)
        else:
            im.convert("RGB").save(STUDIO / full)
    _preview(STUDIO / full, STUDIO / prev)
    item = {"id": iid, "file": full, "preview": prev, "title": title, "collection": collection, "kind": kind,
            "size": size, "caption": caption, "parent": parent or None, "feedback": feedback or None,
            "origin": origin or None, "tenant": tenant, "created": _now()}
    with _lock:
        items = [i for i in load() if i.get("id") != iid]
        items.insert(0, item)
        _save(items)
    if push if push is not None else cloud():
        try:
            push_items([item])
        except Exception as exc:                    # noqa: BLE001 — listed locally; the next push retries
            item["push_error"] = str(exc)[:200]
    return item


# ------------------------------------------------------------------ the bucket

def _bucket():
    from pipeline.gtm_os import state_sync as S
    return S._client().bucket(S.BUCKET)


def _remote_index(bucket) -> list[dict]:
    try:
        return json.loads(bucket.blob(PREFIX + "index.json").download_as_text()).get("items") or []
    except Exception:                               # noqa: BLE001 — none yet
        return []


def push_items(items: Optional[list[dict]] = None) -> dict:
    """Upload these items' files (all when None) and merge the index into the bucket's."""
    b = _bucket()
    items = load() if items is None else items
    sent = 0
    for it in items:
        for name in (it["file"], it["preview"]):
            p = STUDIO / name
            if p.exists():
                blob = b.blob(PREFIX + name)
                if not blob.exists():
                    blob.upload_from_filename(str(p), content_type="image/png" if name.endswith(".png")
                                              else "image/jpeg")
                    sent += 1
    mine = {i["id"]: i for i in items}
    merged = [i for i in _remote_index(b) if i.get("id") not in mine]
    merged = sorted(list(mine.values()) + merged, key=lambda i: str(i.get("created") or ""), reverse=True)
    b.blob(PREFIX + "index.json").upload_from_string(
        json.dumps({"updated": _now(), "items": merged}, ensure_ascii=False, indent=1),
        content_type="application/json")
    return {"files": sent, "items": len(merged)}


def _push_job(job: dict) -> None:
    if not cloud():
        return
    try:
        _bucket().blob(PREFIX + "jobs/" + job["id"] + ".json").upload_from_string(
            json.dumps(job, ensure_ascii=False, default=str), content_type="application/json")
    except Exception:                               # noqa: BLE001 — the local copy still answers
        pass


def fetch_upload(name: str) -> Optional[Path]:
    """An uploaded or studio image by bare name: on disk, else from the bucket (deployed)."""
    if not FILE.match(name):
        return None
    p = STUDIO / name
    if p.exists():
        return p
    if cloud():
        try:
            STUDIO.mkdir(parents=True, exist_ok=True)
            _bucket().blob(PREFIX + name).download_to_filename(str(p))
            return p
        except Exception:                           # noqa: BLE001
            return None
    return None


# ------------------------------------------------------------------ jobs

def _job_path(jid: str) -> Path:
    return JOBS / (jid + ".json")


def job(jid: str) -> Optional[dict]:
    if not JOB_ID.match(jid or ""):
        return None
    try:
        return json.loads(_job_path(jid).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_job(j: dict) -> None:
    JOBS.mkdir(parents=True, exist_ok=True)
    j["updated"] = _now()
    tmp = _job_path(j["id"]).with_suffix(".tmp")
    tmp.write_text(json.dumps(j, ensure_ascii=False, default=str), encoding="utf-8")
    tmp.replace(_job_path(j["id"]))
    _push_job(j)


def _python() -> str:
    exe = sys.executable
    if os.name == "nt" and exe.lower().endswith("python.exe"):
        w = exe[: -len("python.exe")] + "pythonw.exe"
        if os.path.isfile(w):
            return w
    return exe


def start(kind: str, request: str, *, image: str = "", shape: str = "", tenant: str = "vanna",
          thread_id: str = "") -> dict:
    """Start one job in the background; returns it (state 'running')."""
    jid = "v_" + secrets.token_hex(5)
    j = {"id": jid, "kind": kind, "request": request[:2000], "image": image or None, "shape": shape or None,
         "tenant": tenant, "thread_id": thread_id or None, "state": "running", "step": "Starting",
         "started": _now()}
    _write_job(j)
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | 0x08000000 | getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0)
    subprocess.Popen([_python(), "-m", "pipeline.gtm_creative.studio", "job", jid], cwd=str(REPO),
                     env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(REPO), "BRAIN_TENANT": tenant},
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags,
                     start_new_session=os.name != "nt")
    return j


def _step(j: dict, step: str) -> None:
    j["step"] = step
    _write_job(j)


def _aspect_for(w: int, h: int, shape: str = "") -> tuple[str, float]:
    if shape in ASPECTS:
        return shape, ASPECTS[shape]
    r = w / max(1, h)
    best = min(ASPECTS, key=lambda k: abs(ASPECTS[k] - r) / ASPECTS[k])
    return best, r


def _fit(path: Path, ratio: float, width: int) -> None:
    im = Image.open(path).convert("RGB")
    if im.width / im.height > ratio:
        w = int(im.height * ratio)
        im = im.crop(((im.width - w) // 2, 0, (im.width - w) // 2 + w, im.height))
    else:
        h = int(im.width / ratio)
        im = im.crop((0, (im.height - h) // 2, im.width, (im.height - h) // 2 + h))
    if width and abs(im.width - width) > 4:
        im = im.resize((width, round(width / ratio)), Image.LANCZOS)
    im.save(path)


def revise(src: Path, feedback: str, *, out_dir: Path, name: str, shape: str = "",
           on_step=lambda s: None) -> dict:
    """The owner's image + what they did not like -> a new version from the visual agents."""
    from pipeline.brand_brain import context as C
    from pipeline.gtm_creative import format_poster as FP
    from pipeline.gtm_os import agent_runtime as R
    from pipeline.scripts import claim_safety_gate as G
    from pipeline.scripts.gemini_flash_image import generate_gemini_image
    src, out_dir = Path(src), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        w, h = im.size
        if src.suffix.lower() not in (".png", ".jpg", ".jpeg"):     # a WebP upload: the image model gets a PNG
            src = out_dir / "source.png"
            im.convert("RGB").save(src)
    aspect, ratio = _aspect_for(w, h, shape)
    if shape in ASPECTS:
        ratio = ASPECTS[shape]
    width = (2000 if ratio >= 1 else 1600) if shape in ASPECTS else max(w, 1080)
    on_step("The art director is reading your notes")
    system = C.fill("You are {company}'s Motion/Art Director. You turn the owner's feedback on an image "
                    "into exact changes for the image model. Return strict JSON only.")
    prompt = (C.facts_block(feedback[:400], k=4, excerpts=2) + "\n\n----\n\n"
              "THE IMAGE (attached) is one of the company's posters. THE OWNER SAYS: " + feedback + "\n"
              "Decide how much to change. 'edit': the owner wants specific fixes and the rest stays (layout, "
              "type, colours, every string). 'redesign': the owner dislikes the look or asks for something "
              "different; keep the message, every word and number, the logo and the brand (near-black ground, "
              "violet-to-magenta gradient, Plus Jakarta Sans) unless the owner says otherwise, and change the "
              "design. Each change names the element and exactly what it becomes (any new text in quotes, "
              "letter for letter). Never invent a number, venue, partner or claim; never call the test app "
              "'live'. Then list every string the new image must show, top to bottom, exactly.\n"
              'Return JSON: {"mode": "edit"|"redesign", "changes": [str], "keep": [str], '
              '"new_text": [str] (strings a change adds or rewrites), "strings": [str] (all text on the new '
              'image), "composition": str}')
    for _ in range(2):
        d = R.brain_vision(prompt, [src], agent=FP.AGENT_DIRECTOR, system=system, role="director",
                           temperature=0.3, max_output_tokens=4096)
        g = G.check(" \n".join(str(s) for s in d.get("new_text") or []) or ".", platform="x", require_testnet=False)
        blocked = [v["rule"] + ": " + v["matched"] for v in g["violations"] if v.get("severity") == "BLOCK"]
        if not blocked:
            break
        prompt += "\n\nTHE CLAIM GATE BLOCKED: " + "; ".join(blocked) + ". Rewrite those strings."
    else:
        raise RuntimeError("the claim gate blocked the new text twice: " + "; ".join(blocked))
    R.record_decision(FP.AGENT_DIRECTOR, "studio_revise", {"feedback": feedback, "brief": d, "from": str(src)})
    redesign = str(d.get("mode")) == "redesign"
    changes = [str(c) for c in d.get("changes") or []]
    keep = [str(k) for k in d.get("keep") or []]
    strings = [str(s) for s in d.get("strings") or []]
    on_step("Reading every word on your image")
    before = FP._words(src)
    allowed = {t for s in (d.get("new_text") or []) for t in FP._tokens(str(s))}
    history, correction = [], ""
    for k in range(1, 4):
        on_step("Drawing version " + str(k))
        path = out_dir / f"{name}_try{k}.png"
        if redesign:
            p = ("Redesign the attached poster. The owner said: " + feedback + "\nArrange it like this: "
                 + str(d.get("composition") or "") + "\nCHANGES (all visible):\n"
                 + "\n".join("  - " + c for c in changes)
                 + "\nTEXT (exactly these strings and no others, letter for letter, every digit as given):\n"
                 + "\n".join("  " + s for s in strings))
        else:
            p = ("Edit the attached poster. Keep it the same poster: the same layout, type, colours and every "
                 "string and number, except for exactly these changes:\n" + "\n".join("- " + c for c in changes)
                 + ("\nMUST NOT MOVE: " + "; ".join(keep) if keep else ""))
        p += ("\nNothing overlaps any text; nothing cut off by the edge; keep a safe margin. The logo stays as in "
              "the attached image." + ("\n\nFIX THESE PROBLEMS FROM THE LAST ATTEMPT:\n" + correction
                                       if correction else ""))
        generate_gemini_image(prompt=p, output_path=path, model=R.MODELS["poster"],
                              temperature=0.5 if redesign else 0.2, images=[src], aspect_ratio=aspect,
                              image_size=os.environ.get("VANNA_POSTER_SIZE", "4K"))
        _fit(path, ratio, width)
        on_step("The judge is checking version " + str(k))
        try:
            v = R.brain_vision(
                "Image 1 is the owner's poster; image 2 is the new version. The owner asked: " + feedback
                + "\nCheck: (a) the owner's request is met and these changes are visible: " + " | ".join(changes)
                + "; (b) " + ("the message, every word and number stay" if redesign else
                              "nothing else changed: same layout, type, colours, strings and numbers")
                + "; (c) no element overlaps text, nothing cut off, every word legible and spelt right; "
                "(d) the logo appears once. Return JSON: {\"score\": int (0-10), \"differences\": [str] (each a "
                "concrete fix), \"verdict\": \"SHIP\"|\"REVISE\"|\"REJECT\"}",
                [src, path], agent=FP.AGENT_POSTER, role="reasoning", temperature=0.0, max_output_tokens=2048,
                system="You are the visual agent's judge. Be exact and brief.")
        except Exception as exc:                    # noqa: BLE001 — an unjudged image does not ship
            v = {"score": 0, "differences": ["judge failed: " + str(exc)[:120]], "verdict": "UNJUDGED"}
        after = FP._words(path)
        slips = sorted(after - before - allowed)
        if slips:
            v["verdict"], v["score"] = "REVISE", min(int(v.get("score") or 0), 5)
            v.setdefault("differences", []).insert(
                0, "Text that is on neither the owner's image nor the changes: " + ", ".join(
                    repr(s) for s in slips[:10]) + ". Copy every string letter for letter.")
        v["slips"] = slips
        history.append({"path": str(path), **v})
        if not slips and (str(v.get("verdict")).upper() == "SHIP" or int(v.get("score") or 0) >= 8):
            break
        correction = "\n".join("- " + str(x) for x in (v.get("differences") or [])[:8])
    best = max(history, key=lambda hh: (not hh.get("slips"), str(hh.get("verdict")).upper() == "SHIP",
                                        int(hh.get("score") or 0)))
    final = out_dir / f"{name}.png"
    final.write_bytes(Path(best["path"]).read_bytes())
    return {"final": str(final), "director": d, "attempts": [
        {k2: a.get(k2) for k2 in ("score", "verdict", "differences", "slips")} for a in history]}


def run_job(jid: str) -> dict:
    j = job(jid)
    if not j:
        raise SystemExit("no job " + jid)
    work = STUDIO / "work" / jid
    try:
        if j["kind"] == "revise":
            src = fetch_upload(str(j.get("image") or ""))
            if not src:
                raise RuntimeError("the image is gone; attach it again")
            res = revise(src, j["request"], out_dir=work, name="v", shape=str(j.get("shape") or ""),
                         on_step=lambda s: _step(j, s))
            parent = next((i for i in load() if i.get("file") == j.get("image")), None)
            title = (parent or {}).get("title") or "Your image"
            item = add(Path(res["final"]), title=title + " (revised)", collection="From the Assistant",
                       kind="revise", parent=(parent or {}).get("id") or str(j.get("image")),
                       feedback=j["request"], origin=jid, tenant=j.get("tenant") or "vanna")
            j.update(state="done", item=item, director={k: res["director"].get(k) for k in ("mode", "changes")},
                     attempts=res["attempts"])
        else:
            from pipeline.gtm_creative import format_poster as FP
            _step(j, "The agents are writing and drawing (the founder's format)")
            res = FP.run(j["request"], name="v", out_dir=work)
            d = res.get("director") or {}
            item = add(Path(res["final"]), title=str(d.get("headline") or j["request"])[:90],
                       collection="From the Assistant", kind="create", caption=res.get("caption"),
                       feedback=j["request"], origin=jid, tenant=j.get("tenant") or "vanna")
            j.update(state="done", item=item, attempts=[{k2: a.get(k2) for k2 in ("score", "verdict")}
                                                        for a in res.get("attempts") or []])
        j["step"] = "Done"
    except Exception as exc:                        # noqa: BLE001 — the chat shows it
        j.update(state="failed", error=type(exc).__name__ + ": " + str(exc)[:300])
    j["finished"] = _now()
    _write_job(j)
    if j["state"] == "done":
        shutil.rmtree(work, ignore_errors=True)
    return j


# ------------------------------------------------------------------ the posters made so far

EXPORTS = REPO / "exports" / "agent-posts"
# (collection, folder, file stem -> title). Finals only: no tries, earlier rounds or sources.
CURATED: list[tuple[str, str, dict[str, str]]] = [
    ("Galxe quest", "galxe-art/matte", {"cover": "Galxe cover (matte)", "thumbnail": "Galxe thumbnail (matte)",
                                        "banner": "Galxe wide banner (matte)"}),
    ("Galxe quest", "galxe-art", {"cover": "Galxe cover (glossy)", "thumbnail": "Galxe thumbnail (glossy)",
                                  "banner": "Galxe wide banner (glossy)"}),
    ("Galxe quest", "galxe", {"g1_launch": "Quest launch", "g2_steps": "Four steps to early access",
                              "g3_first_move": "What would you do first?"}),
    ("Perps on spot credit", "perps", {"p1_click_long": "One-click long", "p2_real_short": "A real short",
                                       "p3_funding_vs_borrow": "Funding vs borrow", "p4_health_factor":
                                       "One health factor", "p5_lenders": "For lenders",
                                       "p6_one_account_v2": "One account"}),
    ("Real margin", "real-margin-v2", {f"rm{i}": f"Real margin {i}" for i in range(1, 8)}),
    ("Launch deck slides", "improved/final", {"s01_hero": "Hero", "s06_margin_trade": "Margin trade"}),
    ("Launch deck slides", "improved", {"s03_the_fix": "The fix", "s07_farm": "Farm"}),
    ("Format posts", "format", {"aaplx": "AAPLx", "devnet": "Devnet", "earnsol": "Earn on SOL", "zones": "Zones"}),
    ("Format posts", "artifact-posts", {"a1_waitlist": "Waitlist", "a2_perps_v6": "Perps"}),
    ("Format posts", "", {"nb21_earn": "Earn", "nb21_farm": "Farm", "nb21_sign": "Sign"}),
    ("Brand", "brand", {"brand_overview": "Overview", "brand_composable-leverage": "Composable leverage",
                        "brand_one-click": "One click"}),
    ("Covers", "cover", {"linkedin_cover": "LinkedIn cover", "x_header_1_final": "X header 1",
                         "x_header_2_final": "X header 2", "x_header_3_final": "X header 3"}),
]


def import_exports() -> list[dict]:
    out = []
    for collection, folder, files in reversed(CURATED):     # added newest-first: the first listed ends on top
        for stem, title in reversed(list(files.items())):
            p = EXPORTS / folder / (stem + ".png")
            if not p.exists():
                continue
            cap = None
            pj = p.with_suffix(".post.json")
            if pj.exists():
                try:
                    raw = json.loads(pj.read_text(encoding="utf-8")).get("caption") or {}
                except ValueError:
                    raw = {}
                # Only a caption the claim gate passed (some early ones named a private repo).
                from pipeline.scripts import claim_safety_gate as G
                cap = {ch: raw[ch] for ch in ("x", "linkedin") if isinstance(raw.get(ch), str)
                       and G.check(raw[ch], platform=ch, require_testnet=False)["pass"]} or None
            iid = _slug(collection, 20) + "-" + _slug(folder.replace("/", "-") + "-" + stem, 40)
            out.append(add(p, title=title, collection=collection, caption=cap, kind="export",
                           origin=str(p.relative_to(REPO)).replace("\\", "/"), push=False, item_id=iid))
            time.sleep(0.01)                        # distinct timestamps keep the order stable
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "import-exports":
        print(json.dumps([i["id"] for i in import_exports()], indent=1))
    elif cmd == "push":
        print(json.dumps(push_items()))
    elif cmd == "job" and len(sys.argv) > 2:
        print(json.dumps(run_job(sys.argv[2]), ensure_ascii=False, default=str)[:2000])
    else:
        print(__doc__)
