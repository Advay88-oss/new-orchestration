# Vanna backend playbook

How the machine runs. The screens are in `DASHBOARD-PLAYBOOK.md`. This is what those screens are reading.

Checked against the pipeline code on 5 Oct 2026. The hosted clock, the jobs, and the newest post were already confirmed that afternoon in the dashboard playbook.

## The four pieces

| Piece | What it is | Where it runs |
|---|---|---|
| Dashboard | The website. It reads runs and shows them. It starts a job only when you press something or send a brief. | Cloud Run service `vanna-gtm-mission`, region `us-central1` |
| Pipeline | The agents. One content run, one research pass, one brain update. | Cloud Run job `vanna-gtm-pipeline`, same project |
| Clock | Wakes every 2 minutes and starts whichever job is due. | Cloud Scheduler `vanna-gtm-tick` |
| Memory | The brand brain, plus the files the dashboard reads. | Cloud SQL Postgres (`brand-brain`) for the brain. Google Cloud Storage bucket `vanna-gtm-state-504607` for runs, images, and the clock's notes. |

A container starts empty. Before a job works, it pulls the clock and the learned files from the bucket. The brain itself is already in Cloud SQL. When the job finishes, it pushes the new run back, so the dashboard can show it.

The project is `sales-agent-504607`. The account that deploys it is `anand@vanna.finance`.

## What happens every 2 minutes

Cloud Scheduler calls the pipeline job with the command `tick`.

The tick looks at `config/scheduler.yaml`, then at `scheduler_intervals.json` in the bucket. A pill you click on the 24/7 Scheduler page writes that second file. The pill wins over the yaml.

A job runs only when all of these are true:

- It is on the cloud list: writes a post, collects research, listens in public, reads GitHub, syncs Notion, reads published-post results, checks health.
- It is enabled.
- Its last run is older than its gap.
- It is not already running.
- Another long job is not holding the lock. The lock lasts up to 20 minutes so two posts do not start together.

Trend headlines, the ideas panel, and the meme panel are in the yaml with `enabled: false`. The tick skips them.

If a job throws, the clock marks it failed and Telegram gets one note. The same fingerprint is not shouted again every 2 minutes. A later health check can mention that it is still happening.

## One post, agent by agent

The post job is `gtm_cycle`. On the clock it runs with video. A message from the brief page runs the same function with your sentence attached and with video turned off.

The run id looks like `GTM-20261005-080018`. That is the UTC time the run started. Every file for that post sits in `gtm_runs/<that id>/` in the bucket.

Twelve roles do the work. A few older step names still appear in the journal because they were folded into these roles. The maker never grades itself. The two judges are separate.

1. **Intelligence Scout (A01).** No model. Reads live news, Reddit, X, Telegram, and DefiLlama, and prepends the research list the research job already collected. Writes `harvest.json`. This is the scout table on Scraped Intelligence.
2. **Market Analyst (A02).** Reasoning model. Reads that whole harvest. Grades each item direct, adjacent, or not relevant, and writes one post idea on the relevant ones. Writes `analysis.json`. This is References.
3. **Opportunity Selector (A02).** Picks the subject. If you typed a sentence, that sentence is the subject. If the clock started the run, it prefers a scraped source the analyst graded as usable, and uses the next unread GitHub page only as the mechanism. If nothing scraped is usable, it rotates a product page: Solana margin, Solana earn, how Stellar works, the Stellar floor. It remembers the last pages so the next run moves on.
4. **GTM Strategist (A03).** Decides whether there is a real post here. A decline stops the run. The copywriter, the designer, and the judges are then marked skipped. On a clock run it may try up to three subjects. On a sentence you typed, a decline is the answer. It does not quietly swap in a different topic. The machine check and the campaign-shape check run inside this role.
5. **Copywriter (A06).** Writes the X, LinkedIn, and Reddit posts from that strategy. If the subject is a scraped page, the post is about that page.
6. **Creative Director (A07).** Chooses the layout and writes the poster brief. The diagram has to depict the post. It does not add Blend, Aquarius, SmartAccount, or 1.10× unless the post itself names them. Recent layouts are remembered so the next poster is a different shape.
7. **Poster Designer (A08).** Image model. Renders the poster. A meme is the same agent and runs only when the request asked for one. A brief-page request does not ask for a meme.
8. **Video Producer (A09).** Veo. Runs on a clock post. A brief-page request skips it.
9. **Creative Judge (A15).** Looks at the copy and the assets that were actually made. A reject blocks the run.
10. **Reviewer and fact checker (A10).** Checks the channel copy, slop, and every claim against the brand brain plus the claim-safety gate. A blocked claim blocks the run.
11. **Delivery (A11).** Builds the Telegram review packet and sends it. It does not publish. Dispatch stays idle until a person has approved.
12. **Learning (A13).** Reads the reward record and writes what this run added to it.

Then the run is marked `completed` when every gate passed, or `review_blocked` when a judge or the fact check stopped it. Both still have a post. Both still wait for a person. `NO_ACTION` and `KILL` mean the strategist declined and there is no post.

The copy is checkpointed into `summary.json` as soon as it exists, then again after the poster and after the video, so Post History can show a run that is still going.

## Models

| Job | Model |
|---|---|
| Judgement, copy, direction, learning | `gemini-3.8-flash` |
| Poster | `gemini-3.1-flash-image` |
| Meme | `gemini-3-pro-image` |
| Video | `veo-3.1-generate-001` |
| Brain embeddings | `gemini-embedding-2`, 768 dimensions |

The brain's own language calls use the Generative Language API key. They are not routed through Vertex.

A cycle also checks the daily budget before it starts. Over the cap, the run is `refused_budget` and Telegram gets one info note. No agents run.

## The other jobs

These do not write a post.

| Job | Code it runs | What it leaves behind |
|---|---|---|
| Collects research | `research_collect` in the scheduler | `pipeline/state/research_latest.json`, pushed to the bucket. Scraped Intelligence shows it. The next scout reads up to six of those headlines. |
| Listens in public | `brand_brain.watch` | New public items about the company, with sources, inside the brain. Own channels are authority 3. Everyone else is authority 5, so an outside sentence is never proof for a post. |
| Reads GitHub | `brand_brain.github_sync` | Product pages (Solana and Stellar) into the brain on their own cadence, and recent commits on the hourly pass. A post may draw a figure only when that page states it. |
| Syncs Notion | `brand_brain.notion_sync` | Connected Notion pages into the brain. The token is per company. |
| Reads a published post | `metrics_collector.collect` | Engagement for posts marked published and at least about two days old. Writes reward events that Learning shows. |
| Health | `ops.watch` | Failures, the brain database, the Telegram webhook, the dashboard, the budget. Alerts on Telegram when something new breaks. |

## The brand brain

One Postgres database, `brand-brain`, with row-level security so one company cannot read another. Vanna is the primary tenant. Auri is the second.

Agents do not scrape the open web inside the strategist. They ask the brain. At the start of a post the pipeline does three things:

- Refreshes the tenant's live sources if they are stale.
- Asks the brain what is new since the previous run.
- Hands that list to the agents as context.

The brain holds the product pages, the Notion pages, the public listening, and the company's own profile. A claim the brain does not support is blocked by the reviewer.

Assistant chat on the dashboard reads this same brain and shows the sources it used. The chat cannot launch, approve, or publish.

## Telegram

When a post is ready, Delivery sends a review message with Approve, Revise, and Kill.

The webhook on the dashboard (`/api/telegram/webhook`) starts a short pipeline job with the command `telegram`. That job writes the decision.

| Button | What is stored | What it does to the post |
|---|---|---|
| Approve | `feedback.json` on that run, verdict `approve` | Records that it was good. Sends nothing. Asks you to reply with the X link after you post it yourself. |
| Revise | same file, verdict `revise`, then your next message as the note | Records the note. Does not render a new video and does not rewrite the post. |
| Kill | same file, verdict `kill` | Records the rejection. The post stays in history. |

The latest decision is `feedback.json` → `latest`. Older taps stay in `history`. The dashboard card **YOUR DECISION** on that post reads this file. Learning reads the reward: approve is 1, revise is 0.3, kill is 0.

An X link you reply with after an approval is stored as published. The metrics job can then read engagement about two days later.

## Where a file lives

| You want | File | Who writes it |
|---|---|---|
| The post, the status, the source | `gtm_runs/<id>/summary.json` | The cycle, as it goes |
| The scrape table | `gtm_runs/<id>/harvest.json` | Scout |
| Grades and post ideas | `gtm_runs/<id>/analysis.json` | Market analyst |
| Agent lines | `gtm_runs/<id>/decisions.jsonl` and `stages.jsonl` | Each agent |
| Model calls | `gtm_runs/<id>/calls.jsonl` | The model runner |
| Your Approve / Revise / Kill | `gtm_runs/<id>/feedback.json` | Telegram or the decision card |
| The poster and video | `assets/<id>/` | Poster designer and video producer |
| Collected headlines | `state/pipeline/state/research_latest.json` | Research job |
| The gaps you set | `state/pipeline/state/scheduler_intervals.json` | The scheduler page |
| Last run of each job | `state/pipeline/state/scheduler_state.json` | The clock |

The dashboard never trusts a number it was not given. A missing file shows as missing. A visitor who has not used the owner key only sees runs that started after their first visit, so those files can exist in the bucket while Post History looks empty in that browser.

## Status words

| Status | Meaning |
|---|---|
| `running` | The cycle is still writing. |
| `completed` | Copy, assets, and both judges passed. Still waiting for a person. |
| `review_blocked` | A post exists. A judge or the fact check stopped it. Still waiting for a person. |
| `NO_ACTION` / `KILL` | The strategist declined. No post was written. |
| `refused_budget` | The daily cap stopped the run before the agents started. |
| `skipped_locked` | Another cycle was already running. |
| `failed` | The cycle crashed. The reason is on the run. |
| `aborted` | The scout found nothing to read. |

## What the backend never does

It does not publish to X, LinkedIn, or Reddit. Approve means the decision was recorded. You post it.

It does not turn a Revise note into a new video by itself. The note is stored on that run for the next time the agents write.

It does not let a 2-minute or 30-minute pill onto the post job. One post takes longer than that and spends the daily budget. The other jobs can use those gaps.
