/**
 * Starting pipeline work on GCP: an execution of the Cloud Run Job that runs
 * `python -m pipeline.gtm_os.cloud_job <args>` (the same image as this
 * dashboard). A GTM cycle takes minutes — far longer than a request should
 * hold — so the dashboard starts an execution and polls the bucket.
 *
 * Configured by env on the service: VANNA_PIPELINE_JOB (job name) and
 * VANNA_REGION; the project comes from the metadata server.
 */
import { token } from '@/lib/gcs';

const META_PROJECT = 'http://metadata.google.internal/computeMetadata/v1/project/project-id';
let project: string | null = null;

async function projectId(): Promise<string> {
  if (project) return project;
  if (process.env.GOOGLE_CLOUD_PROJECT) return (project = process.env.GOOGLE_CLOUD_PROJECT);
  const r = await fetch(META_PROJECT, { headers: { 'Metadata-Flavor': 'Google' } });
  if (!r.ok) throw new Error('metadata project: HTTP ' + r.status);
  return (project = (await r.text()).trim());
}

export async function runPipelineJob(args: string[]): Promise<{ ok: boolean; execution?: string; error?: string }> {
  const job = process.env.VANNA_PIPELINE_JOB || 'vanna-gtm-pipeline';
  const region = process.env.VANNA_REGION || 'us-central1';
  try {
    const url = `https://run.googleapis.com/v2/projects/${await projectId()}/locations/${region}/jobs/${job}:run`;
    const r = await fetch(url, {
      method: 'POST',
      headers: { Authorization: `Bearer ${await token()}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ overrides: { containerOverrides: [{ args: ['job', ...args] }], taskCount: 1 } }),
      cache: 'no-store',
    });
    const body = await r.json().catch(() => ({}));
    if (!r.ok) return { ok: false, error: `Cloud Run Jobs: HTTP ${r.status} ${JSON.stringify(body).slice(0, 200)}` };
    return { ok: true, execution: body?.metadata?.name || body?.name };
  } catch (e: any) {
    return { ok: false, error: String(e?.message || e) };
  }
}
