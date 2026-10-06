"use client";

/**
 * Posts (every post Herald wrote, with where review left it) and one post's
 * review page. Decisions are recorded with /api/gtm/feedback; the live link
 * after an approval with /api/gtm/learning. Nothing here publishes.
 */
import React, { useEffect, useMemo, useState } from "react";
import {
  Run, STATE_LABEL, blockOf, hasPost, headlineOf, isWriting, noPostReason, posterClass, stateOf, stepsOf, whenOf,
} from "@/lib/herald";
import { Empty, IAlert, IBack, IBad, ICheck, ICopy, IOk, IPlus, IVideo, Seg } from "./ui";

type Filter = "all" | "review" | "blocked" | "approved";

function Poster({ r, brand }: { r: Run; brand: string }) {
  if (r.visual) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img className="poster-img" src={r.visual} alt={"Poster for " + headlineOf(r)} loading="lazy" />;
  }
  const kicker = String(r.pillar || r.machine || "Post").replace(/^Pillar \d+:\s*/, "").split(/[:—]/)[0].slice(0, 28);
  return (
    <div className={"poster " + posterClass(String(r.run_id))}>
      <span className="o" /><span className="k">{kicker}</span><span className="h">{headlineOf(r)}</span><span className="f"><span>{brand}</span></span>
    </div>
  );
}

export function PostsView({ runs, loading, brand, owner, onOpen, onAsk }: {
  runs: Run[]; loading: boolean; brand: string; owner: boolean; onOpen: (id: string) => void; onAsk: () => void;
}) {
  const [f, setF] = useState<Filter>("all");
  const [limit, setLimit] = useState(24);
  const posts = useMemo(() => runs.filter((r) => { const s = stateOf(r); return s !== "nopost" && s !== "running"; }), [runs]);
  const inF = (r: Run, k: Filter) => {
    const s = stateOf(r);
    return k === "all" || (k === "review" && (s === "review" || s === "revised")) || s === k;
  };
  const counts = { all: posts.length, review: posts.filter((r) => inF(r, "review")).length, blocked: posts.filter((r) => inF(r, "blocked")).length, approved: posts.filter((r) => inF(r, "approved")).length };
  const shown = posts.filter((r) => inF(r, f));
  const writing = runs.filter(isWriting);
  const skipped = runs.filter((r) => !isWriting(r) && stateOf(r) === "nopost");

  return (
    <div className="page view">
      <div className="head">
        <div><h1 className="title">Posts</h1><p className="sub">Everything Herald has written for {brand}. Nothing goes live until you approve it and post it yourself.</p></div>
      </div>
      <div className="toolbar">
        <Seg label="Filter posts" value={f} onChange={(k) => { setF(k); setLimit(24); }} options={[
          { key: "all", label: "All", count: counts.all }, { key: "review", label: "To review", count: counts.review },
          { key: "blocked", label: "Blocked", count: counts.blocked }, { key: "approved", label: "Approved", count: counts.approved },
        ]} />
        {owner && <button className="btn btn-sm" onClick={onAsk}><IPlus />Ask for a post</button>}
      </div>

      {f === "all" && writing.map((r) => {
        const steps = stepsOf(r);
        const done = steps.filter((s) => s.s === "done" || s.s === "skipped").length;
        const cur = steps.find((s) => s.s === "running");
        return (
          <button key={r.run_id} className="card writing" onClick={() => onOpen(r.run_id)}>
            <span className="skel" />
            <span style={{ display: "flex", flexDirection: "column", minWidth: 0, flex: 2, gap: 3 }}>
              <span style={{ fontWeight: 600, letterSpacing: "-.01em" }}>{r.title && r.title !== r.run_id ? r.title : "A new post"}</span>
              <span className="meta"><span className="status s-running">Writing</span><span className="dotsep" /><span>{(cur?.name || "Starting") + " · step " + Math.min(done + 1, 12) + " of 12"}</span></span>
            </span>
            <span className="bar"><i style={{ width: Math.max(6, Math.round((done / 12) * 100)) + "%" }} /></span>
          </button>
        );
      })}

      {loading && !runs.length && (
        <div className="grid-cards">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="post-card"><div className="skel" style={{ width: "100%", height: "auto", aspectRatio: "1/1", borderRadius: 12 }} /><div className="post-info"><span className="skel" style={{ width: "80%", height: 14 }} /></div></div>)}</div>
      )}

      {shown.length > 0 && (
        <div className="grid-cards stagger">
          {shown.slice(0, limit).map((r) => {
            const [label, cls] = STATE_LABEL[stateOf(r)];
            return (
              <button key={r.run_id} className="post-card" onClick={() => onOpen(r.run_id)}>
                <div className="poster-frame" style={{ position: "relative" }}>
                  <Poster r={r} brand={brand.toLowerCase()} />
                  {r.video && <span className="vid-badge"><IVideo />Video</span>}
                </div>
                <div className="post-info">
                  <div className="post-title">{headlineOf(r)}</div>
                  <div className="meta" style={{ justifyContent: "space-between" }}><span className={"status " + cls}>{label}</span><span>{whenOf(r.started)}</span></div>
                </div>
              </button>
            );
          })}
        </div>
      )}
      {shown.length > limit && <div className="more"><button className="btn btn-sm" onClick={() => setLimit((l) => l + 24)}>Show more ({shown.length - limit})</button></div>}
      {!loading && shown.length === 0 && (
        <Empty title={posts.length ? "Nothing here" : "No posts yet"}
               text={posts.length ? "No posts with this status right now." : "Ask the Assistant to write the first one. It shows up here when it’s done."}
               action={<button className="btn btn-sm" style={{ marginTop: 6 }} onClick={onAsk}>Open the Assistant</button>} />
      )}

      {f === "all" && skipped.length > 0 && (
        <div style={{ marginTop: 40 }}>
          <div className="sec-h"><h2>Skipped runs</h2><span className="meta">Runs that ended without a post</span></div>
          <div className="card rows stagger">
            {skipped.slice(0, 12).map((r) => {
              const [label, reason] = noPostReason(r);
              return (
                <div key={r.run_id} className="row">
                  <span className="pill" style={{ minWidth: 118 }}>{label}</span>
                  <span style={{ flex: 1, minWidth: 0, color: "var(--muted)" }}>{reason}</span>
                  <span className="meta hide-sm">{whenOf(r.started)}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

type Channel = "x" | "linkedin" | "reddit";

export function PostDetail({ run, brand, brandColor, owner, onBack, onReferences, onChanged, flash }: {
  run: Run | null; brand: string; brandColor: string; owner: boolean;
  onBack: () => void; onReferences: () => void; onChanged: () => void; flash: (t: string) => void;
}) {
  const [ch, setCh] = useState<Channel>("x");
  const [media, setMedia] = useState<"poster" | "video">("poster");
  const [reviseOpen, setReviseOpen] = useState(false);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState("");
  const [changing, setChanging] = useState(false);
  const [link, setLink] = useState<string | null>(null);
  const [linkDraft, setLinkDraft] = useState("");

  const id = run?.run_id as string | undefined;
  useEffect(() => {
    setCh("x"); setMedia("poster"); setReviseOpen(false); setChanging(false); setLink(null); setLinkDraft("");
    if (!id) return;
    fetch("/api/gtm/learning?published=" + id, { cache: "no-store" }).then((r) => r.json())
      .then((d) => { const u = d?.record?.url || d?.published?.url || d?.url; if (typeof u === "string") setLink(u); }).catch(() => {});
  }, [id]);

  if (!run) {
    return <div className="page view"><Empty title="Post not found" text="It may still be starting, or it belongs to another company." action={<button className="btn btn-sm" onClick={onBack}>Back to Posts</button>} /></div>;
  }

  const state = stateOf(run);
  const [sLabel, sCls] = STATE_LABEL[state];
  const writing = state === "running";
  const block = blockOf(run);
  const steps = stepsOf(run);
  const doneN = steps.filter((s) => s.s === "done" || s.s === "skipped").length;
  const claims: { text: string; ok: boolean; basis: string; url?: string }[] = Array.isArray(run.fact_check?.claims)
    ? run.fact_check.claims.map((c: any) => ({ text: c.claim, ok: c.verdict === "SUPPORTED", basis: (c.verdict === "SUPPORTED" ? "" : c.verdict === "CONTRADICTED" ? "Contradicted · " : "Not in your sources · ") + (c.section || c.source || c.why || ""), url: c.url }))
    : [];
  for (const f of (run.review_notes?.facts || []) as string[]) {
    if (!claims.some((c) => f.includes(c.text))) claims.push({ text: f.replace(/^\w+:\s*/, "").split(" — ")[0], ok: false, basis: f.split(" — ")[1] || "Not in your sources" });
  }
  const okN = claims.filter((c) => c.ok).length;
  const claimSummary = claims.length ? okN + " of " + claims.length + " sourced" : writing ? "Not checked yet" : "No claims checked";
  const posts = run.posts || {};
  const copyOf = (k: Channel) => { const p = posts[k] || {}; return String(p.copy || p.hook || ""); };
  const text = copyOf(ch);
  const decided = Boolean(run.decision?.verdict);
  const canDecide = owner && !writing && hasPost(run) && (!decided || changing);
  const verdict = String(run.decision?.verdict || "");
  const src = run.signal_source || {};
  const srcTitle = run.trend && run.trend !== run.run_id ? String(run.trend) : "";
  const asked = run.asked && run.asked !== run.trend ? String(run.asked) : "";

  const decide = async (v: "approve" | "revise" | "kill", n = "") => {
    setBusy(v);
    try {
      const r = await fetch("/api/gtm/feedback", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ runId: run.run_id, verdict: v, note: n }) });
      const j = await r.json();
      if (!r.ok || !j.success) throw new Error(j.error || "HTTP " + r.status);
      flash(v === "approve" ? "Approved" : v === "kill" ? "Killed" : "Note saved");
      setReviseOpen(false); setChanging(false); setNote("");
      onChanged();
    } catch (e: any) {
      flash("That did not save: " + String(e?.message || e).slice(0, 80));
    }
    setBusy("");
  };

  const saveLink = async () => {
    const u = linkDraft.trim();
    if (!u) return;
    setBusy("link");
    try {
      const r = await fetch("/api/gtm/learning", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "published", runId: run.run_id, url: u }) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok || j.ok === false) throw new Error(j.error || "HTTP " + r.status);
      setLink(u); setLinkDraft(""); flash("Link saved");
    } catch (e: any) {
      flash("That link did not save: " + String(e?.message || e).slice(0, 80));
    }
    setBusy("");
  };

  const pv = ch === "reddit"
    ? { sub: "Posted to your community · now", title: String(posts.reddit?.hook || ""), body: text.startsWith(String(posts.reddit?.hook || "@@")) ? text.slice(String(posts.reddit?.hook).length).trim() : text }
    : ch === "linkedin" ? { sub: "Company page · now", title: "", body: text } : { sub: "@" + brand.toLowerCase() + " · now", title: "", body: text };

  return (
    <div className="page view">
      <div className="rv-head">
        <div className="rv-title">
          <button className="btn btn-sm icon-btn" style={{ marginTop: 2, flex: "none" }} onClick={onBack} aria-label="Back to posts"><IBack /></button>
          <div style={{ minWidth: 0 }}>
            <h1 className="title rv-h">{headlineOf(run)}</h1>
            <div className="meta"><span>{whenOf(run.started)}</span>{run.video_mode && <><span className="dotsep" /><span>{run.video ? "With a video" : "Still image"}</span></>}<span className="dotsep" /><span className="mono" style={{ fontSize: 12 }}>{run.run_id}</span></div>
          </div>
        </div>
        <div className="rv-acts">
          {canDecide && (
            <>
              <button className="btn btn-danger" disabled={!!busy} onClick={() => decide("kill")}>{busy === "kill" ? "…" : "Kill"}</button>
              <button className="btn" disabled={!!busy} onClick={() => setReviseOpen((o) => !o)}>Revise</button>
              <button className="btn btn-primary" disabled={!!busy} onClick={() => decide("approve")}><ICheck size={15} />{busy === "approve" ? "Saving…" : "Approve"}</button>
            </>
          )}
          {decided && !changing && owner && <button className="btn" onClick={() => setChanging(true)}>Change decision</button>}
          {!owner && !writing && <span className="note">View only — the owner reviews posts</span>}
        </div>
      </div>

      {block && !decided && <div className="banner b-bad"><IAlert /><div><b style={{ fontWeight: 600 }}>Blocked by {block.by}.</b> {block.reason}</div></div>}
      {writing && <div className="banner b-neutral"><span className="status s-running">Writing</span><div>Usually 15–20 minutes. Review opens here when it’s done.</div></div>}
      {decided && (
        <div className={"banner " + (verdict === "kill" ? "b-bad" : verdict === "revise" ? "b-warn" : "b-ok")} style={{ alignItems: "center", flexWrap: "wrap" }}>
          <ICheck size={18} className={"check-draw " + (verdict === "kill" ? "bad-c" : verdict === "revise" ? "" : "ok-c")} style={{ flex: "none" }} />
          <div style={{ flex: "1 1 260px" }}>
            {verdict === "revise" ? <><b style={{ fontWeight: 600 }}>Revision requested.</b> “{run.decision?.note || ""}”</>
              : verdict === "kill" ? <><b style={{ fontWeight: 600 }}>Killed.</b> It stays in Posts for the record.</>
              : <><b style={{ fontWeight: 600 }}>Approved.</b> {link ? <>Link saved — results are read about 48 hours after it went live. <a href={link} target="_blank" rel="noreferrer">Open</a></> : "Post it from your own account, then paste the link so Herald can learn from the results."}</>}
          </div>
          {verdict !== "kill" && verdict !== "revise" && !link && owner && (
            <div style={{ display: "flex", gap: 8, flex: "1 1 320px" }}>
              <label htmlFor="plink" style={{ position: "absolute", width: 1, height: 1, overflow: "hidden", clip: "rect(0 0 0 0)" }}>Link to the live post</label>
              <input id="plink" className="input" placeholder="Paste the live post link" value={linkDraft} onChange={(e) => setLinkDraft(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") saveLink(); }} />
              <button className="btn btn-primary" disabled={busy === "link"} onClick={saveLink}>Save</button>
            </div>
          )}
        </div>
      )}
      {reviseOpen && (
        <div className="box" style={{ marginBottom: 16, animation: "pop .25s var(--ease) both" }}>
          <div className="box-b" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <div className="field"><label htmlFor="rnote">What should change? Your note is saved with the post and teaches the next one.</label>
              <textarea id="rnote" className="ta" placeholder="Lead with the safety check and cut the second paragraph." value={note} onChange={(e) => setNote(e.target.value)} /></div>
            <div style={{ display: "flex", gap: 6 }}>
              <button className="btn btn-primary btn-sm" disabled={!note.trim() || busy === "revise"} onClick={() => decide("revise", note.trim())}>Save note</button>
              <button className="btn btn-quiet btn-sm" onClick={() => setReviseOpen(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      <div className="rv-stats">
        <div className="stat"><span className="stat-l">Status</span><span className="stat-v"><span className={"status " + sCls} style={{ fontSize: 15, fontWeight: 600 }}>{sLabel}</span></span>
          <span className="stat-s">{writing ? "In progress" : decided ? "Decision recorded" : owner ? "Waiting for your decision" : "Waiting for the owner"}</span></div>
        <div className="stat"><span className="stat-l">Fact check</span><span className="stat-v">{claimSummary}</span><span className="stat-s">Against your own sources</span></div>
        <div className="stat"><span className="stat-l">Agent run</span><span className="stat-v">{doneN} of 12 done</span><span className="stat-s">Twelve agents</span></div>
        <div className="stat"><span className="stat-l">Format</span><span className="stat-v">{run.video ? "Image + short video" : "Still image"}</span><span className="stat-s">X · LinkedIn · Reddit</span></div>
      </div>

      <div className="rv-row1">
        <section className="box rv-panel" aria-label="Creative">
          <div className="box-h" style={run.video ? { padding: "8px 8px 8px 16px" } : undefined}>Creative
            {run.video
              ? <Seg label="Creative" value={media} onChange={setMedia} options={[{ key: "poster", label: "Poster" }, { key: "video", label: "Video" }]} />
              : <span>1080 × 1080</span>}
          </div>
          <div className="rv-creative">
            {media === "video" && run.video ? (
              <video key={String(run.video)} className="rv-poster rv-video" src={String(run.video)} poster={run.visual || undefined}
                     controls playsInline preload="metadata" />
            ) : run.visual ? <div className="poster-frame rv-poster"><Poster r={run} brand={brand.toLowerCase()} /></div>
              : writing ? <div className="skel rv-poster" style={{ height: "auto", aspectRatio: "1/1", borderRadius: 12 }} />
              : <span className="meta">No poster was made for this run.</span>}
          </div>
          <div className="rv-foot">
            <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}><IVideo />{run.video ? "A short video was also made from this post" + (run.video_mode ? " (" + String(run.video_mode).replace(/_/g, " ") + ")." : ".") : "No video — this one is a still image."}</span>
            {run.video && <a className="btn btn-quiet btn-sm" href={String(run.video)} download={run.run_id + ".mp4"}>Download</a>}
          </div>
        </section>

        <section className="box rv-panel" aria-label="Copy">
          <div className="box-h" style={{ padding: "8px 8px 8px 16px" }}>Copy
            <Seg label="Channel" value={ch} onChange={setCh} options={[{ key: "x", label: "X" }, { key: "linkedin", label: "LinkedIn" }, { key: "reddit", label: "Reddit" }]} />
          </div>
          <div className="rv-copy">
            {text ? (
              <div key={ch} style={{ animation: "fade .3s both" }}>
                <div className="pv-head">
                  <span className="pv-av" style={{ background: brandColor }}>{brand.charAt(0)}</span>
                  <div style={{ flex: 1, minWidth: 0 }}><div className="pv-name">{brand}</div><div className="pv-sub">{pv.sub}</div></div>
                </div>
                {pv.title && <div className="pv-title">{pv.title}</div>}
                <div className="pv-text" style={{ margin: 0 }}>{pv.body}</div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <div className="skel" style={{ width: "60%", height: 14, borderRadius: 6 }} /><div className="skel" style={{ width: "90%", height: 14, borderRadius: 6 }} /><div className="skel" style={{ width: "80%", height: 14, borderRadius: 6 }} />
                <span className="meta" style={{ marginTop: 6 }}>{writing ? "The copywriter hasn’t started yet." : "No copy for this channel."}</span>
              </div>
            )}
          </div>
          <div className="rv-foot"><span>{text.length} characters</span>
            <button className="btn btn-quiet btn-sm" disabled={!text} onClick={async () => { try { await navigator.clipboard.writeText(pv.title ? pv.title + "\n\n" + pv.body : text); flash("Copied"); } catch { flash("Copy was blocked"); } }}><ICopy />Copy text</button>
          </div>
        </section>
      </div>

      <div className="rv-row2">
        <section className="box">
          <div className="box-h">Source <span>{src.type ? String(src.type).replace(/_/g, " ") : asked ? "Your request" : ""}</span></div>
          {srcTitle || src.excerpt || asked ? (
            <>
              <div className="box-b" style={{ display: "flex", flexDirection: "column", gap: 10, flex: 1 }}>
                <div><div style={{ fontWeight: 600 }}>{srcTitle || asked}</div>{src.publisher && <div className="meta">{src.publisher}</div>}</div>
                {(src.excerpt || (asked && asked !== srcTitle)) && <p className="excerpt" style={{ flex: 1 }}>{src.excerpt || "You asked: " + asked}</p>}
              </div>
              <div className="rv-foot">
                {src.url ? <a className="btn btn-quiet btn-sm" style={{ marginLeft: -8 }} href={src.url} target="_blank" rel="noreferrer">Open source</a> : <span />}
                <button className="btn btn-quiet btn-sm" onClick={onReferences}>References →</button>
              </div>
            </>
          ) : <div className="box-b meta">{writing ? "Chosen once research finishes." : "No source was recorded."}</div>}
        </section>

        <section className="box">
          <div className="box-h">Fact check <span>{claimSummary}</span></div>
          <div className="box-b" style={{ flex: 1 }}>
            {claims.length ? (
              <div>
                {claims.slice(0, 8).map((c, i) => (
                  <div key={i} className="claim">
                    {c.ok ? <IOk /> : <IBad />}
                    <div>{c.text}<small>{c.url ? <a href={c.url} target="_blank" rel="noreferrer">{c.basis || "Source"}</a> : c.basis}</small></div>
                  </div>
                ))}
                {claims.length > 8 && <span className="meta">+ {claims.length - 8} more</span>}
              </div>
            ) : <span className="meta">{writing ? "Runs after the copy is written." : "No claims were recorded for this post."}</span>}
          </div>
        </section>

        <section className="box">
          <div className="box-h">Agent run <span>{doneN} of 12 done</span></div>
          <div className="box-b" style={{ flex: 1 }}>
            <div className="segbar">{steps.map((st) => <i key={st.name} className={st.s} title={st.name + " — " + st.label} />)}</div>
            <div className="steps2">
              {steps.map((st) => <div key={st.name} className="st2" title={st.label}><span className={"tl-dot " + st.s} /><span>{st.name}</span></div>)}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

