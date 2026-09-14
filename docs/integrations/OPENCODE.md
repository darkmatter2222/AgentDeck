# OpenCode Stream Deck integration and global plugin setup

[Project overview](../../README.md) · [Documentation index](../README.md)

OpenCode uses a global server plugin instead of a per-project hook profile. One process-wide adapter aggregates its sessions into the runtime’s key, tracks permission/question IDs and sends complete snapshots to the local broker.

## Install and launch normally

```powershell
python -m pip install --upgrade agentstreamdeck
python -m ocdeck install
opencode
```

If OpenCode was not on PATH during installation, install it separately and rerun install, or run `python -m ocdeck install-plugin --mode server` after broker setup. Restart OpenCode processes after installing/changing the plugin.

The plugin entry is `plugins/ocdeck.js` inside the selected OpenCode config directory. It points to packaged runtime assets, so ordinary users do not need a checkout. An unmarked existing ocdeck.js is refused rather than overwritten.

## Alternative configuration homes

The installer uses `--config-dir` first, then OPENCODE_CONFIG_DIR, then XDG_CONFIG_HOME/opencode, then ~/.config/opencode.

```powershell
python -m ocdeck install-plugin --mode server --config-dir C:\Tools\OpenCodeConfig
```

Ensure the running OpenCode process uses that same config home. Multiple config homes need their own plugin entries.

## State and reconciliation

The plugin handles session.status, session.idle, session.deleted, session.error, permission.asked/replied and question.asked/replied/rejected. Sets of unresolved IDs resist duplicate events. Known counts appear as 1–9 or 9+ in supported artwork.

A shared Bridge re-registers and publishes snapshots approximately every two seconds and flushes on events. SDK reconciliation is attempted when session.status, permission.list and question.list methods are available; it is version-dependent. An intervening live event prevents an older reconciliation result from overwriting it. Snapshot failures yield unknown rather than false idle.

One plugin instance is reused per OpenCode process. Several sessions in one runtime do not necessarily mean several physical keys. Multiple unrelated clients attached to one server and exact tab selection are not supported as independent focus targets. Unmanaged headless serve/run/web/acp processes are skipped; use an interactive local OpenCode window for the documented workflow.

## TUI compatibility mode

`python -m ocdeck install-plugin --mode tui` adds the packaged TUI adapter URI to tui.json and removes the owned server entry. It refuses tui.jsonc or JSONC disguised as JSON so comments are not destroyed. The implementation and native TUI lifecycle differ from the default server path; see [the TUI adapter](../../plugins/tui.mjs) before using it. Avoid loading duplicate server and TUI entries manually. Returning to server mode requires checking/removing a lingering owned TUI entry; the server installer does not automatically clean that list.

## Verify

Run `python -m ocdeck status --json`, start a task, trigger a supported permission or question and observe the corresponding key. Resolve it in OpenCode, then verify the input count clears. Restart the broker and verify heartbeat recovery. Press the key from another window to verify Windows focus, and check physical input_events separately.

Source: [server plugin](../../plugins/server.mjs), [facts and Bridge](../../plugins/core.mjs), [plugin installer](../../ocdeck/launcher.py).

## Related guides

[All integrations](README.md) · [Status/counts](../features/STATUS.md) · [Focus](../features/FOCUS.md) · [Plugin-first setup](../PLUGIN-FIRST.md)
