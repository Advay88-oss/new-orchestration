import { NextResponse } from 'next/server';
import { viewer } from '@/lib/viewer';

export const dynamic = 'force-dynamic';

/** Owner or visitor, and for a visitor the time their view starts. */
export async function GET() {
  return NextResponse.json(viewer());
}
