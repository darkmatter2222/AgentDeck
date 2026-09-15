# Repository source map and feature-to-code reference

[World module boundaries and design contract](DESIGN_SYSTEM.md#implementation-boundaries)

[Project overview](../../README.md) · [Documentation index](../README.md)

The source is organized around a local broker, two producer paths, physical rendering, and a separate companion subsystem. Use this map to find implementation details and related user documentation.

| Area | Source | Purpose | User documentation |
|---|---|---|---|
| CLI | [__main__.py](../../ocdeck/__main__.py) | Command parser and dispatch | [Complete CLI](../CLI.md) |
| Startup | [bootstrap.py](../../ocdeck/bootstrap.py) | Per-user OS setup and metadata | [Startup](../features/STARTUP.md) |
| Discovery | [common.py](../../ocdeck/common.py) | Config, atomic JSON, auth requests and exact PID identity | [Config](../reference/CONFIG.md) |
| Broker | [broker.py](../../ocdeck/broker.py) | HTTP server, lock and workers | [API](../API.md) |
| Registry | [model.py](../../ocdeck/model.py) | Assignments, generations, stale snapshots, overflow | [Status](../features/STATUS.md) |
| Direct hooks | [direct_hooks.py](../../ocdeck/direct_hooks.py) | Native session identity and event state | [Integrations](../integrations/README.md) |
| Device | [device.py](../../ocdeck/device.py) | HID, reconnect, draw loop, button routing | [Hardware](../features/HARDWARE.md) |
| Focus | [focus.py](../../ocdeck/focus.py) | Windows ownership, activation and keyboard focus | [Focus](../features/FOCUS.md) |
| Appearance | [appearance.py](../../ocdeck/appearance.py), [appearance_io.py](../../ocdeck/appearance_io.py), [art.py](../../ocdeck/art.py) | Defaults, validation, sharing, key rendering | [Appearance](../reference/APPEARANCE.md) |
| Optional settings | [settings.py](../../ocdeck/settings.py) | Config validation before workers start | [Config](../reference/CONFIG.md) |
| Alerts | [alerts.py](../../ocdeck/alerts.py) | State transitions and Windows notification delivery | [Alerts](../features/ALERTS.md) |
| Online updates | [updates.py](../../ocdeck/updates.py), [jelly_update.py](../../ocdeck/jelly_update.py) | PyPI discovery, explicit installation and UI | [Updates](../features/UPDATES.md) |
| Local upgrades | [upgrade_watch.py](../../ocdeck/upgrade_watch.py) | Installed version/file validation and restart | [Updates](../features/UPDATES.md) |
| Diagnostics | [diagnostics.py](../../ocdeck/diagnostics.py), [hardware_check.py](../../ocdeck/hardware_check.py), [observability.py](../../ocdeck/observability.py) | Doctor, reports, logs and interactive HID test | [Diagnostics](../features/DIAGNOSTICS.md) |
| Security/errors | [security.py](../../ocdeck/security.py), [errors.py](../../ocdeck/errors.py) | Scrubbing and actionable error codes | [Privacy](../features/PRIVACY.md) |
| Legacy supervisors | [launcher.py](../../ocdeck/launcher.py), [harness.py](../../ocdeck/harness.py) | Managed children and installer bridge | [Launchers](../LAUNCHERS.md) |
| Removal | [uninstall.py](../../ocdeck/uninstall.py) | Receipt-aware cleanup and backups | [Uninstall](../features/UNINSTALL.md) |
| Jelly movement | [jelly.py](../../ocdeck/jelly.py), [jelly_catalog.py](../../ocdeck/jelly_catalog.py) | Geometry, choreography and catalog | [Jelly catalog](../jelly/README.md) |
| Jelly art | [jelly_art.py](../../ocdeck/jelly_art.py), [jelly_cute.py](../../ocdeck/jelly_cute.py) | Pixel art, palette and face refinements | [Gallery](../GALLERY.md) |
| Jelly mind | [jelly_mind.py](../../ocdeck/jelly_mind.py), [jelly_words.py](../../ocdeck/jelly_words.py) | Needs, moods and authored thoughts | [Jelly settings](../reference/JELLY.md) |
| Coffee | [coffee.py](../../ocdeck/coffee.py) | Invitation scheduling and bundled cup artwork | [Coffee](../features/COFFEE.md) |
| Package version | [__init__.py](../../ocdeck/__init__.py) | Runtime version | [Releases](../PYPI.md) |

## Every JavaScript plugin module

| Source | Responsibility |
|---|---|
| [core.mjs](../../plugins/core.mjs) | Shared Facts, authenticated Bridge and registration |
| [server.mjs](../../plugins/server.mjs) | Global OpenCode server plugin and SDK reconciliation |
| [tui.mjs](../../plugins/tui.mjs) | Optional OpenCode TUI compatibility adapter |
| [profiles.mjs](../../plugins/harnesses/profiles.mjs) | Native event/config mapping and legacy HookFacts reducer |
| [hook.mjs](../../plugins/harnesses/hook.mjs) | Short-lived metadata normalizer and direct/legacy transport |
| [install.mjs](../../plugins/harnesses/install.mjs) | Project config merge, ownership receipts, backup/removal |
| [bridge.mjs](../../plugins/harnesses/bridge.mjs) | Legacy local per-launch hook relay |

## Scripts and examples

### scripts

| Script | Entry point |
|---|---|
| [check-docs.py](../../scripts/check-docs.py) | Local links, media, JSON examples and CLI/settings coverage |
| [Install-Harness.ps1](../../scripts/Install-Harness.ps1) | Source-checkout helper; inspect parameters before use |
| [Install.ps1](../../scripts/Install.ps1) | Source-checkout helper; inspect parameters before use |
| [Launch-Agent.bat](../../scripts/Launch-Agent.bat) | Source-checkout helper; inspect parameters before use |
| [Launch-Claude.bat](../../scripts/Launch-Claude.bat) | Source-checkout helper; inspect parameters before use |
| [Launch-Codex.bat](../../scripts/Launch-Codex.bat) | Source-checkout helper; inspect parameters before use |
| [Launch-Copilot-VSCode.bat](../../scripts/Launch-Copilot-VSCode.bat) | Source-checkout helper; inspect parameters before use |
| [Launch-Copilot.bat](../../scripts/Launch-Copilot.bat) | Source-checkout helper; inspect parameters before use |
| [Launch-Cursor.bat](../../scripts/Launch-Cursor.bat) | Source-checkout helper; inspect parameters before use |
| [Launch-Gemini.bat](../../scripts/Launch-Gemini.bat) | Source-checkout helper; inspect parameters before use |
| [Remove-Integration.ps1](../../scripts/Remove-Integration.ps1) | Source-checkout helper; inspect parameters before use |
| [Run-OpenCode.ps1](../../scripts/Run-OpenCode.ps1) | Source-checkout helper; inspect parameters before use |
| [Test.ps1](../../scripts/Test.ps1) | Source-checkout helper; inspect parameters before use |
| [Uninstall.ps1](../../scripts/Uninstall.ps1) | Source-checkout helper; inspect parameters before use |
| [Verify-Windows.ps1](../../scripts/Verify-Windows.ps1) | Historical task/venv diagnostic; use current doctor/status instructions |
| [check-js.py](../../scripts/check-js.py) | Source-checkout helper; inspect parameters before use |
| [preview_coffee.py](../../scripts/preview_coffee.py) | Source-checkout helper; inspect parameters before use |
| [preview_jelly.py](../../scripts/preview_jelly.py) | Source-checkout helper; inspect parameters before use |
| [preview_jelly_life.py](../../scripts/preview_jelly_life.py) | Source-checkout helper; inspect parameters before use |
| [preview_jelly_update.py](../../scripts/preview_jelly_update.py) | Source-checkout helper; inspect parameters before use |
| [preview_jelly_v3.py](../../scripts/preview_jelly_v3.py) | Source-checkout helper; inspect parameters before use |
| [readme_hero.py](../../scripts/readme_hero.py) | Source-checkout helper; inspect parameters before use |
| [render-gallery.py](../../scripts/render-gallery.py) | Source-checkout helper; inspect parameters before use |
### scripts/examples

| Script | Entry point |
|---|---|
| [Claude-Cloud.bat](../../scripts/examples/Claude-Cloud.bat) | Source-checkout helper; inspect parameters before use |
| [Claude-Local.bat](../../scripts/examples/Claude-Local.bat) | Source-checkout helper; inspect parameters before use |
| [HomeAILab-Claude-5090.bat](../../scripts/examples/HomeAILab-Claude-5090.bat) | Source-checkout helper; inspect parameters before use |
| [HomeAILab-Claude-Cluster.bat](../../scripts/examples/HomeAILab-Claude-Cluster.bat) | Source-checkout helper; inspect parameters before use |
| [HomeAILab-OpenCode-5090.bat](../../scripts/examples/HomeAILab-OpenCode-5090.bat) | Source-checkout helper; inspect parameters before use |
| [HomeAILab-OpenCode-Spark.bat](../../scripts/examples/HomeAILab-OpenCode-Spark.bat) | Source-checkout helper; inspect parameters before use |
| [OpenCode-Cloud.bat](../../scripts/examples/OpenCode-Cloud.bat) | Source-checkout helper; inspect parameters before use |

## Packaging, assets and hardware model

[pyproject.toml](../../pyproject.toml) defines package metadata, dependencies and commands. [setup.py](../../setup.py) copies plugin/PowerShell assets into wheel runtime storage. [MANIFEST.in](../../MANIFEST.in) controls source distribution content. [THIRD-PARTY.md](../../THIRD-PARTY.md) records artwork provenance. [The printable mount](../../3d-models/side-monitor-mount/README.md) has separate source CAD, STL parts and digital mesh checks. The checked-in SHA256SUMS manifest covers repository files; release-asset checksums are separately generated by the publishing workflow.

## Tests by source file

| Test source | Coverage entry point |
|---|---|
| [bridge-integration.mjs](../../tests/bridge-integration.mjs) | Automated fixture/integration assertions; inspect the test for scope |
| [facts.test.mjs](../../tests/facts.test.mjs) | Automated fixture/integration assertions; inspect the test for scope |
| [harnesses.test.mjs](../../tests/harnesses.test.mjs) | Automated fixture/integration assertions; inspect the test for scope |
| [live_codex.py](../../tests/live_codex.py) | Opt-in live harness scenario; not automatic native acceptance |
| [live_opencode.py](../../tests/live_opencode.py) | Opt-in live harness scenario; not automatic native acceptance |
| [next.test.mjs](../../tests/next.test.mjs) | Automated fixture/integration assertions; inspect the test for scope |
| [test_appearance.py](../../tests/test_appearance.py) | Automated fixture/integration assertions; inspect the test for scope |
| [test_coffee.py](../../tests/test_coffee.py) | Automated fixture/integration assertions; inspect the test for scope |
| [test_customization.py](../../tests/test_customization.py) | Automated fixture/integration assertions; inspect the test for scope |
| [test_focus.py](../../tests/test_focus.py) | Automated fixture/integration assertions; inspect the test for scope |
| [test_harness.py](../../tests/test_harness.py) | Automated fixture/integration assertions; inspect the test for scope |
| [test_jelly.py](../../tests/test_jelly.py) | Automated fixture/integration assertions; inspect the test for scope |
| [test_jelly_life.py](../../tests/test_jelly_life.py) | Automated fixture/integration assertions; inspect the test for scope |
| [test_jelly_self_update.py](../../tests/test_jelly_self_update.py) | Automated fixture/integration assertions; inspect the test for scope |
| [test_launch_wrappers.py](../../tests/test_launch_wrappers.py) | Automated fixture/integration assertions; inspect the test for scope |
| [test_next.py](../../tests/test_next.py) | Automated fixture/integration assertions; inspect the test for scope |
| [test_pip_restart.py](../../tests/test_pip_restart.py) | Automated fixture/integration assertions; inspect the test for scope |
| [test_plugin_first.py](../../tests/test_plugin_first.py) | Automated fixture/integration assertions; inspect the test for scope |
| [test_system.py](../../tests/test_system.py) | Automated fixture/integration assertions; inspect the test for scope |
| [test_update_indicator.py](../../tests/test_update_indicator.py) | Automated fixture/integration assertions; inspect the test for scope |
| [test_upgrade_watch.py](../../tests/test_upgrade_watch.py) | Automated fixture/integration assertions; inspect the test for scope |

## Related guides

[Developer hub](README.md) · [Architecture](../ARCHITECTURE.md) · [API](../API.md) · [Verification record](../TEST-RESULTS.md)

World object silhouettes and material animations live in [world_props.py](../../ocdeck/world_props.py); costume overlays and atmosphere remain in [world_art.py](../../ocdeck/world_art.py). Review their [complete artwork gallery](../jelly/artwork.md).

[world_interactions.py](../../ocdeck/world_interactions.py) directs object use with separate prop state and foreground grip sprites. See the [per-prop review](../jelly/prop-review.md).
