# GitHub Copilot in VS Code Stream Deck integration

[Project overview](../../README.md) · [Documentation index](../README.md)

Use GitHub Copilot in VS Code with a physical Stream Deck status key and Windows window switching. Install the broker once and this profile in each project you want to monitor. OpenCode is not a prerequisite.

## Install and launch

Requires Python 3.11+, Node.js 20+ on PATH and the native harness installed separately.

```powershell
python -m pip install --upgrade agentstreamdeck
python -m ocdeck install
cd C:\Projects\MyApp
python -m ocdeck harness-install copilot-vscode --dry-run
python -m ocdeck harness-install copilot-vscode
code
```

The installer merges `.github/hooks/agentdeck-copilot-vscode.json` and records ownership in `.agentdeck/copilot-vscode.json`. It preserves unrelated hooks/settings and writes a backup before changing an existing config. JSONC requires manual reconciliation; the installer refuses to silently strip comments. Restart an already-running harness so it loads new hooks.

## What the key tells you

This is a preview integration for VS Code agent hooks. Open **Chat: Configure Hooks** and verify the generated workspace hooks and trust state. Activity reporting does not guarantee approval detection. Multiple chats/tabs share an editor window, so one-touch focus selects the window, not an exact chat.

Public hook slots expose `pending: null` because a complete pending total is unknown. Normal start/turn-end events establish idle, prompt/tool activity establishes running, and absent or untrustworthy state remains unknown. Post-tool events do not mean the entire agent is idle.

## Exact installed event mapping

These are the mappings shipped by this repository, not a guarantee that every installed upstream harness version emits each event.

| Native event | Adapter action |
|---|---|
| `SessionStart` | `start` |
| `UserPromptSubmit` | `busy` |
| `PreToolUse` | `tool` |
| `PostToolUse` | `result` |
| `Stop` | `idle` |
| `PreCompact` | `busy` |

## Verify and troubleshoot

1. Run `python -m ocdeck status --json` and confirm the broker and device respond.
2. Start a new session from the instrumented project; send a small task and observe running then idle.
3. Use a separate OS window for each monitored session. Press its key and check that the correct window receives focus.
4. Check `device.input_events` before and after a physical press. A rising counter distinguishes USB input from window-mapping problems.
5. Close the session and confirm its slot disappears after session-end delivery or confirmed process death.

If the key never appears, run `python -m ocdeck doctor --project C:\Projects\MyApp --no-device` and check Node, the native config, the receipt, native hook trust and whether hooks can read the broker user's discovery directory. Remote/WSL PIDs cannot register as local Windows processes.

## Update or remove this integration

Rerun the install command after adapter updates, then restart the harness. To remove only this profile:

```powershell
python -m ocdeck harness-install copilot-vscode --project C:\Projects\MyApp --remove --dry-run
python -m ocdeck harness-install copilot-vscode --project C:\Projects\MyApp --remove
```

If a project was moved, the absolute path recorded in its receipt can block changes. Reconcile the old owned hook entries and receipt before reinstalling; preserve unrelated user configuration.

Source: [native profiles](../../plugins/harnesses/profiles.mjs), [installer](../../plugins/harnesses/install.mjs), [direct event reducer](../../ocdeck/direct_hooks.py).

## Related guides

[All integrations](README.md) · [Status semantics](../features/STATUS.md) · [Window focus](../features/FOCUS.md) · [Troubleshooting](../TROUBLESHOOTING.md) · [Remote boundaries](../REMOTE-AND-WSL.md)
