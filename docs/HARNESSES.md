# Agent harness adapters

Implemented for Claude Code, GitHub Copilot CLI, GitHub Copilot in VS Code,
Gemini CLI, and Cursor CLI (`agent`). OpenCode's existing plugins continue to work.
These are native lifecycle-hook integrations, not model prompts, MCP tools, or
extensions that require the model to remember to update its status.

For complete installation, upgrade and removal walkthroughs, see [TUTORIALS.md](TUTORIALS.md).
For diagnostics, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## What is supported

| Profile | Native config in the project | Activity | Pending input |
|---|---|---|---|
| `claude` | `.claude/settings.local.json` | Start, prompt, tools, stop, errors, compaction | `AskUserQuestion` tool IDs counted until result/failure/turn end. Permission hooks lack paired IDs: show LINK ? with diagnostic detail. |
| `copilot-cli` | `.github/hooks/agentdeck-copilot-cli.json` | Start, prompt, tools, agent stop, errors | Not reported: no guaranteed paired request IDs in subscribed payloads. |
| `copilot-vscode` | `.github/hooks/agentdeck-copilot-vscode.json` | Start, prompt, tools, stop, compaction | Not reported. VS Code hooks are a preview feature. |
| `gemini` | `.gemini/settings.json` | Start, turn/model/tool activity, stop, compaction | Permission notifications show LINK ?; no invented pending count. |
| `cursor` | `.cursor/hooks.json` | Start, prompt, tools, stop, compaction | Not reported. This launcher targets Cursor CLI, not the Cursor desktop editor. |

All new adapters are **implemented and fixture-tested, awaiting live harness and
Windows hardware validation**. Copilot cloud agent, remote SSH/WSL/containers,
Codex CLI and Aider are not included in this implementation. No remote relay or
approval automation is installed. Native hooks must be available and enabled in
the user's installed harness; record its version when testing.

## Quick start on your existing Windows AgentDeck installation

Keep this checkout in a permanent location (for example `C:\Tools\AgentDeck`).
Hook commands contain its absolute path. Python 3.11+, Node.js 20+ on PATH,
your harness, and a running AgentDeck broker are required. The BAT files use the
existing AgentDeck Python environment and this checkout's source, so you can test
the branch without repointing the original installed broker or OpenCode plugin.

Run these commands in PowerShell, replacing paths with your own:

```powershell
# Install each integration once per software project, preserving other hooks.
C:\Tools\AgentDeck\scripts\Install-Harness.ps1 -Profile claude -Project C:\Projects\MyApp
C:\Tools\AgentDeck\scripts\Install-Harness.ps1 -Profile copilot-cli -Project C:\Projects\MyApp

# Start agents from the software project directory, each in its own window.
cd C:\Projects\MyApp
C:\Tools\AgentDeck\scripts\Launch-Claude.bat
C:\Tools\AgentDeck\scripts\Launch-Copilot.bat
```

For Gemini and Cursor, repeat with `-Profile gemini` / `-Profile cursor`, and
`Launch-Gemini.bat` / `Launch-Cursor.bat`. Arguments after a BAT launcher are passed
to the harness. Use the Python command below for an explicit executable path.
Continue launching OpenCode as before. All harnesses share the existing six-slot
registry and overflow policy.

To preview installation without writing settings, add `-DryRun`. To remove just
AgentDeck's entries, use the same install command with `-Remove`. Existing settings
and other hooks are preserved; changed config files receive timestamped
`.agentdeck-backup-*` copies. JSONC/malformed settings are refused, not rewritten.
Receipts live in the software project's `.agentdeck/` directory. Keep them until
uninstalling. Add receipts, backups and machine-specific hook settings to that
project's local git excludes if they should not be shared. Reinstall after moving
the AgentDeck checkout; if you move the software project, remove the old hook
entries and receipt manually, then reinstall. Do not restore a whole backup over
subsequent unrelated edits.

On Windows, use an install path without `"`, `$`, backticks, `%`, or `!`; the
installer refuses these characters to avoid shell expansion. Paths with spaces
are supported. Do not move/delete this checkout while hooks refer to it.

## Python CLI / clean test environment

From this checkout, install dependencies once:

```text
python -m pip install -e .
python -m ocdeck broker --mock
```

Keep the mock broker running in one terminal, then use another terminal:

```text
python -m ocdeck harness-install claude --project /path/to/project --dry-run
python -m ocdeck harness-install claude --project /path/to/project
```

Change into that project before launching:

```text
python -m ocdeck harness-launch --profile claude --current-window -- --resume
python -m ocdeck harness-launch --profile copilot-cli --executable /path/to/copilot --current-window
python -m ocdeck status
```

Use your actual executable paths and supported harness arguments. `--current-window`
runs in the current terminal and propagates the harness exit code; window focus is
not guaranteed in this mode. On Windows, omitting it uses a dedicated Windows
Terminal window with exact title matching. Linux/macOS support status testing,
not physical device focus. For real USB use, stop the mock broker and start the
existing installed broker, or run `python -m ocdeck broker` after following the
existing Elgato ownership instructions. Never run two brokers against one device.

`harness-launch` does not automatically edit settings. Without installation and
enabled hooks, the slot remains LINK ? with “Waiting for first harness hook”.
Launching `claude`/`copilot` directly does not attach: use the managed launcher.
Globally installed hooks are deliberately inert outside a matching managed launch.

## Copilot in VS Code (preview)

```powershell
C:\Tools\AgentDeck\scripts\Install-Harness.ps1 -Profile copilot-vscode -Project C:\Projects\MyApp
cd C:\Projects\MyApp
C:\Tools\AgentDeck\scripts\Launch-Copilot-VSCode.bat
```

This starts a **separate VS Code application with a new user-data directory per
launch**, so it cannot reuse another application's stale environment. Install or
enable GitHub Copilot as needed, sign in, trust the project through VS Code's normal
flow, and verify the generated hooks appear in **Chat: Configure Hooks**. This test
profile does not inherit your usual editor settings/authentication. Close its
window to end the launch. Its data is kept under
`~/.opencode-deck/editors/<launch-id>`; you may delete that directory after closing
that instance. Never put the generated hook connection token in settings.

The isolated editor's `window.title` is set to its exact AgentDeck identity. Its
launcher terminal has a different title, so the existing Windows focus adapter
can target the editor without choosing between two matching windows. A workspace
`window.title` override or an OS-added title suffix can prevent matching; verify
physical focus on Windows. No existing user/workspace settings are rewritten by
the launcher. All chat sessions in this editor launch share one key. Ordinary
already-running VS Code windows are not instrumented by this launcher.

VS Code and Copilot CLI can discover each other's hook files (and Claude-format
files). Each hook checks the managed launch's profile, so unrelated adapters do
nothing. Keep all profile event names in the generated format.

## State semantics and limitations

- One managed launch, one verified supervisor PID + creation time, one stable
  producer UUID, one key. Nested sessions inheriting that launch's environment
  aggregate into the same key. Separately launched agents get separate keys.
- Before the first valid hook, status is unknown. After a valid lifecycle event,
  the adapter retains the last observed state and heartbeats every two seconds.
  A real broker restart restores the full state, including unresolved questions.
- `PostToolUse` means the loop can continue; it remains running, not idle. Turn
  stop means idle; subagent completion is not mistaken for parent completion.
- Stop hooks run before other hooks may request continuation. Status can briefly
  show idle until the next activity event. These adapters cannot poll an
  authoritative harness state endpoint to reconcile missed events.
- Missing/disabled hooks in the middle of a session cannot always be detected:
  last observed state may persist. Detected malformed payloads, missing session
  IDs, or delivery failures latch unknown until you restart the managed launch.
  Bridge failure stops heartbeats, allowing the existing ten-second stale timeout.
- The pending counter tracks only identified unresolved Claude question tool calls.
  Other adapters may still show running while an approval is open. They do not
  promise OpenCode's complete approval coverage. Check the capability table above.
- Hooks never return allow/deny/continue/retry decisions. They exit zero even on
  relay failure. Gemini receives an empty JSON object; other profiles emit no
  stdout. Node itself must be installed and executable for this behavior.

## Implementation and extension points

`plugins/harnesses/profiles.mjs` owns native event names, payload normalization and
state reduction. `hook.mjs` is the short-lived stdin observer. `bridge.mjs` keeps a
persistent `Bridge` imported from `plugins/core.mjs`; it does not duplicate broker
HTTP/auth/discovery/sequence logic. `ocdeck/harness.py` owns launch, identity and
cleanup, using the same process identity and exact window-title rules as OpenCode.
The broker, registry, device, focus and existing OpenCode plugin are unchanged.

The per-launch relay binds only `127.0.0.1`, uses a random bearer token, rejects
browser Origin headers, and caps messages at 8 KiB. The hook reads at most 4 MiB
from stdin and forwards only session/tool IDs, event/tool names, notification type
and an error flag. Prompts, commands, arguments, file contents, tool results and
transcripts are not forwarded or logged. A failed-delivery marker contains only
`1`. Normal shutdown deletes the connection descriptor and launch state. On an
abrupt parent exit, stdin EOF stops the bridge and the broker's process-death sweep
reclaims the key. Windows token/descriptor protection relies on the existing
per-user ACL secured by the original installer.

To add another harness, add a profile with verified native hooks and tests. Do not
fabricate activity from text output or register short-lived hook PIDs as agents.
Use a real SDK adapter when a harness supplies better state/approval APIs.

## Live acceptance checklist

Run `scripts/Test.ps1` first. Then, for each installed harness:

1. Record harness, Node, Python and Windows Terminal versions; inspect its hooks UI
   or diagnostics to confirm the generated file loads.
2. Launch from a project, submit a coding task and see idle -> running -> idle.
   Ask for a text-only answer too; this catches missing turn-completion hooks.
3. Claude: request an interactive question, confirm input, answer/cancel, confirm
   it clears. For approval prompts, check the documented limited behavior above.
4. Launch two agents in the same project plus an OpenCode instance. Confirm three
   stable keys and correct window focus. Try minimized-window restoration.
5. Restart the broker while an agent is running / a Claude question is unresolved.
   Confirm the same launch returns with its current state and no duplicate key.
6. Close the harness, interrupt it, disconnect/reconnect USB and verify cleanup.
7. Uninstall the hooks and confirm unrelated hook commands/settings remain.

This authoring environment cannot verify native harness loading, account login,
Windows BAT/PowerShell execution, physical USB, or foreground activation.

## Contract sources

Event/config mappings were checked against these official references on 2026-09-09:

- [Claude Code hooks](https://code.claude.com/docs/en/hooks)
- [GitHub Copilot CLI hooks](https://docs.github.com/en/copilot/reference/hooks-reference)
- [VS Code agent hooks](https://code.visualstudio.com/docs/agent-customization/hooks)
- [Gemini CLI hooks](https://geminicli.com/docs/hooks/reference/)
- [Cursor hooks](https://cursor.com/docs/hooks)


## 2.1 additions

See [the 2.1 feature guide](NEXT.md) for larger decks, Codex, alerts, doctor/report,
appearance import/export, dry-run and complete integration uninstall.
