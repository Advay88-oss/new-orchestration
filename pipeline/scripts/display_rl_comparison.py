#!/usr/bin/env python3
"""Compiles an interactive HTML showcase of the 5-Brief RL Model Arena experiment.
Displays Model A vs Model B vs Model C side-by-side with latency, cost, and critic scores.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

history_file = STATE_DIR / "rl_bandit_history.jsonl"
policy_file = STATE_DIR / "rl_model_routing_policy.json"

trials = [json.loads(l) for l in history_file.read_text(encoding="utf-8").splitlines() if l.strip()]
policy = json.loads(policy_file.read_text(encoding="utf-8")) if policy_file.exists() else {}

brief_ids = [
    ("BRIEF_01_10X_LEVERAGE", "Brief 1: 10x Margin Engine (Capital Efficiency)"),
    ("BRIEF_02_SUBSECOND_TELEMETRY", "Brief 2: Sub-Second Telemetry vs EVM Mempool MEV"),
    ("BRIEF_03_110X_SOLVENCY_FLOOR", "Brief 3: 1.10x Net Health Factor Solvency Rail"),
    ("BRIEF_04_ISOLATED_SANDBOXES", "Brief 4: Isolated SmartAccount Sandboxes"),
    ("BRIEF_05_POLYNOMIAL_RATEMODEL", "Brief 5: Continuous Polynomial RateModel")
]

sections_html = []
for bid, btitle in brief_ids:
    b_trials = [t for t in trials if t.get("brief_id") == bid]
    cards = []
    for t in b_trials:
        m_id = t["model_id"]
        lat = t["latency_seconds"]
        cost = t["cost_usd"]
        base_r = t["critic_eval"]["base_reward"]
        final_r = t["final_reward"]
        dec = t["human_decision"]
        fails = t["critic_eval"]["failure_reasons"]
        fails_str = "<br>".join([f"⚠️ {f}" for f in fails]) if fails else "✅ All 10 dimensions passed threshold"
        is_winner = (dec == "APPROVE" or final_r >= 0.85)

        border_color = "#22D3C4" if is_winner else "rgba(255,255,255,0.08)"
        tag_color = "#22D3C4" if is_winner else "#A387FF"

        card = f"""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid {border_color}; border-radius: 12px; padding: 20px; display: flex; flex-direction: column; justify-content: space-between;">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
              <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; color: {tag_color};">{m_id}</span>
              <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px; background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px;">{dec}</span>
            </div>
            <div style="font-size: 12px; color: #8A8598; font-family: 'JetBrains Mono', monospace; margin-bottom: 12px;">
              Latency: {lat:.2f}s | Cost: ${cost:.5f} | Reward: <strong>{final_r:.2f}</strong> (Base: {base_r:.2f})
            </div>
            <div style="font-family: ui-monospace, monospace; font-size: 13px; line-height: 1.55; color: #E1DFE8; white-space: pre-wrap; background: rgba(0,0,0,0.35); padding: 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.04); margin-bottom: 12px;">
{t['output_content']}
            </div>
          </div>
          <div style="font-size: 11px; color: #FC5457; font-family: 'JetBrains Mono', monospace; border-top: 1px solid rgba(255,255,255,0.04); padding-top: 8px;">
            {fails_str}
          </div>
        </div>
        """
        cards.append(card)

    cards_grid = "\n".join(cards)
    sec = f"""
    <div style="background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; padding: 24px; margin-bottom: 32px;">
      <h3 style="color: #FFF; font-size: 18px; margin-bottom: 16px; font-weight: 700;">{btitle}</h3>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px;">
        {cards_grid}
      </div>
    </div>
    """
    sections_html.append(sec)

all_sections = "\n".join(sections_html)

# Format Policy summary
policy_html_rows = []
for arm_key, arm_data in policy.items():
    policy_html_rows.append(f"""
    <tr>
      <td style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); font-family: 'JetBrains Mono', monospace; color: #A387FF;">{arm_data.get('task_type')}</td>
      <td style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); font-family: 'JetBrains Mono', monospace; font-weight: 700;">{arm_data.get('model_id')}</td>
      <td style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: center;">{arm_data.get('trials_count')}</td>
      <td style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: center; font-weight: 700; color: #22D3C4;">{arm_data.get('average_reward', 0.0):.3f}</td>
      <td style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: center; color: #8A8598;">{arm_data.get('ucb_score', 0.0):.3f}</td>
    </tr>
    """)

policy_table = "\n".join(policy_html_rows)

html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vanna GTM — Reinforcement Learning Model Arena</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #07020D;
    background-image: 
      radial-gradient(circle at 10% 20%, rgba(71, 20, 133, 0.25) 0%, transparent 40%),
      radial-gradient(circle at 90% 80%, rgba(94, 13, 70, 0.2) 0%, transparent 40%);
    color: #F3F4F6;
    font-family: 'Plus Jakarta Sans', sans-serif;
    padding: 40px 24px;
    display: flex;
    justify-content: center;
    min-height: 100vh;
  }}
  .container {{ max-width: 1280px; width: 100%; }}
  .badge {{
    font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #22D3C4;
    background: rgba(34, 211, 196, 0.1); border: 1px solid rgba(34, 211, 196, 0.25);
    padding: 4px 10px; border-radius: 6px; display: inline-block; margin-bottom: 12px;
  }}
  h1 {{ font-size: 28px; font-weight: 800; color: #FFF; margin-bottom: 8px; }}
  .lead {{ font-size: 14px; color: #9CA3AF; margin-bottom: 32px; max-width: 800px; line-height: 1.5; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 12px; }}
  th {{ text-align: left; padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #8A8598; }}
</style>
</head>
<body>
<div class="container">
  <span class="badge">EMPIRICAL REINFORCEMENT LEARNING BANDIT</span>
  <h1>Vanna GTM OS — Model Arena Comparison & Learned Routing</h1>
  <p class="lead">5 Real Vanna Briefs tested independently across integrated models (Gemini 2.5 Pro vs Gemini 2.5 Flash vs Vanna Channel Engine). Shows live text outputs, latency, costs, critic rewards, and learned policy preferences.</p>

  <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 24px; margin-bottom: 40px;">
    <h2 style="font-size: 18px; color: #FFF; margin-bottom: 6px;">Learned Contextual Bandit Policy Arms (UCB1)</h2>
    <p style="font-size: 12px; color: #8A8598; font-family: 'JetBrains Mono', monospace; margin-bottom: 12px;">Q(task, model) = average reward incorporating human feedback signals (APPROVE: +0.25, REVISE: -0.15).</p>
    <table>
      <thead>
        <tr>
          <th>TASK TYPE</th>
          <th>MODEL IDENTIFIER</th>
          <th style="text-align: center;">TRIALS</th>
          <th style="text-align: center;">AVG REWARD (Q)</th>
          <th style="text-align: center;">UCB SCORE</th>
        </tr>
      </thead>
      <tbody>
        {policy_table}
      </tbody>
    </table>
  </div>

  <h2 style="font-size: 22px; color: #FFF; margin-bottom: 20px;">Side-by-Side Model Outputs Across 5 Briefs</h2>
  {all_sections}

</div>
</body>
</html>
"""

out_html = STATE_DIR / "vanna_rl_arena_comparison.html"
out_html.write_text(html_page, encoding="utf-8")
print(f"✅ Generated RL Arena Comparison HTML: {out_html.name} ({out_html.stat().st_size:,} bytes)")
