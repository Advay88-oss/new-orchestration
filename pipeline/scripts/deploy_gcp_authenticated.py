#!/usr/bin/env python3
"""Automated Authenticated Deployment to Google Cloud Run (deploy_gcp_authenticated.py).

Builds and deploys the unified Vanna GTM Operating System to Google Cloud Run:
  1. Refreshes Application Default Credentials (ADC) to ensure seamless auth.
  2. Submits multi-stage Docker build to Google Cloud Build.
  3. Deploys to Cloud Run with 2GB RAM, 2 vCPUs, and managed platform in us-central1.
  4. Probes and returns the live public HTTPS service URL.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PROJECT_ID = "sales-agent-504607"
REGION = "us-central1"
SERVICE_NAME = "vanna-gtm-mission"
IMAGE_TAG = f"gcr.io/{PROJECT_ID}/{SERVICE_NAME}:latest"


def get_authenticated_env():
    """Generates an environment with a freshly refreshed OAuth access token."""
    import google.auth
    from google.auth.transport.requests import Request

    creds, proj = google.auth.default()
    creds.refresh(Request())

    env = os.environ.copy()
    env["CLOUDSDK_AUTH_ACCESS_TOKEN"] = creds.token
    env["CLOUDSDK_CORE_PROJECT"] = PROJECT_ID
    return env


def run_deployment():
    print("=" * 80)
    print("🚀 DEPLOYING VANNA GTM MISSION CONTROL TO GOOGLE CLOUD RUN")
    print("=" * 80)
    print(f"   Project:  {PROJECT_ID}")
    print(f"   Region:   {REGION}")
    print(f"   Service:  {SERVICE_NAME}")
    print(f"   Image:    {IMAGE_TAG}")
    print("=" * 80)

    env = get_authenticated_env()

    # Step 1: Submit build to Google Cloud Build
    print("\n[1/3] Submitting container build to Google Cloud Build...")
    print("      (Building Node.js 20 dashboard + Python 3.11 orchestration + Chromium)...")
    
    build_cmd = f'cmd.exe /c "gcloud builds submit --project {PROJECT_ID} --tag {IMAGE_TAG} ."'
    
    t0 = time.time()
    res_build = subprocess.run(
        build_cmd,
        env=env,
        cwd=str(REPO_ROOT),
        shell=True,
        capture_output=False, # stream live build progress
        text=True
    )
    
    if res_build.returncode != 0:
        print("\n❌ Cloud Build failed. Please verify build configuration.")
        sys.exit(res_build.returncode)

    build_time = time.time() - t0
    print(f"✓ Cloud Build completed successfully in {build_time:.1f}s.")

    # Step 2: Deploy to Google Cloud Run
    print("\n[2/3] Deploying container image to Cloud Run...")
    deploy_cmd = (
        f'cmd.exe /c "gcloud run deploy {SERVICE_NAME} '
        f'--project {PROJECT_ID} '
        f'--image {IMAGE_TAG} '
        f'--platform managed '
        f'--region {REGION} '
        f'--allow-unauthenticated '
        f'--memory 2Gi '
        f'--cpu 2 '
        f'--port 8080 '
        f'--set-env-vars=NODE_ENV=production,PORT=8080,VERTEX_PROJECT={PROJECT_ID},VERTEX_LOCATION={REGION} '
        f'--format=json"'
    )

    t1 = time.time()
    res_deploy = subprocess.run(
        deploy_cmd,
        env=env,
        cwd=str(REPO_ROOT),
        shell=True,
        capture_output=True,
        text=True
    )

    if res_deploy.returncode != 0:
        print("\n❌ Cloud Run deployment failed:")
        print(res_deploy.stderr or res_deploy.stdout)
        sys.exit(res_deploy.returncode)

    deploy_time = time.time() - t1
    print(f"✓ Cloud Run service deployed in {deploy_time:.1f}s.")

    # Step 3: Extract and probe service URL
    import json
    service_url = None
    try:
        deploy_info = json.loads(res_deploy.stdout)
        service_url = deploy_info.get("status", {}).get("url")
    except Exception:
        # Fallback to describe
        desc_cmd = f'cmd.exe /c "gcloud run services describe {SERVICE_NAME} --project {PROJECT_ID} --region {REGION} --format=value(status.url)"'
        res_desc = subprocess.run(desc_cmd, env=env, shell=True, capture_output=True, text=True)
        service_url = res_desc.stdout.strip()

    print("\n" + "=" * 80)
    print("✅ DEPLOYMENT COMPLETE!")
    print(f"   Live Public Service URL: {service_url}")
    print("=" * 80)

    # Health check public URL
    if service_url:
        print("\n[3/3] Probing deployed service...")
        import urllib.request
        for attempt in range(1, 6):
            try:
                time.sleep(3)
                req = urllib.request.Request(service_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    print(f"   ✓ Health probe passed! Status: HTTP {resp.status}")
                    break
            except Exception as e:
                print(f"   Attempt {attempt}/5: waiting for endpoint readiness ({e})...")


if __name__ == "__main__":
    run_deployment()
