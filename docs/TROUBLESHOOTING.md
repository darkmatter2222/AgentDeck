# Troubleshooting AgentStreamDeck

[Project overview](../README.md) · [Documentation index](README.md)

Start with `ocdeck status`, or invoke `-m ocdeck status` with the installed Python
interpreter if no shim exists. Record harness, Python, Node and Windows Terminal
versions. Inspect `%USERPROFILE%\.opencode-deck\broker.log` and native harness hook
diagnostics. Do not share bearer tokens, hook.json connection descriptors, prompts
or provider credentials. A screenshot of a key cannot diagnose hook loading alone.

| Symptom | Check / action |
|---|---|
| No device or flickering/overwritten keys | Release this Mini in Elgato; stop other HID controllers. Check `device.online`, `device.mock`, USB connection and selected serial. |
| Broker unavailable | Start the installed `AgentStreamDeck Broker` Windows task, Linux user service, or foreground broker. Discovery uses a dynamic port; do not hard-code one. |
| No key for Claude/Copilot/etc. | Install the right project profile and launch the harness normally from that directory. Restart it to load hooks. Check overflow at your device’s 6/15/32-key capacity. |
| LINK ?: Waiting for first harness hook | Check `node --version` (20+), config file location, native hooks enabled/trusted, and the harness’s working directory. Submit a prompt; a version may not emit a startup hook. |
| LINK ?: Hook delivery failed | A hook could not parse/deliver metadata or lacked a session ID. Correct the native config/runtime problem. A legacy managed relay has a failure latch that requires a new managed launch; normal direct hooks retry on subsequent native events. |
| LINK ? during a permission prompt | Expected for recognized notifications without paired request IDs. Enable the optional native permission controls only for supported adapters; otherwise use terminal focus. See [deck controls](features/DECK-CONTROLS.md). |
| Running while waiting for approval | Expected for adapters without approval coverage. The absence of red is not proof the agent is unblocked. See HARNESSES.md. |
| Idle/running persists incorrectly | Missing/disabled hooks may leave the last observed state. Check prompt/tool/stop hooks in the native runtime. Bridge heartbeats alone cannot detect every lost event. |
| Broker restarted but no state returns | Direct hooks recover on the next native event; OpenCode recovers through its heartbeat. Check the OS user and discovery/token directory. A crashed legacy managed bridge needs a new managed launch. |
| Key focuses nothing or reports ambiguity | Use one monitored session per OS window and inspect `lastFocus`. Shared terminal tabs/panes can be ambiguous. An optional managed window has its own title-based mapping. |
| Correct target found but foreground denied | Windows foreground/elevation rules can refuse focus. Run agents and broker as the same desktop user and verify minimized-window behavior. Do not disable PID identity checks. |
| VS Code asks for sign-in / lacks settings | Only the optional managed VS Code launcher creates isolated user data. Normal workspace hooks use your existing VS Code profile. If using the legacy helper, enable Copilot/sign in in that instance. |
| VS Code hook activity missing | Inspect Chat: Configure Hooks, workspace trust and hook enablement. Restart the normal editor after installing workspace hooks; preview native hook support depends on the installed VS Code version. |
| VS Code focus ambiguous/absent | For normal launches, inspect captured window mapping and shared editor windows. For the optional isolated managed profile, inspect window.title overrides and keep the launcher terminal’s distinct suffix. |
| Installer refuses JSONC/settings | Preserve the file. Manually reconcile comments/format into valid JSON if appropriate; do not delete unrelated configuration. `--dry-run` shows intended entries for valid JSON. |
| Installer says project moved | Remove the old AgentStreamDeck entries and receipt manually, preserving unrelated hooks, then reinstall at the new location. |
| PowerShell script execution blocked locally | For a trusted downloaded checkout, use the explicit `powershell -NoProfile -ExecutionPolicy Bypass -File ...` invocation shown in FIRST-RUN. Follow managed-device policy if enforced. |
| OpenCode shim not selected | Current setup does not install a shim. Legacy installations can have PATH/alias conflicts; inspect `Get-Command opencode` and see the compatibility launcher guide. |
| Hook command errors after checkout deletion | Restore the source at its recorded path or remove the installed commands manually. Uninstall project hooks before deleting source. |

## Diagnose the installation path

`Verify-Windows.ps1` is a legacy script tied to the old task/venv. For current setups use `python -m ocdeck doctor`, `devices` and `status`, plus the platform controls in [startup](features/STARTUP.md).
`scripts/Test.ps1` exercises fixture/integration tests; it does not launch real
provider-backed agents or confirm Windows/USB behavior.

The installation scripts and BAT files default to `%USERPROFILE%\.opencode-deck`.
For advanced `OCDECK_HOME` setups, use the explicit Python CLI and its environment;
do not assume the original installer/task automatically follows that override.
Hook commands use `node` from the harness's inherited PATH. Restart your terminal
and harness after changing PATH or installing Node.

## Report a failure

Include the profile, native harness version, setup path, failed acceptance step,
redacted status, hook diagnostic errors, and whether a mock or physical broker was
used. Note any WSL/SSH/container boundary: the included per-launch relay is local
and does not add cross-environment support. See [REMOTE-AND-WSL.md](REMOTE-AND-WSL.md).


## HomeAILab keys show state but do not focus

Check [window focus](features/FOCUS.md) and [HomeAILab compatibility prerequisites](LAUNCHERS.md), then relaunch sessions to refresh window mapping.
Normal launches use captured/ancestor windows. If a shared terminal prevents reliable mapping, use separate OS windows; managed wrappers are optional and have documented prerequisites. Do not use the headless `serve`
launcher when you want to focus an interactive agent. In Windows Terminal, retain
`showTerminalTitleInTitlebar: true` and the managed tab title.
The updated fallback attaches both GUI threads and checks keyboard focus as well
as foreground ownership. Restart the broker after updating its source code.


## More diagnostic references

See [diagnostics and error codes](features/DIAGNOSTICS.md), [hardware support](features/HARDWARE.md), [updates](features/UPDATES.md) and [complete CLI reference](CLI.md).


## Jelly presses and minimized agent windows

An ordinary Jelly button responds with a two-second playful reaction. A red `!`
means an update is available, so that button retains its update-install action.
During a visible coffee invitation, either Jelly or the cup opens the support page.
Agent keys always focus their registered session. If that window is minimized,
the key requests **maximize**, waits briefly for the asynchronous Windows state
change, then brings the window forward. Non-minimized windows retain their size.

After upgrading, restart the broker and restart existing coding clients so they
register fresh window mappings. The broker log is normally
`%USERPROFILE%\.opencode-deck\broker.log` on Windows, or
`$OCDECK_HOME/broker.log` if that override is configured. `ocdeck status` shows
`device.input_events`, `device.last_input`, and `lastFocus`; `ocdeck doctor` and
`ocdeck focus 1` help distinguish input delivery from window activation.
The log now records each button-down action without capturing window titles.

If Windows still refuses activation, attach the latest log after one press on a
minimized session and the output of `ocdeck status`. A log entry saying
`Window did not leave minimized state` means the target did not process the
maximize request within the bounded wait. Run the broker and client under the
same interactive desktop user and privilege level.


## Pip succeeded, but the broker still shows the old version

Starting with v3.0.5, the running broker checks installed package metadata every
five seconds. It requires ten seconds of stable metadata with no visible pip
installer, verifies RECORD hashes, and checks that a fresh interpreter imports
the new version before restarting. Interrupted installs leave the current
broker running. Jelly self-updates and the local watcher share a restart lock.

Check `python -m ocdeck status`: `device.pip_upgrade` reports `watching`, `waiting`,
`restarting`, or a source/editable-install exclusion. The log records
`Pip upgrade ready` when automatic activation begins. A `waiting` status means
file verification or the fresh import has not succeeded yet.

A broker started before v3.0.5 cannot detect this first upgrade. Use the red `!`
on Jelly, or stop and start the broker once after pip completes. Ensure pip is
running in the same Python environment as the broker. This feature does not add
pip install hooks, change PATH, or start a broker that is already stopped.
The existing `python -m ocdeck install` command provides background startup for
first-time installations.

To disable automatic activation, set `auto_restart_on_upgrade` to `false` and
restart once. This is separate from `check_updates`, which controls online
PyPI notifications. For the installed Linux systemd service, its existing
restart policy performs the relaunch; unmanaged brokers use a detached helper.

## Related guides

[Project overview](../README.md) · [Documentation index](README.md) · [Feature hub](features/README.md) · [CLI reference](CLI.md)
