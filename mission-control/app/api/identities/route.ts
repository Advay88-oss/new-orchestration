import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const KEYS_PATH = path.resolve('D:/new orchestration/pipeline/keys/agent-keys.json');
const OP_KEYS_PATH = path.resolve('D:/new orchestration/pipeline/keys/operator-key.json');

export async function GET() {
  try {
    const identities: Record<string, string> = {};

    // 1. Load Agent Keys
    if (fs.existsSync(KEYS_PATH)) {
      const raw = fs.readFileSync(KEYS_PATH, 'utf-8');
      const data = JSON.parse(raw);
      for (const [name, entry] of Object.entries(data)) {
        if (entry && typeof entry === 'object' && 'pubkey' in entry) {
          identities[entry.pubkey as string] = name;
        }
      }
    }

    // 2. Load Operator Keys
    if (fs.existsSync(OP_KEYS_PATH)) {
      const raw = fs.readFileSync(OP_KEYS_PATH, 'utf-8');
      const data = JSON.parse(raw);
      for (const [name, entry] of Object.entries(data)) {
        if (entry && typeof entry === 'object' && 'pubkey' in entry) {
          identities[entry.pubkey as string] = name;
        }
      }
    }

    return NextResponse.json(identities);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
