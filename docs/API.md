# Local broker protocol

Endpoint: `http://127.0.0.1:<discovery.port>`. `.opencode-deck/discovery.json` is atomically written after socket binding and removed on graceful shutdown. The token is stored separately in the per-user `token` file. Never print or commit it.

Every request requires `Authorization: Bearer <token>`. JSON bodies must be objects at most 64 KiB. Browser Origin headers are refused. This is a trusted local application protocol, not a LAN service. Clients reread discovery/token instead of assuming the port persists.

| Method | Path | Meaning |
|---|---|---|
| GET | `/v1/status` | Broker epoch, device/input health, slots, overflow, last focus, update state |
| POST | `/v1/register` | Create or renew a matching immutable process identity |
| POST | `/v1/hook` | Deliver one normalized native harness lifecycle event directly to the broker |
| PUT | `/v1/instances/{id}` | Publish a newer complete conventional snapshot |
| DELETE | `/v1/instances/{id}` | Detach and release a conventional slot |
| POST | `/v1/focus` | Synthetic focus request for an existing assignment |
| POST | `/v1/stop` | Graceful broker shutdown |

## Conventional registration and snapshots

Registration example:

```json
{
  "id": "unique-launch-uuid",
  "process": {"pid": 1234, "created": 1770000000.123},
  "label": "HomeAILab",
  "windowToken": "OpenCode [unique-launch-uuid]",
  "harness": "opencode"
}
```

The timestamp is `psutil.Process(pid).create_time()`. The broker rejects a process that is not alive locally. Re-registering the same ID with a different process identity is rejected.

Snapshot example:

```json
{"producer":"fresh-plugin-uuid","seq":42,"status":"busy","pending":1,"detail":""}
```

Status accepts idle, busy, retry, unknown. Pending is a nonnegative count when the producer can prove a complete count. Monotonic sequences apply within a producer epoch. Superseded producer epochs are retired and their delayed messages are ignored.

Optional snapshot fields include `pendingKnown`, `inputNeeded`, `requestIds`, `outcome`, and `outcomeId`. Request IDs are SHA-256 identities, not raw prompt/request contents.

## Direct native hook events

The normal Claude/Codex/Copilot/Gemini/Cursor integration does not require a managed launcher or per-launch relay. The short-lived native hook reads broker discovery/token and posts a normalized event directly:

```json
{
  "profile": "claude",
  "parentPid": 4321,
  "cwd": "C:\\Projects\\MyApp",
  "event": {
    "event": "PreToolUse",
    "action": "tool",
    "session": "native-session-id",
    "tool": "AskUserQuestion",
    "request": "native-request-id",
    "question": true,
    "failed": false
  }
}
```

The broker:

1. validates the profile/action/session fields;
2. resolves the hook's parent PID to an exact PID + creation timestamp;
3. derives a stable local record from profile + native session ID;
4. captures the containing Windows window when possible;
5. reduces the event into idle/running/input/unknown state;
6. keeps the event-driven record current while the verified process is alive;
7. removes the record on a delivered session-end event or confirmed process death.

The direct hook path forwards bounded lifecycle metadata only. Prompt text, commands, file contents, tool arguments/results, model responses, and transcripts are not part of `/v1/hook`.

For backward compatibility, an environment containing `AGENTDECK_HOOK_BINDING` may still route through the older per-launch loopback relay. That relay is an implementation compatibility path, not the normal architecture.

## Focus requests

The focus payload is the assignment returned in `slots`, including `slot` (zero-based), `id`, and `generation`. CLI `ocdeck focus 1` uses user-facing one-based numbering and sends that exact tuple. Physical callbacks are marked `synthetic: false`; CLI/API checks are marked true.

On Windows, focus resolution prefers a captured HWND. If that is unavailable, it can use the legacy exact window token or a unique visible window belonging to the harness process or nearest process ancestor. This supports normal CLI launches inside Windows Terminal without requiring AgentStreamDeck to own the launch command.

Focus success verifies keyboard focus as well as foreground activation. A failed activation can include the observed foreground HWND, keyboard-focus state, attachment failures, and an actionable AD error.

## Status input telemetry

`GET /v1/status` includes the device status map. Important physical-input fields:

```json
{
  "device": {
    "online": true,
    "input_events": 14,
    "last_input": {"key": 2, "pressed": true, "time": 1770000000.123}
  }
}
```

`input_events` increments for physical key down/up reports received by the StreamDeck callback. It is intentionally distinct from `lastFocus`, so diagnostics can tell whether a failure is in USB input or Windows focus.

`/v1/status` also includes `update`, `recentErrors`, `brokerPid`, device render telemetry, slot state, and overflow count.

## HTTP errors and security

HTTP 401 means missing/invalid bearer credentials. 403 means a browser Origin was provided. 400 indicates invalid payload/process identity. 404 means an unknown route/instance. 413 means the body is too large.

The broker binds loopback only, rejects browser Origin requests, limits concurrent HTTP work, caps bodies, scrubs known credentials at the API boundary, and never treats a focus request as authorization to answer an agent prompt.

## Appearance metadata

Registration can include an optional `harness` string for rendering. It is display metadata only and does not change process identity, sequence, slot-generation, or focus invariants. Older clients can omit it.

See [Architecture](ARCHITECTURE.md), [Harnesses](HARNESSES.md), and [Plugin-first setup](PLUGIN-FIRST.md).
