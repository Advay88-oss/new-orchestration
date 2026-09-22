#!/usr/bin/env python3
"""Test Mode Harness:
Part 1: Generates a deliberately bad Vanna post with the old generic layout (4 rows, centered stat, excessive text)
        and runs it through the Final Reviewer Gate. Confirms Telegram is BLOCKED.
Part 2: Generates a genuinely different premium Vanna visual (asymmetric visual metaphor, textless, obsidian/lavender/coral)
        and runs it through the Final Reviewer Gate. Confirms Telegram is REACHED.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from pipeline.reviewer.reviewer import review_package


def create_bad_generic_visual(output_path: Path):
    """Renders a deliberately bad, generic DeFi card with purple glow, 4 horizontal rows, and large stat."""
    width, height = 1080, 1080
    im = Image.new("RGB", (width, height), color=(18, 14, 28))
    draw = ImageDraw.Draw(im)

    # Purple radial-like glow in center
    for r in range(400, 50, -30):
        alpha_color = (45 + r // 10, 20 + r // 15, 75 + r // 5)
        draw.ellipse([(width//2 - r, height//2 - r), (width//2 + r, height//2 + r)], fill=alpha_color)

    # Large centered statistic
    draw.rectangle([(width//2 - 250, 120), (width//2 + 250, 230)], fill=(30, 24, 48), outline=(163, 135, 255), width=2)
    # Centered headline & subtitle placeholder blocks
    draw.rectangle([(180, 260), (900, 310)], fill=(240, 240, 255))
    draw.rectangle([(280, 325), (800, 355)], fill=(180, 175, 200))

    # 4 horizontal card rows
    y_start = 400
    for i in range(4):
        y = y_start + i * 140
        draw.rectangle([(140, y), (940, y + 110)], fill=(25, 20, 40), outline=(100, 80, 160), width=1)
        # Row content placeholders
        draw.rectangle([(170, y + 25), (320, y + 85)], fill=(163, 135, 255))
        draw.rectangle([(360, y + 35), (750, y + 55)], fill=(220, 220, 235))
        draw.rectangle([(360, y + 65), (650, y + 80)], fill=(140, 135, 160))
        draw.rectangle([(780, y + 30), (910, y + 80)], fill=(40, 32, 60))

    # Footer
    draw.rectangle([(340, 1000), (740, 1030)], fill=(100, 95, 120))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    im.save(output_path)
    print(f"Generated bad generic visual at: {output_path}")


def run_test_mode():
    print("=" * 75)
    print("TEST MODE: PART 1 — DELIBERATELY BAD GENERIC LAYOUT")
    print("=" * 75)

    bad_visual_path = REPO_ROOT / "pipeline" / "state" / "bad_template_rendered.png"
    create_bad_generic_visual(bad_visual_path)

    bad_draft = {
        "final_hook": "The Next-Gen Revolutionary Autonomous Credit Protocol in DeFi is Finally Here!",
        "final_body": (
            "The Next-Gen Revolutionary Autonomous Credit Protocol in DeFi is Finally Here!\n\n"
            "We are completely disrupting traditional lending with an all-in-one ecosystem dashboard.\n"
            "• Metric 1: 100% Capital Efficiency across all pools\n"
            "• Metric 2: 500% Borrow Power with zero risk of bad debt\n"
            "• Metric 3: Automated liquidation elimination\n"
            "• Metric 4: Multi-chain expansion coming soon\n\n"
            "Read our whitepaper and join our revolution today: docs.vanna.finance"
        ),
        "visual_brief": {
            "type": "infographic",
            "headline": "Next-Gen Credit Dashboard",
            "subhead": "4 key metrics that define our advantage",
            "hero": {"value": "500%", "label": "Max Power"},
            "data": [
                {"label": "Metric 1", "value": "100%", "note": "Pool efficiency"},
                {"label": "Metric 2", "value": "500%", "note": "Borrow multiplier"},
                {"label": "Metric 3", "value": "0.00%", "note": "Bad debt guarantee"},
                {"label": "Metric 4", "value": "10x", "note": "Growth multiplier"}
            ],
            "footer": "docs.vanna.finance"
        }
    }

    # Spy on telegram dispatch to prove whether it is reached
    telegram_mock_1 = MagicMock()

    run_id_1 = "test-mode-bad-case-run-001"
    review_res_1 = review_package(
        draft=bad_draft,
        image_path=bad_visual_path,
        run_id=run_id_1,
        brief_data=bad_draft["visual_brief"]
    )

    # Pipeline gating simulation matching autonomous_orchestrator.py:590-605
    pipeline_blocked_1 = False
    if review_res_1["decision"] == "PASS":
        telegram_mock_1()
    else:
        pipeline_blocked_1 = True

    print("\n--- [PART 1 REVIEWER JSON RESULT] ---")
    print(json.dumps(review_res_1, indent=2))
    print(f"\nTelegram Dispatch Invoked: {telegram_mock_1.called}")
    print(f"Pipeline Hard Gate Blocked Delivery: {pipeline_blocked_1}")

    print("\n" + "=" * 75)
    print("TEST MODE: PART 2 — GENUINELY DIFFERENT PREMIUM VANNA ASSET")
    print("=" * 75)

    premium_visual_path = REPO_ROOT / "pipeline" / "state" / "vanna_competitor_matched_post2.png"
    
    premium_draft = {
        "final_hook": "Isolated margin walls you in. Unified margin sets you free.",
        "final_body": (
            "Isolated margin walls you in. Unified margin sets you free.\n\n"
            "Standard DeFi forces you to manage risk in fragmented silos—one position liquidation can trigger even while capital sits idle next door.\n\n"
            "Vanna’s unified portfolio margin aggregates cross-margined risk into a single solvency ratio:\n"
            "• Every position marked by unified oracle feeds.\n"
            "• Drawdowns in one asset are offset by gains in another.\n"
            "• Autonomous risk guardians operate beneath scoped session keys—keeping health factors resilient 24/7 without taking custody.\n\n"
            "Explore the credit architecture: vanna.finance"
        ),
        "visual_brief": {
            "content_category": "NARRATIVE_THESIS",
            "layout_archetype": "visual metaphor",
            "headline": "Unified Margin Equilibrium Lattice",
            "footer": "vanna.finance"
        }
    }

    telegram_mock_2 = MagicMock()

    run_id_2 = "test-mode-premium-pass-run-002"
    review_res_2 = review_package(
        draft=premium_draft,
        image_path=premium_visual_path,
        run_id=run_id_2,
        brief_data=premium_draft["visual_brief"]
    )

    pipeline_blocked_2 = False
    telegram_dispatched_2 = False
    if review_res_2["decision"] == "PASS":
        telegram_mock_2(draft=premium_draft, image=str(premium_visual_path))
        telegram_dispatched_2 = True
    else:
        pipeline_blocked_2 = True

    print("\n--- [PART 2 REVIEWER JSON RESULT] ---")
    print(json.dumps(review_res_2, indent=2))
    print(f"\nTelegram Dispatch Invoked: {telegram_dispatched_2}")
    print(f"Pipeline Hard Gate Blocked Delivery: {pipeline_blocked_2}")


if __name__ == "__main__":
    run_test_mode()
