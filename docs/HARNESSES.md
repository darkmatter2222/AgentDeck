# Agent harness adapters

AgentStreamDeck is **plugin-first**. The broker runs independently in the background, and supported harnesses report lifecycle metadata through their native plugin or hook mechanisms. AgentStreamDeck does not need to launch the harness.

For the shortest setup path, see [Plugin-first setup](PLUGIN-FIRST.md). For diagnostics, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Supported integrations

| Profile | Native config | Activity | Pending input |
|---|---|---|---|
| OpenCode | Global AgentStreamDeck server plugin | Sessions, tools, idle/running, permissions/questions | Known permission/question IDs when available |
| `codex` | `.codex/hooks.json` | Start, prompt, tools, stop, interrupt, compaction | Approval requests show INPUT with unknown count; paired `request_user_input` IDs can be tracked |
| `claude` | `.claude/settings.local.json` | Start, prompt, tools, stop, errors, compaction | `AskUserQuestion` IDs are tracked; unpaired permission hooks remain unknown |
| `copilot-cli` | `.github/hooks/agentdeck-copilot-cli.json` | Start, prompt, tools, stop, errors | Activity only where the native payload does not expose paired request IDs |
| `copilot-vscode` | `.github/hooks/agentdeck-copilot-vscode.json` | Start, prompt, tools, stop, compaction | Activity only; VS Code hooks remain a preview integration |
| `gemini` | `.gemini/settings.json` | Start, turn/model/tool activity, stop, compaction | Permission notifications remain unknown rather than inventing a count |
| `cursor` | `.cursor/hooks.json` | Start, prompt, tools, stop, compaction | Activity only; this profile targets Cursor CLI (`agent`) |

Hooks never approve, deny, answer, retry, or type into a harness. They are observers only.

## 1. Install AgentStreamDeck once

```text
python -m pip install --upgrade agentstreamdeck
ocdeck install
```

`ocdeck install` performs the explicit operating-system setup that `pip` itself should not do:

- **Windows:** creates and starts the per-user **AgentStreamDeck Broker** Scheduled Task at interactive logon.
- **Linux:** creates, enables, and starts `agentstreamdeck.service` as a systemd user service.
- **OpenCode:** installs the global server plugin automatically when `opencode` is already on PATH.

`scripts/Install.ps1` combines the package-install and `ocdeck install` steps for Windows.

## 2. Install a native hook in each software project

From the project directory:

```text
ocdeck harness-install claude
ocdeck harness-install codex
ocdeck harness-install copilot-cli
ocdeck harness-install copilot-vscode
ocdeck harness-install gemini
ocdeck harness-install cursor
```

Install only the profiles you use. To preview a change:

```text
ocdeck harness-install claude --dry-run
```

To remove one profile:

```text
ocdeck harness-install claude --remove
```

The installer merges AgentStreamDeck-owned hook entries into existing configuration, preserves unrelated hooks/settings, writes timestamped backups when it changes a config file, and records ownership in the project's `.agentdeck/` receipt directory.

## 3. Launch the harness normally

After the hook/plugin is installed, use whatever launch method you already use:

```text
claude
codex
copilot
gemini
agent
opencode
```

A BAT/CMD file, PowerShell script, HomeAILab launcher, local-model wrapper, IDE shortcut, or another parent process is also fine. The short-lived native hook process reads the local broker discovery/token files and sends normalized lifecycle metadata directly to the broker over authenticated loopback HTTP.

`ocdeck start`, `ocdeck harness-launch`, and the legacy `Launch-*.bat` files remain compatibility/testing helpers. They are **not required** for normal monitoring.

## Direct hook lifetime

Each native hook event includes a harness-native session ID. The broker derives a stable local record from the profile/session pair, verifies the hook's parent process identity, and captures the containing visible Windows window when possible. Event-driven records remain current between hook events while their verified process remains alive; they are not forced stale merely because no two-second heartbeat is present.

The direct hook payload is deliberately bounded. It carries lifecycle fields such as profile, event/action, session ID, tool/request identity, status flags, process identity, and working directory. Prompts, commands, tool arguments, file contents, tool results, model responses, and transcripts are not forwarded to the broker.

The older per-launch Node relay still exists only for compatibility with managed-launcher workflows. If `AGENTDECK_HOOK_BINDING` is present, the hook can use that relay. Otherwise, the normal path is direct-to-broker delivery.

## Window focus and Stream Deck buttons

On Windows, the broker records the visible window owned by the harness process or its nearest process ancestor. This matters for Windows Terminal, where the CLI process does not own the top-level window itself. Pressing the assigned Stream Deck key asks Windows to restore and focus that captured window.

For deterministic one-touch focus, keep one monitored harness per OS window. Several tabs inside one Windows Terminal process can be inherently ambiguous because Windows exposes the shared top-level window, not a unique HWND per terminal tab.

Run:

```text
ocdeck status --json
```

Useful fields include:

- `device.input_events`: count of physical Stream Deck key down/up reports seen by the broker.
- `device.last_input`: most recent physical key event.
- `lastFocus`: most recent focus attempt and diagnostic result.

If `input_events` does not increase when you press a key, troubleshoot USB/HID ownership first. If it increases but `lastFocus` fails, the HID path is working and the remaining issue is window mapping or Windows foreground policy.

## State semantics and limitations

- Native hooks are event-driven. The last trustworthy state is retained while the verified harness process is alive.
- `PostToolUse` means work may continue; it is not treated as idle.
- A native turn/stop event can mark idle, but missed hooks cannot always be reconstructed because most harnesses do not expose an authoritative state API.
- Pending counts are shown only when the native payload contains stable paired request IDs. Unknown is never converted to zero.
- Codex approvals can be observed with an unknown count. Review and trust the installed hooks with Codex's `/hooks` UI.
- Claude `AskUserQuestion` calls have paired IDs and can be tracked until result/failure/turn end. Unpaired permission events remain unknown.
- Hook commands exit zero and never return approval decisions. Gemini receives the expected empty JSON response.
- Node.js 20+ must be available for the JavaScript hook commands.
- Remote SSH/WSL/container sessions need the explicit host boundary described in [REMOTE-AND-WSL.md](REMOTE-AND-WSL.md).

## Copilot in VS Code

Install the `copilot-vscode` profile in the workspace/project and launch VS Code normally. Verify the generated hook in **Chat: Configure Hooks**. This integration is still considered preview because native VS Code hook behavior can vary by installed version and workspace trust state.

## Ask your AI harness to install itself

You can give any coding agent this instruction:

```text
Go to https://github.com/darkmatter2222/AgentStreamDeck and follow the current README plus docs/PLUGIN-FIRST.md and docs/HARNESSES.md. Install/upgrade AgentStreamDeck from PyPI, run `ocdeck install` so its broker starts automatically, then install the native AgentStreamDeck hook/plugin for the harnesses I use. Preserve all unrelated existing hook/settings entries. Do not require an AgentStreamDeck launcher. Verify the broker with `ocdeck status --json` and verify that device.input_events changes when I press a physical Stream Deck key.
```

## Live acceptance checklist

After CI passes, verify locally with the real harnesses and device:

1. Run `ocdeck status --json` and confirm the broker/device are online.
2. Press a physical key and confirm `device.input_events` increments.
3. Launch each harness normally from an instrumented project and confirm a stable slot appears.
4. Minimize the containing window, press its assigned key, and confirm it restores/focuses.
5. Run two harnesses in separate OS windows and confirm each key focuses the correct one.
6. Trigger a Claude question or Codex approval and verify the documented INPUT/unknown behavior.
7. Restart the broker and confirm active event-driven records recover on the next native event without duplicate slots.
8. Close the harness and verify the process sweep or session-end hook releases its slot.
9. Uninstall a hook and confirm unrelated config entries remain.

## Contract sources

Event/config mappings were checked against these official references on 2026-09-09:

- [Claude Code hooks](https://code.claude.com/docs/en/hooks)
- [GitHub Copilot CLI hooks](https://docs.github.com/en/copilot/reference/hooks-reference)
- [VS Code agent hooks](https://code.visualstudio.com/docs/agent-customization/hooks)
- [Gemini CLI hooks](https://geminicli.com/docs/hooks/reference/)
- [Cursor hooks](https://cursor.com/docs/hooks)
