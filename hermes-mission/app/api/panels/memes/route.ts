import { NextResponse } from 'next/server';
import { runPython, lastJson, pythonPath } from '@/lib/python';
import { isDeployed, getText } from '@/lib/gcs';
import fs from 'fs';
import path from 'path';
import { exec, spawn } from 'child_process';

const REPO_ROOT = process.env.REPO_ROOT || (fs.existsSync('/app') ? '/app' : 'D:/new orchestration');
const MEMES_FILE_1 = path.join(REPO_ROOT, 'state/panels/memes.json');
const MEMES_FILE_2 = path.join(REPO_ROOT, 'pipeline/state/panels/memes.json');
const OUTCOMES_FILE = path.join(REPO_ROOT, 'pipeline/state/outcomes.jsonl');
const PUBLIC_DIR = path.join(REPO_ROOT, 'hermes-mission/public');

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    // Deployed there is no pipeline filesystem; the panel comes from the same
    // bucket the runs do. `state_sync.push_panels()` is the writing half.
    if (isDeployed()) {
      const raw = await getText('panels/memes.json');
      if (!raw) {
        return NextResponse.json(
          { success: false, error: 'panels/memes.json not in state bucket' },
          { status: 404 },
        );
      }
      return NextResponse.json({ success: true, ...JSON.parse(raw) });
    }
    const targetFile = fs.existsSync(MEMES_FILE_2) ? MEMES_FILE_2 : MEMES_FILE_1;
    if (!fs.existsSync(targetFile)) {
      return NextResponse.json({ success: false, error: 'memes.json not found' }, { status: 404 });
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
    const { action, meme_id, reason } = body;

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
        entity_type: 'MEME',
        entity_id: meme_id,
        verdict: 'DISMISSED',
        reason: reason || 'Dismissed by founder'
      };
      fs.appendFileSync(OUTCOMES_FILE, JSON.stringify(outcomeRecord) + '\n');
      return NextResponse.json({ success: true, message: `Meme ${meme_id} dismissed and logged to outcomes.jsonl` });
    }

    if (action === 'render_visual') {
      const targetFile = fs.existsSync(MEMES_FILE_2) ? MEMES_FILE_2 : MEMES_FILE_1;
      const data = JSON.parse(fs.readFileSync(targetFile, 'utf-8'));
      const meme = (data.memes || []).find((m: any) => m.id === meme_id);
      if (!meme) {
        return NextResponse.json({ success: false, error: 'Meme not found' }, { status: 404 });
      }

      const outFilename = `meme_${meme_id}_visual.png`;
      const outPath = path.join(REPO_ROOT, 'pipeline/state', outFilename);
            const binary = pythonPath() as string;
      const rawArgs = ['pipeline/scripts/vanna_meme_renderer.py', '--meme-id', meme_id, '--output', outPath];
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
            resolve(NextResponse.json({ success: false, error: stderr || `Render failed with exit code ${code}` }, { status: 500 }));
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
