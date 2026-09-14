import test from 'node:test';
import assert from 'node:assert/strict';
import {reviewPermission, permissionReply, claudeDecision} from '../plugins/permissions.mjs';

test('native responses grant once and never change permission policy', async () => {
  assert.throws(() => permissionReply({}, {id:'r',sessionID:'s'}, 'always', '/repo'), /Invalid decision/);
  assert.deepEqual(claudeDecision('allow'), {hookSpecificOutput:{hookEventName:'PermissionRequest',decision:{behavior:'allow'}}});
  const seen=[];
  await permissionReply({permission:{reply:async x=>seen.push(x)}}, {id:'r',sessionID:'s'}, 'allow','/repo');
  assert.deepEqual(seen,[{requestID:'r',directory:'/repo',reply:'once'}]);
  await permissionReply({postSessionByIdPermissionsByPermissionId:async x=>seen.push(x)}, {id:'r',sessionID:'s'}, 'deny','/repo');
  assert.deepEqual(seen[1],{path:{id:'s',permissionID:'r'},query:{directory:'/repo'},body:{response:'reject'}});
});

test('one-shot handoff finishes only after native apply succeeds', async () => {
  const calls=[], applied=[];
  const call=async(method,route,body)=>{
    calls.push({route,body});
    if(route.endsWith('/control-capabilities')) return {permissions:true};
    if(route.endsWith('/offer')) return {enabled:true,ticket:'t'};
    if(route.endsWith('/poll')) return {state:'decision',decision:'allow'};
    return {};
  };
  assert.equal(await reviewPermission(call,{owner:'a',tool:'Bash'},async d=>applied.push(d)),true);
  assert.deepEqual(applied,['allow']);
  assert.deepEqual(calls.at(-1).body,{ticket:'t',ok:true});
});

test('cancelled, disabled, terminal, lost response, and failed apply never retry approval', async () => {
  for (const scenario of ['cancel','disabled','terminal','lost','failed']) {
    let applies=0;
    const call=async(method,route)=>{
      if(route.endsWith('/control-capabilities')) return {permissions:scenario!=='disabled'};
      if(route.endsWith('/offer')) return {enabled:scenario!=='disabled',ticket:'t'};
      if(route.endsWith('/poll')) {
        if(scenario==='lost') throw Error('lost response');
        return {state:'decision',decision:scenario==='terminal'?'terminal':'allow'};
      }
      return {};
    };
    assert.equal(await reviewPermission(call,{owner:'a',tool:'Bash'},async()=>{
      applies++; if(scenario==='failed') throw Error('SDK error');
    },()=>scenario!=='cancel'),false);
    assert.equal(applies,scenario==='failed'?1:0);
  }
});
