# Vanna testnet waitlist (V3) and Web App V4 — the October 2026 launch surfaces

Source: two design prototypes the team built as claude.ai artifacts, read 10 Oct 2026:
"Vanna Testnet Waitlist" (claude.ai/artifact/8KQg76yMVxB5NPvyM8yXJ7, versions V1–V3) and
"Vanna Web App V4" (claude.ai/artifact/6aG3KrGNZGotE9perhbhmr, "design prototype V4 at
test.vanna.finance, Solana + Stellar, sample data"), plus the team's launch-ops note (email
sending). Every number on these screens is SAMPLE DATA — never quote one as real.

## 1. The waitlist (V3, "credit profile first: your DeFi history decides your place")

**Hero:** "Your on-chain credit profile decides your place." · "Get early access. Early testers
unlock surprise rewards." · "Infrastructure for undercollateralized, leveraged credit you can use
across markets." · one email field + "Join the waitlist" · optional "Send me Vanna product news" ·
"Testnet on Solana and Stellar" · header button "Check your spot".

**The score (0–1,000):** up to 900 from on-chain history and up to 100 from boosters; the higher the
score, the sooner you get in.

| Part | Max | What it reads |
|---|---|---|
| Borrowing history | 250 | loans taken and repaid, months active, liquidations |
| Lending | 200 | what you've supplied and for how long |
| Leverage | 175 | perps and margin, and how healthy you kept it |
| Yield | 125 | LP, vaults and staking held |
| Breadth | 150 | protocols, chains and how old your wallets are |
| Boosters | 100 | friends who join and link a wallet (+10 each, up to 50), wallets on more chains (+20 per extra chain), a Seeker phone or SKR on Solana (+10) |

Tiers: Starter → Active → Seasoned → Pioneer. "Bigger isn't everything: steady, healthy use counts
more than one big trade." "Wash trading and fresh wallets don't count."

**How it works:** (1) Join with email — a 6-digit code confirms it's you; (2) Link the wallets you
use — Solana, Stellar and EVM, as many as you like; (3) Your DeFi history moves you up.

**Trust lines (reuse them):** "We read public history from the wallets you link." "Nothing moves:
one signature proves a wallet is yours, and it's never a transaction." "Public history only."

**Wallets:** Solana — Phantom, Solflare, Backpack; Stellar — Freighter, LOBSTR, OneKey; EVM —
MetaMask, Rabby, WalletConnect.

**States (flows):** Landing · Invited ("[name] invited you. Your join counts for them once you link a
wallet.") · Email code · Returning ("Check your spot", send code) · Profile with no wallet ("Link a
wallet to build your profile"; place shown, "Linking a wallet is the main way up") · Profile (score
ring, place, tier, linked accounts: email, X, "Follow @vannaprotocol — for testnet news, earns no
points", wallets; score breakdown; boosters; invite link vanna.finance/waitlist?ref=NAME with copy,
X and Telegram share) · Link a wallet (modal of 9 wallets) · Reading history ("Wallet confirmed —
signed, no transaction" → "Scanning Solana — loans, supply, perps, LP and staking" → "Updating your
score").

**FAQ (answers):** I'm new to DeFi — "Yes. Everyone gets a place on the list. Link any wallet you use
and invite friends to move up." Is the score a token — "No. The score and boosters are not tokens and
have no cash value. They set the order we let people into testnet." When does testnet open — "In
waves, top of the list first. We email you when your wave opens." What's Vanna — "Infrastructure for
undercollateralized, leveraged credit you can use across markets. You borrow against your collateral
and use that credit to trade spot, perps and more from one account."

**Legal lines:** "Rewards are at Vanna's discretion, have no guaranteed value and are not tokens. The
score and boosters are not tokens. Testnet runs on test funds." · Waitlist Terms and Privacy Policy ·
"© 2026 OneWorld Technology LLC. Vanna is a product of OneWorld Technology LLC."

**Earlier versions:** V1 "gamified waitlist" (code, spot, invites, quests, weekly board; "Join the Vanna
testnet"; what you get: early access in waves, Season 0 points, founding tester badge; abuse states:
invalid email, disposable email, abuse). V2 = V1 plus linked accounts (X follow-checks, several
invites, on-chain profile). V3 replaced points-first with the credit profile.

**Sending (launch ops note):** waitlist email through Resend (Loops' terms bar crypto and lending
without approval) from hello@mail.vanna.finance on a separate subdomain, replies to the team inbox;
fired by Getwaitlist's new-signup event (Make/Zapier or a small function), never from the page; DNS
for mail.vanna.finance, DKIM on Google Workspace, logos at vanna.finance/email/, Getwaitlist pointed
at vanna.finance/waitlist with its own emails off. The simple launch page: one email field, spot
number, invite link, share buttons, an email reminder box, three optional actions; no cookies; Join
above the fold on a phone. Open item: the correct X and Telegram handles ("vannaprotocol" is a
placeholder).

## 2. Web App V4 (test.vanna.finance — design prototype, sample data)

**What it is:** "V4 turns the Solana web app into test.vanna.finance: a waitlist first, one account
by email or wallet, Solana and Stellar behind a chain switcher, Rewards, and Deposit, Withdraw and
Transfer." Launch scope: "one site, one account, Solana and Stellar. Testnet first, behind a
waitlist. Mainnet built alongside." (62 testnet must, 46 nice, 53 mainnet adds, 15 dependencies.)

**Navigation:** Portfolio · Earn · Predict (beta) · Margin · Spot · Perps · Farm · Copilot · Rewards.
Header: chain switcher (Solana / Stellar), points, Deposit, account.

**Portfolio:** net worth split wallet / lending / margin equity; net earnings by lending, trading and
predictions; the health factor bar with borrowed, leverage and interest accrued.

**Perps (Solana):** perps on **Phoenix** from the Vanna margin account — collateral plus borrowed
credit, order leverage 1–5×, Phoenix fee 0.025%; the ticket shows the margin account after the order
(health factor, account leverage, available USDC, room before liquidation) and "Liq. price: none" for
the single position, because the account's one health factor governs. Positions table (e.g. a SOL-PERP
long, a BTC-PERP short). Predict and Perps stay on Solana; Stellar shows XLM and USDC on Blend,
Soroswap and Aquarius plus Farm and Analytics.

**Sign-in and account:** email (code), Google, Apple, X or a wallet (Phantom, Solflare, Backpack,
Freighter, LOBSTR, OneKey); one email creates a Vanna wallet on Solana and on Stellar; a one-time chain
pick, then the switcher. Each chain keeps its own assets, venues, margin account and health factor;
rewards and the account are shared. Testnet: get test funds in one tap.

**Rewards (testnet):** "Testnet Season (Season 0) started Sep 15 and ends at mainnet. Points are not
tokens and have no cash value." Overview (points, pending this week, rank, next weekly drop), claimable
rewards in test USDC ("no value") from fee rebates and referral earnings, points by source (earn,
margin borrow, trading volume, farm, predict, referrals, referred bonus, quests and waitlist),
Referrals, Leaderboard, Profile (display name, optional X connection).

**Predict (beta):** World (Solana) and Polymarket (Polygon) positions linked, not moved; "paired"
shares earn while you wait; a bet slip across outcomes.

**Mainnet workstream (not live):** audits and mainnet deploys on both chains, mainnet oracles (Pyth,
Reflector), risk limits and liquidation keepers, cross-chain deposits, CCTP V2 USDC, card on-ramp and
exchange deposits, rewards claims in USDC, Season 1 rules and sybil review, withdrawal security,
terms, geo-blocking and sanctions screening, Android and iOS apps.

## 3. What this means for content (rules)

- The waitlist is the launch object: the story is "your on-chain history decides your place" — a
  credit-profile idea, on brand with composable credit (it is literally underwriting).
- Every number on these screens is sample data (742, #1,243 of 18,420, 10,121 points…): show it only
  labelled "sample profile", never as a count of real people.
- Say "not a token, no cash value" whenever the score, points or rewards appear; never promise a
  reward's value. (Open founder decision: the facts ledger still bans mentioning points or rewards;
  the product now has testnet points and a USDC raffle.)
- Perps on Phoenix and the merged test.vanna.finance are the V4 design: future tense until live.
