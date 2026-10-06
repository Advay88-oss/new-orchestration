# Vanna dashboard playbook

Checked against the hosted site on 5 Oct 2026, 1:35 PM IST.

Two links, one system.

- Main dashboard: https://vanna-gtm-mission-114262736718.us-central1.run.app
- Brief page (V2): https://vanna-gtm-mission-114262736718.us-central1.run.app/brief

Open the main link once with the owner key. After that, Post History, Live Trace, References, the scheduler controls, and a message typed on the brief page all use the same runs. A browser that has never used the owner key only sees runs that start after that browser first opened the page, so Post History can look empty there even while the clock is writing posts.

Nothing on either page publishes. A finished post waits for a person.

## How one post is made

1. The hosted clock fires every 2 minutes. It is on.
2. Each job waits for its own gap. A gap you set on the 24/7 Scheduler page is the gap this clock uses.
3. Research, public listening, and GitHub pages go into the brand brain and into Scraped Intelligence.
4. When the post job is due, the agents read that material, write one post for X, LinkedIn, and Reddit, and make the image.
5. The run appears in Post History and Live Trace. The brief page shows the newest finished post and the source it used.
6. A person approves it. Until then the status stays held for review.

A message typed on the brief page starts this same job. The new run shows up in Post History, Live Trace, and the other sections that read runs. It takes several minutes. It does not appear the moment Send is clicked.

## The sidebar

### Assistant

A chat about one company. Answers come from that company's brand brain, with the sources the brain used. It can show a Notion connection and a run to open.

It does not start a post, approve a post, or publish. Asking it a question does not create a row in Post History.

### Live Trace

The run while it is happening, then the record after it finishes. Each line is something an agent wrote down: what it chose, what it declined, and which model call it made. The list grows only when the pipeline writes a line.

Open it to see why the latest post looks the way it does.

### 24/7 Scheduler

The clock, in plain language. Each card is one job: what it does, where the result lands, when it last ran, and when it is due again.

The pills are 2m, 30m, 1h, 2h, 6h, 12h, and 24h. Click one and that gap is saved. The hosted clock reads it on the next check.

The post job cannot be shorter than 1 hour. One post takes longer than 2 or 30 minutes and spends the daily budget, so those two pills are not on that card.

Run now starts that job once. The clock keeps going without it.

The spend card on this page is today's budget. A failed job sends one Telegram note.

### Post History

Every finished and in-progress content run, newest first. Open a row for the copy, the image, the claims, and the review status.

The sidebar count is the number of runs that actually contain a post.

A run started from the brief page lands here under the same run id the brief page shows.

### Scraped Intelligence

Two layers.

- Collected research: the headlines the research job just gathered. The next post is allowed to read this list. This box updates when research runs, even between posts.
- The scout table: the docs, posts, news pages, and market pages from a content run. Each row has a source button (the publisher, opening the original page) and Open in References.

This page does not write posts. It is the reading list.

### What Vanna Can Do

Inspiration from other brands. Add a brand and its recent public posts are fetched with the likes, replies, and views those posts reported. A post that got a response becomes a note: what they did, and what Vanna could adapt.

This is a reading shelf for the team. It is not the post job, and it does not publish.

### Learning

What has worked, as numbers the next strategist can read. Each choice (pillar, depth, format, hook, length, posting slot) keeps a mean reward and a run count. The owner can lock one option so later runs use it.

A published post's impressions, likes, reposts, replies, and clicks can be entered here. Until a post is actually published, this page has little to score. The reviewer and the founder's approve / edit / revise / kill also feed the same record.

### References

The same sources as Scraped Intelligence, read by the analyst. Each card can show a grade (direct, adjacent, or not relevant), a post idea, and the move the strategist would make from that source.

Open in References on a scraped row scrolls to that card. On the brief page, Open in References opens this section of the main dashboard.

An item the analyst has not read yet shows as unread.

## The brief page

https://vanna-gtm-mission-114262736718.us-central1.run.app/brief

It shows the newest post that has copy, the source that post used, and a box to ask for another one. Open source goes to the original page. Open in References goes to the main dashboard.

Send starts the same pipeline as the main dashboard, with your sentence attached, and stays on the source already on screen. When the run finishes, this page shows the new post, and Post History on the first link shows the same run.

## Jobs on the clock

| Job on the page | What it does | Where it shows | Shortest gap |
|---|---|---|---|
| Writes a post | One post, then it waits for a person | Post History, Live Trace, the brief page | 1 hour |
| Collects research | Live headlines. It does not write the post | Scraped Intelligence, then the next post | 2 minutes |
| Listens in public | X, Reddit, news, and the web, into the brain | The next post. There is no separate raw-scrape page | 2 minutes |
| Reads our GitHub | Solana and Stellar product pages into the brain | The next post, only when the post is about that page | 30 minutes |
| Syncs Notion | Connected Notion pages into the brain | The next post, and the Notion workspace | 1 hour |
| Reads what a published post did | Engagement about two days after a post goes out | Learning | 1 hour |
| Checks the machine is healthy | Failures and today's spend | This page, and Telegram when something breaks | 10 minutes |

Trend headlines, the ideas panel, and the meme panel are off. They do not appear on the scheduler page.

## What was confirmed on the hosted site

Checked 5 Oct 2026, about 1:35 PM IST, against the live service and the state bucket.

The clock is on. Cloud Scheduler `vanna-gtm-tick` is enabled and fires every 2 minutes. Its last fire before this check was 1:34 PM IST.

These jobs had completed on their own:

- Writes a post. Last finish 1:36 PM IST, about 6.5 minutes of work. The saved gap is 1 hour. The newest run is `GTM-20261005-080018`. It has X, LinkedIn, and Reddit copy. Status is held for review. The two runs before it are the same shape. Posts are being written.
- Collects research. Last finish 11:35 AM IST. The saved gap is 2 hours. Scraped Intelligence is showing that collection: 128 new items, including the CoinDesk, Cointelegraph, DefiLlama, and Stellar fee-stats headlines.
- Listens in public. Last finish 11:25 AM IST.
- Reads our GitHub. Last finish 12:30 PM IST.
- Syncs Notion. Last finish yesterday afternoon, which matches a daily gap.
- Reads published-post results. Last finish 11:30 AM IST, in a fraction of a second, because nothing has been published for it to score.
- Health check. Last finish 12:30 PM IST.

Both pages respond: the main dashboard and `/brief`.

Scraped Intelligence's collected-research list is live on the public API. The per-row scout table and References read a content run. Those files exist for `GTM-20261005-080018` (`harvest.json` and `analysis.json`). A browser without the owner key, whose first visit is "right now", is not shown older runs, so those two views can look empty until the next run or until the owner key is used.

Learning responds and currently has no reward events. That matches a day of posts held for review and none published.

The scheduler controls, the brief Send button, What Vanna Can Do, and the health card answer only after the owner key. Without it they refuse the request. That is the public link behaving as a read-only visitor.
