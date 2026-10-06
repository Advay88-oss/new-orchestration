# The whole dashboard, in plain words

Written 5 Oct 2026 from the screens that are actually in the menu.

Two links. One machine.

- Main dashboard: https://vanna-gtm-mission-114262736718.us-central1.run.app
- Brief page: https://vanna-gtm-mission-114262736718.us-central1.run.app/brief

Open the main link once with the owner key. After that, every section on this page and a sentence typed on the brief page share the same posts.

A browser that has never used the owner key only sees posts that start after that browser first opened the page. Post History can look empty there while the clock is still writing posts.

A finished post waits for a person. You post it yourself. Approve records that you liked it. It does not send the post to X, LinkedIn, or Reddit.

## The picture, in one pass

Think of a classroom.

1. The clock on **24/7 Scheduler** wakes up every 2 minutes and asks, "Is any job due?"
2. **Collects research** and **Listens in public** bring in headlines and public talk. That reading goes into the brand brain, and the headlines also sit on **Scraped Intelligence**.
3. When **Writes a post** is due, twelve agents read that material, pick one subject, write X, LinkedIn, and Reddit, and make the picture.
4. You watch them work on **Live Trace**. The finished post lands in **Post History**. The same post shows on the brief page.
5. Telegram asks you to Approve, Revise, or Kill. That decision shows on the post, and **Learning** keeps the score.
6. **Assistant** can answer questions from the same memory. Asking a question does not start a post.

## Where the hidden pieces show up

There is no sidebar button named Brand Brain, Agents, or Embeddings. You see them inside the sections below.

| You want to see | Open this |
|---|---|
| The twelve agents, and whether each one ran | Live Trace → **See how it was done** → **Agents** |
| What each agent decided, in sentences | Live Trace → **See how it was done** → **Decisions**, and the cards on the main Live Trace view |
| Each model call, with token counts | Live Trace → **See how it was done** → **The work** |
| The brand brain answering a question, with the page it used | Assistant |
| The brain blocking a sentence that the docs do not support | The post in Post History, status **Held for review**, and the blocked-claim lines on Live Trace |
| What the brain has learned from your Approve / Revise / Kill | Learning |
| The embeddings themselves | Nowhere on screen. They are numbers inside the database. You see the sentence the search found, on Assistant. |

---

## 1. Assistant

**What this screen is.** A chat about one company.

**What you can do here.**

- Pick the company when more than one is connected.
- Open an old chat from the thread list, or start a new one.
- Type a question. The answer comes back with the pages the brain used.
- Read **Assistant checks** for the connection status, including Notion.

**Who works.** No content agent. The chat reads the brand brain. The brain search uses embeddings: each saved page was turned into a list of 768 numbers (`gemini-embedding-2`) so a question can find the closest pages. The chat shows you the sentence it found, and the source. It does not show the numbers.

**What comes out.** An answer in the chat. A source you can open.

**Where else it shows up.** Nowhere else. A question does not create a row in Post History, does not approve a post, and does not publish.

---

## 2. Live Trace

**What this screen is.** The diary of the latest post, while it is being made and after it finishes.

**What you see first.**

- A dot and a word: **RUNNING** while agents are working, or the finished status and the run id (it looks like `GTM-20261005-080018`).
- A **NOW** card: which step is current, how many steps ran, how many model calls, how many decisions.
- One card per decision: what was chosen, and why.

**The box above the diary (owner only).** A line that says founder directive. Type a subject, such as a product or a news item, and send it. That starts the same post job as the clock, with your sentence as the subject. The run then appears here, then in Post History. It takes several minutes.

**See how it was done.** This button opens the floor. Three tabs:

### The work

Every line the pipeline wrote, in order. Each line has a clock time, the agent name, and a status (`ok`, `running`, `degraded`, `skipped`). A model line also shows the model name, tokens in, tokens out, and how many seconds it took. A failed call is marked FAILED.

### Decisions

The longer notes, grouped by the agent that wrote them. You will see the Opportunity Selector, the GTM Strategist, and the Creative Director: what they chose, what they turned down, and the reason.

### Agents

The class photo of one run. The heading is **10 specialists · 2 judges**. Four groups:

| Group on screen | Who is in it | What they did on this run |
|---|---|---|
| Intelligence & Strategy | Intelligence Scout, Market Analyst, Opportunity Selector, GTM Strategist & Planner | Found the reading, graded it, picked the subject, decided there was a post |
| Creative & Media | Copywriter, Creative Director, Poster Designer, Video Producer | Wrote the words, chose the layout, made the picture, made the video on a clock run |
| Delivery & Learning | Delivery, Learning & Coach | Sent the Telegram review, wrote what this run added to the score |
| Independent Judges | Reviewer & Fact Checker, Creative Judge | Checked the facts and the creative work. The maker does not grade itself |

Each card shows whether that agent ran, how many model calls it made, and a short note. An agent later in the list that has not started yet is waiting. It has not failed.

**Who works.** All twelve, on a post run. This screen only displays them.

**What comes out.** The diary. The post itself is on Post History.

**Where else it shows up.** The same run id is the row in Post History and the post on the brief page.

---

## 3. 24/7 Scheduler

**What this screen is.** The clock, in plain language. One card per job.

The hosted alarm wakes every 2 minutes. That alarm only checks what is due. It is not the gap between posts. Each card has its own gap. A pill you click is the gap that job keeps.

**On every job card.**

- The plain name (Writes a post, Collects research, and so on).
- One sentence on what it does.
- Where the result lands.
- When it last finished, and when it is due again.
- Status words: Working now, Done, Waiting, Failed, Paused after failures.
- Pills: 2m, 30m, 1h, 2h, 6h, 12h, 24h. Click one. That gap is saved. The next wake-up uses it.
- **Run now** starts that job once. The clock keeps its gap after that.

**Writes a post** hides the 2m and 30m pills. One post takes longer than that and spends the daily budget, so the shortest gap on that card is 1 hour.

**The spend card** is today's budget. **Checks the machine is healthy** is the card that watches failures. A new failure sends one Telegram note.

### The jobs, one by one

| Card name | What the work does | Who does it | What you get | Where you see it | Shortest pill |
|---|---|---|---|---|---|
| Writes a post | One post for X, LinkedIn, and Reddit, plus the picture. A clock run also makes the video. Then it waits for you. | All twelve agents | The post, the poster, the video, the Telegram review | Post History, Live Trace, the brief page, Telegram | 1 hour |
| Collects research | Reads live headlines from news, Reddit, Telegram, docs, and competitor posts on X. It notes how those posts are shaped: length, question or statement, and views or likes when the source reported them. It does not write the post. | No copywriter. The research collectors. | A list of headlines with a style note | Scraped Intelligence, the box **COLLECTED RESEARCH**. The next Copywriter reads that shape. | 2 minutes |
| Listens in public | Reads what people are saying about the company on X, Reddit, news, and the web, and stores it in the brain with the source. The company's own channels count as stronger evidence. Something someone else said is stored, and it is never treated as proof for a claim in a post. | The public-watch job | New pages inside the brain | The next post, and an Assistant answer that happens to use one of those pages | 2 minutes |
| Reads our GitHub | Puts the Solana and Stellar product pages into the brain, and notes new commits. A post may use a figure only when that page states it. | The GitHub sync | Product pages inside the brain | The next post, only when the post is about that page | 30 minutes |
| Syncs Notion | Copies the Notion pages you connected into the brain, so a post can use what you already wrote. | The Notion sync | Those pages inside the brain | The next post, and your Notion workspace | 1 hour |
| Reads what a published post did | After you publish a post yourself and the link is stored, this reads impressions and likes about two days later. | The metrics job | A reward number | Learning | 1 hour |
| Checks the machine is healthy | Looks at failed jobs, the brain database, the Telegram webhook, the dashboard, and today's spend. | The health check | A status, and one Telegram note when something new breaks | This page, and Telegram | 10 minutes |

Trend headlines, the ideas panel, and the meme panel are switched off. They are not on this page.

---

## 4. Post History

**What this screen is.** Every content run, newest first. The number on the sidebar is how many of those runs actually contain a post.

**What you can do here.**

- **Fresh Session** shows runs from this browser tab. **All posts** shows the runs this browser is allowed to see. **Reset** clears the tab's session list.
- A company filter, when more than one company has runs.
- **Show N with no post** reveals runs where the strategist declined and nothing was written.
- Filters: **All**, **Ready**, **Held**, **Posted**.
- A search box.
- Click a row to open that post.

**Who worked.** The twelve agents, on each row that is a real post. This screen lists them.

**What comes out.** The list. Open a row for the post itself.

**Where else it shows up.** The same run is on Live Trace and on the brief page.

**If the list is empty.** Use the owner key once, or wait for the next post. A visitor's first visit starts the clock for that browser at "now", so older posts stay hidden.

---

## 5. One post (you get here from Post History)

This is not its own sidebar item. It is the page behind a row.

**What you see, top to bottom.**

- **← Post History**
- A status word, the run id, and the company.
- The title of the post.
- **YOUR DECISION**, for the owner. This is the same choice as the Telegram buttons.

| Button | What is saved | What happens to the post |
|---|---|---|
| Approve | This run was good. Reward 1. | The post stays here. You are asked for the X link after you post it yourself. Nothing is sent out. |
| Revise | Your note. Reward 0.3. | The note is stored. The video is not remade and the words are not rewritten on the spot. The next posts can read the note. |
| Kill | This run was rejected. Reward 0. | The post stays in history so you can still read it. |

- **POSTER.** The picture, in its own card. If the run has no picture, the card says so.
- **VIDEO.** Its own card, under the poster, only when a clock run made one. A brief-page request skips the video, so this card is absent.
- **X**, **LinkedIn**, **Reddit**. One channel at a time. The first line is the hook. The rest is the body, with the blank lines the writer put in.
- **Copy** puts that channel's text on your clipboard.
- Source links at the bottom when the run recorded them.

**Who worked.**

| Piece on this page | Agent |
|---|---|
| The words on X, LinkedIn, Reddit | Copywriter |
| The poster layout | Creative Director, then Poster Designer |
| The video | Video Producer, on a clock run |
| Held for review | Creative Judge, or Reviewer & Fact Checker |
| YOUR DECISION | You, through this card or through Telegram. Learning & Coach reads it afterwards. |

**Status words on this page.**

| Word | Meaning |
|---|---|
| Running | The agents are still writing. |
| Ready / completed | The judges passed. It still waits for you. |
| Held for review | A post exists. A judge or the fact check stopped it. It still waits for you. |
| Killed | You pressed Kill, or the strategist declined and there is no post. |
| Draft | A post exists and it is still waiting. |

---

## 6. Scraped Intelligence

**What this screen is.** The reading list. It does not write posts.

**Box 1 — COLLECTED RESEARCH.** Headlines from the last **Collects research** job, with the time they were collected. The next post is allowed to read this list. This box updates when research runs, even between posts. The writer uses the shape of these lines (how short they are, whether they open with a question) when it writes the next X, LinkedIn, and Reddit text.

**Box 2 — A01 INTELLIGENCE SCOUT · LIVE HARVEST.** The docs, posts, news pages, and market pages from a content run.

- A small card per source: how many signals came back, or "quiet this cycle", or a short error.
- Company chips. Click one to filter the table.
- The table. Each row has a kind (Post, Docs, News, Market data), the headline, a **source** button that opens the original page, and **Open in References**.

**Who works.** Intelligence Scout writes the harvest during a post run. The research job writes the collected-research box on its own timer. The Market Analyst grades the same items; that grade is on References, not in this table.

**What comes out.** The two boxes.

**Where else it shows up.** Open in References jumps to that card on References. The brief page can open the same card. The Copywriter of the next post reads the collected list.

---

## 7. What Vanna Can Do

**What this screen is.** A shelf of other brands, so the team can see how they post.

**What you can do here.**

- Switch company when more than one is connected.
- Type a brand name. X handle and subreddit are optional. **Add brand** fetches that brand's recent public posts. This takes one to three minutes.
- Each brand shows posts that got a response: likes, replies, and views the source reported, what they did, and what this company could adapt.

**Who works.** No post agent. This fetch is its own job, started by the Add brand button.

**What comes out.** Notes on the shelf.

**Where else it shows up.** It does not become a post by itself, and it does not publish. The Copywriter's competitor-style notes come from the research job and from the brain's pattern summaries, which you see taking effect in the next post's wording.

---

## 8. Learning

**What this screen is.** The scoreboard the next strategist reads.

**The sentence at the top.** Every run earns one reward. If the reviewer blocked it, the reward is 0. Otherwise your decision counts (approve 1, edit 0.8, revise 0.3, kill 0) and, once a post is really published, engagement counts too. The page shows how many reward events exist so far.

**The choice cards.** One card per kind of choice:

- Narrative pillar
- Technical grounding (code versus docs)
- Format
- Hook type
- Post length
- Posting slot

Each option has a bar, a mean reward, and how many runs used it. **lock** forces later runs to use that option. **locked** is the one already forced. Unlock by pressing it again. Only the owner sees the lock button.

**Log a published post's engagement.** Type the run id (`GTM-` plus the date and time) and the impressions, likes, reposts, replies, and clicks. **Record** saves them. Until you publish a post and fill this in, engagement stays empty. That is expected.

**Reward trend.** A table of recent runs: reward, whether the reviewer passed, your decision, engagement, and which choices that run used.

**Preference pairs.** When you edit a draft and then approve it, the old line and your line are kept here as a pair. The count at the top is how many pairs exist. Zero means you have not used Edit & approve yet.

**Who works.** Learning & Coach writes the record at the end of a run. The GTM Strategist and the Copywriter read it on the next run. You see that as the lock, and as the choices on the next post.

**Where else it shows up.** Your Telegram Approve / Revise / Kill is the same record as YOUR DECISION on the post. The metrics job fills engagement about two days after a published link is stored.

---

## 9. References

**What this screen is.** The same sources as Scraped Intelligence, after the Market Analyst has read them.

**What you see on a card.**

- Filters: **All**, **Posts**, **Docs**, **News**, **Market data**.
- A grade: **DIRECT** (this is about us), **ADJACENT** (nearby), **NOT RELEVANT**, or unread if the analyst has not read it yet.
- A post idea, when the item was relevant.
- The move the strategist would make from that source.
- A link to the original page.

**Who works.** Market Analyst writes the grade and the idea. GTM Strategist writes the move. Intelligence Scout collected the item.

**What comes out.** The cards.

**Where else it shows up.** Scraped Intelligence → Open in References scrolls to that card. The brief page → Open in References opens this section of the main dashboard. The subject of the next clock post is often one of the DIRECT or ADJACENT cards.

An item with no grade is unread. It is not the same as NOT RELEVANT.

---

## 10. The brief page

https://vanna-gtm-mission-114262736718.us-central1.run.app/brief

**What this screen is.** The newest post that has copy, the source it used, and a box to ask for another one.

**What you see.**

- Buttons for **X**, **LinkedIn**, **Reddit**, and the words for the one you picked.
- The source title, a short excerpt, **Open source** (the original page), and **Open in References** (the main dashboard, References).
- A text box and **Send**.

**Who works.** Send starts the same twelve agents as Writes a post, with your sentence as the subject, and with the video skipped. The agents still make the poster.

**What comes out.** A new run id. This page keeps asking until the new post is ready, or until about 8 minutes pass. If it is still running, Live Trace has it.

**Where else it shows up.** Post History and Live Trace, under that same run id. It does not appear the moment you press Send.

---

## The twelve agents, in the order they run

You see this order on Live Trace → Agents. This is what each one leaves behind.

| Order | Name on screen | Model | What they do | What you see, and where |
|---|---|---|---|---|
| 1 | Intelligence Scout | none | Reads news, Reddit, X, Telegram, DefiLlama, and the research list | Scraped Intelligence harvest. File on the run: `harvest.json` |
| 2 | Market Analyst | gemini-3.8-flash | Grades each item direct, adjacent, or not relevant, and writes one post idea | References. File: `analysis.json` |
| 3 | Opportunity Selector | gemini-3.8-flash | Picks the subject. Your sentence wins if you typed one. On the clock, it prefers a scraped source the analyst graded as usable | The title of the post, and a decision card on Live Trace |
| 4 | GTM Strategist & Planner | gemini-3.8-flash | Decides there is a real post. A decline stops the run. The writer, the designer, and the judges are then skipped. On the clock it may try up to three subjects. On a sentence you typed, a decline is the answer | Live Trace decision. A decline shows in Post History as a run with no post |
| 5 | Copywriter | gemini-3.8-flash | Writes X, LinkedIn, and Reddit as short lines. It may use a figure only when the brain's product page states it. It matches the shape of scraped posts and news, and it does not paste their words | The three channel buttons on the post |
| 6 | Creative Director | gemini-3.8-flash | Chooses the layout and writes the poster brief from the post itself | A decision on Live Trace, then the poster |
| 7 | Poster Designer | gemini-3.1-flash-image | Renders the poster. A meme is the same agent and runs only when the request asked for one | The POSTER card |
| 8 | Video Producer | veo-3.1-generate-001 | Makes the video on a clock run. A brief-page request skips this agent | The VIDEO card |
| 9 | Creative Judge | gemini-3.8-flash | Looks at the copy and the assets that were actually made. A reject holds the run | Status Held for review, and a decision on Live Trace |
| 10 | Reviewer & Fact Checker | gemini-3.8-flash | Checks the wording and every claim against the brand brain. A claim the brain does not support is blocked | Held for review, with the blocked claim on Live Trace |
| 11 | Delivery | none | Builds the Telegram message with Approve, Revise, and Kill. It does not publish | Telegram, and YOUR DECISION on the post |
| 12 | Learning & Coach | gemini-3.8-flash | Writes what this run added to the score | Learning |

Older names still show up in old diaries because those jobs were folded in: the machine library and the campaign engine are inside the Strategist, the motion director is inside the Creative Director, and the coach is inside Learning.

## The brand brain, and the embeddings

The brain is a Postgres database named `brand-brain`. Vanna is one company in it. Auri is another. One company cannot read the other's rows.

What is stored there:

- The company profile, including figures a post is allowed to say.
- Product pages from GitHub, pages from Notion, and public listening.
- Pattern notes on how competitors post. The notes are shapes, not copied sentences.
- Each chunk of text, plus its embedding: 768 numbers from `gemini-embedding-2`.

Search works by comparing your question's numbers with those stored numbers, then returning the closest sentences. That is why Assistant can cite a page, and why the fact checker can block a sentence the pages do not support.

You do not get a screen of those numbers. The sidebar has no Brand Brain item. A link that asks for `?view=brain` opens Live Trace. The brain shows up as:

- sources under an Assistant answer
- a blocked claim on Live Trace, and **Held for review** on the post
- the scoreboard on Learning, which is a different table the strategist reads next time

The brain's own language calls use the Generative Language API key.

## Telegram

When Delivery finishes, your phone gets Approve, Revise, and Kill.

The dashboard receives that tap and writes `feedback.json` on the run. YOUR DECISION on the post reads that file. Learning reads the reward.

An X link you reply with after Approve is stored as published. **Reads what a published post did** can then fill Learning about two days later.

Revise stores the note. It does not remake the video.

## If something looks wrong

| What you see | What it means |
|---|---|
| Post History is empty, Scraped Intelligence still has headlines | This browser has not used the owner key, so older runs are hidden. The research list is not tied to one run, so it still shows. |
| Learning says no reward events | Posts are waiting for a person. Approve, Revise, or Kill one and the table fills in. |
| A post has no video | It was started from the brief page, or the video step had not finished. Clock posts are the ones that request video. |
| Scheduler pills do nothing | The owner key is missing. Those buttons answer only for the owner. |
| Two posts arrived a few minutes apart | The clock woke up and a job was due. After the gap you set, the next one waits. Writes a post cannot be set under 1 hour. |
