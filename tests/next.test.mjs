import test from 'node:test';
import assert from 'node:assert/strict';
import {Facts} from '../plugins/core.mjs';
import {HookFacts,normalize} from '../plugins/harnesses/profiles.mjs';
import {configuration} from '../plugins/harnesses/install.mjs';

test('OpenCode identities are hashed, stable and independently cleared',()=>{
  const facts=new Facts();
  const emit=(type,id)=>facts.event({type,properties:{sessionID:'secret-session',id,requestID:id}});
  emit('question.asked','secret-request');
  emit('permission.asked','permission-id');
  const first=facts.snapshot();
  assert.equal(first.pending,2); assert.equal(first.pendingKnown,true);
  assert.equal(first.requestIds.length,2);
  assert.ok(first.requestIds.every(x=>/^[0-9a-f]{64}$/.test(x)));
  assert.ok(!JSON.stringify(first).includes('secret-'));
  emit('question.asked','secret-request'); assert.deepEqual(first,facts.snapshot());
  emit('question.replied','secret-request'); assert.equal(facts.snapshot().requestIds.length,1);
});
test('Codex approvals have unknown counts and hooks never decide',()=>{
  const facts=new HookFacts('codex');
  facts.event(normalize('codex','SessionStart',{session_id:'s'}));
  facts.event(normalize('codex','UserPromptSubmit',{session_id:'s',prompt:'secret prompt'}));
  assert.equal(facts.snapshot().status,'busy');
  facts.event(normalize('codex','PermissionRequest',{session_id:'s',tool_input:{command:'secret'}}));
  assert.equal(facts.snapshot().inputNeeded,true);
  assert.equal(facts.snapshot().pendingKnown,false);
  assert.equal(facts.snapshot().pending,0);
  facts.event(normalize('codex','PostToolUse',{session_id:'s',tool_use_id:'t'}));
  assert.equal(facts.snapshot().inputNeeded,false);
  facts.event(normalize('codex','Stop',{session_id:'s'}));
  assert.equal(facts.snapshot().status,'idle');
  assert.equal(configuration('codex').hooks.SessionEnd[0].hooks[0].timeout,3);
});
test('metadata normalization strips randomized credentials from body fields',()=>{
  for(let n=0;n<100;n++){
    const secret=`test-secret-${n}`;
    const value=normalize('codex','PreToolUse',{session_id:'s',tool_use_id:'t',tool_name:'Bash',
      prompt:secret,tool_input:{command:secret},token:secret,transcript_path:secret});
    assert.ok(!JSON.stringify(value).includes(secret));
  }
});
