import crypto from 'node:crypto';
// Native hook names stay here; transport and the broker remain harness-neutral.
export const profiles = {
  codex: {
    label:'Codex', executable:'codex', config:'.codex/hooks.json', format:'nested',
    events:{SessionStart:'start', SessionEnd:'end', UserPromptSubmit:'busy', PreToolUse:'tool',
      PostToolUse:'result', PermissionRequest:'codex-permission', Stop:'idle', Interrupt:'idle', PreCompact:'busy'},
    questions:['request_user_input'],
  },
  claude: {
    label: 'Claude', executable: 'claude', config: '.claude/settings.local.json', format: 'nested',
    events: {SessionStart:'start', SessionEnd:'end', UserPromptSubmit:'busy', PreToolUse:'tool',
      PostToolUse:'result', PostToolUseFailure:'result', PermissionRequest:'permission',
      Notification:'notification', Stop:'idle', StopFailure:'error', PreCompact:'busy'},
    questions: ['AskUserQuestion'],
  },
  'copilot-cli': {
    label: 'Copilot CLI', executable: 'copilot', config: '.github/hooks/agentdeck-copilot-cli.json', format: 'copilot',
    events: {sessionStart:'start', sessionEnd:'end', userPromptSubmitted:'busy', preToolUse:'tool',
      postToolUse:'result', postToolUseFailure:'result', agentStop:'idle', errorOccurred:'error'},
    questions: [], // CLI payloads do not guarantee paired tool-call IDs.
  },
  'copilot-vscode': {
    label: 'Copilot VS Code', executable: 'code', config: '.github/hooks/agentdeck-copilot-vscode.json', format: 'vscode',
    events: {SessionStart:'start', UserPromptSubmit:'busy', PreToolUse:'tool', PostToolUse:'result',
      Stop:'idle', PreCompact:'busy'}, questions: [],
  },
  gemini: {
    label: 'Gemini', executable: 'gemini', config: '.gemini/settings.json', format: 'nested',
    events: {SessionStart:'start', SessionEnd:'end', BeforeAgent:'busy', BeforeModel:'busy',
      BeforeTool:'tool', AfterTool:'result', AfterAgent:'idle', Notification:'notification', PreCompress:'busy'},
    questions: [],
  },
  cursor: {
    label: 'Cursor CLI', executable: 'agent', config: '.cursor/hooks.json', format: 'cursor',
    events: {sessionStart:'start', sessionEnd:'end', beforeSubmitPrompt:'busy', preToolUse:'tool',
      postToolUse:'result', postToolUseFailure:'result', stop:'idle', preCompact:'busy'}, questions: [],
  },
};

// Allowlist only metadata. Never forward prompts, commands, outputs or transcripts.
export function normalize(profile, event, input) {
  const p = profiles[profile];
  if (!p || !Object.hasOwn(p.events, event) || !input || typeof input !== 'object' || Array.isArray(input)) return null;
  const str = x => typeof x === 'string' && x.length <= 512 ? x : '';
  const session = str(input.session_id || input.sessionId || input.conversation_id);
  if (!session) return null; // Never guess identity from cwd or hook PID.
  return {event, session, tool: str(input.tool_name || input.toolName),
    request: str(input.tool_use_id || input.toolUseId),
    notification: str(input.notification_type), failed: input.status === 'error' || input.status === 'aborted',
    // Only explicit terminal success; an ordinary idle/Stop is never a success claim.
    outcome: input.status === 'error' || p.events[event] === 'error' || /toolusefailure$/i.test(event) ? 'failure'
      : input.status === 'success' && ['Stop','stop','agentStop','AfterAgent'].includes(event) ? 'success' : null};
}

export class HookFacts {
  constructor(profile) {
    if (!profiles[profile]) throw Error('Unknown harness');
    this.profile = profiles[profile]; this.sessions = new Map(); this.seen = false; this.broken = false;
  }
  event(e) {
    const action = this.profile.events[e.event];
    if (!action || typeof e.session !== 'string' || !e.session) return;
    this.seen = true;
    if (e.outcome === 'success' || e.outcome === 'failure') {
      this.outcome = {outcome:e.outcome, outcomeId:e.request
        ? crypto.createHash('sha256').update(JSON.stringify([e.session,e.event,e.request])).digest('hex')
        : crypto.randomUUID()};
    }
    if (action === 'end') { this.sessions.delete(e.session); return; }
    const s = this.sessions.get(e.session) || {status:'unknown', pending:new Set(), detail:'', inputNeeded:false};
    this.sessions.set(e.session, s);
    if (action === 'codex-permission') {
      s.inputNeeded = true; s.status = 'busy'; s.detail = 'Approval requested; count unknown'; return;
    }
    if (['start','idle','busy','result','error'].includes(action)) s.inputNeeded = false;
    if (action === 'notification') {
      // No request ID or resolution event: do not invent a pending count.
      if (e.notification === 'permission_prompt' || e.notification === 'ToolPermission') {
        s.status = 'unknown'; s.detail = 'Permission notification; inspect harness';
      }
      return;
    }
    if (action === 'permission') {
      s.status = 'unknown'; s.detail = 'Permission decision; no paired request ID'; return;
    }
    s.detail = '';
    if (action === 'error' || e.failed) {
      s.status = 'unknown'; s.pending.clear(); s.detail = 'Harness error; inspect terminal';
    } else if (action === 'start' || action === 'idle') {
      s.status = 'idle'; s.pending.clear();
    } else {
      s.status = 'busy';
      if (action === 'busy') s.pending.clear(); // New turn cancels unresolved prior-turn questions.
      if (action === 'tool' && e.request && this.profile.questions.includes(e.tool)) s.pending.add(e.request);
      if (action === 'result' && e.request) s.pending.delete(e.request);
    }
  }
  snapshot() {
    let status = this.seen && !this.broken ? 'idle' : 'unknown', pending = 0, detail = '';
    for (const s of this.sessions.values()) {
      pending += s.pending.size;
      if (s.status === 'unknown') status = 'unknown';
      else if (status !== 'unknown' && s.status === 'busy') status = 'busy';
      if (s.detail) detail = s.detail;
    }
    if (!this.seen) detail = 'Waiting for first harness hook';
    if (this.broken) detail = 'Hook delivery failed; restart managed session';
    const requestIds = [];
    for (const [session, s] of this.sessions) for (const id of s.pending)
      requestIds.push(crypto.createHash('sha256').update(JSON.stringify([session,id])).digest('hex'));
    return {status, pending, detail, pendingKnown:false, ...this.outcome,
      inputNeeded:[...this.sessions.values()].some(s => s.inputNeeded), requestIds};
  }
}
