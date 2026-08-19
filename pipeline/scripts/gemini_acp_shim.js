#!/usr/bin/env node
/**
 * ACP shim: adds the `authenticate` step that buzz-acp does not perform.
 *
 * Gemini CLI in --acp mode answers `initialize` with a non-empty `authMethods`
 * list, meaning "pick one before you prompt me". buzz-acp has no auth flag and
 * never calls `authenticate`, so every turn dies with "Gemini API key is missing
 * or not configured" — even though Vertex auth is perfectly fine (the same
 * settings drive a working `gemini -p` call).
 *
 * This sits in the middle and speaks both sides:
 *
 *   buzz-acp  <--stdio-->  shim  <--stdio-->  gemini --acp
 *
 * When the child's `initialize` response comes back, we hold it, send our own
 * `authenticate` with the chosen method, wait for the ack, then release the
 * initialize response upstream with `authMethods` emptied so buzz-acp sees an
 * already-authenticated agent. Everything else is forwarded byte-for-byte.
 *
 * stdout is the protocol channel — all diagnostics go to stderr.
 *
 * Env:
 *   GEMINI_ACP_COMMAND    binary to spawn (default: gemini.cmd from npm)
 *   GEMINI_ACP_AUTH_ID    auth method id (default: vertex-ai)
 *   GEMINI_ACP_DEBUG      set to 1 to log every frame to stderr
 */

'use strict';

const { spawn } = require('child_process');

const AUTH_ID = process.env.GEMINI_ACP_AUTH_ID || 'vertex-ai';
const DEBUG = process.env.GEMINI_ACP_DEBUG === '1';
// Spawn the CLI's entry script with node directly rather than going through
// gemini.cmd. The .cmd shim needs shell:true on Windows, and shell:true mangles
// the space in "Advay Anand" — the child dies with
// "'C:\Users\Advay' is not recognized". No shell, no quoting problem.
const CHILD_ENTRY =
  process.env.GEMINI_ACP_ENTRY ||
  'C:\\Users\\Advay Anand\\AppData\\Roaming\\npm\\node_modules\\@google\\gemini-cli\\bundle\\gemini.js';

// Our injected requests need ids that cannot collide with the client's.
let injectedId = 900000000;
const injectedIds = new Set();

let initializeId = null;   // id of the client's initialize request
let heldInitResponse = null;
let authState = 'idle';    // idle -> pending -> done | failed

function log(...args) {
  if (DEBUG) process.stderr.write(`[shim] ${args.join(' ')}\n`);
}

function warn(...args) {
  process.stderr.write(`[shim] ${args.join(' ')}\n`);
}

const child = spawn(process.execPath, [CHILD_ENTRY, '--acp'], {
  stdio: ['pipe', 'pipe', 'inherit'],
  windowsHide: true,
});

child.on('error', (e) => {
  warn(`failed to spawn ${CHILD_ENTRY}: ${e.message}`);
  process.exit(1);
});

child.on('exit', (code, signal) => {
  warn(`child exited code=${code} signal=${signal}`);
  process.exit(code === null ? 1 : code);
});

function sendToChild(obj) {
  child.stdin.write(JSON.stringify(obj) + '\n');
}

function sendToClient(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

/** Newline-delimited JSON reader that tolerates partial chunks. */
function lineReader(stream, onLine) {
  let buffer = '';
  stream.on('data', (chunk) => {
    buffer += chunk.toString('utf8');
    let idx;
    while ((idx = buffer.indexOf('\n')) !== -1) {
      const line = buffer.slice(0, idx).trim();
      buffer = buffer.slice(idx + 1);
      if (line) onLine(line);
    }
  });
}

function releaseInitialize() {
  if (!heldInitResponse) return;
  const msg = heldInitResponse;
  heldInitResponse = null;
  // Report no required auth methods: from buzz-acp's point of view this agent
  // is ready to prompt, which is now true.
  if (msg.result && Array.isArray(msg.result.authMethods)) {
    msg.result.authMethods = [];
  }
  sendToClient(msg);
  log('released initialize response');
}

// ---- client -> child -------------------------------------------------------

lineReader(process.stdin, (line) => {
  let msg;
  try {
    msg = JSON.parse(line);
  } catch {
    // Not our business to police malformed frames — pass it through.
    child.stdin.write(line + '\n');
    return;
  }
  if (msg.method === 'initialize' && msg.id !== undefined) {
    initializeId = msg.id;
    log(`saw initialize id=${msg.id}`);
  }
  sendToChild(msg);
});

// ---- child -> client -------------------------------------------------------

lineReader(child.stdout, (line) => {
  let msg;
  try {
    msg = JSON.parse(line);
  } catch {
    process.stdout.write(line + '\n');
    return;
  }

  // Our own authenticate ack — consume it, never forward.
  if (msg.id !== undefined && injectedIds.has(msg.id)) {
    injectedIds.delete(msg.id);
    if (msg.error) {
      authState = 'failed';
      warn(`authenticate(${AUTH_ID}) failed: ${JSON.stringify(msg.error)}`);
    } else {
      authState = 'done';
      log(`authenticate(${AUTH_ID}) ok`);
    }
    releaseInitialize();
    return;
  }

  const isInitResponse =
    initializeId !== null && msg.id === initializeId && msg.result !== undefined;

  if (isInitResponse) {
    const methods = msg.result.authMethods;
    if (Array.isArray(methods) && methods.length > 0 && authState === 'idle') {
      const ids = methods.map((m) => m.id);
      const chosen = ids.includes(AUTH_ID) ? AUTH_ID : ids[0];
      if (chosen !== AUTH_ID) {
        warn(`auth method '${AUTH_ID}' not offered (${ids.join(', ')}); using '${chosen}'`);
      }
      authState = 'pending';
      heldInitResponse = msg;
      const id = ++injectedId;
      injectedIds.add(id);
      sendToChild({ jsonrpc: '2.0', id, method: 'authenticate', params: { methodId: chosen } });
      log(`injected authenticate id=${id} method=${chosen}`);
      // Held until the ack arrives; releaseInitialize() sends it.
      return;
    }
    // Already authenticated, or nothing to do.
    sendToClient(msg);
    return;
  }

  sendToClient(msg);
});

process.stdin.on('end', () => {
  try { child.stdin.end(); } catch { /* already closed */ }
});
