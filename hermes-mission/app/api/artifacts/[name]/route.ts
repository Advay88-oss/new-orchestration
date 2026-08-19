import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const STATE_DIR = path.resolve('D:/new orchestration/pipeline/state');

export async function GET(
  request: Request,
  { params }: { params: { name: string } }
) {
  try {
    const { name } = params;

    // Strict path-traversal guard: reject anything with slashes or directory symbols
    if (name.includes('/') || name.includes('\\') || name.includes('..')) {
      return NextResponse.json({ error: 'Access denied: Invalid filename' }, { status: 403 });
    }

    const file = path.join(STATE_DIR, name);
    if (!fs.existsSync(file)) {
      return NextResponse.json({ error: 'Artifact not found' }, { status: 404 });
    }

    const img = fs.readFileSync(file);
    return new Response(img, {
      headers: {
        'Content-Type': 'image/png',
        'Content-Length': img.length.toString()
      }
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
