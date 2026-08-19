import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const DRAFTS_DIR = path.resolve('D:/new orchestration/pipeline/state/drafts');
const KEYS_PATH = path.resolve('D:/new orchestration/pipeline/keys/agent-keys.json');

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const channel = searchParams.get('channel');
    const since = searchParams.get('since');
    const sinceSecs = since ? parseInt(since) : 0;

    // Load keys to obtain pubkeys
    const keysMap: Record<string, string> = {};
    if (fs.existsSync(KEYS_PATH)) {
      const keysData = JSON.parse(fs.readFileSync(KEYS_PATH, 'utf-8'));
      for (const [name, entry] of Object.entries(keysData)) {
        if (entry && typeof entry === 'object' && 'pubkey' in entry) {
          keysMap[name] = entry.pubkey as string;
        }
      }
    }

    const messages = [];

    // In our direct file-based orchestrator, we load drafts and run steps as messages
    if (fs.existsSync(DRAFTS_DIR)) {
      const files = fs.readdirSync(DRAFTS_DIR).filter(f => f.endsWith('.json'));
      for (const file of files) {
        try {
          const raw = fs.readFileSync(path.join(DRAFTS_DIR, file), 'utf-8');
          const data = JSON.parse(raw);
          const unixTime = new Date(data.sent_at).getTime() / 1000;

          if (sinceSecs && unixTime <= sinceSecs) {
            continue;
          }

          // Format as standard Nostr kind-9 event expected by the UI
          messages.push({
            id: data.draft_id ?? file.replace('.json', ''),
            kind: 9,
            created_at: unixTime,
            pubkey: keysMap[data.draft?.arc ? `strategist-${data.draft.arc}` : 'conductor'] ?? '',
            tags: [
              ['h', channel ?? '31098616-3d0b-4202-86b4-96bfd36680cd'],
              ['run', '2026-08-08T16:28:05Z-conductor'] // Step 2: Explicit run tag!
            ],
            content: JSON.stringify(data.draft ?? data)
          });
        } catch (e) {
          // Skip unparseable files
        }
      }
    }

    return NextResponse.json(messages);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
