# First run: install AgentStreamDeck and verify your first agent

[Project overview](../README.md) · [Documentation index](README.md)

Get from a connected deck to your first live coding-agent key. Normal installation needs no Git checkout, managed launcher or Elgato plugin.

## Requirements

| Component | Requirement |
|---|---|
| Python | 3.11 or newer |
| Node.js | 20 or newer for native hook commands |
| Coding harness | Install your chosen CLI/editor separately |
| Device | Supported Mini, Original/MK.2 or XL; one per broker |
| Windows | Reference desktop for USB and window focus |
| Linux | Broker/systemd and rendering support; no desktop focus |

Quit Elgato Stream Deck from the tray before opening hardware. Use your normal desktop account.

## Install once

```powershell
python -m pip install --upgrade agentstreamdeck
python -m ocdeck install
python -m ocdeck status --json
```

The second command registers the background startup task/service and starts the broker. If OpenCode is on PATH, it also installs the global OpenCode plugin. If it is not, you can still use any native-hook profile. The module name remains ocdeck even though the package name is agentstreamdeck.

Windows users with a checkout can alternatively run `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Install.ps1`. The current script accepts only `-Python` for a different interpreter. Old instructions using -OpenCodePath or -ConfigDirectory with that script do not apply.

## Connect a coding agent

OpenCode: launch opencode normally after the global plugin is installed. Other harnesses: install only the profile you use in each software project, then launch normally:

```powershell
cd C:\Projects\MyApp
python -m ocdeck harness-install claude
claude
```

Substitute codex, copilot-cli, copilot-vscode, gemini or cursor. Their executable names and native trust steps are in the [integration hub](integrations/README.md). For example, Codex uses /hooks for reviewing/trusting the installed hooks; VS Code uses Chat: Configure Hooks. Restart already-open sessions after installing hooks.

## Verify the real workflow

1. Confirm status shows a real online device, not mock mode.
2. Launch an instrumented harness and send a task; observe its running key.
3. Wait for native turn end and observe idle where supported.
4. Trigger a supported input request and verify the profile's documented semantics.
5. Switch away, press the agent key, and confirm the correct Windows window and keyboard focus return.
6. Minimize the window and repeat. Use one monitored session per OS window.
7. Close the harness and confirm its slot is released. Jelly can reclaim unused keys.

Check device.input_events to prove that a physical press reached the broker. A successful CLI focus command alone does not verify USB input. Use [doctor and reports](features/DIAGNOSTICS.md) if any step fails.

## First customization

```powershell
python -m ocdeck preview --preset studio --output studio.gif
python -m ocdeck appearance --preset studio
```

Restart the broker to apply the saved appearance. The [startup guide](features/STARTUP.md) contains Windows and Linux restart commands. [Jelly](JELLY.md) is enabled by default; use its settings guide for quieter motion or no coffee invitations.

## Related guides

[Integration setup](integrations/README.md) · [UI controls](UI.md) · [CLI](CLI.md) · [Hardware](features/HARDWARE.md) · [Troubleshooting](TROUBLESHOOTING.md)
