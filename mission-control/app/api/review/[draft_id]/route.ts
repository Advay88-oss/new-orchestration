import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const STATE_DIR = path.resolve('D:/new orchestration/pipeline/state');

export async function GET(
  request: Request,
  { params }: { params: { draft_id: string } }
) {
  try {
    const { draft_id } = params;
    
    // Check in drafts, approved, or rejected subdirectories
    const dirs = ['drafts', 'approved', 'rejected'];
    for (const d of dirs) {
      const file = path.join(STATE_DIR, d, `${draft_id}.json`);
      if (fs.existsSync(file)) {
        const raw = fs.readFileSync(file, 'utf-8');
        const data = JSON.parse(raw);
        return NextResponse.json({
          draft_id,
          status: data.status ?? 'awaiting_review',
          reply: data.reviewer_reply ?? null,
          sent_at: data.sent_at ?? new Date().toISOString()
        });
      }
    }

    return NextResponse.json({ error: `Draft ID ${draft_id} not found` }, { status: 404 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
