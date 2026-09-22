#!/usr/bin/env python3
"""Builds an interactive, high-fidelity HTML preview of the 3 generated Vanna posts.
Embeds the real base64 PNG assets directly for seamless offline and browser viewing.
"""

from __future__ import annotations

import base64
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

img1_path = STATE_DIR / "vanna_research_post1_isolation_models.png"
img2_path = STATE_DIR / "vanna_research_post2_mempool_latency.png"
img3_path = STATE_DIR / "vanna_product_post_soroban_sandbox.png"

img1_b64 = base64.b64encode(img1_path.read_bytes()).decode("utf-8") if img1_path.exists() else ""
img2_b64 = base64.b64encode(img2_path.read_bytes()).decode("utf-8") if img2_path.exists() else ""
img3_b64 = base64.b64encode(img3_path.read_bytes()).decode("utf-8") if img3_path.exists() else ""

p1_text = """The biggest shift in on-chain lending over the last two years isn't higher borrow rates. It is the abandonment of the monolithic shared pool.

In Aave v2 and v3, every depositor effectively underwrites every accepted collateral asset. If an exotic collateral depegs or its oracle lags during a liquidation cascade, the resulting bad debt gets socialized across the entire pool. All depositors take the haircut.

Morpho Blue and Euler v2 proved the alternative: isolate markets to discrete pairs. Risk doesn't bleed across pools because storage state isn't shared.

When you segregate risk at the contract level, lenders choose the exact collateral they want exposure to instead of trusting a DAO governance vote to manage 30 assets safely.

DeFi credit is moving from pooled risk to compartmentalized risk."""

p2_text = """Most liquidations in DeFi aren't caused by borrowers ignoring their positions. They happen because the transaction queue failed them.

During sudden market drops, Ethereum and EVM rollups see gas fees spike ten-fold. When a borrower submits a defensive rebalance to save their margin, MEV searchers pay higher priority fees to front-run the transaction. The searcher bot gets included first, liquidates the position, and pockets an 8% to 10% penalty fee. The borrower gets wiped out while their defensive transaction sits pending in the mempool.

On networks with predictable gas accounting and sub-second block streaming, priority gas auctions don't exist in the same way. Keepers can execute rebalances proactively without competing against predatory bot bundles.

The real bottleneck in DeFi leverage has never been the math. It is the execution queue."""

p3_text = """If you combine isolated risk vaults with sub-second execution, you fix the two worst failure modes in on-chain lending.

That is how we structured Vanna on Stellar Soroban:

1. User-level sandboxes: Borrowers deploy dedicated SmartAccount contract instances. Your collateral, debt, and leverage stay inside your own contract space. If a position enters deficit, the risk is quarantined to that specific sandbox. Core LendingPool reserves never absorb cross-account bad debt.

2. Sub-second telemetry: We use the Mercury indexer to stream ledger state changes in roughly 320 milliseconds.

3. Pre-floor defense: When an account drops toward 1.25x Net Health Factor, our Risk Guardian triggers an automated rebalance directly inside the sandbox. This happens before reaching the protocol's 1.10x hard liquidation floor. The network fee is fixed at 0.00014 XLM, without public mempool front-running.

You can inspect the contract architecture and run testnet sandbox deployments at test.stellar.vanna.finance"""

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vanna Research & Product Posts — Live Preview</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #07020D;
    --card-bg: rgba(255, 255, 255, 0.03);
    --border: rgba(255, 255, 255, 0.08);
    --border-hover: rgba(163, 135, 255, 0.3);
    --text-primary: #F3F4F6;
    --text-secondary: #9CA3AF;
    --text-muted: #6B7280;
    --accent-violet: #A387FF;
    --accent-coral: #FC5457;
    --accent-cyan: #22D3C4;
    --glow-violet: #471485;
    --glow-magenta: #5E0D46;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background-color: var(--bg);
    background-image: 
      radial-gradient(circle at 10% 20%, rgba(71, 20, 133, 0.25) 0%, transparent 40%),
      radial-gradient(circle at 90% 80%, rgba(94, 13, 70, 0.2) 0%, transparent 40%);
    color: var(--text-primary);
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    padding: 40px 24px;
    min-height: 100vh;
  }}
  .container {{
    max-width: 900px;
    margin: 0 auto;
  }}
  header {{
    margin-bottom: 48px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
  }}
  .brand-pill {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    background: rgba(163, 135, 255, 0.1);
    color: var(--accent-violet);
    border: 1px solid rgba(163, 135, 255, 0.25);
    margin-bottom: 16px;
  }}
  .brand-pill .dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent-cyan);
    box-shadow: 0 0 8px var(--accent-cyan);
  }}
  h1 {{
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #FFFFFF;
    margin-bottom: 8px;
  }}
  .subtitle {{
    color: var(--text-secondary);
    font-size: 15px;
    line-height: 1.5;
  }}
  .posts-stack {{
    display: flex;
    flex-direction: column;
    gap: 40px;
  }}
  .post-card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    overflow: hidden;
    transition: all 0.2s ease;
    backdrop-filter: blur(20px);
  }}
  .post-card:hover {{
    border-color: var(--border-hover);
    box-shadow: 0 12px 40px -10px rgba(71, 20, 133, 0.3);
  }}
  .card-header {{
    padding: 20px 24px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  }}
  .post-meta {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .avatar {{
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--glow-violet), var(--glow-magenta));
    border: 1px solid rgba(255, 255, 255, 0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 14px;
    color: #FFF;
  }}
  .author-info {{
    display: flex;
    flex-direction: column;
  }}
  .author-name {{
    font-weight: 700;
    font-size: 14px;
    color: #FFF;
  }}
  .author-handle {{
    font-size: 12px;
    color: var(--text-muted);
  }}
  .category-badge {{
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(0, 0, 0, 0.3);
  }}
  .badge-research {{
    color: var(--accent-cyan);
    border-color: rgba(34, 211, 196, 0.2);
  }}
  .badge-product {{
    color: var(--accent-coral);
    border-color: rgba(252, 84, 87, 0.2);
  }}
  .card-body {{
    padding: 24px;
  }}
  .post-text {{
    font-size: 15px;
    line-height: 1.65;
    color: #E5E7EB;
    white-space: pre-wrap;
    margin-bottom: 24px;
  }}
  .media-wrapper {{
    position: relative;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: #000;
  }}
  .media-wrapper img {{
    width: 100%;
    height: auto;
    display: block;
    transition: transform 0.3s ease;
  }}
  .media-wrapper:hover img {{
    transform: scale(1.01);
  }}
  .card-footer {{
    padding: 16px 24px;
    background: rgba(0, 0, 0, 0.2);
    border-top: 1px solid rgba(255, 255, 255, 0.04);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--text-muted);
  }}
  .chips {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }}
  .chip {{
    padding: 3px 8px;
    background: rgba(255, 255, 255, 0.04);
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.06);
  }}
  .copy-btn {{
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    padding: 6px 12px;
    border-radius: 6px;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }}
  .copy-btn:hover {{
    background: var(--accent-violet);
    color: #000;
    border-color: var(--accent-violet);
  }}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="brand-pill">
      <span class="dot"></span>
      Vanna Intelligence & GTM System
    </div>
    <h1>Post Previews & Visual Synthesis</h1>
    <p class="subtitle">Ground-truth verified social publications covering cross-protocol risk analysis and Vanna's isolated credit architecture on Stellar Soroban.</p>
  </header>

  <div class="posts-stack">

    <!-- POST 1 -->
    <article class="post-card">
      <div class="card-header">
        <div class="post-meta">
          <div class="avatar">V</div>
          <div class="author-info">
            <span class="author-name">Vanna Research</span>
            <span class="author-handle">@vanna_fi · Multi-Protocol Scout</span>
          </div>
        </div>
        <span class="category-badge badge-research">Research: Risk Architecture</span>
      </div>
      <div class="card-body">
        <div class="post-text" id="p1-text">{p1_text}</div>
        <div class="media-wrapper">
          <img src="data:image/png;base64,{img1_b64}" alt="Monolithic vs Isolated Risk Models">
        </div>
      </div>
      <div class="card-footer">
        <div class="chips">
          <span class="chip">Aave v3 / Morpho Blue</span>
          <span class="chip">Contagion Isolation</span>
          <span class="chip">Format: X Post</span>
        </div>
        <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('p1-text').innerText); this.innerText='Copied!'; setTimeout(()=>this.innerText='Copy Text', 2000);">Copy Text</button>
      </div>
    </article>

    <!-- POST 2 -->
    <article class="post-card">
      <div class="card-header">
        <div class="post-meta">
          <div class="avatar">V</div>
          <div class="author-info">
            <span class="author-name">Vanna Research</span>
            <span class="author-handle">@vanna_fi · Multi-Protocol Scout</span>
          </div>
        </div>
        <span class="category-badge badge-research">Research: Liquidation Mechanics</span>
      </div>
      <div class="card-body">
        <div class="post-text" id="p2-text">{p2_text}</div>
        <div class="media-wrapper">
          <img src="data:image/png;base64,{img2_b64}" alt="Mempool Latency & Execution Queue">
        </div>
      </div>
      <div class="card-footer">
        <div class="chips">
          <span class="chip">Mempool MEV</span>
          <span class="chip">Gas Volatility</span>
          <span class="chip">Format: X Post</span>
        </div>
        <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('p2-text').innerText); this.innerText='Copied!'; setTimeout(()=>this.innerText='Copy Text', 2000);">Copy Text</button>
      </div>
    </article>

    <!-- POST 3 -->
    <article class="post-card">
      <div class="card-header">
        <div class="post-meta">
          <div class="avatar" style="background: linear-gradient(135deg, var(--accent-coral), var(--glow-magenta));">V</div>
          <div class="author-info">
            <span class="author-name">Vanna Protocol</span>
            <span class="author-handle">@vanna_fi · Product Architecture</span>
          </div>
        </div>
        <span class="category-badge badge-product">Vanna: Stellar Soroban</span>
      </div>
      <div class="card-body">
        <div class="post-text" id="p3-text">{p3_text}</div>
        <div class="media-wrapper">
          <img src="data:image/png;base64,{img3_b64}" alt="Vanna Composable SmartAccount Sandbox">
        </div>
      </div>
      <div class="card-footer">
        <div class="chips">
          <span class="chip">Soroban Protocol 20</span>
          <span class="chip">SmartAccount Sandboxes</span>
          <span class="chip">Fixed 0.00014 XLM</span>
        </div>
        <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('p3-text').innerText); this.innerText='Copied!'; setTimeout(()=>this.innerText='Copy Text', 2000);">Copy Text</button>
      </div>
    </article>

  </div>
</div>
</body>
</html>"""

out_file = STATE_DIR / "vanna_posts_preview.html"
out_file.write_text(html_content, encoding="utf-8")
print(f"✅ Generated standalone preview HTML: {out_file.resolve()}")
print(f"File size: {out_file.stat().st_size:,} bytes")
