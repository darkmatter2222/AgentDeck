// Short-lived observer: no approval decisions, no diagnostics on stdout, always exit 0.
import fs from 'node:fs/promises';
import {writeFileSync} from 'node:fs';
import {normalize} from './profiles.mjs';
const [profile, event] = process.argv.slice(2);
const descriptor = process.env.AGENTDECK_HOOK_BINDING;
const timer = setTimeout(() => {
  if (descriptor) { try { writeFileSync(descriptor + '.failed', '1', {mode:0o600}); } catch {} }
  if (profile === 'gemini') process.stdout.write('{}\n');
  process.exit(0);
}, 1800);
try {
  if (descriptor) {
    const d = JSON.parse(await fs.readFile(descriptor, 'utf8'));
    if (d.profile === profile && Number.isInteger(d.port) && d.port > 0 && d.port <= 65535) {
      process.stdin.setEncoding('utf8');
      let input = '', size = 0;
      for await (const chunk of process.stdin) {
        size += Buffer.byteLength(chunk);
        if (size > 4 * 1024 * 1024) throw Error('Oversized hook input');
        input += chunk;
      }
      const value = normalize(profile, event, JSON.parse(input));
      if (!value) throw Error('Invalid hook input');
      const response = await fetch(`http://127.0.0.1:${d.port}/event`, {method:'POST',
        headers:{Authorization:`Bearer ${d.token}`, 'Content-Type':'application/json'},
        body:JSON.stringify(value), signal:AbortSignal.timeout(800)});
      if (!response.ok) throw Error('Delivery failed');
    }
  }
} catch {
  // Persist only a failure marker. A later heartbeat must not make lost events look reliable.
  if (descriptor) { try { await fs.writeFile(descriptor + '.failed', '1', {mode:0o600}); } catch {} }
} finally {
  clearTimeout(timer);
  if (profile === 'gemini') process.stdout.write('{}\n');
  process.exit(0);
}
