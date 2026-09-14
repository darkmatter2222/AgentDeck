// One persistent producer per managed launch, all descendant sessions share its slot.
import fs from 'node:fs/promises';
import http from 'node:http';
import crypto from 'node:crypto';
import {Bridge} from '../core.mjs';
import {HookFacts, profiles} from './profiles.mjs';

export async function serve({profile, registration, descriptor, root}) {
  const facts = new HookFacts(profile);
  const token = crypto.randomBytes(32).toString('hex');
  const bridge = new Bridge({root, registration, readSnapshot:async () => {
    try { await fs.access(descriptor + '.failed'); facts.broken = true; } catch {}
    return facts.snapshot();
  }});
  const server = http.createServer(async (req, res) => {
    const reply = code => { res.writeHead(code); res.end(); };
    if (req.headers.origin || req.headers.authorization !== `Bearer ${token}`) return reply(403);
    if (req.method !== 'POST' || req.url !== '/event') return reply(404);
    try {
      let raw = '', size = 0;
      for await (const c of req) { size += c.length; if (size > 8192) return reply(413); raw += c; }
      const e = JSON.parse(raw);
      if (!e || Array.isArray(e) || typeof e.session !== 'string' || !e.session || e.session.length > 512 ||
          !Object.hasOwn(profiles[profile].events, e.event)) return reply(400);
      facts.event(e); reply(204); void bridge.flush();
    } catch { reply(400); }
  });
  server.requestTimeout = 2000;
  server.headersTimeout = 2000;
  server.on('connection', socket => socket.setTimeout(2000, () => socket.destroy()));
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  try {
    await fs.writeFile(descriptor + '.tmp', JSON.stringify({profile, owner:registration.id, port:server.address().port, token}), {mode:0o600});
    await fs.rename(descriptor + '.tmp', descriptor);
  } catch (error) { server.close(); throw error; }
  bridge.start();
  return {facts, bridge, close: async () => {
    await bridge.close(); server.close(); server.closeAllConnections();
    await fs.rm(descriptor, {force:true}); await fs.rm(descriptor + '.failed', {force:true});
  }};
}

if (process.argv[2] === '--worker') {
  const [profile, binding, descriptor] = process.argv.slice(3);
  const registration = JSON.parse(await fs.readFile(binding, 'utf8'));
  const service = await serve({profile, registration, descriptor});
  let closing = false;
  const close = async () => { if (closing) return; closing = true; await service.close(); process.exit(0); };
  // Parent owns stdin. EOF also cleans up after an abrupt supervisor exit.
  process.stdin.resume(); process.stdin.on('end', close);
  process.on('SIGTERM', close); process.on('SIGINT', close);
}
