"""Website analyzer — a company's URL in, a draft brand profile out.

The architecture's onboarding step (Phase 2). The founder types a URL; this
builds a DRAFT profile and fills the knowledge base and visual memory, and
the founder reviews and approves the draft on the dashboard before any agent
relies on it as approved.

  1. Crawl      the site's sitemap.xml, the pages the home page links to,
                and the docs. / blog. / app. subdomains that exist; every page
                is rendered in a real browser and screenshotted.
  2. Visual     colours from the browser's COMPUTED styles, weighted by the
                area they cover — measured, never guessed by a model — and
                ranked into background, text and accents with usage ratios;
                fonts the same way, by the amount of text set in them; the
                screenshots go to the vision model for layout and style.
  3. Voice      the pages' text to the model: tone, formality, sentence
                length, jargon, CTA patterns, audiences, pillars.
  4. Rivals     3-5 competitors SUGGESTED for the founder to confirm (they are
                marked unconfirmed); only a patterns summary is ever kept.
  5. Review     the draft is saved as a new profile version with status
                "draft" and a list of open questions.

For a tenant that already has a profile the analysis is written as a report
only (analysis.json in the tenant folder) — it never replaces a profile the
founder built — unless --save is passed.

    python -m pipeline.brand_brain.analyzer https://example.com --tenant example
    python -m pipeline.brand_brain.analyzer https://vanna.finance --tenant vanna   # report only
"""
from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pipeline.brand_brain import store as S

AGENT = "BRAIN_analyzer"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")

# Measured in the page: every visible element's colours, weighted by area,
# and its font by the length of text it sets.
_MEASURE_JS = r"""
() => {
  const out = {bg: {}, text: {}, border: {}, fonts: {}, images: [], logo: null};
  const add = (m, k, w) => { if (!k) return; m[k] = (m[k] || 0) + w; };
  const els = Array.from(document.querySelectorAll('body *')).slice(0, 4000);
  const vw = window.innerWidth, vh = Math.max(window.innerHeight, document.body.scrollHeight);
  const bodyBg = getComputedStyle(document.body).backgroundColor;
  add(out.bg, bodyBg, vw * vh);
  add(out.bg, getComputedStyle(document.documentElement).backgroundColor, vw * vh);
  for (const el of els) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) continue;
    const r = el.getBoundingClientRect();
    const area = Math.max(0, r.width) * Math.max(0, r.height);
    // On the page and actually painted: off-canvas menus and collapsed
    // drawers carry colours nobody sees.
    if (area < 4 || r.right <= 0 || r.left >= vw || r.bottom <= -vh) continue;
    add(out.bg, cs.backgroundColor, area);
    const own = Array.from(el.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(' ');
    if (own.length) {
      add(out.text, cs.color, own.length * parseFloat(cs.fontSize || '16'));
      add(out.fonts, cs.fontFamily.split(',')[0].replace(/["']/g, '').trim(), own.length);
    }
    if (parseFloat(cs.borderTopWidth) > 0) add(out.border, cs.borderTopColor, r.width);
    if (el.tagName === 'IMG' && el.naturalWidth >= 160 && el.naturalHeight >= 120 && el.currentSrc)
      out.images.push({src: el.currentSrc, w: el.naturalWidth, h: el.naturalHeight, alt: el.alt || ''});
    if (!out.logo && (el.tagName === 'IMG' || el.tagName === 'svg') && r.top < 120 && r.left < vw / 2 &&
        /logo|brand/i.test((el.getAttribute('alt') || '') + (el.getAttribute('class') || '') + (el.parentElement && el.parentElement.getAttribute('class') || '')))
      out.logo = el.tagName === 'IMG' ? el.currentSrc : 'svg';
  }
  return out;
}
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rgb(css: str) -> Optional[tuple[int, int, int, float]]:
    m = re.match(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s/]+([\d.]+))?", css or "")
    if not m:
        return None
    a = float(m.group(4)) if m.group(4) is not None else 1.0
    return int(float(m.group(1))), int(float(m.group(2))), int(float(m.group(3))), a


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#%02X%02X%02X" % rgb


def _bucket(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    """Merge near-identical shades (anti-aliasing, hover tints) into one."""
    return tuple(min(255, int(round(c / 8.0) * 8)) for c in rgb)  # type: ignore[return-value]


def palette_from(measures: list[dict]) -> dict[str, Any]:
    """Background, text and accent colours with their usage ratios."""
    bg, text, border = Counter(), Counter(), Counter()
    for m in measures:
        for src, dst in ((m.get("bg", {}), bg), (m.get("text", {}), text), (m.get("border", {}), border)):
            for css, w in src.items():
                c = _rgb(css)
                if c and c[3] >= 0.5:
                    dst[_bucket(c[:3])] += float(w)
    total = sum(bg.values()) + sum(text.values()) or 1.0

    def sat(c):
        h, l, s = colorsys.rgb_to_hls(*(x / 255 for x in c))
        return s * (1 - abs(2 * l - 1))

    ground = bg.most_common(1)[0][0] if bg else (255, 255, 255)

    def lum(c):
        def ch(x):
            x /= 255
            return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
        r, g, b = (ch(v) for v in c)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def contrast(a, b):
        la, lb = sorted((lum(a), lum(b)), reverse=True)
        return (la + 0.05) / (lb + 0.05)

    # Text that cannot be read on the page's ground (dark text on a dark
    # site, from light-themed widgets or hidden copy) is not the brand's ink.
    legible = Counter({c: w for c, w in text.items() if contrast(c, ground) >= 3})
    ink = (legible or text).most_common(1)[0][0] if text else (0, 0, 0)
    everything = bg + text + border
    accents = [c for c, _ in everything.most_common(60) if sat(c) > 0.25 and c not in (ground, ink)]
    merged: list[tuple[int, int, int]] = []
    for c in accents:                                # distinct accents only
        if all(sum(abs(a - b) for a, b in zip(c, m)) > 60 for m in merged):
            merged.append(c)
    palette = {"ground": _hex(ground), "text": _hex(ink)}
    for i, c in enumerate(merged[:4]):
        palette["accent" if i == 0 else "accent_" + str(i + 1)] = _hex(c)
    usage = {}
    for k, v in palette.items():
        rgb = tuple(int(v[i:i + 2], 16) for i in (1, 3, 5))
        usage[k] = round((bg.get(rgb, 0) + text.get(rgb, 0)) / total, 3)
    usage["_basis"] = "measured: share of rendered area (backgrounds) and text weight, across the crawled pages"
    return {"palette": palette, "palette_usage": usage}


def fonts_from(measures: list[dict]) -> dict[str, str]:
    f = Counter()
    for m in measures:
        for name, w in (m.get("fonts") or {}).items():
            if name and not name.startswith("-"):
                f[name] += w
    generic = {"monospace", "sans-serif", "serif", "system-ui", "ui-sans-serif", "ui-monospace",
               "cursive", "inherit", "initial", "-apple-system", "blinkmacsystemfont", "arial",
               "helvetica", "times new roman"}
    named = [n for n, _ in f.most_common(12) if n.lower() not in generic]
    ranked = (named or [n for n, _ in f.most_common(4)])[:4]
    out = {"display": ranked[0]} if ranked else {}
    mono = next((n for n in ranked if re.search(r"mono|code|courier", n, re.I)), None)
    if mono:
        out["mono"] = mono
    if len(ranked) > 1 and ranked[1] != mono:
        out["secondary"] = ranked[1]
    return out


# ------------------------------------------------------------------- crawling

def _same_site(url: str, root: str) -> bool:
    h, r = urllib.parse.urlparse(url).netloc.lower(), urllib.parse.urlparse(root).netloc.lower()
    base = r[4:] if r.startswith("www.") else r
    return h == r or h.endswith("." + base) or h == base


def _sitemap(root: str, limit: int = 80) -> list[str]:
    urls: list[str] = []
    try:
        req = urllib.request.Request(urllib.parse.urljoin(root, "/sitemap.xml"), headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            tree = ET.fromstring(r.read())
        for loc in tree.iter():
            if loc.tag.endswith("loc") and loc.text:
                urls.append(loc.text.strip())
    except Exception:                               # noqa: BLE001 — no sitemap
        pass
    return urls[:limit]


def _subdomains(root: str) -> list[str]:
    host = urllib.parse.urlparse(root).netloc.lower()
    base = host[4:] if host.startswith("www.") else host
    found = []
    for sub in ("docs", "blog", "app"):
        url = "https://" + sub + "." + base
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
            with urllib.request.urlopen(req, timeout=8) as r:
                if r.status < 400:
                    found.append(url)
        except Exception:                           # noqa: BLE001 — not there
            continue
    return found


def crawl(root: str, out_dir: Path, *, max_pages: int = 18) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    out_dir.mkdir(parents=True, exist_ok=True)
    queue = [root] + _subdomains(root) + _sitemap(root)
    seen: set[str] = set()
    pages: list[dict] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, user_agent=UA)
        page = ctx.new_page()
        while queue and len(pages) < max_pages:
            url = queue.pop(0).split("#")[0].rstrip("/") or root
            if url in seen or not _same_site(url, root):
                continue
            seen.add(url)
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception:                       # noqa: BLE001 — slow page: use what loaded
                try:
                    page.wait_for_timeout(2000)
                except Exception:                   # noqa: BLE001 — page gone
                    continue
            try:
                title = page.title()
                text = page.evaluate("() => document.body ? document.body.innerText : ''")
                measure = page.evaluate(_MEASURE_JS)
                links = page.evaluate("() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)")
                shot = out_dir / (hashlib.sha1(url.encode()).hexdigest()[:10] + ".png")
                page.screenshot(path=str(shot))
            except Exception:                       # noqa: BLE001 — this page fails alone
                continue
            pages.append({"url": url, "title": title, "text": text[:40000], "measure": measure,
                          "screenshot": str(shot)})
            for l in links:
                l = l.split("#")[0].rstrip("/")
                if l and l not in seen and _same_site(l, root) and not re.search(
                        r"\.(pdf|zip|png|jpe?g|svg|mp4)$|/(login|signin|signup)", l, re.I):
                    queue.append(l)
        browser.close()
    return {"root": root, "pages": pages}


# --------------------------------------------------------------- the models

def _voice(pages: list[dict]) -> dict[str, Any]:
    from pipeline.gtm_os import agent_runtime as R
    corpus = "\n\n".join("## " + p["title"] + " (" + p["url"] + ")\n" + p["text"][:3500] for p in pages[:10])[:24000]
    return R.brain_json(
        "These are the pages of one company's website. Describe the company and how it writes, "
        "from the text only. Invent nothing that is not on the pages.\n\n" + corpus
        + '\n\nReturn JSON: {"name": str, "one_liner": str, "what_it_is": str (2 sentences), '
          '"category": str, "stage": str (e.g. live, beta, testnet, unknown), '
          '"tone": [str], "formality": "formal"|"neutral"|"casual", '
          '"sentence_length": "short"|"medium"|"long", "jargon_level": "low"|"medium"|"high", '
          '"cta_patterns": [str], "cta": str (their main call to action, verbatim if possible), '
          '"do": [str], "dont": [str], "audiences": [{"name": str, "core_pain": str}], '
          '"pillars": [str], "relevance_terms": [str] (10-25 lowercase words and phrases for '
          'their domain), "known_entities": [str] (products, partners, chains named on the pages), '
          '"partners_named": [str], "product_terms": [str]}',
        agent=AGENT, role="reasoning", temperature=0.2, max_output_tokens=4096,
        system="You analyse a brand's own website precisely and never invent facts.")


def _visual_style(pages: list[dict]) -> dict[str, Any]:
    from pipeline.gtm_os import agent_runtime as R
    shots = [Path(p["screenshot"]) for p in pages[:4] if Path(p["screenshot"]).exists()]
    if not shots:
        return {}
    return R.brain_vision(
        "These are screenshots of one company's website. Describe its visual style so a designer "
        "could make social posts that look like this brand. Return JSON: "
        '{"house_style": str (2-3 sentences: ground, colour use, typography, imagery, layout), '
        '"layout_patterns": [str], "illustration_type": str, "style_tags": [str], '
        '"avoid": [str] (what this brand visibly never does)}',
        shots, agent=AGENT, role="reasoning", temperature=0.2, max_output_tokens=2048,
        system="You are a precise brand designer.")


def _competitors(voice: dict) -> list[dict]:
    from pipeline.gtm_os import agent_runtime as R
    try:
        out = R.brain_json(
            "Company: " + str(voice.get("name")) + " — " + str(voice.get("what_it_is")) + " Category: "
            + str(voice.get("category")) + ".\nSuggest 3-5 direct competitors a founder would name. "
            'Return JSON: {"competitors": [{"name": str, "why": str (under 15 words)}]}',
            agent=AGENT, role="reasoning", temperature=0.2, max_output_tokens=2048,
            system="You know the market. Suggest only real, currently operating companies.")
        return [{"name": c["name"], "focus": c.get("why", ""), "confirmed": False}
                for c in (out.get("competitors") or [])[:5] if c.get("name")]
    except Exception:                               # noqa: BLE001 — none suggested
        return []


# ------------------------------------------------------------------- assembly

def draft_profile(root: str, crawl_out: dict, voice: dict, style: dict,
                  competitors: list[dict], logo: Optional[str]) -> dict[str, Any]:
    measures = [p["measure"] for p in crawl_out["pages"] if p.get("measure")]
    pal = palette_from(measures)
    open_q = [
        "Competitors were suggested by a model — confirm or edit the list.",
        "Approved claims, true figures and never-claim rules are empty: add them from the "
        "company's docs or facts ledger before the reviewer can fact-check posts.",
    ]
    if not logo:
        open_q.append("No logo was detected on the site — add visual.logo.path.")
    if voice.get("stage") in (None, "", "unknown"):
        open_q.append("The product's stage (live, beta, testnet) is not stated on the site.")
    return {
        "schema": "brand-profile/1",
        "company": {"name": voice.get("name"), "one_liner": voice.get("one_liner"),
                    "what_it_is": voice.get("what_it_is"), "category": voice.get("category"),
                    "stage": voice.get("stage"), "deployment": "", "website": root},
        "voice": {"tone": voice.get("tone", []), "formality": voice.get("formality"),
                  "sentence_length": voice.get("sentence_length"),
                  "jargon_level": voice.get("jargon_level"), "do": voice.get("do", []),
                  "dont": voice.get("dont", []), "cta_patterns": voice.get("cta_patterns", []),
                  "cta": voice.get("cta", ""), "required_disclosure": ""},
        "audiences": [{"segment_id": "A" + str(i + 1), **a} for i, a in enumerate(voice.get("audiences") or [])],
        "pillars": voice.get("pillars", []),
        "claims": {"approved": [], "prohibited": [], "true_figures": [], "never_state": []},
        "partners": {},
        "partners_named_on_site": voice.get("partners_named", []),
        "competitors": competitors,
        "relevance_terms": voice.get("relevance_terms", []),
        "known_entities": voice.get("known_entities", []),
        "visual": {**pal, "fonts": fonts_from(measures),
                   "logo": {"path": logo or "", "description": "the logo as it appears on " + root},
                   "house_style": style.get("house_style", ""),
                   "layout_patterns": style.get("layout_patterns", []),
                   "illustration_type": style.get("illustration_type", ""),
                   "style_tags": style.get("style_tags", []),
                   "prohibited": "; ".join(style.get("avoid", [])), "avoid_colors": [],
                   "anchors": {}},
        "open_questions": open_q,
        "analyzer": {"at": _now(), "root": root, "pages": [p["url"] for p in crawl_out["pages"]]},
    }


def _logo(crawl_out: dict, dest: Path) -> Optional[str]:
    for p in crawl_out["pages"]:
        src = (p.get("measure") or {}).get("logo")
        if src and src != "svg" and src.startswith("http"):
            try:
                req = urllib.request.Request(src, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=15) as r:
                    data = r.read()
                ext = ".svg" if src.lower().endswith(".svg") else ".png"
                f = dest / ("logo" + ext)
                f.write_bytes(data)
                return f.relative_to(S.ROOT.parents[2]).as_posix()
            except Exception:                       # noqa: BLE001 — try the next page
                continue
    return None


def analyze(root: str, tenant: str, *, save: bool = False, max_pages: int = 18,
            authority: int = 3) -> dict[str, Any]:
    from pipeline.brand_brain.chunking import chunk_page
    from pipeline.brand_brain.client import Brain
    from pipeline.brand_brain.onboard import index_profile, remember_image

    t0 = time.time()
    tdir = S.tenant_dir(tenant)
    work = tdir / "website"
    existing = S.exists(tenant) and bool(Brain(tenant).profile_versions())
    crawl_out = crawl(root, work, max_pages=max_pages)
    if not crawl_out["pages"]:
        return {"ok": False, "error": "nothing could be crawled at " + root}
    voice = _voice(crawl_out["pages"])
    style = _visual_style(crawl_out["pages"])
    competitors = _competitors(voice)
    logo = _logo(crawl_out, work)
    profile = draft_profile(root, crawl_out, voice, style, competitors, logo)
    report = {"root": root, "tenant": tenant, "at": _now(), "pages": len(crawl_out["pages"]),
              "profile": profile, "seconds": round(time.time() - t0, 1)}
    (tdir).mkdir(parents=True, exist_ok=True)
    (tdir / "analysis.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    if existing and not save:
        report["saved"] = False
        report["note"] = ("tenant already has a profile: the analysis is a report "
                          "(analysis.json); pass --save to add it as a new draft")
        return report
    brain = Brain(tenant, create=True)
    report["version"] = brain.save_profile(profile, status="draft", source="website analyzer: " + root,
                                           note="drafted from " + str(len(crawl_out["pages"])) + " pages")
    name = profile["company"].get("name") or tenant
    added = 0
    for p in crawl_out["pages"]:
        chunks = chunk_page(p["text"], title=p["title"] or p["url"], company=name, source_label="website")
        r = brain.upsert_page("website:" + p["url"], chunks, source="website", authority=authority, url=p["url"])
        added += r["added_or_changed"]
        remember_image(Path(p["screenshot"]), kind="website", note=p["url"], tenant=tenant)
    report["knowledge_chunks"] = added
    report["reindexed"] = index_profile(tenant)
    report["saved"] = True
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description="Draft a brand profile from a website")
    ap.add_argument("url")
    ap.add_argument("--tenant", required=True)
    ap.add_argument("--save", action="store_true", help="also save as a new draft for an existing tenant")
    ap.add_argument("--pages", type=int, default=18)
    ap.add_argument("--authority", type=int, default=3,
                    help="how far site text counts as evidence (3 knowledge, 4 archive: not proof)")
    ap.add_argument("--status-file", default=None, help="write running / done / failed here (dashboard jobs)")
    a = ap.parse_args()
    url = a.url if a.url.startswith("http") else "https://" + a.url
    status = Path(a.status_file) if a.status_file else None

    def mark(state: str, **kw) -> None:
        if status:
            status.parent.mkdir(parents=True, exist_ok=True)
            status.write_text(json.dumps({"state": state, "url": url, "tenant": a.tenant,
                                          "at": _now(), **kw}, ensure_ascii=False, default=str),
                              encoding="utf-8")

    mark("running")
    try:
        out = analyze(url, a.tenant, save=a.save, max_pages=a.pages, authority=a.authority)
    except Exception as exc:                        # noqa: BLE001 — reported to the dashboard
        mark("failed", error=str(exc)[:400])
        raise
    mark("done" if out.get("ok", True) else "failed",
         result={k: v for k, v in out.items() if k != "profile"},
         name=(out.get("profile") or {}).get("company", {}).get("name"))
    brief = {k: v for k, v in out.items() if k != "profile"}
    brief["palette"] = (out.get("profile") or {}).get("visual", {}).get("palette")
    brief["fonts"] = (out.get("profile") or {}).get("visual", {}).get("fonts")
    brief["name"] = (out.get("profile") or {}).get("company", {}).get("name")
    print(json.dumps(brief, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
