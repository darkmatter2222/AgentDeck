// Observer by default. Opt-in Claude permission requests wait for a physical decision.
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {writeFileSync} from 'node:fs';
import {normalize} from './profiles.mjs';
import {Bridge} from '../core.mjs';
import {reviewPermission, claudeDecision} from '../permissions.mjs';

const [profile, event] = process.argv.slice(2);
const descriptor = process.env.AGENTDECK_HOOK_BINDING;
let timer = setTimeout(() => {
  if (descriptor) { try { writeFileSync(descriptor + '.failed', '1', {mode:0o600}); } catch {} }
  if (profile === 'gemini') process.stdout.write('{}\n');
  process.exit(0);
}, 1800);

async function direct(value) {
  const root = process.env.OCDECK_HOME || path.join(os.homedir(), '.opencode-deck');
  const discovery = JSON.parse(await fs.readFile(path.join(root, 'discovery.json'), 'utf8'));
  const token = (await fs.readFile(path.join(root, 'token'), 'utf8')).trim();
  if (!Number.isInteger(discovery.port) || discovery.port < 1 || discovery.port > 65535) throw Error('Bad broker port');
  const response = await fetch(`http://127.0.0.1:${discovery.port}/v1/hook`, {
    method:'POST', headers:{Authorization:`Bearer ${token}`, 'Content-Type':'application/json'},
    body:JSON.stringify({profile, event:value, parentPid:process.ppid, cwd:process.cwd()}),
    signal:AbortSignal.timeout(900)
  });
  if (!response.ok) throw Error('Broker delivery failed');
  return response.json();
}

try {
  process.stdin.setEncoding('utf8');
  let input = '', size = 0;
  for await (const chunk of process.stdin) {
    size += Buffer.byteLength(chunk);
    if (size > 4 * 1024 * 1024) throw Error('Oversized hook input');
    input += chunk;
  }
  const raw = JSON.parse(input);
  const value = normalize(profile, event, raw);
  if (!value) throw Error('Invalid hook input');
  let owner;
  if (descriptor) {
    const d = JSON.parse(await fs.readFile(descriptor, 'utf8'));
    if (d.profile !== profile || !Number.isInteger(d.port) || d.port < 1 || d.port > 65535) throw Error('Bad binding');
    const response = await fetch(`http://127.0.0.1:${d.port}/event`, {method:'POST',
      headers:{Authorization:`Bearer ${d.token}`, 'Content-Type':'application/json'},
      body:JSON.stringify(value), signal:AbortSignal.timeout(800)});
    if (!response.ok) throw Error('Delivery failed');
    owner = d.owner;
  } else {
    owner = (await direct(value)).id;
  }
  if (profile === 'claude' && event === 'PermissionRequest' && owner) {
    clearTimeout(timer);
    timer = setTimeout(() => process.exit(0), 119000);
    const bridge = new Bridge({registration:{id:owner}, readSnapshot:async () => ({})});
    await reviewPermission(bridge.call.bind(bridge), {owner, tool:value.tool || 'Permission',
      summary:JSON.stringify(raw.tool_input || {}).slice(0,2000)}, async decision => {
      process.stdout.write(JSON.stringify(claudeDecision(decision)) + '\n');
    });
  }
} catch {
  if (descriptor) { try { await fs.writeFile(descriptor + '.failed', '1', {mode:0o600}); } catch {} }
} finally {
  clearTimeout(timer);
  if (profile === 'gemini') process.stdout.write('{}\n');
  process.exit(0);
}
