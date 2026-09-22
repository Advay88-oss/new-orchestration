import { NextResponse } from 'next/server';
import { runPython, lastJson } from '@/lib/python';

export const dynamic = 'force-dynamic';

/**
 * Trigger one live intelligence poll.
 *
 * Previously spawned a bare `python3` (and `cmd.exe /c python` on Windows),
 * which does not exist on this machine, so the Agents view's scan button
 * always failed. The interpreter is now resolved from the project venv, and
 * a failure returns the real stderr rather than a generic error string.
 */
export async function POST() {
  const r = await runPython(
    ['-c',
     'import sys; sys.path.insert(0, ".");\n'
     + 'from pipeline.intelligence_stream.continuous_ingestion_daemon import ContinuousIngestionDaemon\n'
     + 'import json\n'
     + 'print(json.dumps(ContinuousIngestionDaemon().run_single_poll(), default=str))'],
    240_000,
  );

  if (!r.ok) {
    return NextResponse.json(
      {
        success: false,
        error: r.error || r.stderr.trim().slice(-600) || `exit ${r.code}`,
      },
      { status: 500 },
    );
  }

  const parsed = lastJson<Record<string, unknown>>(r.stdout);
  return NextResponse.json({
    success: true,
    result: parsed,
    // When the script printed something unparseable, say so instead of
    // returning an empty object that reads like a clean scan.
    ...(parsed ? {} : { note: 'poll completed but returned no JSON', stdout: r.stdout.slice(-1500) }),
  });
}

export async function GET() {
  return NextResponse.json({ error: 'POST to trigger a scan' }, { status: 405 });
}
