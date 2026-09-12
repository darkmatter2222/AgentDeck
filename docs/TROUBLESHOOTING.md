# Troubleshooting AgentStreamDeck

Start with `ocdeck status`, or invoke `-m ocdeck status` with the installed Python
interpreter if no shim exists. Record harness, Python, Node and Windows Terminal
versions. Inspect `%USERPROFILE%\.opencode-deck\broker.log` and native harness hook
diagnostics. Do not share bearer tokens, hook.json connection descriptors, prompts
or provider credentials. A screenshot of a key cannot diagnose hook loading alone.

| Symptom | Check / action |
|---|---|
| No device or flickering/overwritten keys | Release this Mini in Elgato; stop other HID controllers. Check `device.online`, `device.mock`, USB connection and selected serial. |
| Broker unavailable | Start the installed `OpenCode Deck` task or your foreground broker. Discovery uses a dynamic port; do not hard-code one. |
| No key for Claude/Copilot/etc. | Install the right profile in the software project, then use its BAT/managed launcher from that directory. Direct CLI launches do not attach. Check overflow if six slots are occupied. |
| LINK ?: Waiting for first harness hook | Check `node --version` (20+), config file location, native hooks enabled/trusted, and the managed launcher's working directory. Submit a prompt; a version may not emit a startup hook. |
| LINK ?: Hook delivery failed | A hook could not parse/deliver metadata or lacked a session ID. Correct the native config/runtime problem, then restart the managed launch to clear its failure latch. |
| LINK ? during a permission prompt | Expected for recognized notifications without paired request IDs. This integration observes approvals; it never supplies approval decisions. |
| Running while waiting for approval | Expected for adapters without approval coverage. The absence of red is not proof the agent is unblocked. See HARNESSES.md. |
| Idle/running persists incorrectly | Missing/disabled hooks may leave the last observed state. Check prompt/tool/stop hooks in the native runtime. Bridge heartbeats alone cannot detect every lost event. |
| Broker restarted but no state returns | Ensure the managed supervisor and Node bridge still run and can read discovery/token. A crashed bridge needs a new managed launch. |
| Key focuses nothing or reports ambiguity | Use a dedicated managed window; verify its exact title and `lastFocus`. Current-window launches and multiple panes are not exact-focus integrations. |
| Correct target found but foreground denied | Windows foreground/elevation rules can refuse focus. Run agents and broker as the same desktop user and verify minimized-window behavior. Do not disable PID identity checks. |
| VS Code asks for sign-in / lacks settings | Its launcher intentionally creates new user data per launch to inherit the current bridge connection. Enable Copilot and sign in in that instance. |
| VS Code hook activity missing | Inspect Chat: Configure Hooks, workspace trust and hook enablement. The ordinary existing VS Code instance is not instrumented. |
| VS Code focus ambiguous/absent | The isolated user profile sets `window.title`; workspace overrides or OS title suffixes can change it. The launcher terminal must retain its distinct `launcher` suffix. |
| Installer refuses JSONC/settings | Preserve the file. Manually reconcile comments/format into valid JSON if appropriate; do not delete unrelated configuration. `--dry-run` shows intended entries for valid JSON. |
| Installer says project moved | Remove the old AgentStreamDeck entries and receipt manually, preserving unrelated hooks, then reinstall at the new location. |
| PowerShell script execution blocked locally | For a trusted downloaded checkout, use the explicit `powershell -NoProfile -ExecutionPolicy Bypass -File ...` invocation shown in FIRST-RUN. Follow managed-device policy if enforced. |
| OpenCode shim not selected | Check `Get-Command opencode`; aliases or machine PATH can outrank the user shim. Use `oc` or `ocdeck launch`. |
| Hook command errors after checkout deletion | Restore the source at its recorded path or remove the installed commands manually. Uninstall project hooks before deleting source. |

## Diagnose the installation path

`Verify-Windows.ps1` expects the original installer: its per-user environment,
OpenCode shims and scheduled task. It will not validate a foreground-only setup.
For that setup, inspect `-m ocdeck devices` and `-m ocdeck status` directly.
`scripts/Test.ps1` exercises fixture/integration tests; it does not launch real
provider-backed agents or confirm Windows/USB behavior.

The installation scripts and BAT files default to `%USERPROFILE%\.opencode-deck`.
For advanced `OCDECK_HOME` setups, use the explicit Python CLI and its environment;
do not assume the original installer/task automatically follows that override.
Hook commands use `node` from the harness's inherited PATH. Restart your terminal
and managed harness after changing PATH or installing Node.

## Report a failure

Include the profile, native harness version, setup path, failed acceptance step,
redacted status, hook diagnostic errors, and whether a mock or physical broker was
used. Note any WSL/SSH/container boundary: the included per-launch relay is local
and does not add cross-environment support. See [REMOTE-AND-WSL.md](REMOTE-AND-WSL.md).


## HomeAILab keys show state but do not focus

Use the [managed HomeAILab wrapper](LAUNCHERS.md), then relaunch the old sessions.
Direct launches lack the dedicated window token. Do not use the headless `serve`
launcher when you want to focus an interactive agent. In Windows Terminal, retain
`showTerminalTitleInTitlebar: true` and the managed tab title.
The updated fallback attaches both GUI threads and checks keyboard focus as well
as foreground ownership. Restart the broker after updating its source code.


## 2.1 additions

See [the 2.1 feature guide](NEXT.md) for larger decks, Codex, alerts, doctor/report,
appearance import/export, dry-run and complete integration uninstall.
