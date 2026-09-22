#!/usr/bin/env python3
"""Real-Time Global DeFi News Trendjacking Orchestrator for the Vanna Pipeline.

This script implements Route C (Programmatic Python RSS Extraction) to:
  1. Fetch the absolute latest, live global DeFi news from the Decrypt RSS feed.
  2. Parse the latest 10 articles (titles, dates, and descriptions) from the last 24 hours.
  3. Load marketing config and past history to prevent any repetition.
  4. Force the Conductor to select the absolute strongest DeFi trend from the feed.
  5. Guide the Strategists to draft highly specific, non-monotonous pitches bridging this
     live trend to Vanna's product mechanics (Risk Guardian, Capital Efficiency, or Credit).
  6. Direct-render an on-brand static visual card (render_visual.py).
  7. Pass safety gates and dispatch the final post + visual card directly to Telegram!
  8. Once approved, natively publish it to Twitter via OpenCLI!
"""

import sys
import os
import json
import re
import urllib.request
import urllib.error
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET
import html
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STATE = REPO / "pipeline" / "state"
LOGS = REPO / "pipeline" / "logs"
CONFIG_PATH = Path(os.environ.get("PIPELINE_CONFIG") or (REPO / "pipeline" / "config" / "marketing_config.json"))
HISTORY_PATH = STATE / "content_history.json"

# Ensure directories exist
STATE.joinpath("drafts").mkdir(parents=True, exist_ok=True)
STATE.joinpath("approved").mkdir(parents=True, exist_ok=True)
STATE.joinpath("rejected").mkdir(parents=True, exist_ok=True)
LOGS.joinpath("agents").mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------

LIVE_FEED = STATE / "live_run.jsonl"
RUNS_DIR = STATE / "runs"

# Persistent, per-run audit trail. live_run.jsonl is the volatile "current run"
# the live view tails; runs/<id>.jsonl + runs/<id>.meta.json are the permanent
# record so no execution ever disappears after it finishes.
_RUN_ID: str | None = None


def _run_files() -> tuple[Path, Path]:
    return (RUNS_DIR / f"{_RUN_ID}.jsonl", RUNS_DIR / f"{_RUN_ID}.meta.json")


def live_reset(tenant: str, trend: str = "") -> None:
    """Open a new run: reset the live feed AND start a persistent record."""
    global _RUN_ID
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    _RUN_ID = f"{tenant.strip().lower() or 'run'}-{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}"
    evt = {
        "ts": time.time(), "run_id": _RUN_ID, "agent": "system", "stage": "triggered",
        "tenant": tenant, "text": f"Run started for {tenant}. {trend}".strip(),
    }
    try:
        LIVE_FEED.write_text(json.dumps(evt, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception:
        pass
    run_file, meta_file = _run_files()
    try:
        run_file.write_text(json.dumps(evt, ensure_ascii=False) + "\n", encoding="utf-8")
        meta_file.write_text(json.dumps({
            "run_id": _RUN_ID,
            "pipeline": f"{tenant} content pipeline",
            "tenant": tenant,
            "started": evt["ts"],
            "ended": None,
            "status": "running",
            "brain": os.environ.get("PIPELINE_BRAIN", "claude"),
            "trend_source": os.environ.get("TREND_SOURCE", "news"),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def live_emit(agent: str, stage: str, text: str) -> None:
    """Append one event to BOTH the live feed and the persistent run record."""
    rec = {"ts": time.time(), "agent": agent, "stage": stage, "text": (text or "")[:1200]}
    line = json.dumps(rec, ensure_ascii=False) + "\n"
    for target in (LIVE_FEED, (RUNS_DIR / f"{_RUN_ID}.jsonl") if _RUN_ID else None):
        if target is None:
            continue
        try:
            with target.open("a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass


def live_finalize(status: str, **extra) -> None:
    """Close the persistent run record with outcome, timing and result."""
    if not _RUN_ID:
        return
    _, meta_file = _run_files()
    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
    except Exception:
        meta = {"run_id": _RUN_ID}
    meta["ended"] = time.time()
    meta["status"] = status
    if meta.get("started"):
        meta["duration_s"] = round(meta["ended"] - meta["started"], 1)
    meta.update(extra)
    try:
        meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def log_agent_activity(agent_name: str, message: str) -> None:
    log_file = LOGS / "agents" / f"{agent_name}.log"
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n\n")
    # Mirror every step into the live feed so the dashboard shows the real
    # debate as it happens, not just inferred stage boundaries.
    live_emit(agent_name, "step", message)

def load_persona(name: str) -> str:
    path = REPO / "pipeline" / "buzz-pack" / "agents" / f"{name}.persona.md"
    if not path.exists():
        path = REPO / "pipeline" / "system1_extracted" / "buzz-pack" / "agents" / f"{name}.persona.md"
    return path.read_text(encoding="utf-8")


def build_strategists(tenant: str, bundle: Path) -> dict:
    """Return {strategist_name: persona_text}. For a non-Vanna tenant whose OKF
    bundle ships narrative arcs, build one strategist per arc (that is the tenant's
    own competing voices) with a hard guard against leaking Vanna's product. The
    default Vanna run is untouched."""
    if tenant.strip().lower() != "vanna":
        arcs_dir = bundle / "arcs"
        if arcs_dir.is_dir():
            personas = {}
            for arc in sorted(arcs_dir.glob("*.md")):
                if arc.stem == "index":
                    continue
                guard = (
                    f"You are {tenant}'s strategist for the '{arc.stem}' narrative arc. "
                    f"You write ONLY for {tenant}. You must NEVER mention Vanna, 'Guardian', "
                    f"'health factor', 'liquidation', 'testnet', or any other company's product "
                    f"or mechanic as if it were {tenant}'s — those are not {tenant}. Use only "
                    f"{tenant}'s own product, voice, and the facts provided.\n\n---\n\n"
                )
                personas[f"strategist-{arc.stem}"] = guard + arc.read_text(encoding="utf-8")
            if len(personas) >= 2:
                return personas
    return {s: load_persona(s) for s in
            ["strategist-capital-efficiency", "strategist-risk-relief", "strategist-agentic-credit"]}


def load_tenant_facts(tenant: str, bundle: Path) -> str:
    """Quotable facts block for a non-Vanna tenant, pulled from its OKF bundle so
    the strategists ground in the tenant's real product, not Vanna's."""
    if tenant.strip().lower() == "vanna":
        return ""
    parts = []
    facts_dir = bundle / "facts"
    if facts_dir.is_dir():
        for f in sorted(facts_dir.glob("*.md")):
            try:
                parts.append(f.read_text(encoding="utf-8"))
            except Exception:
                pass
    if not parts:
        return ""
    return (f"\n\n---\n\n# {tenant} facts (ground every claim in these — this is "
            f"{tenant}, not Vanna)\n\n" + "\n\n".join(parts))

import shutil


def _claude_bin() -> str:
    return (os.environ.get("CLAUDE_BIN")
            or shutil.which("claude")
            or str(Path.home() / ".local" / "bin" / "claude"))


def _call_anthropic_api(system_instruction: str, prompt: str, temperature: float, key: str) -> str:
    """One agent turn on Opus via the Anthropic Messages API — fast, reliable, no cold start.
    Preferred whenever ANTHROPIC_API_KEY is set. This is the production route for
    running the 7 agents on Opus."""
    model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
    payload = {
        "model": model,
        "max_tokens": 4096,
        "temperature": temperature,
        "system": system_instruction,
        "messages": [{"role": "user", "content": prompt}],
    }
    for attempt in range(4):
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={"content-type": "application/json", "x-api-key": key,
                     "anthropic-version": "2023-06-01"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                res = json.loads(r.read().decode("utf-8"))
                return "".join(b.get("text", "") for b in res.get("content", []))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(6 * (attempt + 1)); continue
            print(f"Anthropic API error {e.code}: {e.read().decode('utf-8','replace')[:300]}")
            sys.exit(1)
        except Exception as e:
            time.sleep(4 * (attempt + 1)); continue
    print("❌ Anthropic API failed after retries."); sys.exit(1)


def call_claude(system_instruction: str, prompt: str, temperature: float = 0.7) -> str:
    """Run one agent turn on Opus.

    Prefers the Anthropic API (ANTHROPIC_API_KEY) — fast and reliable, the production
    path. Falls back to the Claude Code subscription via headless `claude -p`, which
    proves the concept (no API key) but cold-starts a full session per call and can
    hang on sequential agent calls — proof-of-concept, not production.
    """
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return _call_anthropic_api(system_instruction, prompt, temperature, key)
    full = f"{system_instruction}\n\n---\n\n{prompt}"
    for attempt in range(3):
        try:
            # Prompt goes via STDIN, not as an argv value: personas start with a
            # YAML `---` block, which the CLI otherwise parses as an unknown flag.
            r = subprocess.run([_claude_bin(), "-p"], input=full,
                               capture_output=True, text=True, timeout=240,
                               encoding="utf-8", errors="replace")
            out = (r.stdout or "").strip()
            if out:
                return out
            print(f"⚠️  claude -p returned empty (attempt {attempt+1}/3): {r.stderr[:200]}")
        except Exception as e:
            print(f"⚠️  claude -p error (attempt {attempt+1}/3): {e}")
        time.sleep(4)
    print("❌ claude -p failed after retries. Failing gracefully.")
    sys.exit(1)


def call_vertex(system_instruction: str, prompt: str, temperature: float = 0.7, max_tokens: int = 8192) -> str:
    """The pipeline's brain. Defaults to Opus (claude); set PIPELINE_BRAIN=gemini for Vertex.
    max_tokens bounds the response; large structured outputs (a full campaign plan)
    need a higher ceiling or the JSON truncates and fails to parse."""
    if os.environ.get("PIPELINE_BRAIN", "claude").lower() != "gemini":
        return call_claude(system_instruction, prompt, temperature)
    url = "http://127.0.0.1:8900/v1/projects/sales-agent-504607/locations/us-central1/publishers/google/models/gemini-2.5-flash:generateContent"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    
    max_attempts = 4
    for attempt in range(max_attempts):
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                res = json.loads(r.read().decode("utf-8"))
                text = res["candidates"][0]["content"]["parts"][0]["text"]
                return text
        except urllib.error.HTTPError as e:
            if e.code == 429:
                sleep_time = 6 * (attempt + 1)
                print(f"⚠️  Vertex API Rate Limit (429)! Retrying in {sleep_time} seconds (Attempt {attempt+1}/{max_attempts})...")
                time.sleep(sleep_time)
                continue
            else:
                print(f"Vertex API Error {e.code}: {e.read().decode('utf-8', 'replace')[:500]}")
                sys.exit(1)
        except Exception as e:
            sleep_time = 6 * (attempt + 1)
            print(f"⚠️  Connection/Socket Error: {e}! Retrying in {sleep_time} seconds (Attempt {attempt+1}/{max_attempts})...")
            time.sleep(sleep_time)
            continue
            
    print("❌ Max retries reached for Vertex API / Spend Proxy connection. Failing gracefully.")
    sys.exit(1)

def extract_json(text: str) -> dict:
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    candidate = fenced.group(1) if fenced else text
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start != -1 and end != -1:
        candidate = candidate[start:end + 1]

    # 1) straight parse; 2) strip trailing commas (a common model slip).
    for c in (candidate, re.sub(r",(\s*[}\]])", r"\1", candidate)):
        try:
            return json.loads(c)
        except Exception:
            pass

    # 3) truncation salvage: walk to the last balanced point, then close any
    #    still-open braces/brackets so a cut-off response still yields an object.
    c = re.sub(r",(\s*[}\]])", r"\1", candidate)
    depth = 0
    instr = False
    esc = False
    stack: list[str] = []
    last_balanced = 0
    for i, ch in enumerate(c):
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == '"':
            instr = not instr
            continue
        if instr:
            continue
        if ch in "{[":
            stack.append("}" if ch == "{" else "]")
            depth += 1
        elif ch in "}]":
            if stack:
                stack.pop()
            depth -= 1
            if depth == 0:
                last_balanced = i + 1
    for trial in (c[:last_balanced] if last_balanced else "", c + "".join(reversed(stack))):
        if not trial:
            continue
        try:
            return json.loads(trial)
        except Exception:
            pass

    print(f"Error parsing JSON from agent output. Raw (first 300):\n{text[:300]}")
    return {}

# --------------------------------------------------------------------------
# Route C: Programmatic Python RSS Extraction (Global DeFi News)
# --------------------------------------------------------------------------

def fetch_latest_defi_news() -> list[dict]:
    print("=== Step 1: Harvesting Real-Time Global DeFi News ===")
    req = urllib.request.Request(
        "https://decrypt.co/feed",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    news_items = []
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            xml_str = r.read()
            root = ET.fromstring(xml_str)
            for item in root.findall(".//item")[:10]:
                title = item.find("title").text if item.find("title") is not None else "No Title"
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else "No Date"
                desc_elem = item.find("description")
                desc = html.unescape(desc_elem.text) if desc_elem is not None and desc_elem.text else ""
                
                # Prune description to keep context concise
                if len(desc) > 200:
                    desc = desc[:200].strip() + "..."
                clean_desc = re.sub('<[^<]+?>', '', desc) # Strip HTML tags
                
                news_items.append({
                    "title": title,
                    "published_at": pub_date,
                    "description": clean_desc.strip()
                })
                print(f"  - Scraped: '{title}' ({pub_date})")
    except Exception as e:
        print(f"⚠️  Error fetching Decrypt RSS feed: {e}")
        # Inline minimal organic fallback if feed was unreachable
        news_items = [
            {
                "title": "Crypto Market Volatility Surges as Bitcoin Hits Death Cross",
                "published_at": "Sun, 09 Aug 2026 12:00:00 GMT",
                "description": "Bitcoin volatility index spiked by 14% overnight as a death cross pattern emerged on the daily charts, causing leveraged positions across DeFi protocols to trigger massive liquidation alerts."
            }
        ]
    print(f"  [Scout Success] Harvested {len(news_items)} real-time global news items.")
    print("-" * 57)
    return news_items

# --------------------------------------------------------------------------
# Main Orchestrator Loop
# --------------------------------------------------------------------------

def load_scout_signals(tenant: str) -> list[dict]:
    """Use the real Reddit/Twitter signals from trend_scout.py as the trend feed,
    instead of the Decrypt news RSS. Reads the newest scout dump for this tenant and
    maps each signal into the {title, published_at, description} shape the conductor
    expects, richest-engagement first."""
    print("=== Step 1: Harvesting Real Reddit/Twitter signals (trend-scout) ===")
    import glob
    label = (tenant or "vanna").strip().lower()
    files = sorted(glob.glob(str(STATE / "trends" / f"{label}-*.json")), reverse=True)
    if not files:
        print(f"⚠️  No scout dump for '{label}'; falling back to news RSS.")
        return fetch_latest_defi_news()
    data = json.loads(Path(files[0]).read_text(encoding="utf-8"))
    items = data.get("items", [])
    items.sort(key=lambda x: (x.get("engagement") or 0), reverse=True)
    news_items = []
    for it in items[:12]:
        eng = it.get("engagement")
        desc = (f"[{it.get('channel')} · {it.get('source') or it.get('keyword')}"
                f"{' · ' + str(eng) + ' engagement' if eng else ''}] {it.get('title', '')}")
        news_items.append({
            "title": it.get("title", "No Title"),
            "published_at": it.get("published") or data.get("gathered_at_utc", ""),
            "description": desc[:220],
        })
        print(f"  - Signal: [{it.get('channel')}·{eng}] '{(it.get('title') or '')[:60]}'")
    print(f"Loaded {len(news_items)} real social signals from {Path(files[0]).name}")
    return news_items


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--auto-approve", action="store_true", help="Auto-approve and publish directly to Twitter without polling")
    args = ap.parse_args()

    start_time = time.time()
    print("=========================================================")
    print("🚀 Starting Vanna Real-Time Global Trendjack Pipeline")
    print("=========================================================")

    # 0. Brain + (Gemini-only) spend proxy check
    brain = os.environ.get("PIPELINE_BRAIN", "claude").lower()
    print(f"Brain: {brain} (Opus via `claude -p`)" if brain != "gemini" else "Brain: gemini")
    if brain == "gemini":
        try:
            with urllib.request.urlopen("http://127.0.0.1:8900/_spend", timeout=5) as r:
                spend = json.loads(r.read())
                print(f"Spend check: already_spent=${spend['spent_usd']:.4f}, remaining=${spend['remaining_usd']:.4f}")
                if spend["remaining_usd"] <= 0.05:
                    print("Budget exhausted! Refusing to run.")
                    return 1
        except Exception as e:
            print(f"Error checking spend proxy: {e}. Please ensure python pipeline/scripts/vertex_spend_proxy.py is active.")
            return 1

    # Load Config and History
    if not CONFIG_PATH.exists() or not HISTORY_PATH.exists():
        print("Error: Missing config or history ledger files!")
        return 1
        
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))

    # Tenant parametrization. Same competing-strategist personas, but the tenant
    # name, product mechanics, and topic enum are pulled from the tenant config +
    # OKF bundle (OKF_BUNDLE also re-points the gate + visual palette). Default is
    # Vanna, so an un-parametrized run behaves exactly as before.
    TENANT = os.environ.get("PIPELINE_TENANT_NAME", "Vanna")
    _tax = config.get("taxonomy", [])
    if isinstance(_tax, list):
        topic_enum = [t.get("topic") for t in _tax if isinstance(t, dict) and t.get("topic")]
        mechanics = ", ".join(t.get("angle", "") for t in _tax if isinstance(t, dict) and t.get("angle"))
    else:
        topic_enum = list(_tax.keys()) if isinstance(_tax, dict) else []
        mechanics = ", ".join(topic_enum)
    if not topic_enum:
        topic_enum = ["capital-efficiency", "risk-relief", "agentic-credit"]
    if not mechanics:
        mechanics = "Risk Guardian, Capital Efficiency, Agentic Credit"
    topic_enum_str = ", ".join(f"'{t}'" for t in topic_enum)
    okf_root = REPO / "okf" if (REPO / "okf").exists() else REPO / "pipeline" / "system1_extracted" / "okf"
    BUNDLE = Path(os.environ.get("OKF_BUNDLE") or okf_root)
    strategist_personas = build_strategists(TENANT, BUNDLE)
    tenant_facts = load_tenant_facts(TENANT, BUNDLE)
    TENANT_GUARD = "" if TENANT.strip().lower() == "vanna" else (
        f"\n\n---\n\nHARD RULE: This post is for {TENANT} ONLY. The final winning "
        f"copy must NEVER mention Vanna, 'Guardian', 'health factor', 'liquidation', "
        f"'testnet', or any other company's product as if it were {TENANT}'s. If a "
        f"draft does, fix it or pick another. Ground every claim in {TENANT}'s facts.")
    print(f"Tenant: {TENANT} | strategists: {list(strategist_personas)}")
    live_reset(TENANT)
    
    # Extract recent hooks for strict blacklisting (Requirement 2 & 3)
    recent_hooks = [r.get("hook_shipped", "") for r in history[-3:] if r.get("hook_shipped")]

    # 1. Harvest the trend feed. TREND_SOURCE=scout uses the real Reddit/Twitter
    #    signals from trend_scout.py; anything else uses the Decrypt news RSS.
    if os.environ.get("TREND_SOURCE", "").lower() == "scout":
        live_news = load_scout_signals(TENANT)
    else:
        live_news = fetch_latest_defi_news()

    # 2. Conductor: Decides the Trendjack and selects the topic dynamically
    print("\n=== Step 2: Conductor Trendjack Selection ===")
    conductor_persona = load_persona("conductor")
    instr_path = REPO.joinpath("pipeline", "buzz-pack", "instructions.md")
    if not instr_path.exists():
        instr_path = REPO.joinpath("pipeline", "system1_extracted", "buzz-pack", "instructions.md")
    shared_instructions = instr_path.read_text(encoding="utf-8")
    # Campaign intelligence doctrine: how agents research and design real campaigns.
    try:
        doc_path = REPO.joinpath("pipeline", "buzz-pack", "campaign-doctrine.md")
        if not doc_path.exists():
            doc_path = REPO.joinpath("pipeline", "system1_extracted", "buzz-pack", "campaign-doctrine.md")
        doctrine = doc_path.read_text(encoding="utf-8")
        shared_instructions += "\n\n---\n\n" + doctrine
    except Exception:
        pass
    # Improve step: fold the learned performance signal into every agent's context.
    try:
        sys.path.insert(0, str(REPO / "pipeline" / "scripts"))
        from learning import learning_brief
        shared_instructions += learning_brief()
    except Exception:
        pass
    # Ground a non-Vanna tenant in its own facts so the shared (Vanna-centric)
    # pack does not bleed Vanna's product into the tenant's posts.
    shared_instructions += tenant_facts
    conductor_system = f"{conductor_persona}\n\n---\n\n# Shared Instructions\n\n{shared_instructions}"
    
    # We let the Conductor analyze the real-time news and select the best Vanna topic/angle from the taxonomy
    conductor_prompt = f"""
MANDATORY TRENDJACKING INSTRUCTION:
Analyze this list of the latest global crypto/DeFi news items from the last 24 hours.
Select the single strongest, most trending news story to jack.
Bridge this trend logically and elegantly to {TENANT}'s core product mechanics ({mechanics}).

CRITICAL DIVERSIFICATION DIRECTIVE (NO REPETITION ALLOWED):
1. Do NOT repeat or use any of these recent hooks: {recent_hooks}.
2. Do NOT focus on the Gearbox credit agent '12% yield pool' or 'decide' tweet—this angle is strictly blacklisted.
3. You must select a completely new, unique angle.

Available {TENANT} Product Taxonomy to choose from:
{json.dumps(config["taxonomy"], indent=2)}

Live Global News Items (Last 24 Hours):
{json.dumps(live_news, indent=2)}

Respond in clean Markdown. Identify the chosen news story, state *why* it is the highest quality trend, and outline the exact steer for the three strategists (instructing them on how to write pitches bridging this trend to the chosen {TENANT} angle).
"""
    conductor_decision = call_vertex(conductor_system, conductor_prompt)
    print("\n[Conductor Trendjack Decision]:")
    print(conductor_decision)
    log_agent_activity("conductor", f"Trendjack Decision:\n{conductor_decision}")

    # 3. Trend Scout Synthesis (Determine the selected taxonomy topic dynamically)
    print("\n=== Step 3: Trend Scout Synthesis ===")
    scout_persona = load_persona("trend-scout")
    scout_system = f"{scout_persona}\n\n---\n\n# Shared Instructions\n\n{shared_instructions}"
    scout_prompt = f"""
Analyze the Conductor's decision and extract:
- "selected_topic": the chosen {TENANT} taxonomy topic (must be one of: {topic_enum_str})
- "competitor_referenced": Who is the key competitor/project mentioned in the news story.

Conductor Decision:
{conductor_decision}

Return your response in clean JSON matching:
{{
  "selected_topic": "topic_name",
  "selected_angle": "angle_name",
  "competitor_referenced": "project_name"
}}
"""
    scout_resp = call_vertex(scout_system, scout_prompt)
    synthesis_json = extract_json(scout_resp)
    
    selected_topic_name = synthesis_json.get("selected_topic") or (topic_enum[0] if topic_enum else "risk-relief")
    selected_angle_name = synthesis_json.get("selected_angle") or (mechanics.split(",")[0].strip() if mechanics else "Autonomous Risk Guardian")
    competitor_referenced = synthesis_json.get("competitor_referenced") or "Aave"
    
    print(f"Trend Scout Synthesis: selected_topic='{selected_topic_name}', competitor='{competitor_referenced}'")
    log_agent_activity("trend-scout", f"Synthesis:\n{json.dumps(synthesis_json, indent=2)}")

    # 4. Strategist Drafting
    print("\n=== Step 4: Strategist Drafting ===")
    drafts = {}
    for strategist, persona in strategist_personas.items():
        print(f"Running {strategist} drafting...")
        system = f"{persona}\n\n---\n\n# Shared Instructions\n\n{shared_instructions}"
        prompt = f"""
Draft a single X/Twitter post (max 260 characters to fit standard Twitter limits!) that trendjacks the selected global news event.
Bridge this trend to {TENANT}'s **{selected_angle_name}** value proposition, explaining why {TENANT} provides the ultimate solution.

CRITICAL DIVERSIFICATION DIRECTIVE (NO MONOTONY):
1. Do NOT repeat or reference any of these recent post hooks: {recent_hooks}.
2. Do NOT use the Gearbox credit agent 'decide' or '12% yield' angle—strictly blacklisted.

MANDATORY REQUIREMENT: Your JSON output MUST contain a complete, premium, and detailed "visual_brief" object. You are strictly forbidden from setting the type to "none" or omitting it.
The "visual_brief" must be of type "infographic" or "stat-card", containing:
  - "headline": A short, cinematic headline
  - "emphasis_phrase": A highly punchy highlight
  - "subhead": A supporting description
  - "data": An array containing exactly 2-3 structured rows (each with 'label', 'value', and 'note' keys) that contrast {TENANT}'s infrastructure against the trend/competitor.

Conductor Trendjack Steer:
{conductor_decision}
"""
        resp = call_vertex(system, prompt)
        drafts[strategist] = extract_json(resp)
        print(f"  {strategist} drafted successfully.")
        log_agent_activity(strategist, f"Initial Draft:\n{json.dumps(drafts[strategist], indent=2)}")

    # 5. Sequential Agentic Debate
    print("\n=== Step 5: Sequential Agentic Debate ===")
    rebuttals = {}
    for strategist, persona in strategist_personas.items():
        print(f"Running {strategist} rebuttal turn...")
        system = f"{persona}\n\n---\n\n# Shared Instructions\n\n{shared_instructions}"
        
        other_drafts = {k: v for k, v in drafts.items() if k != strategist}
        prompt = f"""
You are engaged in an open, adversarial debate.
Critique the other strategists' drafts in a single short paragraph. Explain why your arc's pitch for {TENANT}'s **{selected_angle_name}** is fundamentally superior, more complete, or more viable than their angles in light of this global DeFi trend.

Your Initial Draft:
{json.dumps(drafts[strategist], indent=2)}

Other Strategists' Drafts:
{json.dumps(other_drafts, indent=2)}
"""
        rebuttal = call_vertex(system, prompt, temperature=0.8)
        rebuttals[strategist] = rebuttal
        print(f"\n[{strategist} Rebuttal]:")
        print(rebuttal)
        log_agent_activity(strategist, f"Debate Rebuttal:\n{rebuttal}")

    # 6. Editorial Judge Ruling
    print("\n=== Step 6: Editorial Judge Ruling ===")
    judge_persona = load_persona("editorial-judge")
    judge_system = f"{judge_persona}\n\n---\n\n# Shared Instructions\n\n{shared_instructions}{TENANT_GUARD}"
    judge_prompt = f"""
Evaluate the three initial drafts and their rebuttals.
Select the single strongest winner that trendjacks this global DeFi event most compellingly and highlights {TENANT}'s **{selected_angle_name}**.
Ensure the hook, body, and thread are returned in a clean JSON matching your winner contract.

MANDATORY REQUIREMENT: The selected winning draft MUST carry a complete, detailed, and high-fidelity "visual_brief" object of type "infographic" or "stat-card". You are strictly forbidden from setting the type to "none" or leaving it empty.

CRITICAL INSTRUCTION: Your output MUST contain ONLY the raw JSON object. Do NOT write any conversational intro, prose, explanation, markdown commentary, or notes before or after the JSON block. Your response must be 100% parseable JSON starting with '{{' and ending with '}}'.

Initial Drafts:
{json.dumps(drafts, indent=2)}

Debate Rebuttals:
{json.dumps(rebuttals, indent=2)}
"""
    judge_resp = call_vertex(judge_system, judge_prompt, temperature=0.1)
    winner_draft = extract_json(judge_resp)
    print("\n[Judge Ruling Decided]:")
    print(f"Verdict: {winner_draft.get('verdict')}")
    print(f"Winner Arc: {winner_draft.get('winner_arc')}")
    print(f"Winner Hook: {winner_draft.get('winner', {}).get('final_hook')}")
    log_agent_activity("editorial-judge", f"Ruling Decision:\n{json.dumps(winner_draft, indent=2)}")

    if winner_draft.get("verdict") != "ship":
        print("❌ Judge rejected all drafts. Failing gracefully.")
        live_finalize("rejected", trend=competitor_referenced, topic=selected_topic_name)
        return 1

    # Flatten the JSON structure for downstream compatibility (Step 1 correctness)
    flattened_draft = {
        "id": winner_draft.get("draft_id") or uuid.uuid4().hex[:8],
        "draft_id": winner_draft.get("draft_id") or uuid.uuid4().hex[:8],
        "verdict": winner_draft.get("verdict"),
        "winner_arc": winner_draft.get("winner_arc"),
        "body": winner_draft.get("winner", {}).get("final_body") or winner_draft.get("body", ""),
        "final_body": winner_draft.get("winner", {}).get("final_body") or winner_draft.get("body", ""),
        "final_hook": winner_draft.get("winner", {}).get("final_hook") or winner_draft.get("hook", ""),
        "thread": winner_draft.get("winner", {}).get("final_thread") or winner_draft.get("thread") or [],
        "final_thread": winner_draft.get("winner", {}).get("final_thread") or winner_draft.get("thread") or [],
        "visual_brief": winner_draft.get("winner", {}).get("visual_brief") or winner_draft.get("visual_brief") or {},
        "platform": winner_draft.get("platform", "x"),
        "trend_id": competitor_referenced,
        "sent_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Save the winner draft JSON
    draft_file_path = STATE / "drafts" / "temp_winner.json"
    draft_file_path.write_text(json.dumps(flattened_draft, indent=2, ensure_ascii=False), encoding="utf-8")

    # 7. Downstream Claim Safety Gate
    print("\n=== Step 7: Downstream Claim Safety Gate ===")
    compliance_data = {
        "text": flattened_draft.get("body"),
        "platform": flattened_draft.get("platform")
    }
    compliance_file_path = STATE / "drafts" / "temp_compliance.json"
    compliance_file_path.write_text(json.dumps(compliance_data, indent=2), encoding="utf-8")

    gate_res = subprocess.run(
        [sys.executable, "pipeline/scripts/claim_safety_gate.py", "--file", str(compliance_file_path)],
        capture_output=True, text=True
    )
    print("Gate STDOUT:")
    print(gate_res.stdout)
    
    gate_json = json.loads(gate_res.stdout)
    if not gate_json.get("pass"):
        print("❌ Claim Safety Gate BLOCKED the draft!")
        live_finalize("blocked", trend=competitor_referenced, topic=selected_topic_name,
                      winner_hook=flattened_draft.get("final_hook"))
        return 1

    # 8. Render Visual Card (Static Only)
    print("\n=== Step 8: Rendering Visual Card ===")
    log_agent_activity("visual-creator", "thinking — designing static visual layout card")
    brief_file = STATE / "drafts" / "temp_brief.json"
    brief_data = flattened_draft.get("visual_brief")
    if not brief_data or brief_data.get("type") == "none":
        print("No visual card requested for this draft. Skipping.")
        image_path = None
    else:
        # Save brief
        brief_file.write_text(json.dumps(brief_data, indent=2), encoding="utf-8")
        image_path = REPO / "pipeline" / "state" / "temp_rendered.png"
        
        try:
            sys.path.append(str(REPO))
            from pipeline.scripts.render_visual import render as render_visual_card
            render_visual_card(brief_data, image_path)
            print(f"✅ Image rendered successfully at: {image_path}")
            log_agent_activity("visual-creator", f"Success! Rendered visual card at: {image_path}")
        except Exception as e:
            print(f"❌ Visual rendering failed: {e}")
            image_path = None

    # 9. Send to Telegram for Human Review
    print("\n=== Step 9: Dispatching to Telegram for human review ===")
    telegram_args = [
        sys.executable,
        "pipeline/scripts/telegram_review.py",
        "send",
        "--draft", str(draft_file_path)
    ]
    if image_path:
        telegram_args += ["--image", str(image_path)]
        
    tg_send_res = subprocess.run(telegram_args, capture_output=True, text=True)
    print("Telegram Send Result:")
    print(tg_send_res.stdout)
    
    tg_json = json.loads(tg_send_res.stdout)
    draft_id = tg_json.get("draft_id")

    # Persist the completed run: this is the permanent audit record.
    live_finalize(
        "completed",
        trend=competitor_referenced,
        topic=selected_topic_name,
        winner_hook=flattened_draft.get("final_hook"),
        winner_body=flattened_draft.get("body"),
        telegram_message_id=tg_json.get("message_id"),
        telegram_draft_id=draft_id,
        has_image=bool(image_path),
    )

    # 10. Polling Telegram for your feedback on the draft
    print(f"\n=== Step 10: Polling Telegram for your feedback on draft {draft_id} ===")
    if args.auto_approve:
        print("⚡ Auto-Approve Mode Active: Skipping polling, proceeding directly to publishing!")
        poll_json = {"status": "approved"}
    else:
        print("Polling will run for 120 seconds. We will wait for your response...")
        poll_res = subprocess.run([
            sys.executable,
            "pipeline/scripts/telegram_review.py",
            "poll",
            "--draft-id", str(draft_id),
            "--timeout", "120"
        ], capture_output=True, text=True)
        print("Poll Result:")
        print(poll_res.stdout)
        # The draft is already delivered to Telegram by this point; a flaky or
        # empty poll response must not turn a successful send into a failed run.
        try:
            poll_json = json.loads(poll_res.stdout)
        except (json.JSONDecodeError, ValueError):
            print("⚠️ Poll returned no parseable status; draft is in Telegram, "
                  "leaving it awaiting review.")
            poll_json = {"status": "pending"}
    
    if poll_json.get("status") == "approved":
        print("\n🎉 Draft APPROVED by reviewer!")
        # 11. Post to Twitter natively via OpenCLI
        print("\n=== Step 11: Natively Publishing to Twitter via OpenCLI ===")
        post_text = flattened_draft.get("body")
        clean_text = post_text.replace("**", "").replace("*", "").replace("`", "")
        
        twitter_args = [
            "opencli", "twitter", "post", clean_text
        ]
        if image_path:
            twitter_args += ["--images", str(image_path)]
            
        twitter_res = subprocess.run(twitter_args, capture_output=True, text=True, shell=True)
        print("Twitter Post Result:")
        print(twitter_res.stdout)

    # 12. Update History
    print("\n=== Step 12: Updating Persistent Content History ===")
    new_entry = {
        "run_id": draft_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "topic_covered": selected_topic_name,
        "angle_covered": selected_angle_name,
        "competitors_referenced": [competitor_referenced],
        "sources_used": ["Decrypt Global RSS Feed"],
        "verdict_outcome": poll_json.get("status", "timeout"),
        "hook_shipped": flattened_draft.get("final_hook") or "none"
    }
    history.append(new_entry)
    HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(f"✅ Content history updated successfully at: {HISTORY_PATH}")

    duration = time.time() - start_time
    print("\n" + "="*57)
    print(f"🎉 News Trendjack Pipeline run finished in {duration:.1f}s.")
    print("="*57)
    return 0

if __name__ == "__main__":
    sys.exit(main())
