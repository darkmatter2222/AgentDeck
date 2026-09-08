# Contributing

Thanks for picking this up. The whole design is built around one idea, so hold onto it:

> **The broker is the stable core. The plugin layer is where every harness lives.**

If you keep that true, your change fits. If it blurs the line, it doesn't.

## The architecture in one paragraph

The Python broker (`ocdeck/`) never talks to any agent harness. It owns six slots, an authenticated loopback API, the USB/HID connection, artwork, and window focus. It only understands one vocabulary, delivered by whatever harness adapter is running:

```json
{"producer": "<adapter uuid>", "seq": 42, "status": "busy", "pending": 1, "detail": ""}
```

Plus process identity (`pid` + exact creation timestamp) and a window token for focus. A new harness only has to produce that vocabulary. That's the entire contract.

## What we want you to touch

**A new harness adapter**, shaped like `plugins/server.mjs`:

- Reuse `Facts` (or an equivalent event → `{status, pending}` state machine) and `Bridge` from `plugins/core.mjs`. Don't reimplement HTTP, discovery, tokens, sequences, or producer epochs.
- Register once per harness runtime with a stable `id` and verified process identity; heartbeat re-registration is how broker restarts self-heal.
- Map your harness's real activity to the four statuses: `busy`, `retry`, `idle`, `unknown`. Count *unresolved request IDs* for `pending` — sets, not guesses. "The model printed a question" is not `pending`; "the harness is blocked on an approval with a request ID" is.
- Keep harness assumptions inside your module. Everything your harness exposes differently (event names, SDK methods, config file locations) stays in your file.

## What we want you to leave alone (please)

1. **`ocdeck/model.py` — the registry.** Slot generations, producer epochs, monotonic sequences, and pending-priority are load-bearing. They exist because someone hit a real bug (stale snapshot overwrites a newer one, delayed message from a dead producer, reused PID). Read the tests first: they are the spec.
2. **`ocdeck/broker.py` — the protocol.** Bearer auth, no-`Origin`, 64 KiB body cap, atomic `discovery.json`, port 0, graceful epoch-checked cleanup. The protocol is documented in `docs/API.md`; treat that doc as a contract. If the contract must change, say so loudly in the PR.
3. **`plugins/core.mjs` — shared transport and facts.** It is deliberately harness-neutral. Harness-specific behavior belongs in a sibling module that imports it, not in it.
4. **`ocdeck/device.py` / `art.py` / `focus.py`.** USB, pixels, and foreground activation are Windows/desktop problems, not harness problems.
5. **The identity rules.** PID + creation timestamp pairing, the `.claim` file for managed bindings, exact window-token matching. Do not loosen identity to make a test pass — the whole point is that a dead or reused process can never steal a key.

If your change *does* have to touch the core, that's allowed — but the PR should explain which invariant moved and why no adapter could have absorbed it, and it should update `docs/API.md` / `docs/ARCHITECTURE.md` in the same PR.

## Adding a new harness: the checklist

- [ ] New module in `plugins/` (e.g. `plugins/<harness>.mjs`) importing `Bridge`/`Facts` from `core.mjs`; zero new npm dependencies.
- [ ] Status mapping tested: busy, retry, idle, pending>0, stale/unknown, and "snapshot failure → unknown, not false idle".
- [ ] Pending count uses real request IDs (ask/reply pairs), survives duplicates, clears on reject/cancel.
- [ ] Registration idempotent; re-register after broker restart restores full state including pending.
- [ ] One runtime per managed window assumption stated honestly in the module header (or handled, if your harness allows it).
- [ ] `node --check` passes on every plugin file.
- [ ] `scripts\Test.ps1` passes (Python suite + Node suite).
- [ ] README's "Today: OpenCode. Tomorrow: your harness." section updated with your harness in the supported list.
- [ ] `docs/TEST-RESULTS.md` updated with what you verified and what you couldn't — no gate gets marked "passed" from code inspection alone.

## Ground rules

- **Windows is the reference platform.** The broker, focus, and managed launcher are Windows-native; keep other platforms working as far as they already do (the lock and registry are portable; focus and launcher are not, and that's documented).
- **No silent config mutation.** The installer already refuses to overwrite unmarked files and backs up `tui.json`. Extend that caution, don't waive it.
- **Be honest about unverified gates.** This project's culture is: *implemented* ≠ *verified on hardware*. Record evidence, name the environment, and leave the unverified table row unverified.
- **Don't bind the broker to `0.0.0.0`.** Loopback + local token is a feature.
- **Small PRs, named invariants.** "Add Codex adapter" beats "refactor transport and add Codex adapter".

## Where to start reading

`docs/ARCHITECTURE.md` → `docs/API.md` → `tests/test_system.py` (the registry spec) → `plugins/server.mjs` (the reference adapter) → `tests/facts.test.mjs` + `tests/bridge-integration.mjs` (what "correct" looks like end to end).
