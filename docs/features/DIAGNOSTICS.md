# Doctor, status telemetry, logs and diagnostic reports

[Project overview](../../README.md) · [Documentation index](../README.md)

Start by identifying whether the problem is setup, event delivery, USB input or Windows focus.

```powershell
python -m ocdeck doctor --project C:\Projects\MyApp --no-device --json
python -m ocdeck status --json
python -m ocdeck report --output agentstreamdeck-report.zip --lines 200
```

## Doctor results

Doctor checks configuration, Node, packaged runtime assets, project receipts, broker response, slot capacity and optional HID/Elgato state. Each row includes a suggested fix/check. PASS means the condition was verified, FAIL means a detected problem, and MANUAL means interactive verification is still required. The exit code is 1 if any row fails. A collection of MANUAL rows is not proof of physical success.

`--no-device` never enumerates or opens HID but still checks whether the broker responds. `--project` selects the project whose installed hooks should be examined. Use the exact software project path rather than the AgentStreamDeck source checkout unless that is the project you are diagnosing.

## Useful status fields

| Field | What to inspect |
|---|---|
| brokerPid / epoch | Current broker process and lifecycle identity |
| slots | Assigned label, harness, state, request metadata and generation |
| overflow | Sessions waiting for physical capacity |
| device.online / device.mock | Real device availability versus simulation |
| device.input_events / device.last_input | Physical HID reports, independent of focus success |
| lastFocus | Result of the most recent activation attempt |
| update / device.update | Available package or active update state when present |
| device.jelly_life | Current mood, action, selected hop and needs when enabled |
| device.render_timing | Requested/effective loop FPS and renderer cost breakdown |
| recentErrors | At most ten recent warnings/errors |

## Logs and report contents

The broker writes structured JSON lines with correlation IDs to broker.log. Rotation retains up to three backups at approximately 2 MB each. Report ZIPs include only status.json, versions.json, config.json and logs.json. The default tail is 100 log lines and the cap is 2,000. An existing report filename is never overwritten.

Reports exclude raw hook files, launch/discovery descriptors, prompts and transcripts. Credential-shaped fields, recognizable secret patterns and the exact broker token are scrubbed. Arbitrary prose cannot be reliably classified as a secret, so avoid credentials in display labels and inspect the report before sharing it.

## Error code reference

| Code | Meaning | First action |
|---|---|---|
| AD001 | Elgato may own device | Quit it from tray |
| AD002 | Device missing/disconnected | Run devices |
| AD003 | Broker unavailable | Check startup/service and interpreter |
| AD004 | Invalid config/request | Check JSON and run doctor --no-device |
| AD005 | Stale registration | Inspect status; restart affected session if needed |
| AD006 | Focus failed | Compare physical input telemetry with focus 1 |
| AD007 | Local authentication rejected | Check OS user and shared OCDECK_HOME |
| AD008 | Broker lock unavailable | Check for another broker using the same data directory |
| AD500 | Unexpected broker error | Create and inspect a diagnostic report |

Source: [doctor/report](../../ocdeck/diagnostics.py), [logs](../../ocdeck/observability.py), [error catalog](../../ocdeck/errors.py).

## Related guides

[Troubleshooting](../TROUBLESHOOTING.md) · [API fields](../API.md) · [Hardware](HARDWARE.md) · [Focus](FOCUS.md)
