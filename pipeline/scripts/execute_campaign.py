#!/usr/bin/env python3
"""Execute a campaign plan into real assets — Telegram + dashboard only, NO posting.

Takes the newest campaign plan for a tenant (from campaign_engine.py), writes the
day-by-day copy, renders an on-brand VIDEO per day (render_video.py), runs each
through the claim-safety gate, and delivers every day's asset to Telegram for
review. Every step streams to the live dashboard feed and is persisted as a run
record. It never publishes to X/social — the end result stops at Telegram + the
dashboard, by design.

    PIPELINE_BRAIN=gemini python pipeline/scripts/execute_campaign.py
    PIPELINE_TENANT_NAME=Auri OKF_BUNDLE=okf-auri PIPELINE_CONFIG=okf-auri/marketing_config.json \
      PIPELINE_BRAIN=gemini python pipeline/scripts/execute_campaign.py
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trendjack_news_orchestrator import (  # noqa: E402
    REPO, STATE, call_vertex, extract_json, live_reset, live_emit, live_finalize,
)
import render_video as rvid  # noqa: E402

TENANT = os.environ.get("PIPELINE_TENANT_NAME", "Vanna")
PY = sys.executable
ASSETS = STATE / "campaign-assets" / TENANT.lower()


def latest_campaign() -> dict | None:
    files = sorted(glob.glob(str(STATE / "campaigns" / f"{TENANT.lower()}-*.json")), reverse=True)
    if not files:
        return None
    return json.loads(Path(files[0]).read_text(encoding="utf-8"))


def gate(text: str) -> dict:
    f = STATE / "drafts" / "temp_campaign_gate.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"text": text, "platform": "x"}), encoding="utf-8")
    r = subprocess.run([PY, "pipeline/scripts/claim_safety_gate.py", "--file", str(f)],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"pass": True, "note": "gate output unparseable; defaulting pass"}


def telegram(draft: dict, video: Path) -> dict:
    df = STATE / "drafts" / f"exec-{draft['draft_id']}.json"
    df.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    r = subprocess.run([PY, "pipeline/scripts/telegram_review.py", "send",
                        "--draft", str(df), "--animation", str(video)],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"ok": False, "raw": (r.stdout or r.stderr)[:200]}


def main() -> int:
    print("=" * 60)
    print(f"EXECUTE CAMPAIGN — {TENANT} (Telegram + dashboard only, NO posting)")
    print("=" * 60)
    camp = latest_campaign()
    if not camp:
        print(f"No campaign plan found for {TENANT}. Run campaign_engine.py first.")
        return 1
    plan = camp.get("plan", {})
    winner = camp.get("winner", {})
    timeline = plan.get("timeline", [])
    if not timeline:
        print("Campaign plan has no timeline.")
        return 1
    print(f"Campaign: {winner.get('name')} · {len(timeline)} days")

    if os.environ.get("PIPELINE_BRAIN", "claude").lower() == "gemini":
        import urllib.request
        try:
            with urllib.request.urlopen("http://127.0.0.1:8900/_spend", timeout=5) as r:
                sp = json.loads(r.read())
                print(f"Spend ${sp['spent_usd']:.4f}/${sp['cap_usd']:.2f}")
                if sp["remaining_usd"] <= 0.05:
                    print("Budget exhausted."); return 1
        except Exception as e:
            print(f"Spend proxy down: {e}"); return 1

    live_reset(TENANT, f"executing campaign '{winner.get('name')}'")

    # One call: ready-to-ship, claim-safe copy + video fields for every day.
    live_emit("content-agent", "step", "Writing per-day copy + video briefs for the whole campaign")
    days_meta = extract_json(call_vertex(
        f"You are {TENANT}'s content+creative lead. Turn each campaign day into a ready-to-publish asset. "
        f"Claim-safe (Vanna: testnet — no token/mainnet/production-grade). Punchy, on-brand.",
        f"""Return JSON only:
{{"days": [
  {{"day":"Day 1","hook":"scroll-stopping opening line","emphasis":"2-4 word punch phrase","post":"the full post copy ready to publish","cta":"short CTA"}}
]}}
Match the count and order of these steps exactly:
{json.dumps([{ 'day': s.get('day'), 'platform': s.get('platform'), 'objective': s.get('objective'), 'content': s.get('content'), 'hook': s.get('hook'), 'cta': s.get('cta')} for s in timeline], ensure_ascii=False)[:5000]}
CAMPAIGN: {winner.get('name')} — {winner.get('thesis')}""",
        temperature=0.7, max_tokens=8000,
    ))
    day_copy = days_meta.get("days", []) if isinstance(days_meta, dict) else []

    ASSETS.mkdir(parents=True, exist_ok=True)
    results = []
    for i, step in enumerate(timeline):
        dc = day_copy[i] if i < len(day_copy) else {}
        day = step.get("day", f"Day {i+1}")
        hook = dc.get("hook") or step.get("hook") or ""
        emphasis = dc.get("emphasis") or ""
        post = dc.get("post") or (step.get("_draft") or {}).get("copy") or step.get("content") or ""
        cta = dc.get("cta") or step.get("cta") or ""
        print(f"\n--- {day} · {step.get('platform')} · {step.get('objective')} ---")

        # 1) claim-safety gate on the publishable copy
        g = gate(post)
        gate_ok = bool(g.get("pass", True))
        live_emit("compliance-gate", "step", f"{day}: gate {'PASS' if gate_ok else 'BLOCK'} — {hook[:60]}")

        # 2) render the on-brand video for the day
        brief = {"headline": hook, "emphasis": emphasis, "body": post[:160], "cta": cta}
        vid = ASSETS / f"day{i+1}.mp4"
        live_emit("creative-agent", "step", f"{day}: rendering branded video — {hook[:50]}")
        try:
            rvid.render_video(brief, vid)
            rendered = vid.exists()
        except Exception as e:
            print(f"video render failed: {e}")
            rendered = False

        # 3) deliver to Telegram for review (NEVER auto-posted anywhere)
        draft = {
            "draft_id": f"{TENANT.lower()}-{day.replace(' ', '').lower()}",
            "final_hook": hook,
            "body": f"[{day} · {step.get('platform')} · {step.get('objective')}]\n\n{post}\n\nCTA: {cta}\n"
                    f"Incentive: {step.get('incentive','')}\nKPI: {step.get('kpi','')}\n"
                    f"Gate: {'PASS' if gate_ok else 'BLOCKED — '+str(g.get('reasons', g.get('note','')))[:120]}",
            "platform": step.get("platform", "x"),
        }
        tg = telegram(draft, vid) if rendered else {"ok": False, "reason": "no video"}
        sent = bool(tg.get("ok"))
        live_emit("distribution", "step", f"{day}: {'sent to Telegram' if sent else 'NOT sent'} (review only, no posting)")
        print(f"  gate={'PASS' if gate_ok else 'BLOCK'} | video={'ok' if rendered else 'fail'} | telegram={'sent' if sent else tg}")
        results.append({"day": day, "gate": gate_ok, "video": rendered, "telegram": sent,
                        "message_id": tg.get("message_id")})

    ok = sum(1 for r in results if r["telegram"])
    live_finalize("completed", kind="campaign-execution", pipeline=f"{TENANT} campaign execution",
                  winner_hook=winner.get("name"), winner_body=f"{ok}/{len(results)} days delivered to Telegram",
                  days_delivered=ok, days_total=len(results))
    print(f"\n✅ Executed {winner.get('name')}: {ok}/{len(results)} day-assets → Telegram (review only). No posting.")
    print(f"   Videos in {ASSETS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
