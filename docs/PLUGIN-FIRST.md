# Plugin-first setup

[Project overview](../README.md) · [Documentation index](README.md)

AgentStreamDeck does not need to launch your AI harness. The broker is a per-user background process, and each supported harness reports lifecycle metadata through its native plugin or hook system.

## 1. Install the broker

```text
python -m pip install --upgrade agentstreamdeck
ocdeck install
```

On Windows, `ocdeck install` creates and starts the per-user **AgentStreamDeck Broker** Scheduled Task at interactive logon. On Linux, it creates and enables the `agentstreamdeck.service` systemd user service. OpenCode's global server plugin is installed automatically when `opencode` is already on PATH.

A normal `pip install` intentionally does not make operating-system startup changes by itself. The explicit `ocdeck install` step performs that one-time user-level registration. `scripts/Install.ps1` combines both commands for Windows users who prefer one setup script.

## 2. Install harness hooks

From the software project you work in:

```text
ocdeck harness-install claude
ocdeck harness-install codex
ocdeck harness-install copilot-cli
ocdeck harness-install copilot-vscode
ocdeck harness-install gemini
ocdeck harness-install cursor
```

Install only the profiles you use. Existing configuration is merged, unrelated hooks are preserved, and AgentStreamDeck writes backups and receipts before changes.

## 3. Launch normally

Start `claude`, `codex`, `copilot`, `gemini`, `agent`, VS Code, OpenCode, your own BAT file, or a local-model wrapper exactly as you normally would. Native hook processes authenticate to the local broker over loopback and send bounded lifecycle metadata directly to it. Prompts, tool output, and transcripts are not forwarded.

The old `ocdeck start`, `harness-launch`, and `Launch-*.bat` paths remain optional compatibility helpers. They are not required for monitoring.

## 4. Verify physical buttons

Run `ocdeck status`. The `device.input_events` counter increments for physical key down and key up reports, and `device.last_input` shows the most recent event. This separates a USB/HID input problem from a window-focus problem immediately.

On Windows, pressing an assigned agent key restores and focuses the captured containing window. For reliable one-touch focus, keep one monitored harness per OS window. Several tabs that all share one Windows Terminal process cannot always be distinguished by Windows APIs.

## Ask an AI harness to configure itself

You can give a coding agent this instruction:

```text
Go to https://github.com/darkmatter2222/AgentStreamDeck and follow the current README and docs/HARNESSES.md. Install AgentStreamDeck from PyPI, run `ocdeck install` so the broker starts automatically, then install the native AgentStreamDeck plugin or hook for the harnesses I use. Preserve my existing harness configuration. Do not require an AgentStreamDeck launcher; I want to start each harness normally. Verify the setup with `ocdeck status` and the physical button test.
```

## Related guides

[First-run verification](FIRST-RUN.md) · [Integration guides](integrations/README.md) · [Startup controls](features/STARTUP.md)

[Project overview](../README.md) · [Documentation index](README.md) · [Feature hub](features/README.md) · [CLI reference](CLI.md)
