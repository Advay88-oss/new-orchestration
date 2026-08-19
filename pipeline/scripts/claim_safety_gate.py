#!/usr/bin/env python3
"""Vanna claim-safety gate — deterministic compliance check for generated content.

Implements the hard prohibitions, Tier F poison list and Tier C labelling rules
from files/08-facts-ledger-and-claim-safety.md, plus the voice prohibitions from
files/04-brand-voice-and-message-library.md.

This is a GATE, not a filter. Any BLOCK-severity violation fails the draft and
sends it back to the strategist. It never appears in front of a human reviewer.

Usage:
    python claim_safety_gate.py --text "post copy here"
    python claim_safety_gate.py --file draft.json          # {"text": ..., "platform": ...}
    echo '{"text":"..."}' | python claim_safety_gate.py --stdin

Exit codes: 0 = pass, 1 = blocked, 2 = usage error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

BLOCK = "BLOCK"
WARN = "WARN"


@dataclass
class Rule:
    id: str
    severity: str
    pattern: str
    why: str
    fix: str
    flags: int = re.IGNORECASE


@dataclass
class Violation:
    rule: str
    severity: str
    matched: str
    why: str
    fix: str


# --------------------------------------------------------------------------
# The 14 hard prohibitions (08 §3)
# --------------------------------------------------------------------------
HARD_PROHIBITIONS = [
    Rule(
        "P1-mainnet-live",
        BLOCK,
        r"\b(?:live on mainnet|now live|mainnet is live|launched on mainnet|"
        r"trading live|funds are (?:live|deployed)|our mainnet|"
        r"launch(?:ing)? soon|going live|"
        r"(?:is|are|we'?re)\s+live(?!\s+on\s+(?:Stellar\s+)?testnet))\b",
        "Implies mainnet is live or imminent. Vanna is pre-mainnet, Stellar testnet only.",
        "Say 'Currently on Stellar testnet. Mainnet addresses will be published at launch.'",
    ),
    Rule(
        "P1-tvl",
        BLOCK,
        r"\b(?:TVL|total value locked)\b",
        "There is no TVL. Vanna is pre-mainnet.",
        "Remove entirely. No TVL figure of any kind may be published.",
    ),
    Rule(
        "P2-security-claims",
        BLOCK,
        r"\b(?:audited|audit(?:s)?\b|bug bount(?:y|ies)|multi-?sig|timelock(?:s|ed)?|"
        r"formal(?:ly)? verif(?:ied|ication)|insur(?:ed|ance))\b",
        "No audits, bug bounty, multi-sig, timelocks, formal verification or insurance exist.",
        "Say 'Security documentation is being published ahead of mainnet.'",
    ),
    Rule(
        "P3-token",
        BLOCK,
        r"\b(?:airdrop|token(?:omics)?\b|\$VANNA|points? program(?:me)?|"
        r"early users will be remembered|retro(?:active)? reward|farming points)\b",
        "No token, airdrop, points or rewards exist. This is an absolute rule — "
        "including jokes, emoji and winks.",
        "Remove entirely. Never hint otherwise, in any channel, ever.",
    ),
    Rule(
        "P4-demo-as-result",
        BLOCK,
        r"\b(?:our users earned|users earned|returns of|we delivered|"
        r"traders earn(?:ed)?|generated returns)\b",
        "Presents demo/mock figures as realised results.",
        "Label as 'illustrative example' / 'a worked scenario' / 'in this example'.",
    ),
    Rule(
        "P5-returns-promise",
        BLOCK,
        r"\b(?:guaranteed|risk-?free|can'?t lose|no downside|assured returns|"
        r"promised? (?:returns|yield)|will earn)\b",
        "Promises or implies returns.",
        "Remove. Use conditional framing and state that risk remains.",
    ),
    Rule(
        "P6-financial-advice",
        BLOCK,
        r"\b(?:you should (?:buy|invest|deposit|allocate)|we recommend (?:buying|investing)|"
        r"financial advice|investment advice|(?:this|it) is a good investment)\b",
        "Constitutes financial, investment, legal or tax advice.",
        "Remove. Describe mechanisms, never recommend allocation.",
    ),
    Rule(
        "P7-competitor-superiority",
        BLOCK,
        r"\b(?:better than|superior to|beats|outperforms|kills|destroys|"
        r"replaces)\s+(?:Gearbox|Hyperliquid|Morpho|Aave|Blend|Compound|dYdX|GMX|Euler|Spark)\b",
        "Claims superiority over a named competitor. Explicitly forbidden.",
        "Compare jobs-to-be-done instead: 'Gearbox is universal leverage. Vanna is built for "
        "derivatives and hedging.' Use 'X vs Vanna' framing, never superiority.",
    ),
    Rule(
        "P8-internal-leak",
        BLOCK,
        r"\b(?:break-?even TVL|launch blocker|funding gap|scorecard|35/70|"
        r"remove Stellar|single EVM L2|cut integrations|staged leverage rollout|"
        r"43[- ]tool|design without execution)\b",
        "Tier E internal-only material. Never appears in external content.",
        "Remove entirely.",
    ),
    Rule(
        "P10-live-integrations",
        BLOCK,
        r"\b(?:live|now|today|currently)\s+(?:\w+\s+){0,2}"
        r"(?:perps?|options|prediction market|tokeni[sz]ed stock|AI[- ]compute)\s+"
        r"(?:integration|support|trading|market)",
        "Claims live perps/options/prediction/tokenized-stock/AI-compute integrations. "
        "Only Blend, Aquarius and Soroswap are integrated, on testnet.",
        "Use future tense: 'built for' / 'designed for'. Name only Blend, Aquarius, Soroswap as live.",
    ),
    Rule(
        "P11-agent-autonomy",
        BLOCK,
        r"\b(?:(?:our|the) AI trades for you|trades? on your behalf|"
        r"fully autonomous trading|it trades while you sleep|bot trades your)\b",
        "Overstates the agent layer's autonomy. It is policy-bounded, human-approved, zero-custody.",
        "Say 'You state the intent. The copilot compiles it into a guarded position and hands it "
        "back — nothing signs without you.'",
    ),
    Rule(
        "P12-regulatory",
        BLOCK,
        r"\b(?:compliant|licen[sc]ed|regulated|KYC-?ready|SEC[- ]approved|"
        r"MiCA[- ]compliant|registered with)\b",
        "Makes a regulatory or compliance claim. None exist.",
        "Remove entirely.",
    ),
    Rule(
        "P14-fabricated-proof",
        BLOCK,
        r"\b(?:our customer|our client|case study|testimonial|"
        r"trusted by \d|\d+ companies use|as used by)\b",
        "Fabricates a customer, testimonial, case study or partnership. "
        "Ecosystem logos may not be described as customers.",
        "Remove. Ecosystem logos can be shown as ecosystem only.",
    ),
    Rule(
        "P13-infra-overclaim",
        BLOCK,
        r"\b(?:production-?grade|enterprise-?grade|bank-?grade|military-?grade|"
        r"carrier-?grade|battle-?tested|proven at scale|(?:99\.?\d*)\s*%?\s*uptime|"
        r"SLA-?backed|five nines)\b",
        "Infrastructure emphasis is the campaign lead, but Vanna is on testnet — "
        "there is no production, so proven-reliability or proven-scale language is false.",
        "Frame as architecture and design intent, e.g. 'built for B2B and B2C from one "
        "system' or 'designed to scale', not as proven production performance.",
    ),
]

# --------------------------------------------------------------------------
# Tier F — poison list (08 §2). Never repeat these.
# --------------------------------------------------------------------------
TIER_F = [
    Rule("F-1000x", BLOCK, r"\b1000\s*[x×]\b|\b1,?000\s*[x×]\s*leverage\b",
         "'1000× leverage' is a legacy/hackathon-era error. Canonical max is 10×.",
         "Use 10×."),
    Rule("F-tiered-leverage", BLOCK, r"\b5\s*[x×]\s*base\b|\b7\s*[x×]\s*blue-?chip\b",
         "Legacy EVM-era tiered leverage design. Current canonical is a flat 10×.",
         "Use 10×."),
    Rule("F-erc4337", BLOCK, r"\b(?:ERC|EIP)-?4337\b|\baccount abstraction\b",
         "Legacy. Current architecture is native Soroban per-user contracts.",
         "Say 'each user gets their own deployed SmartAccount contract on Soroban'."),
    Rule("F-legacy-dashboards", BLOCK, r"\b(?:Greeks Dashboard|Prop Dashboard)\b",
         "Legacy vocabulary. Not in the current product or docs.",
         "Remove."),
    Rule("F-optimism-legacy", BLOCK,
         r"\blive on Optimism\b|\bPerp Protocol\b",
         "Legacy EVM deployment. Current is Stellar Soroban testnet.",
         "Say 'Stellar testnet'."),
    Rule("F-2m-users", BLOCK, r"\b2\s*M\+?\s*users\b|\b2 million users\b",
         "'2M+ users' is aggregate reach of integrated protocols, not Vanna users.",
         "Say 'ecosystem reach across integrated protocols', or omit."),
    Rule("F-subscribers", WARN, r"\b40,?000\+?\s*subscribers\b",
         "Unconfirmed internal figure.",
         "Confirm with a human before external use."),
    Rule("F-perps-78", WARN, r"\b78%\s*of\s*derivatives\b",
         "Unverified internal research figure.",
         "Verify against a current public source before publishing."),
]

# --------------------------------------------------------------------------
# Retired claims (11 §1, §7). These were true until Aug 2026 and are now false
# or indefensible. Repeating them describes a competitor's shipped product.
# --------------------------------------------------------------------------
RETIRED = [
    Rule("R-mcp-differentiator", BLOCK,
         r"\b(?:first|only|unique(?:ly)?)\s+(?:\w+\s+){0,3}MCP\b|"
         r"\bMCP-native\s+(?:is|as)\s+(?:our|the)\s+(?:differentiator|advantage|edge)\b|"
         r"\bMCP\s+(?:is\s+)?(?:our|the)\s+(?:differentiator|moat|advantage)\b",
         "MCP is table stakes since Morpho Agents (Apr 2026, mainnet, ~$11.8B TVL) and "
         "Base MCP (May 2026). Leading with it describes a competitor's shipped product.",
         "Lead with undercollateralized credit: 'Morpho gives agents access to a lending "
         "market. Vanna gives them a balance sheet.'"),
    Rule("R-category-claim", BLOCK,
         r"\bnobody else is building\b|\bno one else is building\b|"
         r"\b(?:first|only) (?:protocol|company|team) to (?:build|offer)\b",
         "Category-invention claim. Kojiru ships an Agent Credit Score; ERC-8004, Visa TAP, "
         "WEF KYA and an IETF draft are standardising agent reputation.",
         "Claim the underwriting layer, not the category. See file 11 §2.3."),
    Rule("R-unforkable-moat", BLOCK,
         r"\bunforkable\b|\bcannot be forked\b|\bcan'?t be forked\b",
         "The 'unforkable data moat' framing was retired by file 11 §1.",
         "Say 'a credit decision needs a margin account to generate — that's the part that "
         "can't be copied from outside.'"),
    Rule("R-agent-score-present-tense", BLOCK,
         r"\b(?:our|the) Agent Score (?:gives|provides|underwrites|determines|scores|powers)\b|"
         r"\bAgent Score (?:is|does) (?:live|working|underwriting)\b",
         "The Agent Score has no documented sybil resistance (file 11 §3). It must stay in "
         "future tense until that design ships.",
         "Say 'Vanna is building an Agent Score that turns on-chain behaviour into a credit line.'"),
    Rule("R-logo-wall-as-live", BLOCK,
         r"\b1[0-9]\+?\s*integrations\b|\b6\+?\s*chains\b|"
         r"\b(?:live|integrated) (?:with|on) (?:\w+\s+){0,2}"
         r"(?:Hyperliquid|Uniswap|Morpho|Aerodrome|Avantis|Derive|Aster|Katana)\b",
         "Only Blend, Aquarius and Soroswap are live, all on Stellar testnet. The logo wall "
         "is ecosystem, not integrations (file 11 §6).",
         "Say 'Deep integrations with Blend, Aquarius and Soroswap today, with a broader "
         "venue roadmap.'"),
    Rule("R-stellar-liquidity", WARN,
         r"\bStellar (?:is where|has) (?:\w+\s+){0,2}(?:DeFi )?liquidity\b",
         "Stellar's entire DeFi TVL is ~$161M. The liquidity framing does not survive scrutiny.",
         "Say 'Stellar has $2.4B in RWAs, institutions and live agentic payment rails — and "
         "no credit layer.'"),
]

# --------------------------------------------------------------------------
# Voice prohibitions (04 §Voice — DON'T)
# --------------------------------------------------------------------------
VOICE = [
    Rule("V-hype-register", BLOCK,
         r"(?:^|[^\w])(?:moon(?:ing|shot)?|wen\b|WAGMI|LFG|gm\b|ape(?:d|ing)?\b|degen)(?:[^\w]|$)",
         "Crypto hype register is banned brand-wide.",
         "Remove. The brand is professional, educational, confident — never hype."),
    Rule("V-banned-adjectives", BLOCK,
         r"\b(?:revolutionary|game[- ]chang(?:er|ing)|next[- ]gen(?:eration)?|seamlessly)\b",
         "Explicitly banned word.",
         "Delete the adjective and state the mechanism instead."),
    Rule("V-exclamation", BLOCK, r"!",
         "Exclamation marks are banned — 'the brand does not shout.'",
         "Replace with a period.", re.NOFLAG),
    Rule("V-leverage-as-verb", WARN,
         r"\bleverage\s+(?:our|your|their|its|the)\s+\w+\s+to\b",
         "'leverage' as a verb meaning 'use' is banned.",
         "Use 'use'. Reserve 'leverage' for the financial noun."),
    Rule("V-fomo", BLOCK,
         r"\b(?:don'?t miss out|last chance|act now|limited time|only \d+ spots|"
         r"before it'?s too late)\b",
         "FOMO or scarcity pressure is banned.",
         "Remove."),
]

# --------------------------------------------------------------------------
# Tier C — demo figures that require an illustrative label
# --------------------------------------------------------------------------
DEMO_FIGURES = re.compile(
    r"\b(?:26%\s*ROI|742(?:/850)?|\+?\$302|47 saves|\$1,?200,?000|1\.8 avg|"
    r"11\.5%\s*APY|\+\$265|net \+?\$\d+)\b",
    re.IGNORECASE,
)
LABEL_PHRASES = re.compile(
    r"\b(?:illustrative|worked scenario|in this example|hypothetical|for example|"
    r"modelled scenario|example only)\b",
    re.IGNORECASE,
)
TESTNET_DISCLOSURE = re.compile(r"\btestnet\b", re.IGNORECASE)


def active_rules() -> tuple[list, str]:
    """The rule set to evaluate, and where it came from.

    Prefers an OKF bundle so a new company is a markdown edit rather than a
    code edit. Falls back to the built-in literals below whenever a bundle is
    absent, unreadable, or carries no rules — a safety control must never fail
    open because a knowledge pack is missing.

    Returns (rules, source) where source is 'okf:<path>' or 'builtin'.
    """
    builtin = HARD_PROHIBITIONS + TIER_F + RETIRED + VOICE
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from okf_loader import Bundle, default_bundle_path

        path = default_bundle_path()
        rules = Bundle.load(path).rules()
        if not rules:
            return builtin, "builtin"
        return rules, f"okf:{path}"
    except Exception:
        # Any bundle problem falls back to the built-ins. Deliberate: a broken
        # pack degrades to the stricter known-good rules, never to no rules.
        return builtin, "builtin"


def check(text: str, platform: str = "x", require_testnet: bool = True) -> dict:
    """Run every rule against the text. Returns a structured verdict."""
    violations: list[Violation] = []
    rules, rules_source = active_rules()

    for rule in rules:
        for match in re.finditer(rule.pattern, text, rule.flags):
            snippet = match.group(0).strip()
            if not snippet:
                continue
            violations.append(
                Violation(rule.id, rule.severity, snippet, rule.why, rule.fix)
            )
            break  # one hit per rule is enough to fail it

    # Tier C: demo figures present but no illustrative label
    if DEMO_FIGURES.search(text) and not LABEL_PHRASES.search(text):
        found = DEMO_FIGURES.search(text).group(0)
        violations.append(
            Violation(
                "C-unlabelled-demo",
                BLOCK,
                found,
                "Uses a Tier C demo figure without an illustrative label. "
                "These numbers are website/video mocks, not results.",
                "Add 'illustrative example', 'a worked scenario', or 'in this example'.",
            )
        )

    # Any leverage or credit claim should disclose testnet status
    if require_testnet and re.search(r"\b10\s*[x×]\b|\bcredit line\b|\bborrow\b", text, re.I):
        if not TESTNET_DISCLOSURE.search(text):
            violations.append(
                Violation(
                    "A-missing-testnet",
                    WARN,
                    "leverage/credit claim without testnet disclosure",
                    "Leverage and credit claims imply live capital unless testnet is stated.",
                    "Add 'on Stellar testnet' or the standard disclaimer line.",
                )
            )

    blocked = [v for v in violations if v.severity == BLOCK]
    return {
        "pass": not blocked,
        "platform": platform,
        "block_count": len(blocked),
        "warn_count": len(violations) - len(blocked),
        "violations": [asdict(v) for v in violations],
        # Which knowledge pack produced this verdict. Callers that log verdicts
        # should keep it: 'builtin' on a run that expected a bundle means the
        # company's own rules were silently not applied.
        "rules_source": rules_source,
        "rule_count": len(rules),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Vanna claim-safety gate")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--text")
    src.add_argument("--file", type=Path)
    src.add_argument("--stdin", action="store_true")
    ap.add_argument("--platform", default="x")
    ap.add_argument("--no-testnet-check", action="store_true")
    args = ap.parse_args()

    if args.text:
        text, platform = args.text, args.platform
    else:
        raw = sys.stdin.read() if args.stdin else args.file.read_text(encoding="utf-8")
        try:
            payload = json.loads(raw)
            text = payload.get("text", "")
            platform = payload.get("platform", args.platform)
        except json.JSONDecodeError:
            text, platform = raw, args.platform

    if not text.strip():
        print(json.dumps({"pass": False, "error": "empty text"}), file=sys.stderr)
        return 2

    verdict = check(text, platform, require_testnet=not args.no_testnet_check)
    print(json.dumps(verdict, indent=2, ensure_ascii=False))
    return 0 if verdict["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
