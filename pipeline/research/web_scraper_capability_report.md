# Web Scraper & Browser Extension Capability Report

**Date of Verification:** 2026-09-19  
**Host Environment:** Windows 11 / Node v22.23.2 / Python 3.11 / Chrome Profile 6  

---

## Executive Summary & Core Identity

| Field | Value |
| :--- | :--- |
| **SCRAPER_NAME** | OpenCLI Browser Bridge Extension (`ildkmabpimmkaediidaifkhjpohdnifk`) & OpenCLI CLI |
| **VERSION** | Extension: `v1.0.24` / OpenCLI CLI Daemon: `v1.8.6` |
| **INSTALLATION_STATUS** | **INSTALLED & LIVE CONNECTED** |
| **INVOCATION_METHOD** | CLI via `opencli browser <session> <command>` and `opencli web read --url <url> --stdout true -f json`, or direct WebSocket/HTTP daemon at `http://127.0.0.1:19825` |
| **AUTH_STATUS** | **AUTHENTICATED / LOCAL BRIDGE** — Connected via Chrome Profile 6 (profile alias: `e6bevacq`). Inherits active user sessions and cookies without external API keys. |
| **HERMES_INTEGRATION_STATUS** | **PROGRAMMATICALLY ACCESSIBLE** via Python subprocess execution (`['cmd.exe', '/c', 'opencli', ...]` or direct Node/HTTP daemon calls). Also interoperable with Hermes native `web_extract` / `browser_exec`. |

---

## 1. Extension & Daemon Architecture

The installed web scraper is **OpenCLI Browser Bridge**, consisting of a two-tier architecture:
1. **Chrome Extension:**  
   * **Extension ID:** `ildkmabpimmkaediidaifkhjpohdnifk`
   * **Install Path:** `C:\Users\Advay Anand\AppData\Local\Google\Chrome\User Data\Profile 6\Extensions\ildkmabpimmkaediidaifkhjpohdnifk\1.0.24_0`
   * **Active Connected Profile:** `e6bevacq`
   * **Function:** Operates directly inside the user's Google Chrome instance, allowing full DOM access, JavaScript evaluation, network request capture, and visual rendering with real user session cookies.
2. **Local Daemon & CLI Client:**
   * **Binary Path:** `C:\Users\Advay Anand\AppData\Roaming\npm\opencli.cmd`
   * **Daemon Port:** `127.0.0.1:19825`
   * **Protocol:** Local inter-process bridge connecting CLI commands to the Chrome extension tab manager.

---

## 2. Available Operations & Command Schema

The installed scraper supports two primary programmatic invocation surfaces:

### A. High-Level Page Extractor (`opencli web read`)
* **Command:** `opencli web read --url <url> [options]`
* **Capabilities:**
  * `--stdout true`: Directly streams markdown content to stdout.
  * `-f json` / `-f yaml`: Formats output as structured JSON/YAML with metadata (title, author, publish_time, size).
  * `--wait <seconds>`: Waits for specified duration (default: 3s) for dynamic JavaScript hydration.
  * `--wait-until domstable | networkidle`: Waits for network requests to settle.
  * `--wait-for <selector>`: Waits for specific DOM elements before extracting.
  * `--frames same-origin | all-same-origin | none`: Extracts embedded iframes.
  * `--window background | foreground`: Controls headless/background or visible execution.

### B. Stateful Interactive Browser Session (`opencli browser <session> <command>`)
* **Session Lifecycle:** `opencli browser <session> open <url> --window background` keeps a persistent leased browser tab alive across calls.
* **Operations:**
  * `open <url>`: Navigates session to target URL.
  * `state`: Returns active URL, page title, viewport, scroll coordinates, and an indexed interactive element hierarchy (with all links `[N]<a href="...">`, buttons, inputs).
  * `extract`: Extracts structured JSON with `url`, `title`, `selector`, `total_chars`, and paragraph-aware markdown `content`.
  * `screenshot <path>`: Captures full-page or viewport PNG screenshots.
  * `find [options]`: Evaluates CSS or semantic locators returning `{matches_n, entries[]}`.
  * `click <target>`: Interactively clicks buttons or navigation links.
  * `eval <js>`: Runs arbitrary JavaScript inside page context.
  * `scroll <direction>`: Scrolls viewport up/down.
  * `wait <type> [value]`: Explicitly waits for selectors, text, time, or XHR endpoints.
  * `close`: Releases session lease.

---

## 3. Supported Page Types & Data Outputs

| Dimension | Supported | Verification Proof |
| :--- | :---: | :--- |
| **JavaScript-Rendered SPAs** | **YES** | Verified on `https://docs.vanna.finance` (Mintlify React SPA rendered fully). |
| **Full DOM Text Extraction** | **YES** | Emits clean markdown with headings, links, tables, and images preserved. |
| **Visual Screenshots** | **YES** | Verified saving PNG to `pipeline/state/vanna_docs_screenshot.png`. |
| **Link Extraction & Traversal** | **YES** | `opencli browser state` outputs structured indices (`[N]<a href="...">`) enabling deterministic link traversal. |
| **Iframe Content** | **YES** | Supports `--frames same-origin` or `all-same-origin`. |
| **Multi-Domain Crawling** | **YES** | Orchestrator can iteratively command session navigation across multiple domains within controlled depth limits. |

---

## 4. Limitations & Rate-Limits

1. **Local Chrome Dependency:** Requires Google Chrome to be active with the OpenCLI extension enabled (Profile 6).
2. **Session Lease Management:** Persistent sessions must be explicitly closed via `opencli browser <session> close` to avoid orphan tab buildup.
3. **Subprocess Quoting on Windows:** In Windows environments with spaces in usernames (`C:\Users\Advay Anand\`), invocations must use safe list-based execution (`['cmd.exe', '/c', 'opencli', ...]`) or forward-slash paths.
4. **Rate Limits:** No external API token rate-limits apply; rate-limiting is purely governed by target website bot-detection / Cloudflare policies and polite crawler delays (1.0s – 2.0s per page recommended).

---

## 5. Hermes Integration Verdict

**STATUS: READY FOR PRODUCTION TOOL ADAPTER (PHASE 2)**
* The scraper is **100% installed, live, and functional**.
* It can be driven directly via Python `subprocess` using `opencli web read` for fast extraction, and `opencli browser` for deep stateful multi-page crawling and screenshot capture.
* No mock data or third-party scraper replacement is needed.
