// One ephemeral broker ticket per native request; no background auto-approval.
import {setTimeout as delay} from 'node:timers/promises';

export async function reviewPermission(call, {owner, tool, summary}, apply, isPending = () => true) {
  let ticket;
  let completed = false;
  try {
    const capabilities = await call('GET', '/v1/control-capabilities');
    if (!capabilities.permissions) return false;
    const offered = await call('POST', '/v1/permissions/offer', {owner, tool, summary});
    if (!offered.enabled) return false;
    ticket = offered.ticket;
    const deadline = Date.now() + 115000;
    while (Date.now() < deadline && isPending()) {
      const reply = await call('POST', '/v1/permissions/poll', {ticket});
      if (reply.state === 'decision') {
        if (!isPending() || reply.decision === 'terminal') return false;
        if (!['allow', 'deny'].includes(reply.decision)) return false;
        await apply(reply.decision);
        completed = true;
        return true;
      }
      if (reply.state !== 'pending') return false;
      await delay(350);
    }
  } catch {
    // A lost response is never retried as a new approval. Native UI remains authoritative.
  } finally {
    if (ticket) {
      try { await call('POST', '/v1/permissions/finish', {ticket, ok:completed}); } catch {}
    }
  }
  return false;
}

export function claudeDecision(decision) {
  if (!['allow', 'deny'].includes(decision)) throw Error('Invalid decision');
  return {hookSpecificOutput:{hookEventName:'PermissionRequest', decision:{behavior:decision,
    ...(decision === 'deny' ? {message:'Rejected on Stream Deck'} : {})}}};
}

export function permissionReply(client, request, decision, directory) {
  if (!['allow', 'deny'].includes(decision)) throw Error('Invalid decision');
  const response = decision === 'allow' ? 'once' : 'reject';
  if (typeof client.permission?.reply === 'function') {
    return client.permission.reply({requestID:request.id, directory, reply:response});
  }
  if (typeof client.postSessionByIdPermissionsByPermissionId === 'function') {
    return client.postSessionByIdPermissionsByPermissionId({
      path:{id:request.sessionID, permissionID:request.id}, query:{directory}, body:{response}});
  }
  throw Error('OpenCode SDK has no supported permission reply method');
}
