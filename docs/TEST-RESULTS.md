# Verification record

Bundle final verification: 2026-09-08. Environment: Linux authoring workspace, Python 3.12, Node, Pillow, psutil 7.2.2, streamdeck 0.10.0 and hidapi 0.15.0. No physical Stream Deck or Windows desktop was available.

## Passed here

- **23 Python unittest tests passed**, including a real JavaScript-to-Python HTTP integration scenario. Exact final output: `python-test-output.txt`.
- **5 JavaScript state tests passed**. Exact output: `javascript-test-output.txt`.
- Python implementation source parses, and each plugin passes `node --check`.
- Animated preview was generated and visually inspected. This is rendered artwork, not a photograph or proof of hardware operation.

The Python suite covers six stable assignments and overflow, concurrent registrations, pending-input priority, busy/retry mapping, closing and actual process death, PID reuse rejection, stale state, out-of-order snapshots and retired producer epochs, generation-safe button handling, singleton lock, blank-key no-op, READY relinquishing a slot, authenticated real HTTP registration/update/deletion, and Origin rejection.

One Python test launches Node and drives the real Bridge class through the real Python broker HTTP server. It verifies pending state recovery after losing a registry entry. It also loads the actual conventional plugin entrypoint with a fixture SDK client and sends permission/question/status hooks through the broker. The final extension verifies that an explicit SDK snapshot failure produces unknown and later recovers to running. This exercises the plugin code but **is not equivalent to OpenCode loading it**.

The image protocol test uses the actual pinned StreamDeck Mini driver and Pillow native conversion, checking encoded image packets with a fake transport. Callback tests exercise key-down behavior and captured assignment generation. They do not test the operating system's physical HID driver or USB timing.

This workspace exposes a process namespace mismatch between runtime PIDs and `/proc`. The suite contains a test-only identity translator for that environment. Production Windows PID validation is unchanged. Test dependencies were installed outside the bundle for authoring; the Windows installer installs its own environment.

## Unverified gates

| Gate | Status |
|---|---|
| Mini image appearance, orientation, all six physical callbacks | Requires user's device |
| USB reconnect / exclusive ownership after Elgato restart | Requires user's device and Windows |
| PowerShell installer and Task Scheduler registration/recovery | Requires Windows; scripts not executed here |
| Exact foreground activation/minimized-window restoration | Requires user's Windows desktop |
| Reboot -> user logon -> READY | Requires user's PC |
| Installed OpenCode loads plugin and emits real runtime events | Requires local validation |
| Optional newer TUI adapter | Source-based implementation; runtime compatibility unverified |
| WSL/SSH/container relay | Not implemented; see REMOTE-AND-WSL.md |

An OpenCode 1.18.29 package was downloaded and its `--version` checked. A live-runtime test was attempted using a local deterministic model fixture. Execution was interrupted by this environment's network approval controls (`network approval was cancelled before a decision was returned`); there was no successful end-to-end runtime result. The optional fixture remains in `tests/live_opencode.py` for local adaptation and verification. No claim of live OpenCode compatibility follows from the version check.

## Run locally

After installation, run `scripts/Test.ps1` (Node 20+ needed for JavaScript). Follow FIRST-RUN.md for real hardware, state, focus and reboot acceptance. `ocdeck hardware-check` requires the broker stopped and records actual key-down events. Its display-confirmation field remains false because a program cannot verify visible pixels merely by submitting images.

Record local outcomes here, including OpenCode and terminal versions, adapter mode, serial/model, exact failed step, relevant redacted logs, and eventual fix. Do not replace an unverified gate with “passed” based on code inspection or a simulated test.


## Harness adapter branch verification — 2026-09-09

Linux authoring environment, Python 3.12 and Node 24.19.0. No native agent logins,
Windows desktop or physical device were available.

- 25 Python tests passed (23 existing + 2 new integrations).
- 20 Node tests passed (5 existing + 15 new harness/installer/relay tests).
- A real hook subprocess sends events through the authenticated Node relay,
  existing Bridge, real HTTP server and Python registry. The test fully stops and
  recreates the broker and verifies pending state returns without duplicate keys.
- A real Python supervisor launches a fixture child that sends hooks, observes
  broker states, validates literal arguments and exits 7; exit status propagates
  and launch files/registration are removed.
- Concurrent hook processes, duplicate question IDs, independent resolutions,
  malformed payloads, profile isolation, no prompt forwarding, silent hook output,
  Origin/auth rejection, config merge/idempotence/backup/uninstall were exercised.
- The existing broker, registry, transport core and OpenCode plugin tests pass.

These are protocol and fixture tests, not successful runs of Claude, Copilot,
Gemini or Cursor themselves. Native hooks, BAT/PowerShell, VS Code isolated-profile
sign-in/title matching and physical focus/USB remain unverified. Follow
[HARNESSES.md](HARNESSES.md) for live acceptance and known coverage limitations.


## Main merge verification — 2026-09-10

The adapter code and documentation were integrated with main's newer demo-video
change. In the Linux authoring environment, after installing the declared Python
dependencies, 25 Python tests and 20 Node tests passed. CLI help was checked against
the documented harness-install/harness-launch examples. Relative Markdown links
and section anchors were checked with no missing targets; merge markers and diff
whitespace checks were clean (Windows BAT CRLF endings retained intentionally).

Exact outputs: [Python merge tests](merge-python-test-output.txt) and
[Node merge tests](merge-javascript-test-output.txt). No native harness, Windows
script, hardware or foreground-focus gate became verified merely by this merge.

## Customizable smooth buttons — 2026-09-12

Linux/Python 3.11+ checkout verification:

- Python suite: 29 passed (including 4 new appearance/regression tests).
- JavaScript suite: 20 passed.
- Appearance matrix covers all five themes, three layouts, six harness values,
  and six states; blank keys stay black. Final text-fitting optimization:
  four appearance tests passed again in 1.469 seconds.
- CLI checks: global settings + per-slot override persisted; unrelated serial
  and device brightness preserved; invalid NaN speed rejected without writing.
- Harness/Aurora/glow GIF generated and a frame visually inspected.
- Real Stream Deck Mini USB throughput, six-key sustained 24/30 FPS, and Windows
  display/focus acceptance: **not verified on hardware**.

## Official icons and ten customization additions — 2026-09-12

- Python suite: 34 passed; JavaScript suite: 20 passed on the Linux test host.
- Five new customization tests cover source checksums / real logo loading,
  Copilot registration aliases, unknown-brand fallback, display alias behavior,
  clipped animated text, new options and presets, invalid configuration rejection,
  CLI precedence / label preservation, and non-mutating preview generation.
- After the preview timing adjustment, all five customization tests passed again.
- Built the wheel without dependencies and inspected its contents: all five PNGs,
  original Copilot SVG, source manifest, and Octicons license are included.
- Regenerated README galleries and official-logo animation; visually inspected
  official logos, extended styles, typography, and an animated-text frame.
- Verified local documentation links and decoded every gallery animation frame.
- Physical Stream Deck throughput, readability on-device, and Windows acceptance
  remain unverified; this update does not claim to pass those hardware gates.

## Focus fix and HomeAILab wrappers — 2026-09-12

- 42 Python tests passed; 20 JavaScript tests passed. The first full run lacked
  psutil/streamdeck in the refreshed test runtime; after installing the declared
  dependencies, the full Python suite passed in 17.450 seconds.
- Six mocked Win32 regression tests cover both-thread attachment, minimized
  restore, input-child preservation, missing keyboard focus, denied attachment,
  cleanup after exceptions, and already-focused targets.
- Two launcher tests cover external BAT path/argument retention and nested
  OpenCode shim routing without creating another managed window.
- Inspected HomeAILab harness sources: they directly invoke their real CLI and
  leave backend selection in their own scripts. New AgentDeck wrappers preserve
  that behavior inside a managed window; HomeAILab itself was not modified.
- Documentation links and BAT CRLF line endings verified.
- Physical Stream Deck presses, native Windows focus, and executing HomeAILab
  BATs against live local/cloud backends remain unverified on this Linux host.
