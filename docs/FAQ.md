# AgentStreamDeck frequently asked questions

[Project overview](../README.md) · [Documentation index](README.md)

## Do I need an Elgato plugin or MCP server?

No. AgentStreamDeck controls supported hardware through USB HID and observes native harness plugins/hooks. Quit Elgato's desktop app so it releases the device. See [hardware setup](features/HARDWARE.md).

## Can I launch agents normally?

Yes. Install the broker once, then the OpenCode global plugin or native project hooks. Existing BAT scripts and editor shortcuts can keep launching the harness. [Managed launchers](LAUNCHERS.md) are optional compatibility paths.

## Is there a graphical settings application?

The physical deck is the UI. The current project exposes its customization through [CLI commands](CLI.md) and [JSON settings](reference/CONFIG.md), with preview GIFs and dry-run output.

## Is OpenCode required for Claude, Codex or another agent?

No. `python -m ocdeck install` supports broker startup without OpenCode. Add the profile you use to each software project. See [integrations](integrations/README.md).

## Does green always mean the agent is not waiting for me?

No. Some integrations report activity without complete approval events. Read [coverage and state semantics](features/STATUS.md) before relying on input detection. Unknown pending totals are not converted to zero.

## Can a button approve a tool or answer a question?

Agent buttons request window focus only. Reply in the harness itself. Jelly has separate touch, support-link and explicit update-install interactions documented in the [UI guide](UI.md).

## Can I use a local LLM or a remote inference server?

The integration observes the local coding harness, not the model provider. A local CLI can call your chosen backend if that harness supports its API. AgentStreamDeck does not configure model endpoints, context windows or credentials. Running the CLI itself in SSH/WSL is a separate [unsupported host boundary](REMOTE-AND-WSL.md).

## Does it support larger decks or multiple decks?

Supported Original/MK.2 and XL devices provide 15 and 32 keys. One broker controls one device; use serial selection when several are connected. Additional sessions wait in overflow until a key is free. See [hardware](features/HARDWARE.md).

## Why does an alias show on a different agent later?

Aliases are attached to physical slots, not agent identities. A new session using the slot inherits its appearance override. See [appearance precedence](reference/APPEARANCE.md).

## Can I turn Jelly, thoughts or coffee off independently?

Yes. `jelly.enabled` controls the companion, `jelly.thoughts` controls ambient thought frequency, and `jelly.coffee` controls invitations. Touch messages can still appear with thoughts off. See [Jelly settings](reference/JELLY.md).

## Why is the empty deck not black?

READY and Jelly are enabled by default. Set ready false and jelly.enabled false for an entirely blank unassigned deck. See [config reference](reference/CONFIG.md).

## Does checking for an update install it?

No. Detection shows the notice. Pressing the marked Jelly explicitly installs the detected version. Separately, the installed-version watcher can restart after a pip upgrade you performed. See [updates](features/UPDATES.md).

## Where is the original YouTube demonstration?

[Watch Ryan’s original OpenCode hardware walkthrough](https://www.youtube.com/watch?v=NTWLbLbJiO0). The [gallery](GALLERY.md) also collects the renderer animations, including later Jelly behavior.

## Why does pip say agentstreamdeck but commands say ocdeck?

The distribution was renamed while the Python module, CLI entry point and state-directory compatibility names were retained. See [migration](RENAMING.md).

## Related guides

[First run](FIRST-RUN.md) · [Feature hub](features/README.md) · [Troubleshooting](TROUBLESHOOTING.md)
