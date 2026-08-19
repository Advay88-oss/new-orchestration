import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const PACK_PATH = path.resolve('D:/new orchestration/pipeline/buzz-pack/.plugin/plugin.json');
const PERSONA_DIR = path.resolve('D:/new orchestration/pipeline/buzz-pack');
const LOGS_DIR = path.resolve('D:/new orchestration/pipeline/logs/agents');
const KEYS_PATH = path.resolve('D:/new orchestration/pipeline/keys/agent-keys.json');

function splitFrontmatter(text: string): { fields: Record<string, string>; body: string } {
  if (!text.startsWith('---')) {
    return { fields: {}, body: text };
  }
  const end = text.indexOf('\n---', 3);
  if (end === -1) {
    return { fields: {}, body: text };
  }
  const raw = text.slice(3, end);
  const body = text.slice(end + 4).trim();
  const fields: Record<string, string> = {};
  for (const line of raw.split('\n')) {
    if (line.includes(':') && !line.startsWith(' ') && !line.startsWith('-') && !line.startsWith('\t')) {
      const parts = line.split(':');
      const k = parts[0].trim();
      const v = parts.slice(1).join(':').trim().replace(/^["']|["']$/g, '');
      fields[k] = v;
    }
  }
  return { fields, body };
}

export async function GET() {
  try {
    const agents = [];

    // 1. Load keys map for pubkeys
    const keysMap: Record<string, string> = {};
    if (fs.existsSync(KEYS_PATH)) {
      const keysData = JSON.parse(fs.readFileSync(KEYS_PATH, 'utf-8'));
      for (const [name, entry] of Object.entries(keysData)) {
        if (entry && typeof entry === 'object' && 'pubkey' in entry) {
          keysMap[name] = entry.pubkey as string;
        }
      }
    }

    if (fs.existsSync(PACK_PATH)) {
      const manifest = JSON.parse(fs.readFileSync(PACK_PATH, 'utf-8'));
      for (const rel of manifest.personas) {
        const personaPath = path.join(PERSONA_DIR, rel);
        if (fs.existsSync(personaPath)) {
          const content = fs.readFileSync(personaPath, 'utf-8');
          const { fields } = splitFrontmatter(content);
          const name = fields.name ?? path.basename(personaPath, '.persona.md');

          // Tail log to derive state
          const logPath = path.join(LOGS_DIR, `${name}.log`);
          let status = 'idle';
          let working_on = 'idle';
          let last_log = '';

          if (fs.existsSync(logPath)) {
            const rawLog = fs.readFileSync(logPath, 'utf-8');
            const lines = rawLog.split('\n').filter(l => l.trim() !== '');
            if (lines.length > 0) {
              last_log = lines[lines.length - 1];
              const logLower = rawLog.toLowerCase();
              
              if (logLower.includes('error') || logLower.includes('fail') || logLower.includes('exception')) {
                status = 'errored';
                working_on = 'error state';
              } else if (logLower.includes('thinking') || logLower.includes('drafting') || logLower.includes('rebuttal')) {
                status = 'thinking';
                working_on = 'thinking...';
              } else if (logLower.includes('connected') || logLower.includes('subscribed')) {
                status = 'connected';
                working_on = 'idle';
              }
            }
          }

          agents.push({
            id: name,
            role: fields.description ?? 'Agent process',
            distinct: fields.distinct ?? 'Autonomous worker',
            pubkey: keysMap[name] ?? '',
            status,
            working_on,
            log: last_log || undefined,
            arc: name.startsWith('strategist-') ? name.replace('strategist-', '') : undefined,
            arcline: fields.arcline ?? undefined
          });
        }
      }
    }

    return NextResponse.json(agents);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
