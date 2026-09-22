#!/usr/bin/env python3
"""Automated GCP Cloud Build & Cloud Run Deployer (deploy_gcp.py).

Handles ADC token authentication and deploys vanna-gtm-mission with:
  - --no-cpu-throttling
  - --min-instances 1
  - Safe argument arrays (immune to Windows username spaces)
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ID = "sales-agent-504607"
REGION = "us-central1"
SERVICE_NAME = "vanna-gtm-mission"
IMAGE_NAME = f"us-central1-docker.pkg.dev/{PROJECT_ID}/vanna-repo/{SERVICE_NAME}:latest"
REPO_ROOT = Path(__file__).resolve().parent

gcloud = shutil.which("gcloud.cmd") or shutil.which("gcloud") or "gcloud"

print("=" * 80)
print("🚀 DEPLOYING VANNA GTM MISSION CONTROL TO GOOGLE CLOUD RUN")
print("=" * 80)

# 1. Obtain ADC Token
print("\n[1/4] Retrieving Application Default Credentials (ADC) token...")
try:
    token = subprocess.check_output([gcloud, "auth", "application-default", "print-access-token"], text=True).strip()
    print("✓ Valid ADC access token obtained.")
except Exception as e:
    print(f"❌ Failed to obtain ADC access token: {e}")
    sys.exit(1)

# Write token to scratch file
with tempfile.NamedTemporaryFile("w", delete=False) as tf:
    tf.write(token)
    token_file = tf.name

try:
    # 2. Configure GCP Project
    print(f"\n[2/4] Setting active project to {PROJECT_ID}...")
    subprocess.check_call([
        gcloud, "config", "set", "project", PROJECT_ID,
        f"--access-token-file={token_file}"
    ])
    print(f"✓ Project set to {PROJECT_ID}")

    # 3. Cloud Build
    print(f"\n[3/4] Building container via Google Cloud Build (tag: {IMAGE_NAME})...")
    build_cmd = [
        gcloud, "builds", "submit",
        "--project", PROJECT_ID,
        "--tag", IMAGE_NAME,
        f"--access-token-file={token_file}",
        str(REPO_ROOT)
    ]
    subprocess.check_call(build_cmd)
    print("✓ Container image built and pushed successfully.")

    # 4. Deploy to Cloud Run
    print(f"\n[4/4] Deploying {SERVICE_NAME} to Cloud Run ({REGION})...")
    deploy_cmd = [
        gcloud, "run", "deploy", SERVICE_NAME,
        "--project", PROJECT_ID,
        "--image", IMAGE_NAME,
        "--platform", "managed",
        "--region", REGION,
        "--allow-unauthenticated",
        "--memory", "2Gi",
        "--cpu", "2",
        "--port", "8080",
        "--no-cpu-throttling",
        "--min-instances", "1",
        f"--access-token-file={token_file}",
        f"--set-env-vars=NODE_ENV=production,PORT=8080,VERTEX_PROJECT={PROJECT_ID},VERTEX_LOCATION={REGION}"
    ]
    subprocess.check_call(deploy_cmd)

    print("\n" + "=" * 80)
    print("✅ DEPLOYMENT COMPLETE!")
    print("   Live Service URL: https://vanna-gtm-mission-114262736718.us-central1.run.app")
    print("   Always-on CPU (--no-cpu-throttling) & 24/7 background scheduler active (--min-instances 1).")
    print("=" * 80)

finally:
    if os.path.exists(token_file):
        os.unlink(token_file)
