import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {profiles} from './profiles.mjs';

export function configuration(profile, script = fileURLToPath(new URL('./hook.mjs', import.meta.url))) {
  const p = profiles[profile];
  if (!p) throw Error('Unknown harness: ' + profile);
  // Double quotes work in Bash, cmd and PowerShell for these paths. Refuse shell metacharacters
  // that could expand even inside quotes; never interpolate user prompts into commands.
  script = script.replaceAll('\\', '/');
  if (/["$`%!\r\n]/.test(script)) throw Error('Move AgentDeck to a path without quotes, $, backticks, %, or !');
  const hooks = {};
  for (const event of Object.keys(p.events)) {
    const command = `node "${script}" ${profile} ${event}`;
    let entry = {type:'command', command, timeout:5};
    if (p.format === 'copilot') entry = {type:'command', bash:command, powershell:command, timeoutSec:5};
    if (p.format === 'cursor') entry = {command, timeout:5};
    if (p.format === 'nested') {
      // Gemini measures hook timeout in milliseconds; Claude measures seconds.
      if (profile === 'gemini') entry.timeout = 5000;
      if (profile === 'codex' && ['SessionEnd','Interrupt'].includes(event)) entry.timeout = 3;
      entry = {hooks:[entry]};
    }
    hooks[event] = [entry];
  }
  return {...(['copilot','cursor'].includes(p.format) ? {version:1} : {}), hooks};
}
const same = (a,b) => JSON.stringify(a) === JSON.stringify(b);
export function mergeConfig(existing, generated, prior = null) {
  const result = structuredClone(existing);
  if (!result || typeof result !== 'object' || Array.isArray(result)) throw Error('Config must be an object');
  result.hooks ??= {};
  if (typeof result.hooks !== 'object' || Array.isArray(result.hooks) || result.hooks === null) throw Error('hooks must be an object');
  if (generated.version && result.version !== undefined && result.version !== generated.version) throw Error('Unsupported config version');
  if (generated.version) result.version = generated.version;
  for (const [event, entries] of Object.entries(prior?.hooks || {})) {
    if (result.hooks[event] !== undefined && !Array.isArray(result.hooks[event])) throw Error('Invalid hook array: ' + event);
    if (result.hooks[event]) result.hooks[event] = result.hooks[event].filter(x => !entries.some(y => same(x,y)));
  }
  for (const [event, entries] of Object.entries(generated.hooks)) {
    result.hooks[event] ??= [];
    if (!Array.isArray(result.hooks[event])) throw Error('Invalid hook array: ' + event);
    for (const entry of entries) if (!result.hooks[event].some(x => same(x,entry))) result.hooks[event].push(entry);
  }
  for (const event of Object.keys(result.hooks)) if (result.hooks[event].length === 0) delete result.hooks[event];
  return result;
}
async function read(file, fallback) {
  try { return JSON.parse((await fs.readFile(file,'utf8')).replace(/^\uFEFF/, '')); }
  catch (e) { if (e.code === 'ENOENT') return fallback; throw Error(`Cannot parse ${file}; merge JSONC manually: ${e.message}`); }
}
async function atomic(file, value) {
  await fs.mkdir(path.dirname(file), {recursive:true});
  await fs.writeFile(file + '.agentdeck-tmp', JSON.stringify(value,null,2)+'\n', {flag:'wx'});
  await fs.rename(file + '.agentdeck-tmp', file);
}
export async function install(profile, project, {remove=false, dryRun=false} = {}) {
  if (!profiles[profile]) throw Error('Unknown harness');
  const target = path.resolve(project, profiles[profile].config);
  const manifest = path.resolve(project, '.agentdeck', profile + '.json');
  const prior = await read(manifest, null);
  if (prior && prior.target !== target) throw Error('Project moved; remove old hooks manually before reinstalling');
  const existing = await read(target, {});
  const generated = remove ? {hooks:{}} : configuration(profile);
  const merged = mergeConfig(existing, generated, prior?.configuration);
  if (dryRun) return {target, configuration:merged};
  if (remove && !prior) throw Error('No AgentDeck installation manifest; nothing removed');
  if (!same(existing,merged)) {
    try { await fs.copyFile(target, target + `.agentdeck-backup-${Date.now()}`, 1); }
    catch (e) { if (e.code !== 'ENOENT') throw e; }
    await atomic(target,merged);
  }
  if (remove) await fs.rm(manifest, {force:true});
  else await atomic(manifest, {target, configuration:generated});
  return {target, action:remove ? 'removed' : 'installed'};
}
if (process.argv[2] === '--cli') {
  try {
    const [profile, project, ...flags] = process.argv.slice(3);
    console.log(JSON.stringify(await install(profile, project, {remove:flags.includes('--remove'), dryRun:flags.includes('--dry-run')}),null,2));
  } catch (e) { console.error(e.message); process.exitCode = 1; }
}
