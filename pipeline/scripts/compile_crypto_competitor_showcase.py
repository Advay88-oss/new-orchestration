#!/usr/bin/env python3
"""Compiles the interactive HTML showcase:
1. 3 Vanna Crypto Architecture Posts with textless geometric visuals.
2. 3 Underrated Competitor Scout Dossiers with live evidence links.
"""

from __future__ import annotations

import base64
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = REPO_ROOT / "pipeline" / "state"

v1_b64 = base64.b64encode((STATE_DIR / "vanna_vis_crypto_telemetry.png").read_bytes()).decode("utf-8")
v2_b64 = base64.b64encode((STATE_DIR / "vanna_vis_crypto_isolation.png").read_bytes()).decode("utf-8")
v3_b64 = base64.b64encode((STATE_DIR / "vanna_vis_crypto_multiplier.png").read_bytes()).decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vanna Crypto Architecture & Competitor Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #07020D;
    --card-bg: rgba(255, 255, 255, 0.025);
    --border: rgba(255, 255, 255, 0.08);
    --accent-violet: #A387FF;
    --accent-coral: #FC5457;
    --accent-cyan: #22D3C4;
    --glow-violet: #471485;
    --glow-magenta: #5E0D46;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
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
  .container {{ max-width: 960px; width: 100%; display: flex; flex-direction: column; gap: 48px; }}
  .header-badge {{
    font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700;
    color: var(--accent-cyan); background: rgba(34, 211, 196, 0.1);
    border: 1px solid rgba(34, 211, 196, 0.25); padding: 4px 10px; border-radius: 6px;
    display: inline-block; margin-bottom: 12px;
  }}
  h1 {{ font-size: 30px; font-weight: 800; color: #FFF; }}
  .lead {{ font-size: 14px; color: #9CA3AF; margin-top: 6px; line-height: 1.5; }}
  
  .section-title {{
    font-size: 20px; font-weight: 700; color: #FFF;
    display: flex; align-items: center; gap: 12px;
    border-bottom: 1px solid var(--border); padding-bottom: 14px;
  }}
  .grid {{ display: flex; flex-direction: column; gap: 32px; }}
  
  .post-card {{
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px;
    padding: 24px; display: flex; flex-direction: column; gap: 16px; backdrop-filter: blur(20px);
  }}
  .meta-row {{ display: flex; justify-content: space-between; align-items: center; }}
  .author-block {{ display: flex; align-items: center; gap: 12px; }}
  .avatar {{
    width: 38px; height: 38px; border-radius: 50%;
    background: linear-gradient(135deg, var(--glow-violet), var(--glow-magenta));
    display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 14px; color: #FFF;
  }}
  .tag {{
    font-family: 'JetBrains Mono', monospace; font-size: 11px; padding: 4px 10px;
    border-radius: 6px; border: 1px solid rgba(255,255,255,0.08); background: rgba(0,0,0,0.3);
  }}
  .tag.vanna {{ color: var(--accent-violet); border-color: rgba(163,135,255,0.3); }}
  .tag.scout {{ color: var(--accent-cyan); border-color: rgba(34,211,196,0.3); }}

  .post-text {{ font-size: 15px; line-height: 1.65; color: #E5E7EB; white-space: pre-wrap; }}
  .image-container {{
    width: 100%; border-radius: 12px; overflow: hidden;
    border: 1px solid rgba(255,255,255,0.1); background: #000;
  }}
  .image-container img {{ width: 100%; height: auto; display: block; }}

  /* Competitor Dossier Card */
  .dossier-card {{
    background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: 16px;
    padding: 24px; display: flex; flex-direction: column; gap: 14px;
  }}
  .dossier-header {{ display: flex; justify-content: space-between; align-items: baseline; }}
  .dossier-title {{ font-size: 18px; font-weight: 700; color: #FFF; }}
  .dossier-handle {{ font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--accent-violet); }}
  .evidence-box {{
    background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px;
    padding: 14px; font-size: 12px; font-family: 'JetBrains Mono', monospace; color: #C4C2CF; line-height: 1.6;
  }}
  .evidence-box a {{ color: var(--accent-cyan); text-decoration: none; word-break: break-all; }}
  .evidence-box a:hover {{ text-decoration: underline; }}
  .analysis-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 6px; font-size: 13px; line-height: 1.55; }}
  .analysis-item {{ background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; }}
  .analysis-item strong {{ color: #FFF; display: block; margin-bottom: 4px; font-size: 11px; font-family: 'JetBrains Mono', monospace; text-transform: uppercase; }}
  .analysis-item.pro strong {{ color: var(--accent-coral); }}
  .analysis-item.vanna strong {{ color: var(--accent-cyan); }}
</style>
</head>
<body>
<div class="container">
  <div>
    <span class="header-badge">VANNA GTM ENGINE // LIVE RESEARCH & SCOUT RUN</span>
    <h1>Vanna Architecture & Underrated Competitor Intelligence</h1>
    <p class="lead">Live intelligence scout run pairing 3 Vanna protocol architecture posts (with pure textless geometric visuals) alongside 3 verified dossiers on underrated lending competitors with verified evidence links.</p>
  </div>

  <!-- SECTION 1: 3 VANNA CRYPTO POSTS -->
  <div class="section-title">
    <span>01 // Vanna Protocol Architecture Posts (Stellar Soroban)</span>
  </div>

  <div class="grid">

    <!-- POST 1 -->
    <div class="post-card">
      <div class="meta-row">
        <div class="author-block">
          <div class="avatar">V</div>
          <div>
            <div style="font-weight: 700; font-size: 14px;">Vanna Protocol</div>
            <div style="font-size: 12px; color: #6B7280;">@vanna_fi · Telemetry & Liquidation Defense</div>
          </div>
        </div>
        <span class="tag vanna">Protocol Pillar 3</span>
      </div>
      <div class="post-text">Most liquidations in DeFi don\'t fail on the math. They fail in the mempool.

During sudden market drops, Ethereum gas fees spike ten-fold. When a borrower submits a defensive rebalance to save their margin, MEV searchers front-run the transaction for a 10% liquidation fee. The borrower gets wiped out while their defensive transaction sits pending in the mempool.

Vanna eliminates mempool front-running with sub-second off-chain telemetry on Stellar Soroban:

Mercury streams ledger state in ~320ms. When a position approaches 1.25x Net Health Factor, our Risk Guardian rebalances directly inside the sandbox before touching the 1.10x liquidation floor. 

Execution gas is fixed at 0.00014 XLM. No priority gas auctions.

test.stellar.vanna.finance</div>
      <div class="image-container">
        <img src="data:image/png;base64,{v1_b64}" alt="Sub-Second Telemetry Deflection Visual">
      </div>
    </div>

    <!-- POST 2 -->
    <div class="post-card">
      <div class="meta-row">
        <div class="author-block">
          <div class="avatar" style="background: linear-gradient(135deg, #FC5457, #5E0D46);">V</div>
          <div>
            <div style="font-weight: 700; font-size: 14px;">Vanna Protocol</div>
            <div style="font-size: 12px; color: #6B7280;">@vanna_fi · Contagion Containment</div>
          </div>
        </div>
        <span class="tag vanna">Protocol Pillar 2</span>
      </div>
      <div class="post-text">In pooled lending, when an exotic collateral asset depegs, every depositor absorbs the haircut. Even if you only deposited stablecoins.

Vanna isolates risk at the smart contract instance level on Stellar Soroban:

Borrowers execute within dedicated SmartAccount sandboxes. If an unexpected deficit occurs, it stays quarantined in that specific contract sandbox. It cannot drain other user accounts or compromise core LendingPool reserves.

LPs earn sustainable yield without cross-account bad debt contagion.

docs.vanna.finance</div>
      <div class="image-container">
        <img src="data:image/png;base64,{v2_b64}" alt="Isolated Compartment Equilibrium Visual">
      </div>
    </div>

    <!-- POST 3 -->
    <div class="post-card">
      <div class="meta-row">
        <div class="author-block">
          <div class="avatar" style="background: linear-gradient(135deg, #A387FF, #22D3C4);">V</div>
          <div>
            <div style="font-weight: 700; font-size: 14px;">Vanna Protocol</div>
            <div style="font-size: 12px; color: #6B7280;">@vanna_fi · Composable Multiplier</div>
          </div>
        </div>
        <span class="tag vanna">Protocol Pillar 1</span>
      </div>
      <div class="post-text">Overcollateralization locks capital in stasis. Pledging $150 to borrow $100 is not capital efficiency.

Vanna unlocks up to 10× undercollateralized margin borrowing on Stellar Soroban.

Deposit collateral into a dedicated SmartAccount, access amplified borrowing power, and deploy straight to Blend (b-tokens) and Aquarius (AMM pools) in a single atomic transaction.

Keep your balance sheet active without giving up non-custodial wallet sovereignty.

test.stellar.vanna.finance</div>
      <div class="image-container">
        <img src="data:image/png;base64,{v3_b64}" alt="10x Margin Optical Refraction Visual">
      </div>
    </div>

  </div>

  <!-- SECTION 2: 3 UNDERRATED COMPETITORS SCOUT REPORT -->
  <div class="section-title">
    <span>02 // Underrated Competitor Intelligence Scout Dossiers</span>
  </div>

  <div class="grid">

    <!-- COMPETITOR 1: SILO FINANCE -->
    <div class="dossier-card">
      <div class="dossier-header">
        <div>
          <div class="dossier-title">1. Silo Finance (Silo v3 Launch)</div>
          <div class="dossier-handle">@SiloFinance · silo.finance</div>
        </div>
        <span class="tag scout">Isolated Money Markets</span>
      </div>
      <div class="evidence-box">
        <div><strong>SIGNAL:</strong> Launched Silo v3 — money markets designed to remain solvent without reliance on immediate DEX liquidations.</div>
        <div><strong>EVIDENCE LINK:</strong> <a href="https://www.globenewswire.com/news-release/2026/03/26/3263502/0/en/silo-introduces-silo-v3-a-new-class-of-money-markets-designed-to-remain-solvent-without-reliance-on-dex-liquidity.html" target="_blank">globenewswire.com/news-release/2026/03/26/silo-v3-money-markets</a></div>
        <div><strong>OFFICIAL SITE:</strong> <a href="https://www.silo.finance/" target="_blank">silo.finance</a></div>
      </div>
      <div class="analysis-grid">
        <div class="analysis-item pro">
          <strong>Silo v3 Mechanism & Moat</strong>
          Decouples solvency from immediate forced DEX sales. When collateral liquidity dries up, the protocol avoids cascading fire-sales by isolating asset pairs.
        </div>
        <div class="analysis-item vanna">
          <strong>Vanna Advantage & Narrative Wedge</strong>
          Silo operates on EVM rollups and still inherits priority gas volatility and multi-second block latency. Vanna combines isolation with sub-second (~320ms) Mercury event feeds and fixed 0.00014 XLM execution fees on Stellar Soroban.
        </div>
      </div>
    </div>

    <!-- COMPETITOR 2: WILDCAT PROTOCOL -->
    <div class="dossier-card">
      <div class="dossier-header">
        <div>
          <div class="dossier-title">2. Wildcat Protocol (Institutional Private Credit)</div>
          <div class="dossier-handle">@WildcatFi · wildcat.finance</div>
        </div>
        <span class="tag scout">Undercollateralized Credit</span>
      </div>
      <div class="evidence-box">
        <div><strong>SIGNAL:</strong> Raised $3.5M seed extension led by Robot Ventures to scale undercollateralized institutional credit.</div>
        <div><strong>EVIDENCE LINK:</strong> <a href="https://www.theblock.co/news/deals/2025-09-05-wildcat-labs-3-5-million-usd-round-robot-ventures-369453" target="_blank">theblock.co/news/deals/wildcat-labs-3-5-million-seed-extension</a></div>
        <div><strong>ETHEREUM APP:</strong> <a href="https://ethereum.org/apps/wildcat" target="_blank">ethereum.org/apps/wildcat</a></div>
      </div>
      <div class="analysis-grid">
        <div class="analysis-item pro">
          <strong>Wildcat Mechanism & Moat</strong>
          Lets trusted borrowers (Wintermute, Amber Group, Keyrock) parameterize custom reserve ratios and withdrawal cycles for institutional uncollateralized credit lines.
        </div>
        <div class="analysis-item vanna">
          <strong>Vanna Advantage & Narrative Wedge</strong>
          Wildcat relies on off-chain legal reputation and whitelisted institutions. If a borrower defaults, lenders must pursue legal arbitration. Vanna enforces on-chain isolated SmartAccount sandboxes with programmatic 1.10x Net Health Factor liquidation floors.
        </div>
      </div>
    </div>

    <!-- COMPETITOR 3: GEARBOX PROTOCOL -->
    <div class="dossier-card">
      <div class="dossier-header">
        <div>
          <div class="dossier-title">3. Gearbox Protocol (Credit Account Composable Leverage)</div>
          <div class="dossier-handle">@GearboxProtocol · gearbox.fi</div>
        </div>
        <span class="tag scout">Composable Credit Accounts</span>
      </div>
      <div class="evidence-box">
        <div><strong>SIGNAL:</strong> Pioneer of isolated Credit Accounts on EVM, facilitating up to 10x leverage across Uniswap, Curve, and Convex.</div>
        <div><strong>EVIDENCE LINK:</strong> <a href="https://gearbox.fi" target="_blank">gearbox.fi/how-it-works</a></div>
        <div><strong>TVL BENCHMARK:</strong> $64.8M TVL on Ethereum/Arbitrum (DeFiLlama live).</div>
      </div>
      <div class="analysis-grid">
        <div class="analysis-item pro">
          <strong>Gearbox Mechanism & Moat</strong>
          Credit Account architecture ensures borrowed capital stays within the proxy contract, enabling composable leverage without giving users direct custody of borrowed funds.
        </div>
        <div class="analysis-item vanna">
          <strong>Vanna Advantage & Narrative Wedge</strong>
          Gearbox is bound to Ethereum/Arbitrum mempool priority auctions. When gas spikes to 150+ gwei, liquidator bots front-run user positions. Vanna delivers the same Credit Account sandbox on Stellar Soroban Protocol 20 with fixed 0.00014 XLM fees and sub-second Mercury keeper telemetry.
        </div>
      </div>
    </div>

  </div>
</div>
</body>
</html>
"""

out_file = STATE_DIR / "vanna_crypto_and_competitors.html"
out_file.write_text(html_content, encoding="utf-8")
print(f"✅ Generated Showcase: {out_file.name} ({out_file.stat().st_size:,} bytes)")
