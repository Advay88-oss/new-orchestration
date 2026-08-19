import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const PUBKEYS_PATH = path.resolve('D:/new orchestration/pipeline/keys/agent-pubkeys.json');

export async function GET() {
  try {
    const identities: Record<string, string> = {};

    if (fs.existsSync(PUBKEYS_PATH)) {
      const raw = fs.readFileSync(PUBKEYS_PATH, 'utf-8');
      const data = JSON.parse(raw);
      for (const [name, pubkey] of Object.entries(data)) {
        if (pubkey && typeof pubkey === 'string') {
          identities[pubkey] = name;
        }
      }
    }

    return NextResponse.json(identities);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
