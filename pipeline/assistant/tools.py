"""What the Mission Control assistant can do — its tools.

The assistant is an agent like the pipeline's: it reaches the brand brain
only through the Brain MCP server (context.brain()), for the company the
chat has selected. It can read everything, start the website analyzer and
the competitor analysis, and make Notion connection links. It never runs a
cycle, approves, kills or publishes by itself: for those it returns an
ACTION CARD, a button the owner presses in the chat.

Each tool returns a JSON-able dict. A tool result may carry `card`, which
the chat window renders (an analysis in progress, a Notion button, an
action to confirm, a run).
"""
from __future__ import annotations

import contextvars
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

# The turn sets this before a tool runs, so a scrape can write its headlines
# back into the chat that asked for them.
_turn_thread: contextvars.ContextVar[str] = contextvars.ContextVar("assistant_thread", default="")


def bind_thread(thread_id: str) -> None:
    _turn_thread.set(thread_id or "")

REPO = Path(__file__).resolve().parents[2]
RUNS = REPO / "pipeline" / "state" / "gtm_runs"
STATUS_DIR = REPO / "pipeline" / "state" / "analyzer"
TENANT = re.compile(r"^[a-z0-9][a-z0-9_-]{1,40}$")
RUN_ID = re.compile(r"^GTM-\d{8}-\d{6}$")


def _brain(tenant: str):
    from pipeline.brand_brain import context as C
    return C.brain(tenant)


def _clip(v: Any, n: int = 600) -> str:
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)
    return s[:n]


# ------------------------------------------------------------------ reading

def list_companies(tenant: str) -> dict:
    from pipeline.brand_brain import store as S
    from pipeline.brand_brain.client import Brain
    out = []
    for t in S.tenants():
        try:
            p = Brain(t).get_brand_profile()
            out.append({"tenant": t, "name": (p.get("company") or {}).get("name") or t,
                        "profile": str(p.get("_status") or "none") + " v" + str(p.get("_version") or "-")})
        except Exception:                           # noqa: BLE001 — listed anyway
            out.append({"tenant": t, "name": t, "profile": "unreadable"})
    return {"companies": out}


def brand_profile(tenant: str, section: str = "") -> dict:
    p = _brain(tenant).get_brand_profile()
    if not p:
        return {"error": "no profile yet for " + tenant}
    if section and section in p:
        return {"section": section, "value": p[section], "version": p.get("_version"), "status": p.get("_status")}
    # The whole profile is long; a summary plus the section names.
    comp = p.get("company") or {}
    return {"version": p.get("_version"), "status": p.get("_status"), "company": comp,
            "voice": (p.get("voice") or {}).get("tone"), "pillars": p.get("pillars"),
            "partners": list((p.get("partners") or {}).keys()),
            "competitors": [c.get("name") for c in p.get("competitors") or []],
            "palette": (p.get("visual") or {}).get("palette"),
            "sections": [k for k in p.keys() if not k.startswith("_")]}


def _search(brain: Any, query: str, **kwargs: Any) -> list:
    """Call the brain search with whatever arguments this process accepts.

    A long-lived brain server can be one revision behind the assistant. Passing
    include_legal to that older method raises TypeError and the whole answer
    shows up red. Drop the argument it does not know and search anyway.
    """
    import inspect
    try:
        allowed = inspect.signature(brain.search_knowledge).parameters
    except (TypeError, ValueError):
        allowed = {}
    if allowed:
        kwargs = {key: value for key, value in kwargs.items() if key in allowed}
    try:
        rows = brain.search_knowledge(query, **kwargs)
    except TypeError as exc:
        if "include_legal" not in str(exc):
            raise
        kwargs.pop("include_legal", None)
        rows = brain.search_knowledge(query, **kwargs)
    return list(rows or [])


def search_knowledge(tenant: str, query: str, k: int = 6) -> dict:
    # The company's own brain first; then, separately, the top public items
    # brain_watch kept (news, Reddit, X; authority 5), which rank below the
    # company's own pages and would otherwise never make the cut. They are
    # marked external so they are quoted as reported, not as fact.
    b = _brain(tenant)
    hits = _search(b, query, k=max(1, min(int(k or 6), 10)), max_authority=4, include_legal=True)
    seen = {h.get("id") for h in hits}
    hits += [h for h in _search(b, query, k=3, sources=["public"], max_authority=5)
             if h.get("id") not in seen]
    return {"query": query, "results": [
        {"text": _clip(h.get("text"), 700), "section": h.get("section"), "title": h.get("title"),
         "source": h.get("source"), "authority": h.get("authority"), "url": h.get("url"),
         "updated_at": h.get("updated_at"),
         **({"external": "reported by others, not confirmed by the company"} if (h.get("authority") or 0) >= 5 else {})}
        for h in hits]}


def whats_new(tenant: str, days: int = 30) -> dict:
    from datetime import timedelta
    since = (datetime.now(timezone.utc) - timedelta(days=int(days or 30))).isoformat()
    return {"since": since, "events": _brain(tenant).get_whats_new(since, 20)}


def competitor_patterns(tenant: str, topic: str = "") -> dict:
    return {"patterns": _brain(tenant).get_competitor_patterns(topic or None, 10)}


def web_search(tenant: str, query: str) -> dict:
    """Google-Search-grounded answer for what the brain cannot know: recent
    news, incidents, market events. External and untrusted, with the pages."""
    import datetime as _dt
    from pipeline.gtm_os import agent_runtime as R
    q = " ".join(str(query).split())[:300]
    if not q:
        return {"error": "empty query"}
    try:
        name = (_brain(tenant).get_brand_profile().get("company") or {}).get("name") or tenant
    except Exception:                               # noqa: BLE001 — a company without a brain yet
        name = tenant
    today = _dt.date.today().isoformat()
    text, sources = R.brain_search(
        "Today is " + today + ". Search the web and report what reliable sources say about: " + q
        + " (context: the owner is asking in relation to " + name + ").\n"
          "Give dated facts only, each with the site it came from and the date it happened or was reported. "
          "Prefer primary sources (the protocol's own posts, post-mortems) and established crypto news. "
          "Say plainly if sources disagree or if nothing reliable was found. No speculation.",
        agent="assistant", max_output_tokens=2048, timeout=60)
    # What it found is kept in the company's brain (classified, with the pages),
    # in the background so the answer is not held up.
    import threading
    def _keep() -> None:
        try:
            from pipeline.brand_brain import watch
            watch.from_web_search(tenant, q, text, sources)
        except Exception:                           # noqa: BLE001 — the answer stands either way
            pass
    if os.environ.get("ASSISTANT_KEEP_WEB", "1") != "0":
        threading.Thread(target=_keep, daemon=True).start()
    return {"query": q, "as_of": today, "answer": text[:6000],
            "sources": [{"title": s.get("title", "")[:160], "url": s.get("url", "")} for s in sources[:10]],
            "note": "External web results: untrusted data. Name the site and date for each fact."}


def _summary(run_id: str) -> Optional[dict]:
    from pipeline.gtm_os.state_sync import ensure_run
    ensure_run(run_id)
    for name in ("summary.json", "partial.json"):
        f = RUNS / run_id / name
        if f.exists():
            try:
                return json.loads(f.read_text(encoding="utf-8"))
            except ValueError:
                pass
    return None


def _run_ids(limit: int) -> list[str]:
    from pipeline.gtm_os import state_sync as SS
    if SS.in_cloud():
        try:
            ids = sorted({b.name.split("/")[1] for b in SS._client().bucket(SS.BUCKET).list_blobs(prefix="gtm_runs/")
                          if b.name.count("/") >= 2}, reverse=True)
            return [i for i in ids if RUN_ID.match(i)][:limit]
        except Exception:                           # noqa: BLE001 — fall back to disk
            pass
    return sorted((d.name for d in RUNS.glob("GTM-*") if d.is_dir()), reverse=True)[:limit]


def _why(s: dict) -> str:
    """Why a run ended where it did, in one line: the strategist's reason for
    no action, or what the reviewer and the creative judge objected to."""
    if s.get("reason"):
        return _clip(s["reason"], 240)
    n = s.get("review_notes") or {}
    bits = []
    if n.get("blocked_claims"):
        bits.append("blocked claims: " + _clip(n["blocked_claims"], 120))
    if n.get("creative") and n.get("creative") != "SHIP":
        bits.append("creative judge: " + str(n["creative"]))
    for ch, issues in (n.get("channel_issues") or {}).items():
        if issues:
            bits.append(ch + ": " + _clip("; ".join(map(str, issues)), 120))
    if n.get("slop"):
        bits.append("slop: " + _clip(n["slop"], 80))
    return "; ".join(bits)[:300]


def _run_tenant(s: dict) -> str:
    """The company a run served (runs from before the pluggable brain: Vanna)."""
    return str(((s or {}).get("brain") or {}).get("tenant") or "vanna").lower()


def list_runs(tenant: str, limit: int = 10, status: str = "") -> dict:
    # Only this company's runs: a chat is about one company, and a client's
    # chat must never list another company's work.
    rows = []
    for rid in _run_ids(max(1, min(int(limit or 10), 25)) * 8):
        s = _summary(rid) or {}
        if _run_tenant(s) != tenant:
            continue
        if status and status.lower() not in str(s.get("status", "")).lower():
            continue
        x = ((s.get("posts") or {}).get("x") or {})
        rows.append({"run_id": rid, "status": s.get("status"), "review_passed": s.get("review_passed"),
                     "signal": _clip(s.get("signal"), 140), "hook": _clip(x.get("hook") or "", 160),
                     "why": _why(s), "started_at": s.get("started_at")})
        if len(rows) >= int(limit or 10):
            break
    return {"runs": rows}


def get_run(tenant: str, run_id: str) -> dict:
    if not RUN_ID.match(str(run_id)):
        return {"error": "run ids look like GTM-20260926-133104"}
    s = _summary(run_id)
    if s and _run_tenant(s) != tenant:
        return {"error": run_id + " is not a run of this company"}
    if not s:
        return {"error": "no run " + run_id}
    posts = s.get("posts") or {}
    fb = {}
    try:
        fb = json.loads((RUNS / run_id / "feedback.json").read_text(encoding="utf-8")).get("latest") or {}
    except Exception:                               # noqa: BLE001 — no decision yet
        pass
    return {"run_id": run_id, "status": s.get("status"), "review_passed": s.get("review_passed"),
            "signal": s.get("signal"), "pillar": s.get("pillar"), "reason": s.get("reason"),
            "review_notes": s.get("review_notes"), "posting_plan": s.get("posting_plan"),
            "x": {"hook": (posts.get("x") or {}).get("hook"), "copy": _clip((posts.get("x") or {}).get("copy"), 1500)},
            "linkedin": _clip((posts.get("linkedin") or {}).get("copy") or "", 800),
            "assets": {k: bool(s.get(k)) for k in ("visual_path", "meme_path", "video_path")},
            "founder_decision": fb.get("verdict"), "brain": s.get("brain"),
            "card": {"type": "run", "run_id": run_id}}


def learning_overview(tenant: str) -> dict:
    from pipeline.gtm_learning import bandit as B
    o = B.overview()
    best = {}
    for dim, opts in (o.get("arms") or {}).items():
        tried = [x for x in opts if x.get("n")]
        if tried:
            top = max(tried, key=lambda x: x.get("mean", 0))
            best[dim] = {"option": top["option"], "mean": top["mean"], "runs": top["n"]}
    return {"events": o.get("n_events"), "preference_pairs": o.get("n_pairs"), "locks": o.get("locks"),
            "best_so_far": best}


# ------------------------------------------------------------------ doing

def _python_exe() -> str:
    """pythonw on Windows: python.exe is a console program and opens a window
    when this dashboard (which has no console) starts it."""
    exe = sys.executable
    if os.name == "nt" and exe.lower().endswith("python.exe"):
        windowless = exe[: -len("python.exe")] + "pythonw.exe"
        if os.path.isfile(windowless):
            return windowless
    return exe


def _hidden_popen(argv: list[str]) -> None:
    # CREATE_NO_WINDOW only. DETACHED_PROCESS makes Windows ignore it and
    # open a PowerShell window for every scrape, post and study.
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | 0x08000000 | getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0)
    subprocess.Popen(
        argv, cwd=str(REPO),
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(REPO)},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags,
        start_new_session=os.name != "nt",
    )


def _spawn(args: list[str], status_file: Path) -> None:
    status_file.parent.mkdir(parents=True, exist_ok=True)
    # Written before the child starts, so the child's own status always wins.
    status_file.write_text(json.dumps({"state": "running", "at": datetime.now(timezone.utc).isoformat()}),
                           encoding="utf-8")
    _hidden_popen([_python_exe(), "-m", *args, "--status-file", str(status_file)])


def add_company(tenant: str, url: str, new_tenant_id: str = "") -> dict:
    """Onboard a company from its website: crawl, measure colours and fonts,
    read the voice, find competitors, and save a DRAFT profile for review."""
    url = url.strip()
    if not re.match(r"^https?://", url):
        url = "https://" + url
    host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0].lower()
    if "." not in host:
        return {"error": "that does not look like a website address"}
    tid = (new_tenant_id or host.split(".")[0]).lower()
    tid = re.sub(r"[^a-z0-9_-]", "-", tid).strip("-")[:40]
    if not TENANT.match(tid):
        return {"error": "the company id must be letters, digits, - or _"}
    f = STATUS_DIR / (tid + ".json")
    if f.exists() and json.loads(f.read_text(encoding="utf-8") or "{}").get("state") == "running":
        return {"error": "an analysis for " + tid + " is already running", "card": {"type": "analysis", "tenant": tid}}
    _spawn(["pipeline.brand_brain.analyzer", url, "--tenant", tid], f)
    return {"started": True, "tenant": tid, "url": url,
            "note": "Takes 1-3 minutes. The draft profile waits for the owner's approval before agents rely on it.",
            "card": {"type": "analysis", "tenant": tid, "url": url}}


def analysis_status(tenant: str, company: str = "") -> dict:
    tid = (company or tenant).lower()
    f = STATUS_DIR / (tid + ".json")
    if not f.exists():
        return {"state": "none", "tenant": tid}
    d = json.loads(f.read_text(encoding="utf-8") or "{}")
    return {"tenant": tid, "state": d.get("state"), "name": d.get("name"),
            "result": d.get("result"), "error": d.get("error"), "card": {"type": "analysis", "tenant": tid}}


def analyse_competitors(tenant: str, find_new: bool = False) -> dict:
    f = STATUS_DIR / (tenant + ".competitors.json")
    args = ["pipeline.brand_brain.analyzer", "competitors", "--tenant", tenant] + (["--suggest"] if find_new else [])
    _spawn(args, f)
    return {"started": True, "tenant": tenant, "note": "Reads each competitor's website and last 30 days of X posts; a few minutes.",
            "card": {"type": "competitors", "tenant": tenant}}


def notion_connect(tenant: str, for_client: bool = False) -> dict:
    from pipeline.brand_brain import notion_oauth as O
    base = os.environ.get("ASSISTANT_BASE_URL", "")
    inv = O.make_invite(tenant, base=base)
    st = O.status(tenant)
    return {"tenant": tenant, "configured": st.get("configured"), "connected": st.get("connected"),
            "workspace": st.get("workspace"), "for_client": bool(for_client),
            "card": {"type": "notion", "tenant": tenant, "url": inv.get("url") or "/connect/notion?invite=" + inv["invite"],
                     "for_client": bool(for_client), "configured": st.get("configured"),
                     "connected": st.get("connected")}}


def find_campaigns(tenant: str, query: str, source: str = "galxe") -> dict:
    """Start a campaign search. The Campaigns page keeps each source in its own list."""
    q = " ".join(str(query or "").split())[:400]
    src = " ".join(str(source or "galxe").split())[:300] or "galxe"
    if not q:
        return {"error": "say what kind of campaign you want"}
    if not TENANT.match(tenant):
        return {"error": "bad company"}
    _hidden_popen([_python_exe(), "-m", "pipeline.gtm_os.campaigns", "run", tenant, q, src])
    return {"started": True, "query": q, "source": src,
            "message": "Searching " + src + ". It lands in its own list on Campaigns."}


def study_brand(tenant: str, name: str, where: str = "") -> dict:
    """Put a company on What Vanna Can Do. A name is enough; a link is optional."""
    who = " ".join(str(name or "").split())[:80]
    src = " ".join(str(where or "").split())[:200]
    if not who:
        return {"error": "say which company"}
    if not TENANT.match(tenant):
        return {"error": "bad company"}
    args = [_python_exe(), "-m", "pipeline.brand_brain.inspiration", "add", tenant, who]
    handle = re.search(r"(?:x|twitter)\.com/([A-Za-z0-9_]{1,30})", src, re.I)
    if handle:
        args += ["--x", handle.group(1)]
    elif re.fullmatch(r"@?[A-Za-z0-9_]{1,30}", src):
        args += ["--x", src.lstrip("@")]
    _hidden_popen(args)
    return {"started": True, "name": who,
            "message": "Studying " + who + ". It lands on What Vanna Can Do, with what a post from it could be."}


def set_post_cadence(tenant: str, instruction: str) -> dict:
    """The owner says how often a post should appear, or says stop, or start."""
    from pipeline.scheduler.configurable_scheduler_daemon import apply_tell, remember_news_chat
    tid = _turn_thread.get()
    # The schedule is the sentence the person typed. A shortened tool
    # argument used to turn "Twitter, every minute, one protocol" into
    # "headlines every 2m".
    said = ""
    if tid:
        try:
            from pipeline.assistant.store import history
            _, recent = history(tenant, tid)
            for msg in reversed(recent):
                if msg.get("role") == "user" and str(msg.get("text") or "").strip():
                    said = str(msg["text"]).strip()
                    break
        except Exception:                           # noqa: BLE001 — the tool argument still applies
            said = ""
    text = said or instruction
    if tid and re.search(r"\b(news|scrape|scraping|fetch|twitter|tweets?|reddit|headline|headlines|socials?|protocols?|defi)\b", text, re.I):
        remember_news_chat(tenant, tid)
    try:
        out = apply_tell(text)
    except Exception as exc:                       # noqa: BLE001 — the chat shows the sentence
        return {"error": str(exc)[:240]}
    return out


def propose_action(tenant: str, action: str, run_id: str = "", directive: str = "", note: str = "") -> dict:
    """An action the OWNER confirms with a button: nothing happens until then."""
    action = action.lower()
    if action not in ("launch_run", "approve", "revise", "kill", "approve_profile"):
        return {"error": "unknown action"}
    if action in ("approve", "revise", "kill") and not RUN_ID.match(run_id):
        return {"error": "which run? (GTM-YYYYMMDD-HHMMSS)"}
    return {"proposed": action, "card": {"type": "action", "action": action, "run_id": run_id or None,
                                         "directive": directive or None, "note": note or None, "tenant": tenant}}


# ------------------------------------------------------------------ registry

def _p(**props: Any) -> dict:
    return {"type": "object", "properties": props}


S_ = {"type": "string"}
I_ = {"type": "integer"}
B_ = {"type": "boolean"}

TOOLS: dict[str, tuple[Callable[..., dict], str, dict]] = {
    "list_companies": (list_companies, "The companies (tenants) that have a brand brain.", _p()),
    "brand_profile": (brand_profile, "The selected company's approved brand profile: identity, voice, pillars, "
                      "partners, competitors, palette. Pass `section` for one part in full.", _p(section=S_)),
    "search_knowledge": (search_knowledge, "Search the selected company's knowledge base (docs, Notion, knowledge "
                         "pack). Use it for any factual question; cite the source it returns.",
                         {**_p(query=S_, k=I_), "required": ["query"]}),
    "web_search": (web_search, "Search the web (Google) for what the brain cannot know: recent news, incidents, "
                   "exploits, market events, anything after the brain's last update or outside the company's own "
                   "docs. Returns a sourced answer and the pages it came from.",
                   {**_p(query=S_), "required": ["query"]}),
    "whats_new": (whats_new, "Dated events (launches, factual updates) in the last `days` days.", _p(days=I_)),
    "competitor_patterns": (competitor_patterns, "How competitors post (pattern summaries), optionally on a topic.",
                            _p(topic=S_)),
    "list_runs": (list_runs, "Recent GTM runs (newest first) with status, signal, hook and `why` (what "
                  "blocked it, or why no action) — enough to answer most questions about runs without opening each. "
                  "`status` filters, e.g. review_blocked, completed, NO_ACTION.", _p(limit=I_, status=S_)),
    "get_run": (get_run, "One run in detail: copy, review notes, why it was blocked, the founder's decision.",
                {**_p(run_id=S_), "required": ["run_id"]}),
    "learning_overview": (learning_overview, "What the learning loop has found so far: best options per strategy arm.",
                          _p()),
    "add_company": (add_company, "Onboard a new company from its website (the website analyzer). Starts in the "
                    "background and shows a live card; the draft profile then waits for approval.",
                    {**_p(url=S_, new_tenant_id=S_), "required": ["url"]}),
    "analysis_status": (analysis_status, "Progress of a website analysis.", _p(company=S_)),
    "analyse_competitors": (analyse_competitors, "Analyse the selected company's competitors (websites + X posts "
                            "into patterns). find_new also web-searches for new ones.", _p(find_new=B_)),
    "notion_connect": (notion_connect, "A Notion connection link for the selected company: a Connect button for the "
                       "owner, or with for_client an invite link to send to the client.", _p(for_client=B_)),
    "study_brand": (study_brand, "Study a company for What Vanna Can Do. name is the company. "
                     "where is optional (an X link or handle). The agents find the handle when it is missing. "
                     "Call this when the owner names a company to learn from. Do it yourself.",
                     {**_p(name=S_, where=S_), "required": ["name"]}),
    "find_campaigns": (find_campaigns, "Search live campaigns. query is what kind. source is where: Galxe, a website, "
                       "a company name, or an X handle. Starts the search; the Campaigns page shows that source on its own.",
                       {**_p(query=S_, source=S_), "required": ["query"]}),
    "set_post_cadence": (set_post_cadence, "The schedule. Pass the owner's sentence unchanged, including "
                         "the source and the gap: Twitter, Reddit, news, a protocol name, \"every minute\", "
                         "\"one protocol\". Twitter means posts from those protocols on Twitter. News is included "
                         "only when they asked for news. Also for stop, pause, band karo, resume. Each job runs "
                         "on its own. Nothing is published.",
                         {**_p(instruction=S_), "required": ["instruction"]}),
    "propose_action": (propose_action, "Offer the owner a button for something only they may do: launch_run "
                       "(optional directive), approve / revise / kill a run, approve_profile. It does NOT do it.",
                       {**_p(action=S_, run_id=S_, directive=S_, note=S_), "required": ["action"]}),
}


# A company's own client (a client link, not the owner) talks about their
# company only: no list of the other companies, no onboarding a new one.
CLIENT_BLOCKED = {"list_companies", "add_company", "set_post_cadence", "find_campaigns", "study_brand"}

# A visitor to the public link reads and asks; nothing they say changes the
# schedule, adds a company, starts paid work or proposes a run.
VISITOR_ALLOWED = {"brand_profile", "search_knowledge", "whats_new", "competitor_patterns",
                   "list_runs", "get_run", "learning_overview", "analysis_status"}


def allowed(name: str, role: str = "owner") -> bool:
    if role == "visitor":
        return name in VISITOR_ALLOWED
    if role == "client":
        return name not in CLIENT_BLOCKED
    return True


def declarations(client: bool = False, role: str = "") -> list[dict]:
    """What the model is offered. A visitor is offered every tool on purpose:
    an action they ask for is then called, refused in chat.turn (allowed()),
    and the refusal is what the model answers with. Hidden tools made it
    answer "set" for a schedule it had no way to set."""
    role = role or ("client" if client else "owner")
    return [{"name": n, "description": d, "parameters": p} for n, (_, d, p) in TOOLS.items()
            if role == "visitor" or allowed(n, role)]


def call(name: str, tenant: str, args: dict) -> dict:
    if name not in TOOLS:
        return {"error": "no tool " + name}
    fn = TOOLS[name][0]
    try:
        return fn(tenant, **{k: v for k, v in (args or {}).items() if v not in (None, "")})
    except TypeError as exc:
        return {"error": "bad arguments: " + str(exc)[:200]}
    except Exception as exc:                        # noqa: BLE001 — the model is told, and can recover
        return {"error": type(exc).__name__ + ": " + str(exc)[:300]}
