import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {HookFacts, normalize, profiles} from '../plugins/harnesses/profiles.mjs';
import {configuration, mergeConfig, install} from '../plugins/harnesses/install.mjs';
import {serve} from '../plugins/harnesses/bridge.mjs';

for (const [profile, spec] of Object.entries(profiles)) {
  test(`${profile}: native lifecycle, error, session aggregation, reset`, () => {
    const f = new HookFacts(profile);
    assert.equal(f.snapshot().status, 'unknown');
    const emit = (action, session='s', rest={}) => {
      const event = Object.keys(spec.events).find(k=>spec.events[k]===action);
      if (event) f.event({event, session, ...rest});
    };
    emit('start'); assert.equal(f.snapshot().status, 'idle');
    emit('busy'); assert.equal(f.snapshot().status, 'busy');
    emit('start','other'); assert.equal(f.snapshot().status, 'busy');
    emit('idle','other'); assert.equal(f.snapshot().status, 'busy');
    emit('idle'); assert.equal(f.snapshot().status, 'idle');
    emit('idle','s',{failed:true}); assert.equal(f.snapshot().status, 'unknown');
    emit('busy'); assert.equal(f.snapshot().status,'busy');
    f.broken = true; assert.equal(f.snapshot().status, 'unknown');
  });
  test(`${profile}: configuration + metadata only`, () => {
    assert.deepEqual(Object.keys(configuration(profile).hooks), Object.keys(spec.events));
    const event = Object.keys(spec.events)[0];
    const value = normalize(profile,event,{session_id:'s',prompt:'SECRET',tool_input:{command:'SECRET'},transcript_path:'SECRET'});
    assert.equal(value.session,'s'); assert.ok(!JSON.stringify(value).includes('SECRET'));
    assert.equal(normalize(profile,event,{}),null);
    assert.equal(normalize(profile,'not-real', {session_id:'s'}),null);
  });
}
test('question IDs survive duplicates, concurrent results, cancel and completion', () => {
  const f = new HookFacts('claude');
  const event=(event,request)=>f.event({event,session:'s',request,tool:'AskUserQuestion'});
  event('PreToolUse','q1'); event('PreToolUse','q1'); event('PreToolUse','q2');
  assert.equal(f.snapshot().pending,2);
  event('PostToolUse','q1'); assert.equal(f.snapshot().pending,1);
  event('PostToolUse','unrelated'); assert.equal(f.snapshot().pending,1);
  event('PostToolUseFailure','q2'); assert.equal(f.snapshot().pending,0);
  event('PreToolUse','q3'); event('UserPromptSubmit'); assert.equal(f.snapshot().pending,0);
  event('PreToolUse','q4'); event('Stop'); assert.equal(f.snapshot().pending,0);
  event('PermissionRequest'); assert.equal(f.snapshot().status,'unknown'); assert.equal(f.snapshot().pending,0);
  event('PostToolUse','x'); assert.equal(f.snapshot().status,'busy');
  event('SessionEnd'); assert.equal(f.sessions.size,0);
});
test('normalization accepts native identity spellings without guessing', () => {
  for (const key of ['session_id','sessionId','conversation_id'])
    assert.equal(normalize('cursor','stop',{[key]:'abc'}).session,'abc');
  assert.equal(normalize('claude','Stop',{session_id:123}),null);
});
test('merge preserves unrelated settings/hooks, idempotent upgrade and removal', () => {
  const original={permissions:{deny:['Bash']},hooks:{Stop:[{hooks:[{type:'command',command:'my-existing-hook'}]}]}};
  const a=configuration('claude','/old repo/hook.mjs'), b=configuration('claude','/new repo/hook.mjs');
  const merged=mergeConfig(original,a);
  assert.deepEqual(mergeConfig(merged,a,a),merged);
  const upgrade=mergeConfig(merged,b,a);
  assert.equal(upgrade.hooks.Stop.length,2);
  assert.deepEqual(mergeConfig(upgrade,{hooks:{}},b),original);
  assert.throws(()=>mergeConfig({hooks:{Stop:{}}},a));
  assert.throws(()=>configuration('claude','/tmp/$oops/hook.mjs'));
});
test('installer backups, dry run, uninstall and malformed settings preservation', async () => {
  const dir=await fs.mkdtemp(path.join(os.tmpdir(),'agentdeck install '));
  try {
    const target=path.join(dir,'.claude/settings.local.json');
    await fs.mkdir(path.dirname(target));
    const original='{"permissions":{"deny":["Bash"]}}\n';
    await fs.writeFile(target,original);
    await install('claude',dir,{dryRun:true}); assert.equal(await fs.readFile(target,'utf8'),original);
    await install('claude',dir); await install('claude',dir);
    assert.equal(JSON.parse(await fs.readFile(target,'utf8')).hooks.Stop.length,1);
    assert.ok((await fs.readdir(path.dirname(target))).some(x=>x.includes('backup')));
    await install('claude',dir,{remove:true});
    assert.deepEqual(JSON.parse(await fs.readFile(target,'utf8')).permissions,{deny:['Bash']});
    await fs.writeFile(target,'// JSONC');
    await assert.rejects(install('claude',dir)); assert.equal(await fs.readFile(target,'utf8'),'// JSONC');
  } finally { await fs.rm(dir,{recursive:true,force:true}); }
});
function hook(descriptor, profile, event, value) {
  return new Promise((resolve,reject)=>{
    const child=spawn(process.execPath,['plugins/harnesses/hook.mjs',profile,event],
      {env:{...process.env,AGENTDECK_HOOK_BINDING:descriptor},stdio:['pipe','pipe','pipe']});
    let out='',err=''; child.stdout.on('data',x=>out+=x); child.stderr.on('data',x=>err+=x);
    child.on('error',reject); child.on('close',code=>resolve({code,out,err}));
    child.stdin.end(typeof value==='string'?value:JSON.stringify(value));
  });
}
test('real hook processes -> authenticated relay; concurrent events; silent failure', async () => {
  const dir=await fs.mkdtemp(path.join(os.tmpdir(),'agentdeck-relay-'));
  const descriptor=path.join(dir,'hook.json');
  const service=await serve({profile:'claude',descriptor,root:dir,registration:{id:'test',managed:true}});
  try {
    const d=JSON.parse(await fs.readFile(descriptor,'utf8'));
    assert.equal((await fetch(`http://127.0.0.1:${d.port}/event`,{method:'POST',body:'{}'})).status,403);
    assert.equal((await fetch(`http://127.0.0.1:${d.port}/event`,{method:'POST',headers:{Authorization:`Bearer ${d.token}`,Origin:'https://example.com'},body:'{}'})).status,403);
    const results=await Promise.all(Array.from({length:8},(_,i)=>hook(descriptor,'claude','PreToolUse',
      {session_id:'s',tool_name:'AskUserQuestion',tool_use_id:'q'+i,prompt:'DO NOT FORWARD'})));
    assert.ok(results.every(r=>r.code===0 && r.out==='' && r.err===''));
    assert.equal(service.facts.snapshot().pending,8);
    await hook(descriptor,'claude','PostToolUseFailure',{session_id:'s',tool_use_id:'q1'});
    assert.equal(service.facts.snapshot().pending,7);
    await hook(descriptor,'gemini','BeforeAgent',{session_id:'s'}); // Other globally loaded profile cannot contaminate.
    assert.equal(service.facts.snapshot().pending,7);
    assert.deepEqual(await hook(descriptor,'claude','Stop','bad JSON'),{code:0,out:'',err:''});
    // No broker available here; explicitly sample readSnapshot to pick up loss marker.
    const value=await service.bridge.readSnapshot(); assert.equal(value.status,'unknown');
  } finally { await service.close(); await fs.rm(dir,{recursive:true,force:true}); }
});
