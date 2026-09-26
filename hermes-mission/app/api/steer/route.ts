import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const REPO_ROOT = process.env.REPO_ROOT || (fs.existsSync('/app') ? '/app' : path.resolve(process.cwd(), '..'));
const STEER_FILE = path.join(REPO_ROOT, 'pipeline/state/founder_steering.json');

export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const directive = (body.directive || body.founderNote || "").trim();

    if (!directive) {
      return NextResponse.json({ error: "Directive text is required" }, { status: 400 });
    }

    const steerData = {
      directive,
      submitted_by: "Advay Anand (Founder)",
      submitted_at: new Date().toISOString(),
      status: "PENDING_INGESTION"
    };

    fs.writeFileSync(STEER_FILE, JSON.stringify(steerData, null, 2), 'utf-8');

    return NextResponse.json({
      success: true,
      message: `Founder steering directive persisted: "${directive}". Will be consumed on next autonomous cycle.`,
      data: steerData
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
