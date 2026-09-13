# Configuration and maintenance

[Back to the README](../README.md)

## Commands and configuration


| Command | Purpose |
|---|---|
| `python -m pip install --upgrade agentstreamdeck` | Install or upgrade the Python package |
| `python -m ocdeck install` | Register/start the per-user broker startup task/service; also installs the OpenCode plugin when available |
| `python -m ocdeck harness-install claude` | Merge Claude hooks into the current project; use another supported profile as needed |
| `python -m ocdeck harness-install codex --dry-run` | Preview hook changes without writing |
| `python -m ocdeck harness-install claude --remove` | Remove only AgentStreamDeck-owned Claude hook entries |
| `python -m ocdeck status --json` | Device health, physical `input_events`, active slots, update state and last focus result |
| `python -m ocdeck stop` | Stop the current broker process |
| `python -m ocdeck focus 1` | Synthetic focus check for key 1 |
| `python -m ocdeck devices` | Detect supported Mini/MK.2/XL devices |
| `python -m ocdeck hardware-check` | Physical diagnostic; stop the broker first |
| `python -m ocdeck broker --mock` | Foreground broker with a mock device |
| `python -m ocdeck preview` | Render the animation preview |
| `python -m ocdeck doctor --no-device --json` | Diagnose configuration and broker without HID access |
| `python -m ocdeck report --output report.zip --lines 200` | Create a redacted diagnostic ZIP |
| `python -m ocdeck appearance --dry-run` | Inspect settings changes and an in-memory sample preview |
| `python -m ocdeck uninstall --all --scan C:\Projects --dry-run` | Preview hook/startup/config removal |
| `python -m ocdeck start ...` / `harness-launch ...` | Optional legacy/compatibility launch helpers, not required for monitoring |

Use `python -m ocdeck` instead of `ocdeck` when the console entry point is not on PATH.

Broker settings live in `%USERPROFILE%\.opencode-deck\config.json` (or `OCDECK_HOME`):

```json
{
  "fps": 24,
  "brightness": 45,
  "animations": true,
  "ready": true,
  "serial": null,
  "allow_elgato": false,
  "check_updates": true,
  "alerts": {
    "sound": false,
    "toast": false,
    "states": ["input"],
    "cooldown_seconds": 10,
    "muted_slots": []
  }
}
```

Merge settings into existing config rather than replacing unrelated preferences.

| Setting | Default / accepted values |
|---|---|
| `fps` | 24; integers 1–30 |
| `brightness` | 45; hardware backlight 0–100, distinct from per-key image brightness |
| `animations` / `ready` | Both true; false disables motion / the initial READY key |
| `serial` | null; select one detected device serial when necessary |
| `slots` | 6 in mock mode; 6, 15 or 32; real deck capacity is automatic |
| `allow_elgato` | false; advanced opt-out of the Elgato process guard |
| `check_updates` | true for hardware broker, false for mock unless explicitly configured |
| `alerts.sound` / `alerts.toast` | false; independently opt in |
| `alerts.sound_file` | Omitted uses system sound; otherwise a WAV path |
| `alerts.states` | `["input"]`; sound transitions only |
| `alerts.cooldown_seconds` | 10; finite number 0–3600 |
| `alerts.muted_slots` | `[]`; one-based strings `"1"` through `"32"` |
| `appearance` / `buttons` | Global preferences / per-slot overrides; [full field reference](APPEARANCE.md) |

Restart the broker after edits. FPS is configurable from 1 to 30; new installations target 24. Disable animations for static
images, disable ready for an empty black deck, or select a serial when multiple
decks are connected. Compatibility names remain `ocdeck` and the `.opencode-deck` state directory. New Windows startup registration uses the **AgentStreamDeck Broker** Scheduled Task; uninstall also recognizes an owned legacy `OpenCode Deck` task.

## Sound alerts and Windows notifications


Merge an `alerts` object into your existing config, then restart the broker:

```json
{
  "alerts": {
    "sound": true,
    "toast": true,
    "states": ["input"],
    "cooldown_seconds": 10,
    "muted_slots": ["2"]
  }
}
```

Both channels default off. Sound uses SystemExclamation unless `sound_file` names
a WAV path, such as `"C:\\Sounds\\input.wav"`. The `states` list selects sound
transitions: `input`, `running`, `idle`, or `unknown`. Cooldown is global; repeated
snapshots do not produce another chime. Muted slots are one-based **strings** and
suppress both channels. Alerts are processed independently of USB rendering.

Toasts require a newly identified request. Multiple new IDs in one snapshot
produce one slot toast. Repeated delivery and stale-state recovery do not repeat
that toast during the broker lifetime. A broker restart resets deduplication
history. INPUT without a request ID can trigger sound but not a request-specific
toast; `states` does not turn toasts into generic activity notifications.

Windows delivery uses normal-priority notifications, silent toast audio and the
shell interruption-state check. The first opted-in toast registers the per-user
AgentStreamDeck notification identity. Enable AgentStreamDeck in Windows notification
settings. Focus Assist/Do Not Disturb and fullscreen/presentation states may
suppress delivery. Sound and desktop toasts are Windows-only; mock tests elsewhere
exercise the transition logic. [Live notification checks](NEXT.md#live-acceptance-checklist)
remain required.

## Diagnostics, logs and bug reports


```powershell
python -m ocdeck doctor --project C:\Projects\MyApp
python -m ocdeck doctor --no-device --json
python -m ocdeck status --json
python -m ocdeck report --output agentdeck-report.zip --lines 200
```

Doctor checks configuration, Node, runtime assets, hook receipts, broker health,
capacity and (unless excluded) device/Elgato state. It also lists interactive
checks for native hook trust, focus and other troubleshooting cases. Every line
includes a fix/check; PASS means verified, FAIL means a detected problem, and
MANUAL means unverified. Exit status is 1 if any check fails, otherwise 0. A MANUAL
result is not a pass. `--no-device` never enumerates or opens HID; it still checks
whether the broker responds. Errors use stable AD codes and troubleshooting links.

`broker.log` contains JSON lines, request correlation IDs and up to three rotated
backups, each capped at approximately 2 MB. Status includes at most ten recent
warning/error excerpts. Report ZIPs contain only `status.json`, `versions.json`,
`config.json` and `logs.json`, with 100 log lines by default and a 2,000-line cap.
An existing output ZIP is never overwritten.

Credential-named fields, recognizable secret patterns and the exact local bearer
token are scrubbed. Reports exclude raw hook/launch/discovery files, prompts and
transcripts. Automated tests cover metadata, rendered labels, logs and reports;
arbitrary prose is not reliably classifiable as a secret. Avoid credentials in
custom labels and inspect a report before sharing it. [Troubleshooting](TROUBLESHOOTING.md)
contains the symptom guide; [the API reference](API.md) describes status fields.

## Uninstall and backups


Close monitored harness sessions before complete removal. Preview first:

```powershell
python -m ocdeck uninstall --all --scan C:\Projects --scan D:\Work --dry-run
python -m ocdeck uninstall --all --scan C:\Projects --scan D:\Work
```

The command preflights project receipts before mutation, removes only AgentStreamDeck-owned native-hook entries, preserves unrelated hook/settings entries, and retains backups. On Windows it removes the owned **AgentStreamDeck Broker** Scheduled Task (and an owned legacy `OpenCode Deck` task if present). On Linux it disables/stops and removes the `agentstreamdeck.service` systemd user service. It also removes owned OpenCode integration and legacy shims where applicable.

Local configuration/token metadata move under a timestamped `backups` directory. Logs, backups and the Python environment remain. Remove the Python distribution separately when desired:

```text
python -m pip uninstall agentstreamdeck
```

To remove only one project hook profile:

```text
python -m ocdeck harness-install codex --remove
```

[Plugin-first setup](PLUGIN-FIRST.md) · [Full uninstall behavior](NEXT.md#uninstall) · [Troubleshooting](TROUBLESHOOTING.md)
## Pip upgrades restart the broker automatically


With **v3.0.5 or newer already running**, update using your normal Python environment:

```powershell
python -m pip install --upgrade agentstreamdeck
```

The broker notices the newly installed version, waits for pip to finish and the
installation to remain stable, verifies the package files and a fresh import,
then restarts itself in the background. Usually this takes **10–20 seconds after
pip finishes**, plus broker shutdown/startup time. Your configuration folder is
preserved. No open terminal or separate stop/start commands are needed.

**Moving from v3.0.4 or older?** Use Jelly's red `!` update button for the first
upgrade; it already installs and restarts for you. If you use pip for that first
upgrade, restart the broker once to load the new watcher. Afterward, normal pip
upgrades are enough. The broker must be running, and pip must use its Python
environment. Pip alone does not start a stopped broker or set up a first install.

This works offline and independently of online update checks. Set
`"auto_restart_on_upgrade": false` in `config.json` to keep manual restarts.
Editable installs and source checkouts are excluded. Reinstalling the same
version does not trigger a restart. Clients reconnect through their normal
heartbeat or next native hook event.

