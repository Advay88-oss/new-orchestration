import { NextResponse } from 'next/server';
import { runPython, lastJson, pythonPath } from '@/lib/python';
import { isDeployed, getText } from '@/lib/gcs';
import fs from 'fs';
import path from 'path';
import { exec, spawn } from 'child_process';

const REPO_ROOT = process.env.REPO_ROOT || (fs.existsSync('/app') ? '/app' : path.resolve(process.cwd(), '..'));
const IDEAS_FILE_1 = path.join(REPO_ROOT, 'state/panels/ideas.json');
const IDEAS_FILE_2 = path.join(REPO_ROOT, 'pipeline/state/panels/ideas.json');
const OUTCOMES_FILE = path.join(REPO_ROOT, 'pipeline/state/outcomes.jsonl');
const PUBLIC_DIR = path.join(REPO_ROOT, 'hermes-mission/public');

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    // Deployed there is no pipeline filesystem; the panel comes from the same
    // bucket the runs do. `state_sync.push_panels()` is the writing half.
    if (isDeployed()) {
      const raw = await getText('panels/ideas.json');
      if (!raw) {
        return NextResponse.json(
          { success: false, error: 'panels/ideas.json not in state bucket' },
          { status: 404 },
        );
      }
      return NextResponse.json({ success: true, ...JSON.parse(raw) });
    }
    const targetFile = fs.existsSync(IDEAS_FILE_2) ? IDEAS_FILE_2 : IDEAS_FILE_1;
    if (!fs.existsSync(targetFile)) {
      return NextResponse.json({ success: false, error: 'ideas.json not found' }, { status: 404 });
    }
    const data = JSON.parse(fs.readFileSync(targetFile, 'utf-8'));
    return NextResponse.json({ success: true, ...data });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { action, idea_id, reason } = body;

    // Both actions need the pipeline: `dismiss` appends to outcomes.jsonl and
    // `render_visual` spawns Python. Neither exists in the container, and a
    // dismiss written to an ephemeral disk would report success and vanish.
    if (isDeployed()) {
      return NextResponse.json(
        {
          success: false,
          error:
            `'${action}' runs the pipeline, which lives on the founder's ` +
            'machine. The deployed dashboard is read-only.',
        },
        { status: 501 },
      );
    }

    if (action === 'dismiss') {
      const outcomeRecord = {
        timestamp: new Date().toISOString(),
        entity_type: 'IDEA',
        entity_id: idea_id,
        verdict: 'DISMISSED',
        reason: reason || 'Dismissed by founder'
      };
      fs.appendFileSync(OUTCOMES_FILE, JSON.stringify(outcomeRecord) + '\n');
      return NextResponse.json({ success: true, message: `Idea ${idea_id} dismissed and logged to outcomes.jsonl` });
    }

    if (action === 'render_visual') {
      const targetFile = fs.existsSync(IDEAS_FILE_2) ? IDEAS_FILE_2 : IDEAS_FILE_1;
      const data = JSON.parse(fs.readFileSync(targetFile, 'utf-8'));
      const idea = (data.ideas || []).find((i: any) => i.id === idea_id);
      if (!idea) {
        return NextResponse.json({ success: false, error: 'Idea not found' }, { status: 404 });
      }

      const archetype = idea.format_spec?.archetype || 'blend_composability';
      const title = idea.hook || 'Vanna Composable Credit Mechanism';
      const subtitle = idea.rationale || 'Single collateral deposit into isolated SmartAccount.';
      const outFilename = `idea_${idea_id}_visual.png`;
      const outPath = path.join(REPO_ROOT, 'pipeline/state', outFilename);
            const binary = pythonPath() as string;
      const rawArgs = [
        'pipeline/scripts/vanna_schematic_generator.py',
        '--archetype', archetype,
        '--title', title,
        '--subtitle', subtitle,
        '--output', outPath
      ];
      const spawnArgs = rawArgs;

      return new Promise<Response>((resolve) => {
        const py = spawn(binary, spawnArgs, {
          cwd: REPO_ROOT,
          env: {
            ...process.env,
            PYTHONPATH: REPO_ROOT,
            REPO_ROOT: REPO_ROOT,
            CHROME_PATH: process.env.CHROME_PATH || '/usr/bin/chromium'
          }
        });

        let stderr = '';
        py.stderr.on('data', (d) => { stderr += d.toString(); });

        py.on('close', (code) => {
          if (code !== 0) {
            resolve(NextResponse.json({ success: false, error: stderr || `Render failed with code ${code}` }, { status: 500 }));
            return;
          }
          const pubDest = path.join(PUBLIC_DIR, outFilename);
          if (fs.existsSync(outPath)) {
            try { fs.copyFileSync(outPath, pubDest); } catch {}
          }
          resolve(NextResponse.json({ success: true, visual_url: `/${outFilename}` }));
        });
      });
    }

    return NextResponse.json({ success: false, error: `Unknown action: ${action}` }, { status: 400 });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}
