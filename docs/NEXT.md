# Historical 2.1 implementation and acceptance record

[Project overview](../README.md) · [Documentation index](README.md)

This page preserves the original 2.1 engineering record and anchors. Some setup and release statements describe that historical branch, not current behavior. Use the [current feature hub](features/README.md), [installation](FIRST-RUN.md), [updates](features/UPDATES.md) and [release workflow](PYPI.md) for current instructions. The live acceptance checklist remains a useful manual checklist.

## Alerts

Merge this into `%USERPROFILE%\.opencode-deck\config.json`, then restart the broker:

```json
{
  "alerts": {
    "sound": true,
    "toast": true,
    "states": ["input"],
    "cooldown_seconds": 10,
    "muted_slots": ["2"]
  },
  "check_updates": true
}
```

Both alert channels default off. `sound_file` optionally names an absolute WAV
path; otherwise Windows' SystemExclamation sound is used. `states` can include
`running`, `idle`, `input`, and `unknown`. Sound is globally rate limited. Each
entry into a selected state is eligible; periodic snapshots do not retrigger it.

Toasts require a new hashed request identity. A refresh, stale-state recovery,
or repeated delivery of the same request cannot cause a duplicate during that
managed session. Several newly identified requests in one snapshot produce one
slot notification. Unidentified permission notifications can trigger a sound
when they establish INPUT but cannot generate a request-specific toast. A broker
restart resets in-memory notification history. Muted slots suppress both channels.

Delivery uses Windows' ordinary notification system, default priority, silent
toast audio and the shell interruption-state check. It never uses an alarm or
priority bypass. Enable **AgentStreamDeck** in Windows notification settings. The first
opted-in toast creates a per-user notification identity. Focus Assist/Do Not
Disturb and fullscreen/presentation modes may suppress alerts. Linux mock mode
validates transitions but does not emit desktop notifications. Delivery failures
appear in rotating logs; the device loop never waits for notifications.

## Diagnostics and reports

```powershell
ocdeck doctor
ocdeck doctor --no-device --project C:\src\my-project
ocdeck doctor --json
ocdeck status --json
ocdeck report --output agentdeck-report.zip --lines 200
```

Doctor prints PASS, FAIL, or MANUAL, with a fix/check on every line. It covers the
troubleshooting table, including hook receipts, broker health, Node version,
capacity, USB/Elgato, focus and native-runtime checks. It exits 1 for detected
failures and 0 otherwise. MANUAL explicitly means unverified, not passing.
`--no-device` never enumerates or opens HID devices. It still checks the broker;
an intentionally stopped broker is a failure.

Reports contain only `status.json`, `versions.json`, `config.json`, `logs.json`.
They exclude raw hook files, discovery descriptors, launch specifications, prompt
bodies and transcripts. Credential-named fields, recognizable credential strings,
and the exact local bearer token are redacted. Arbitrary prose cannot reliably be
classified as a secret: do not put credentials in custom labels, and inspect a
report before sharing it. Reports refuse to overwrite an existing ZIP. Logs are
JSON lines, capped at 2 MB with three backups. Correlation IDs identify HTTP
requests; status contains at most ten recent warning/error excerpts.

## Larger decks

Mini: 6 keys. Original/MK.2: 15 keys. XL: 32 keys. Detection uses the installed
StreamDeck drivers and product IDs. Slots automatically resize on attachment,
preserve registration order, and invalidate stale button generations. Overflow
agents take a newly freed slot. Select `serial` when multiple decks are attached.
This version controls one deck per broker. Per-button settings and `ocdeck focus`
accept the larger slot range. Mock tests can use `"slots": 15` or `32`.

```powershell
ocdeck devices
ocdeck hardware-check
ocdeck appearance --slot 15 --alias Reviewer
```

The broker refuses to open hardware while an Elgato Stream Deck process is
running, with an actionable message. Quit it from the tray. Advanced users who
have explicitly released this device in Elgato can set `"allow_elgato": true`.
Process detection is conservative: it cannot prove which device Elgato holds.
The physical acceptance check also requires Elgato to be closed.

## Codex CLI

```powershell
ocdeck harness-install codex --project C:\src\my-project --dry-run
ocdeck harness-install codex --project C:\src\my-project
cd C:\src\my-project
ocdeck start --profile codex
```

Review and trust the exact installed hooks using Codex `/hooks`; the installer
never changes native trust or approval policy. The adapter merges
`.codex/hooks.json`, keeps unrelated hooks, writes a receipt and backs up changes.
It uses SessionStart, SessionEnd, UserPromptSubmit, PreToolUse, PostToolUse,
PermissionRequest, Stop, Interrupt and PreCompact. The launcher observes the child
process and removes its slot when it exits.

UserPromptSubmit/tool activity maps to RUNNING, Stop/Interrupt to IDLE. An observed
PermissionRequest maps to INPUT with an unknown count until a result, new turn,
stop or interrupt. This is observed lifecycle state, not proof an approval dialog
is still open: Codex does not supply a paired approval-resolution ID in the
PermissionRequest schema. `request_user_input` tool calls with paired IDs can also
be tracked. Hooks emit no approval decisions. Missing hooks remain UNKNOWN.
Native hooks can be concurrent, so ordering and all tool paths need live testing.

Source: [OpenAI Codex hook reference](https://developers.openai.com/codex/hooks),
checked 2026-09-12. Native trust and hook coverage depend on the installed CLI.

OpenCode exposes known pending counts, rendered as 1–9 or `9+`. Hook adapters
expose `pending: null` in the public slot view rather than inventing a total.
`requestIds` contains SHA-256 metadata identities, never raw request text.

## Appearance

```powershell
ocdeck appearance --theme high-contrast --effect steady --text-size large
ocdeck appearance --export my-look.json
ocdeck appearance --import my-look.json --dry-run
ocdeck appearance --import my-look.json
```

Import/export is schema version 1 and includes only `appearance`, `buttons`, and
`fps`. Unknown fields, invalid slots and malformed values are rejected. Import
replaces visual settings while preserving serial, alerts and other broker options.
Combining import and explicit appearance flags applies those flags last. Dry-run
prints a settings diff plus an in-memory PNG data URI of example keys with the
resulting settings; it writes neither configuration nor preview/export files.
For a GIF file, use `ocdeck preview --output preview.gif`.

![High-contrast palette and input counts](visuals/next-high-contrast.png)

## Uninstall

```powershell
ocdeck uninstall --all --scan C:\src --dry-run
ocdeck uninstall --all --scan C:\src
```

New hook installations are recorded in `projects.json`. Uninstall also scans the
specified roots (current directory by default) for old `.agentdeck` receipts,
skipping dependency folders and symlinks. Specify all project roots containing
older installations. Every receipt is preflighted before writes. Close managed
sessions first. Unrelated hooks remain; changed files get backups. Moved projects
or malformed native configs stop removal so they can be reconciled.

The Windows task, managed OpenCode plugin/TUI entry, PATH shims and notification
identity are removed. Local config/metadata/token move to a timestamped `backups`
directory. Backups and the Python environment remain, so the running interpreter
is never deleted. Use `python -m pip uninstall agentstreamdeck` separately to remove the
package after completing integration removal. `scripts/Uninstall.ps1` delegates
to this command and supports `-DryRun` and `-Scan`.

## Updates and releases

On broker start a background worker checks GitHub's latest release with a 3-second
network timeout and a bounded response. A new stable version is announced once
per cached version with release notes, also available through `ocdeck status`.
Network errors do not block startup. Mock brokers disable this lookup unless explicitly enabled. Set `"check_updates": false` to disable all
release lookups. Nothing is downloaded or installed automatically.

The distribution is named `agentstreamdeck`, with `ocdeck --version`. The wheel contains
Node adapters, PowerShell runtime helpers and renderer assets. Python 3.11+ and
Node 20+ are required; the Windows OpenCode task/shim installation still uses
`scripts/Install.ps1` from a checkout. Hook harnesses run from an installed wheel.

CI runs Python mock/integration tests and Node suites on Windows and Ubuntu,
Python 3.11/3.13, plus Ruff, formatting, Pyright basic and wheel checks.
The manual **Signed Python release** workflow builds wheel/sdist, checksums and a
CycloneDX SBOM, then publishes using PyPI trusted publishing and attestations from
`main`. Before publishing, configure the `pypi` GitHub environment and establish
ownership/trusted publishing for the PyPI `agentstreamdeck` project. Registry name
availability/ownership is not established by building the wheel. No PyPI or
GitHub release is published merely by pushing this feature branch.

## Live acceptance checklist

- Mini/MK.2/XL: close Elgato, run hardware-check, confirm numbered images and every
  physical key event; reconnect USB; launch more sessions than capacity and close one.
- Windows: confirm managed focus including a minimized window, same-user/elevation,
  and no unexpected focus changes from alerts.
- Enable alerts, send an identified OpenCode question, keep snapshots refreshing,
  mute its slot, enable Focus Assist, and verify suppression. Disable Focus Assist
  and verify a subsequent request. Test a WAV path with spaces and a missing path.
- Codex: install/trust hooks, start a managed session, observe startup/prompt/tool/
  approval/result/stop/interrupt/exit. Run `python tests/live_codex.py` to collect
  an interactive state check against a running broker. This can use your model
  credentials; it is not run by CI.
- Uninstall: create two projects with unrelated hooks, run dry-run, then removal;
  check backups, remaining hooks, task/PATH cleanup, and reinstall successfully.


## Request coverage

| # | Improvement | Implementation / verification |
|---|---|---|
| 1 | Sound alerts | Optional WAV/default chime; state filtering, muting, rate-limit fixtures |
| 2 | PR CI | Windows/Ubuntu Python and Node matrix; README badge |
| 3 | Windows notifications | Native normal-priority toasts; request dedup fixtures; Windows check pending |
| 4 | Doctor | Read-only PASS/FAIL/MANUAL checks and exit status; no-device fixture |
| 5 | Issue report | Allowlisted ZIP with recursive/known-token redaction tests |
| 6 | Structured logs | JSON, correlation IDs, capped rotation and status excerpts |
| 7 | Scrubbing gate | Randomized snapshot/log/pixel and Node metadata tests in CI |
| 8 | Updates | Bounded background check, cached version/notes, offline and disable fixtures |
| 9 | Pre-commit | Ruff lint/format and per-file Node syntax checks |
| 10 | Larger decks | Driver detection, resizing, 15/32 mock loops and stale-focus tests |
| 11 | Codex | Native hook merge, BAT/CLI launcher, fixtures and opt-in live runner |
| 12 | Input counts | Known OpenCode count/9+ badge; unknown hook totals remain null |
| 13 | Types | Incremental concrete types and Pyright basic over ocdeck/ |
| 14 | Python release | Wheel/sdist assets, clean install, SBOM/checksums/attestations workflow; publishing setup pending |
| 15 | Uninstall | Receipt preflight/scanning, dry-run, hook preservation and backups |
| 16 | Actionable errors | AD error catalog, fix commands, docs links and assertions |
| 17 | High contrast | Palette, renderer gallery and contrast fixture |
| 18 | Appearance dry-run | Diff and in-memory preview; zero filesystem writes fixture |
| 19 | Appearance sharing | Versioned validated JSON import/export; unrelated config preserved |
| 20 | Elgato conflict | Conservative process guard before HID open and doctor check |

## Related guides

[Project overview](../README.md) · [Documentation index](README.md) · [Feature hub](features/README.md) · [CLI reference](CLI.md)
