# Mac Mini Setup & Migration Guide — Vanna Autonomous Agent Pipeline

This document outlines the step-by-step setup and migration guide to move the entire **Vanna Autonomous Agent Pipeline** and the **Hermes Multi-Platform Gateway** to a dedicated **Mac Mini** (Apple Silicon - M1/M2/M3/M4 running macOS Sonoma or Sequoia).

---

## 1. System Prerequisites

Install the official macOS developer toolchain and dependencies via Homebrew first:

```bash
# 1. Install Xcode Command Line Tools
xcode-select --install

# 2. Install Homebrew (if not already present)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to your PATH (for Apple Silicon Macs)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
source ~/.zshrc

# 3. Install core system dependencies
brew install git python@3.11 node@22 redis postgresql@17 minio prometheus keycloak
brew install --cask docker google-chrome
```

---

## 2. Directory Layout & Workspace Setup

We recommend matching your folder structure under a single directory in your user home `~/vanna-pipeline/`:

```
~/vanna-pipeline/
  ├── orchestrator/         # This active repository (autonomous-orchestrator)
  │     ├── pipeline/       # Prompts, state, logs, and keys
  │     └── ...
  ├── buzz/                 # The Buzz Relay repository (block/buzz checkout)
  └── cargo-home/           # Rust build caches
```

To set up:

```bash
mkdir -p ~/vanna-pipeline
cd ~/vanna-pipeline

# Clone your repositories here
git clone <orchestrator-repo-url> orchestrator
git clone <buzz-relay-repo-url> buzz
```

---

## 3. Rebuilding the Buzz Relay on macOS (aarch64)

The Buzz Rust workspace binaries (`buzz-relay`, `buzz-acp`, `buzz-agent`, `buzz-dev-mcp`) must be compiled natively for **Apple Silicon (`aarch64-apple-darwin`)**. Do **not** copy Windows `.exe` files!

```bash
cd ~/vanna-pipeline/buzz

# 1. Set macOS-specific Rust build environments
export CARGO_HOME="~/vanna-pipeline/cargo-home"

# 2. Build the exact workspace binaries (exempting broken crates)
cargo build --bin buzz-relay --bin buzz-acp --bin buzz-agent --bin buzz-dev-mcp --release

# 3. Verify the built Mach-O executable architectures
file target/release/buzz-relay
# Should print: target/release/buzz-relay: Mach-O 64-bit executable arm64
```

---

## 4. Python Environment & Dependency Setup

Use Python 3.11 with the `uv` package manager for instant, deterministic, and sandboxed package installs:

```bash
# 1. Install 'uv'
brew install uv

# 2. Navigate to your orchestrator directory and create a virtualenv
cd ~/vanna-pipeline/orchestrator
uv venv .venv --python 3.11
source .venv/bin/activate

# 3. Install Python dependencies
uv pip install fastapi uvicorn pydantic pydantic-settings urllib3 requests
```

---

## 5. Google Cloud SDK (Vertex AI Print Token)

For Vertex AI authentication through our metered spend proxy, you must install the native macOS Google Cloud SDK:

```bash
# 1. Download and extract Google Cloud SDK for Apple Silicon (arm64)
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-darwin-arm.tar.gz
tar -xf google-cloud-sdk-darwin-arm.tar.gz -C ~
rm google-cloud-sdk-darwin-arm.tar.gz

# 2. Run the installer and add to your .zshrc
~/google-cloud-sdk/install.sh
source ~/.zshrc

# 3. Authenticate Application Default Credentials (ADC)
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/cloud-platform
```

---

## 6. Configuring Hermes Gateway on macOS

Install Hermes Agent on your Mac Mini and configure the Telegram and Slack adapters:

```bash
# 1. Run the native macOS Hermes installer
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
source ~/.zshrc

# 2. Copy your existing credentials from your Windows host to your Mac Mini at:
# ~/.hermes/.env

# 3. Copy your settings from Windows to Mac Mini at:
# ~/.hermes/config.yaml

# 4. Generate the official Vanna Slack Manifest on your Mac
hermes slack manifest --agent-view --write
```
*Note: Follow the manifest guide to update your app at api.slack.com, click "Reinstall to Workspace", and copy the fresh bot and app tokens to your `~/.hermes/.env`.*

---

## 7. macOS-Specific Script Configurations

Before running the orchestrator on your Mac Mini, you need to update a few absolute paths inside your scripts:

### A. Chrome Executable Path (`render_visual.py`)
In `pipeline/scripts/render_visual.py`, headless Chrome is used to screenshot visuals. Update `CHROME_CANDIDATES` at the top of the file to include the standard macOS application path:

```python
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", # macOS standard
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    # ... keep others
]
```

### B. Spend Proxy Google Cloud Path (`vertex_spend_proxy.py`)
In `pipeline/scripts/vertex_spend_proxy.py`, update `gcloud` resolution in the `access_token` function to point to your macOS path:

```python
    gcloud = os.environ.get(
        "GCLOUD_BIN",
        os.path.expanduser("~/google-cloud-sdk/bin/gcloud") # macOS standard
    )
```

---

## 8. Launching the Services (Mac Mini Launch Commands)

Run these commands in separate terminal sessions, or set them up as permanent background daemons:

### 1. Start Docker Containers (Buzz infrastructure)
```bash
cd ~/vanna-pipeline/buzz
docker compose up -d
```

### 2. Start the local Buzz Relay
```bash
DATABASE_URL="postgres://buzz:buzz@127.0.0.1:5432/buzz?sslmode=disable" \
REDIS_URL="redis://127.0.0.1:6379" \
BUZZ_BIND_ADDR="0.0.0.0:3000" \
  ~/vanna-pipeline/buzz/target/release/buzz-relay
```

### 3. Start the Google Vertex Spend Metering Proxy (Port 8900)
```bash
cd ~/vanna-pipeline/orchestrator
source .venv/bin/activate
python pipeline/scripts/vertex_spend_proxy.py --port 8900
```

### 4. Start the Hermes Multi-Platform Gateway (Telegram + Slack)
```bash
# Starts the gateway permanently in the background as a launchd service
hermes gateway start
```

### 5. Launch the Next.js Mission Control Dashboard (Port 3100)
```bash
cd ~/vanna-pipeline/orchestrator/mission-control
npm run dev
# Dashboard is live at http://127.0.0.1:3100
```

---

## 9. Setting Up Permanent Background Daemons (`launchd` Plists)

Instead of manually running terminal commands, set up your background services as native macOS `launchd` agents so they start automatically when your Mac Mini boots.

Create a plist file at `~/Library/LaunchAgents/com.vanna.spendproxy.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vanna.spendproxy</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/yourusername/vanna-pipeline/orchestrator/.venv/bin/python</string>
        <string>/Users/yourusername/vanna-pipeline/orchestrator/pipeline/scripts/vertex_spend_proxy.py</string>
        <string>--port</string>
        <string>8900</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/Users/yourusername/vanna-pipeline/orchestrator</string>
    <key>StandardOutPath</key>
    <string>/Users/yourusername/vanna-pipeline/orchestrator/pipeline/logs/spend_proxy.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/yourusername/vanna-pipeline/orchestrator/pipeline/logs/spend_proxy.err</string>
</dict>
</plist>
```

Activate the service:
```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.vanna.spendproxy.plist
```

---

## 10. macOS traps to avoid

*   **IPv6 Port Binding:** In macOS, `localhost` resolves heavily to `::1` (IPv6). If your Docker containers bind to `127.0.0.1`, macOS clients querying `localhost:3000` or `localhost:5432` will get refused connections. **Always use the absolute IPv4 address `127.0.0.1`** in all connection URLs.
*   **System Integrity Protection (SIP) & Dyld:** macOS blocks certain environment variable injection (like `DYLD_LIBRARY_PATH`) into system binaries (like `/bin/bash` or python). Running scripts using virtualenv-wrapped interpreters ensures that system protections do not strip your paths.
*   **Prevent Sleep Mode:** A Mac Mini acting as a server must not go to sleep when idle. Disable system sleep via System Settings or run:
    `sudo pmset -a sleep 0 displaysleep 0`
*   **Rust Binary Signing:** If macOS blocks your compiled Rust executables due to signing restrictions ("damaged" or "unknown developer"), clear their extended quarantine attributes by running:
    `xattr -cr ~/vanna-pipeline/buzz/target/release/`
