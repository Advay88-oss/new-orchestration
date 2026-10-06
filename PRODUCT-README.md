# Vanna GTM — product map (A to Z)

This file is a product description for a redesign. It says what the product is, what each screen is for, what the backend does, which model sits in which step, and where a person still has to act.

It matches the working tree as of 6 Oct 2026. The hosted site (`vanna-gtm-mission` on Cloud Run) can be one deploy behind this file.

**The product does not publish.** A finished post waits for a person. Telegram can record Approve, Revise, or Kill. Nobody, including the Assistant, posts to X, LinkedIn, or Reddit.

---

## 1. What the product is

Vanna GTM is an internal mission-control for **Vanna Protocol** (composable credit: Stellar/Soroban is the approved company profile; Solana product pages also live in the brain). It watches the market, writes one post at a time (X, LinkedIn, Reddit), draws a poster, sometimes a short video, checks every claim, and stops at human review.

A second company, **Auri**, can use the same engine. The brain is per company. One company cannot read another.

Two websites:

| Surface | URL shape | Job |
|---|---|---|
| Mission Control | `/` | The working desk: chat, history, research, inspiration, campaigns, references |
| Brief | `/brief` | One post, the source it used, and a box that asks for another post |

Owner opens the public link once with `?key=`. After that they can change the clock, start work, and review. A visitor who never used the key only sees runs that started after their first visit, and cannot change anything.

---

## 2. How finished it is

The loop exists and has produced real posts.

| Done | Still thin or local-only |
|---|---|
| Scout, analyst, strategist, copy, poster, claim check, creative judge, Telegram review | Learning scores stay empty until someone actually publishes and pastes the link |
| Brand brain (profile, docs, Notion, GitHub pages, public watch) | Approved profile is still the Stellar one. Solana pages sit beside it as knowledge, not as a replacement profile |
| Assistant that answers from the brain and can set a schedule, study a brand, and search campaigns | Creating the real Cloud Scheduler cron needs `gcloud auth login` on the machine that runs the Assistant |
| Scraped Intelligence, What Vanna Can Do, Campaigns, References, Post History | Scheduler, Live Trace, Learning, Memes, and Ideas still exist in code. They are **not** in the current sidebar |
| Poster path (image model) and video path (Veo) | Video stops for the day when the Veo budget cap is hit. Glassmorphism is banned in prompts; the image model can still copy old reference posters until a judge rejects it |
| Human review on the run and on Telegram | There is no publish button and there must not be one |

---

## 3. Workflow (one post)

```
Clock or a sentence on /brief or a proposed launch
        |
        v
Research already collected (headlines, public watch, GitHub, Notion)
        |
        v
A01 Scout          no model     harvest.json
A02 Analyst        reasoning    grades each item, writes a post idea
A02 Selector       reasoning    one subject (your sentence wins)
A03 Strategist     reasoning    accept or decline. Decline = no post
A06 Copywriter     reasoning    X, LinkedIn, Reddit
A07 Creative dir.  director     layout + poster brief. Opaque surfaces only
A08 Poster         image model  1080 square PNG
A09 Video          Veo          short MP4 when the request asked for motion
A15 Creative judge reasoning    REJECT blocks the run
A10 Fact checker   reasoning    claim gate. A bad claim blocks the run
A11 Delivery       no model     Telegram review packet. Does not publish
A13 Learning       director     writes what this run added to the reward record
        |
        v
Status completed or review_blocked
A person approves, revises, or kills
If they post it themselves and reply with the link, metrics can be read ~48h later
```

A typed sentence on `/brief` is the subject. The strategist may decline it. It does not quietly swap in a different topic.

A clock run with no sentence picks a scraped item the analyst graded as usable, and uses a product page only as the mechanism.

One post takes on the order of 10–20 minutes. The shortest allowed gap between posts is **20 minutes**. A scrape can be every **2 minutes**.

---

## 4. Architecture

```
Browser
  Mission Control (/) and Brief (/brief)
  Next.js app: hermes-mission
        |
        |  reads JSON, starts jobs, streams the Assistant
        v
Cloud Run service  vanna-gtm-mission
        |
        |  starts
        v
Cloud Run job  vanna-gtm-pipeline
  one container, many commands: a full post, a scrape, a brain update, a tick
        |
        +--> Brand brain   Cloud SQL Postgres + pgvector, one row-level tenant
        |    embeddings: gemini-embedding-2, 768 dimensions
        |
        +--> State bucket  vanna-gtm-state-504607
        |    runs, posters, videos, the clock's interval file
        |
        +--> Telegram webhook on the dashboard
             Approve / Revise / Kill comes back as a short pipeline job

Cloud Scheduler  vanna-gtm-tick
  fires every 2 minutes
  only starts a job whose own gap has elapsed
  jobs that have their own cron are left to that cron
```

GCP project `sales-agent-504607`, region `us-central1`.

The dashboard is a window. Opening it does not scrape, embed, or write a post. The brain is the database. Agents read the company through the brain. They do not read the dashboard.

Laptop: Next.js on port 3000, Python pipeline, SQLite brain when Cloud SQL is unreachable. Production brain is Cloud SQL.

---

## 5. Models

Declared in `pipeline/gtm_os/agent_runtime.py`. Env vars can override the id. The brain's language calls use the Generative Language API key. Do not route the brain through Vertex.

| Role | Model id | Used for |
|---|---|---|
| reasoning | `gemini-3.8-flash` | Analyst, selector, strategist, copywriter, both judges, Assistant |
| director | `gemini-3.8-flash` | Motion director (poster brief and video plan), learning coach |
| image | `gemini-3-pro-image` on the direct poster path (`direct_image_posters.MODEL`). The runtime table still lists `gemini-3.1-flash-image` as the fallback image role | The square poster |
| meme | `gemini-3-pro-image` | Meme image, only when a meme was asked for |
| video | `veo-3.1-generate-001` | Short motion clip. Daily cap applies |
| embeddings | `gemini-embedding-2` | Every brain chunk and captioned image. 768 floats |

A run over the daily budget is `refused_budget`. No agents run. Telegram gets one note.

---

## 6. Agents (the twelve that run a post)

Older ids were merged. The journal may still show `A14` or `A16` on old runs. Current names:

| Id | Name | Model role | What it does | What it writes |
|---|---|---|---|---|
| A01 | Intelligence Scout | none | Reads news, Reddit, X, Telegram previews, DefiLlama, plus headlines the research job already stored | `harvest.json` |
| A02 | Market Analyst | reasoning | Grades each item direct / adjacent / not relevant. Writes one post idea on the usable ones | `analysis.json` |
| A02 | Opportunity Selector | reasoning | Picks the one subject | decision row |
| A03 | GTM Strategist | reasoning | Accepts or declines. Machine check and campaign-shape check sit inside this role | strategy, or a decline |
| A06 | Copywriter | reasoning | X, LinkedIn, Reddit from that strategy | copy in `summary.json` |
| A07 | Creative Director | director | One layout, one headline, one surface. Glass, frost, blur, and see-through cards are a fault | poster brief |
| A08 | Poster Designer | image | Draws the poster from the brief plus approved posters (type, spacing, logo, contrast — not their glass) | PNG |
| A09 | Video Producer | video | Motion from the same post. Skipped when the request is a still, or when the sentence says "post" and never says video | MP4 |
| A15 | Creative Judge | reasoning | Looks at the copy and the actual image. A glass poster is a reject | verdict |
| A10 | Reviewer | reasoning | Slop and claims against the brain and the claim-safety gate. No invented numbers | pass or block |
| A11 | Delivery | none | Builds the Telegram packet. Dispatch stays idle until a person has approved | Telegram message |
| A13 | Learning | director | Reads the reward record and notes what this run added | learning state |

The maker never grades itself. A15 and A10 are separate from A06 and A08.

---

## 7. Frontend

Stack: Next.js (`hermes-mission`), one shell (`MissionControl`) plus `/brief`. Sidebar is fixed. Mobile gets a menu button. Theme is light/dark on the rail. Company switcher selects the tenant the Assistant and the brain talk about.

There is **no Launch Run button** in the header. A post starts from `/brief`, from the clock, or from an Assistant card that only proposes an action the owner confirms.

### Sidebar (what a person sees)

#### Assistant

Chat for the selected company. Answers come from that company's brain, with the sources used. A line that says the turn did not consult the brain is a label, not a crash.

It can, from one sentence:

- answer a product question (`search_knowledge`, `brand_profile`, `whats_new`)
- look up recent news the brain does not have (`web_search`)
- list or open a run (`list_runs`, `get_run`)
- study a brand onto What Vanna Can Do (`study_brand`) — name, optional X handle
- search campaigns (`find_campaigns`) — the Campaigns page shows the shelf
- set the clock (`set_post_cadence`) — scrape gap, post gap, meme gap, stop, a post count. The tool also tries to create one Cloud Scheduler cron per job
- offer a button the owner must press (`propose_action`): launch, approve, revise, kill, approve profile. The chat does not do those by itself

A client link (not the owner) cannot list other companies, onboard a company, set the clock, search campaigns, or study a brand.

#### Post History

One card per content run, newest first. The sidebar count is runs that actually contain a post. Open a card for the run detail: copy per channel, poster, video if any, claims, status, and the owner's decision.

Empty state tells the person to use the Assistant. It does not offer a launch button.

#### Scraped Intelligence

The reading list. Two layers:

- **Collected research** — headlines from the research job (`research_latest.json`). Kind, source, headline, style. Updates when research runs, between posts. These items also feed the learning record lightly.
- **Scout table** — docs, posts, news, and market pages from a content run (`harvest.json`). Each row can open the original page and jump to References.

This page does not write posts.

#### What Vanna Can Do

Inspiration cards. A brand (Gearbox, Morpho, and others the watch already knows) shows what they posted and what Vanna could adapt. The person does not type a brand, an X handle, and a subreddit into a form. They tell the Assistant. A research timer also files watched X accounts onto this shelf and refreshes the stalest card.

Company switcher stays. It changes tenant. It is not the brand form.

#### Campaigns

Shelves of live campaigns (Galxe and other sources the Assistant searched). No query form on the page. "Search again" reruns the shelf's last query. The Assistant's `find_campaigns` is how a new search starts.

#### References

The analyst's reading of the same sources: grade (direct, adjacent, not relevant), a post idea, and the move a strategist would make. Unread items stay unread until a run's analyst has graded them. "Open in References" from a scraped row or from `/brief` lands here.

#### Run detail (not a sidebar item)

Reached only by opening a post. Shows the work of that run: copy, image, video, why it was blocked, Approve / Revise / Kill for the owner.

### Pages that exist and are not on the sidebar

| View | Still in the app | How you reach it now |
|---|---|---|
| `/brief` | Yes, own route | Direct URL. Newest post, its source, a box to ask for another |
| Live Trace | Component exists | Not in the nav. The run journal (decisions, model calls) is what it was for |
| 24/7 Scheduler | Component exists | Not in the nav. The Assistant's cadence sentence is the control. The view can still render if something sets that view |
| Learning | Component exists | Not in the nav. Reward arms (pillar, format, hook, slot) update in the backend. Approve = 1, revise = 0.3, kill = 0 |
| Crypto Memes / Ideas | Components exist | Not in the nav. Jobs can still be turned on by a cadence sentence |
| Brand Brain screen | Removed from the dashboard | The database is still there. The Assistant is the way in |
| Notion connect | `/connect/notion` | OAuth return. The Assistant can hand the owner a connect link |

### `/brief`

Shows the newest post that has copy, the source that run recorded (title, publisher, excerpt, link), and a text box. Send starts the same cycle with that sentence and does not ask for a video. The new run appears in Post History when it finishes. It does not appear the moment Send is clicked.

### Visual rules the screens should respect

- One company at a time.
- Status words a person can read: running, held for review, blocked, declined, over budget, failed.
- Missing data stays missing. Do not draw a zero for a scrape that returned nothing.
- No publish control. No purple Launch Run control in the header.
- Owner vs visitor is real: visitors do not get cadence, campaign search, or review buttons.

---

## 8. Backend sections

Code lives under `pipeline/`. A job is a command on the pipeline container. The 2-minute tick starts whichever of these is due.

| Job id | Plain name | Model? | Shortest gap | What it leaves |
|---|---|---|---|---|
| `gtm_cycle` | Writes a post | yes | 20 min | `gtm_runs/GTM-…/` copy, poster, maybe video, status |
| `research_collect` | Collects headlines | light | 2 min | `research_latest.json`. Scraped Intelligence. Next scout reads a few of them |
| `brain_watch` | Listens in public | no | 60 min in yaml | X, Reddit, news, blog, web summary into the brain. Own channels authority 3. Everyone else authority 5 (never proof for a claim) |
| `github_commits` | Reads product GitHub | no | 30 min | Solana and Stellar docs into the brain. A figure may be used only when that page states it |
| `notion_sync` | Syncs Notion | no | 60 min | Connected Notion pages. Token is per company |
| `metrics_collect` | Reads a published post | no | 60 min | Engagement ~48h after a link was stored. Feeds Learning |
| `ops_watch` | Health | no | 10 min | Failed jobs, brain, Telegram webhook, dashboard, budget. Telegram when something new breaks |
| `memes_panel` | Memes | light | 5 min | Off unless a cadence sentence turns it on |
| `ideas_panel` | Idea list | yes | 5 min | Off unless a cadence sentence turns it on |
| `trend_scan` | Extra headlines | no | 2 min | Off in the yaml |

Telling the Assistant "scrape every 5 minutes, a post every 20 minutes, memes on" writes `scheduler_intervals.json` and tries to create:

- `vanna-cron-research-collect`
- `vanna-cron-gtm-cycle`
- `vanna-cron-memes-panel`

"Stop" pauses that cron. The 2-minute tick skips jobs that have their own cron so they do not run twice.

If a post is still running, the next one waits. The lock is about 20 minutes.

### Brand brain (`pipeline/brand_brain`)

Postgres `brand-brain`, row-level security per tenant. On a laptop that cannot reach Cloud SQL, the code falls back to SQLite so the Assistant still answers.

Holds: approved profile, docs, Notion, GitHub pages, public-watch items, competitor pattern summaries, inspiration brands, campaign shelves, chat is separate. Search is vector plus keyword. Authority 1 is founder-confirmed. Authority 5 is an outside page.

Agents do not treat an outside sentence as a fact. The reviewer blocks a claim the brain does not support. The profile is not rewritten by a chat. A new profile version waits for approval.

### Other backend areas

| Area | Path | Work |
|---|---|---|
| Content cycle | `pipeline/gtm_os/autonomous_cycle.py` | The twelve-agent post |
| Creative | `pipeline/gtm_creative/` | Brief, poster, video, archetypes, taste. Glassmorphism is banned |
| Learning | `pipeline/gtm_learning/` | Bandit over pillar, depth, format, hook, length, slot. Coach writes rules |
| Assistant | `pipeline/assistant/` | Chat, tools, 45s tool cap. A slow file upload is not reported as a failed save |
| Scheduler | `pipeline/scheduler/` | Parse a sentence, write intervals, create or pause crons |
| Claim gate | `pipeline/scripts/claim_safety_gate.py` | Deterministic pass/fail. No invented numbers |
| Ingestion | `pipeline/intelligence_stream/` | Continuous scrape. After a poll it can file watched accounts onto What Vanna Can Do |
| Ops / budget | `pipeline/ops/budget.py` | Daily caps, including Veo |

### Status words

| Status | Meaning |
|---|---|
| `running` | The cycle is still writing |
| `completed` | Copy and judges passed. Still waiting for a person |
| `review_blocked` | A post exists. A judge or the fact check stopped it. Still waiting for a person |
| `NO_ACTION` / `KILL` | Strategist declined. No post |
| `refused_budget` | Daily cap, before agents started |
| `skipped_locked` | Another cycle was already running |
| `failed` | The cycle crashed |
| `aborted` | The scout found nothing to read |

### Telegram

Approve records a good verdict and asks for the link after the person posts it themselves. Revise stores the note and does not redraw. Kill stores the rejection. The post stays in history either way.

---

## 9. What a redesign should keep true

- One desk, one company, six jobs in the rail: talk, history, scraped reading, inspiration, campaigns, references. Brief can stay a second page or fold into the desk, but it is the same post.
- The Assistant is the control. Forms for "type Gearbox, paste X, paste subreddit" and "type a campaign query" are gone on purpose.
- Every post shows its source. A number on a poster exists only if a source stated it.
- Review is the end of the machine. The design can show Approve, Revise, and Kill. It cannot show Publish.
- Say when data is empty. Learning is empty until a post has actually gone out. Scraped Intelligence can be full while Post History is waiting on a person.
- Posters are opaque. The product banned frosted glass, blur, and glowing glass borders. A redesign of the **app** can still be calm and sharp. A redesign of the **posters** should not bring glassmorphism back.
