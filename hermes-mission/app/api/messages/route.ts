import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const DRAFTS_DIR = path.resolve('D:/new orchestration/pipeline/state/drafts');
const KEYS_PATH = path.resolve('D:/new orchestration/pipeline/keys/agent-pubkeys.json');

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const channel = searchParams.get('channel');
    const since = searchParams.get('since');
    const sinceSecs = since ? parseInt(since) : 0;

    // Load keys to obtain pubkeys
    let keysMap: Record<string, string> = {};
    if (fs.existsSync(KEYS_PATH)) {
      keysMap = JSON.parse(fs.readFileSync(KEYS_PATH, 'utf-8'));
    }

    const messages = [];

    // In our direct file-based orchestrator, we load drafts and run steps as messages
    if (fs.existsSync(DRAFTS_DIR)) {
      const files = fs.readdirSync(DRAFTS_DIR).filter(f => f.endsWith('.json'));
      for (const file of files) {
        try {
          const raw = fs.readFileSync(path.join(DRAFTS_DIR, file), 'utf-8');
          const data = JSON.parse(raw);
          
          // Step 1: Fallback timestamp safety check (prevent NaN/05:30:00 issues)
          let unixTime = Math.floor(Date.now() / 1000);
          if (data.sent_at) {
            unixTime = new Date(data.sent_at).getTime() / 1000;
          }

          if (sinceSecs && unixTime <= sinceSecs) {
            continue;
          }

          // Step 2: Determine correct sender with robust key-normalization (underscores vs hyphens)
          let senderName = 'conductor';
          let content = '';

          if (data.draft) {
            senderName = `strategist-${data.draft.arc}`;
            // Step 2 Fix: Pass the JSON string of the draft as expected by the classify() and component parsers
            content = JSON.stringify(data.draft);
          } else if (data.verdict) {
            senderName = 'editorial-judge';
            content = JSON.stringify(data);
          } else if (data.pass !== undefined) {
            senderName = 'visual-creator';
            content = JSON.stringify(data);
          } else {
            content = JSON.stringify(data);
          }

          // Normalize sender name lookup (agent-keys uses underscores like 'trend_scout' and 'editorial_judge')
          const normalizedSender = senderName.replace(/-/g, '_');
          const pubkey = keysMap[senderName] ?? keysMap[normalizedSender] ?? senderName;

          // Format as standard Nostr kind-9 event expected by the UI
          messages.push({
            id: data.draft_id ?? file.replace('.json', ''),
            kind: 9,
            created_at: unixTime,
            pubkey,
            tags: [
              ['h', channel ?? '31098616-3d0b-4202-86b4-96bfd36680cd'],
              ['run', '2026-08-08T16:28:05Z-conductor'] // Step 2: Explicit run tag!
            ],
            content
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
