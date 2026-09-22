import { NextResponse } from 'next/server';
import { runPython, lastJson, pythonPath } from '@/lib/python';
import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';

const REPO_ROOT = process.env.REPO_ROOT || (fs.existsSync('/app') ? '/app' : 'D:/new orchestration');
const RUNS_DIR = path.join(REPO_ROOT, 'pipeline/state/research_runs');
const BRAIN_EVIDENCE_FILE = path.join(REPO_ROOT, '../marketing intelligence system/intelligence/db/evidence.jsonl');
const LOCAL_EVIDENCE_FILE = path.join(REPO_ROOT, 'pipeline/state/evidence.jsonl');
const DISCOVERED_PLAYERS_FILE = path.join(REPO_ROOT, 'registry/discovered_players.jsonl');
const DISCOVERY_LOG_FILE = path.join(REPO_ROOT, 'registry/discovery_log.jsonl');
const SOCIAL_POSTS_FILE = path.join(REPO_ROOT, 'pipeline/state/scraped_social_posts.jsonl');

export const dynamic = 'force-dynamic';

/**
 * Remove pre-authored analysis from scraped posts before it reaches the UI.
 *
 * `vanna_strategic_implication` and `recommended_gtm_counter` are written into
 * the collector's seed list, not derived from the post: 76 posts carried 15
 * distinct implications and 7 distinct counters between them, so the same
 * sentence appeared under unrelated posts. A canned string assigned to a post
 * is not analysis of that post.
 *
 * `post_url` is also checked: the collector stores profile URLs (x.com/handle)
 * where a post URL belongs, so a link that cannot reach the post is labelled
 * rather than presented as one.
 */
function stripFabricatedFields(posts: any[]): any[] {
  return (posts ?? []).map((p) => {
    const { vanna_strategic_implication, recommended_gtm_counter, ...rest } = p ?? {};
    const url = String(rest.post_url ?? '');
    const isPermalink = /\/(status|comments|posts)\//.test(url) || /t\.me\/[^/]+\/\d+/.test(url);
    return {
      ...rest,
      links_to_post: isPermalink,
      link_note: isPermalink ? null : 'collector stored a profile link, not a permalink',
    };
  });
}


export async function GET() {
  try {
    // 1. Read Deep Research Runs
    const researchRuns: any[] = [];
    const files = fs.existsSync(RUNS_DIR) ? fs.readdirSync(RUNS_DIR) : [];

    for (const f of files) {
      if (f.startsWith('RUN_RESEARCH_') && f.endsWith('.json')) {
        try {
          const raw = fs.readFileSync(path.join(RUNS_DIR, f), 'utf-8');
          researchRuns.push(JSON.parse(raw));
        } catch {}
      }
    }

    researchRuns.sort((a, b) => {
      const timeA = a.run_id?.split('_').pop() || '0';
      const timeB = b.run_id?.split('_').pop() || '0';
      return parseInt(timeB) - parseInt(timeA);
    });

    // 2. Read Canonical Evidence Claims
    const claims: any[] = [];
    const targetEvidence = fs.existsSync(BRAIN_EVIDENCE_FILE) ? BRAIN_EVIDENCE_FILE : LOCAL_EVIDENCE_FILE;
    if (fs.existsSync(targetEvidence)) {
      const lines = fs.readFileSync(targetEvidence, 'utf-8').split('\n');
      for (const line of lines.slice(-50)) {
        if (line.trim()) {
          try {
            claims.push(JSON.parse(line.trim()));
          } catch {}
        }
      }
    }

    // 3. Read Discovered Ecosystem Players & Generate Post Ideas
    const discoveredPlayers: any[] = [];
    if (fs.existsSync(DISCOVERED_PLAYERS_FILE)) {
      const lines = fs.readFileSync(DISCOVERED_PLAYERS_FILE, 'utf-8').split('\n');
      for (const line of lines) {
        if (line.trim()) {
          try {
            const p = JSON.parse(line.trim());
            // Synthesize actionable GTM Post Idea & Vanna Advantage
            const idea = derivePostIdeaForPlayer(p);
            discoveredPlayers.push({
              ...p,
              post_idea: idea.post_idea,
              vanna_advantage: idea.vanna_advantage,
              hook_angle: idea.hook_angle,
              target_segment: idea.target_segment,
              prompt_suggestion: idea.prompt_suggestion
            });
          } catch {}
        }
      }
    }

    // 4. Read Discovery Log Ledger
    const discoveryLogs: any[] = [];
    if (fs.existsSync(DISCOVERY_LOG_FILE)) {
      const lines = fs.readFileSync(DISCOVERY_LOG_FILE, 'utf-8').split('\n');
      for (const line of lines) {
        if (line.trim()) {
          try {
            discoveryLogs.push(JSON.parse(line.trim()));
          } catch {}
        }
      }
    }

    // 5. Read Scraped Social Media Posts (X, Reddit, LinkedIn)
    const socialPosts: any[] = [];
    if (fs.existsSync(SOCIAL_POSTS_FILE)) {
      const lines = fs.readFileSync(SOCIAL_POSTS_FILE, 'utf-8').split('\n');
      for (const line of lines) {
        if (line.trim()) {
          try {
            socialPosts.push(JSON.parse(line.trim()));
          } catch {}
        }
      }
    }

    return NextResponse.json({
      success: true,
      total_runs: researchRuns.length,
      runs: researchRuns,
      recent_claims: claims.reverse(),
      discovered_players_count: discoveredPlayers.length,
      discovered_players: discoveredPlayers,
      discovery_logs: discoveryLogs.reverse(),
      social_posts_count: socialPosts.length,
      social_posts: stripFabricatedFields(socialPosts).reverse(),
      supported_sources: [
        { name: "Official Primary Websites", hierarchy: "Level 2", tool: "OpenCLI Web Read" },
        { name: "Technical Documentation (Mintlify/GitBook)", hierarchy: "Level 3", tool: "OpenCLI Browser Bridge" },
        { name: "Research Blogs & Substack/Mirror", hierarchy: "Level 4", tool: "OpenCLI Web Reader" },
        { name: "DeFiLlama Money Markets API", hierarchy: "Level 1", tool: "Direct REST API" },
        { name: "Stellar Horizon RPC Node", hierarchy: "Level 1", tool: "On-Chain RPC /fee_stats" },
        { name: "Google News Crypto Syndication", hierarchy: "Level 6", tool: "XML Syndication Parser" }
      ]
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

/**
 * A post idea for a discovered player.
 *
 * This was a chain of `if (p.player_id === "blend-pools-v2")` branches, each
 * returning a hand-written post idea with hardcoded figures — "$148.5M TVL",
 * "$37.2M TVL", "0.00014 XLM gas" — typed into this file. Five players had a
 * bespoke pitch; everyone else fell through to one of two generic ones. None
 * of it was derived from the player's actual record, and the figures did not
 * come from the TVL the record carries.
 *
 * It now derives from the record in front of it and says plainly that the
 * angle is a template, not a generated idea. Real ideas come from a GTM cycle
 * (A02 selects, A03 formulates) and appear in the Ideas Panel.
 */
function derivePostIdeaForPlayer(p: any) {
  const name = p.name || p.player_id;
  const tvl = p.tvl_usd ? `$${Number(p.tvl_usd).toLocaleString()}` : null;
  const cat = p.category_raw || 'DeFi';
  const rel = p.relevance;

  const angle =
    rel === 'MECHANISM'
      ? 'Solvency architecture: isolated SmartAccount sandboxes vs pooled default risk'
      : rel === 'AUDIENCE'
        ? 'Liquidity routing: deploying credit into this venue in one transaction'
        : 'Ecosystem composability on Soroban';

  return {
    post_idea: `${name}${tvl ? ` (${tvl} TVL)` : ''} — ${angle}.`,
    vanna_advantage: null,
    hook_angle: angle,
    target_segment: rel === 'MECHANISM' ? 'Risk-focused allocators' : 'Stellar DeFi users',
    // A prompt to hand to a real cycle, which is where an actual idea is formed.
    prompt_suggestion: `${angle} — ${name} (${cat})`,
    source: 'TEMPLATE_FROM_PLAYER_RECORD',
    note: 'Derived from the player record. Not a generated idea; run a GTM cycle for one.',
  };
}


export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    const entity = (body.entity || "Morpho").trim();

    console.log(`[Research API] Triggering live web research on entity: ${entity}...`);

    return new Promise<NextResponse>((resolve) => {
      const pyScript = path.join(REPO_ROOT, 'pipeline/research/run_live_research.py');
      const py = spawn(pythonPath() as string, [pyScript, '--entity', entity], {
        cwd: REPO_ROOT,
        env: {
          ...process.env,
          PYTHONPATH: REPO_ROOT,
          REPO_ROOT: REPO_ROOT
        }
      });

      let stdout = '';
      let stderr = '';

      py.stdout.on('data', (d) => { stdout += d.toString(); });
      py.stderr.on('data', (d) => { stderr += d.toString(); });

      py.on('close', (code) => {
        if (code === 0) {
          resolve(NextResponse.json({
            success: true,
            message: `Deep web research complete for ${entity}.`,
            stdout
          }));
        } else {
          resolve(NextResponse.json({
            success: false,
            error: stderr || 'Error running research agent',
            raw: stdout
          }, { status: 500 }));
        }
      });
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
