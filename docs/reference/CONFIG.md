# Complete broker configuration and environment reference

[Project overview](../../README.md) · [Documentation index](../README.md)

AgentStreamDeck reads `config.json` from `%USERPROFILE%\.opencode-deck` on Windows or `~/.opencode-deck` elsewhere. `OCDECK_HOME` selects another data directory. Use the same directory and OS user for the broker and native hooks. Configuration is JSON, without comments or trailing commas. Merge changes and restart the broker; settings are not hot-reloaded.

| Top-level field | Default | Meaning and accepted values |
|---|---|---|
| `controls` | disabled | [CLI-configurable launcher and permission menus](../features/DECK-CONTROLS.md#configuration-reference); enabled, permissions, hold_ms, menu_timeout, request_timeout |
| `fps` | `24` | Integer 1–30; render-loop target, not a guaranteed USB refresh rate |
| `brightness` | `45` | Integer 0–100; hardware backlight |
| `animations` | `true` | Global motion; false also disables Jelly |
| `ready` | `true` | Initial READY artwork when no agents are registered |
| `serial` | omitted | Select an exact detected serial; one device per broker |
| `slots` | `6` | Mock capacity: 6, 15 or 32; physical deck capacity is detected |
| `allow_elgato` | `false` | Advanced bypass of the competing-process guard |
| `check_updates` | `true` on hardware | PyPI version lookup; mock defaults false unless explicitly enabled |
| `auto_restart_on_upgrade` | `true` | Watch installed package for verified version changes and restart |
| `appearance` | default fields | Global [appearance preferences](APPEARANCE.md) |
| `buttons` | `{}` | Per-slot appearance overrides with string keys `"1"` through `"32"` |
| `alerts` | channels off | [Sound and toast controls](../features/ALERTS.md) |
| `jelly` | enabled | [Companion settings](JELLY.md) |

## Every alert field

| Field under alerts | Default | Values |
|---|---|---|
| `sound` | `false` | Boolean; Windows sound delivery |
| `toast` | `false` | Boolean; Windows request-specific notifications |
| `sound_file` | omitted | WAV path; omission uses SystemExclamation |
| `states` | `["input"]` | List containing input, running, idle, unknown; affects sound only |
| `cooldown_seconds` | `10` | Finite number 0–3600; global sound rate limit |
| `muted_slots` | `[]` | List of one-based slot strings, e.g. `["2","5"]`; suppresses both channels |

## Practical complete example

```json
{
  "fps": 24,
  "brightness": 45,
  "animations": true,
  "ready": true,
  "check_updates": true,
  "auto_restart_on_upgrade": true,
  "appearance": {"layout":"harness","theme":"aurora","primary":"project","secondary":"status"},
  "buttons": {"2":{"alias":"Reviewer","primary":"alias"}},
  "alerts": {"sound":false,"toast":false,"states":["input"],"cooldown_seconds":10,"muted_slots":[]},
  "jelly": {"enabled":true,"personality":"balanced","thoughts":"normal","coffee":true}
}
```

To make a completely black deck when no agents are present, set both `ready` and `jelly.enabled` to false. Setting only `ready` false leaves Jelly available. To keep a still agent display without Jelly, set `animations` false. To disable online update checks and automatic activation of separately installed upgrades, set both `check_updates` and `auto_restart_on_upgrade` false; those mechanisms are independent.

## Environment and data files

| Name | Purpose |
|---|---|
| `OCDECK_HOME` | Shared per-user broker data directory |
| `OPENCODE_CONFIG_DIR` | Alternate OpenCode config home for plugin installation |
| `XDG_CONFIG_HOME` | Fallback base for OpenCode config, otherwise ~/.config/opencode |
| `OCDECK_BINDING` | Internal legacy OpenCode launch binding; ordinary users do not set it |
| `AGENTDECK_HOOK_BINDING` | Internal legacy hook relay binding; ordinary direct hooks do not need it |
| `config.json` | User preferences |
| `install.json` | Python interpreter, runtime path and plugin installation metadata |
| `discovery.json` / `token` | Current local broker port and separate authentication secret |
| `projects.json` | Projects recorded by hook installation |
| `broker.log` | Rotating structured diagnostic log |
| `update.json` | Cached discovered package version metadata |
| `jelly-state.json` | Optional bounded companion state |
| `backups/` | Retained configuration/metadata backups after removal |
| Project `.agentdeck/<profile>.json` | Ownership receipt used for safe hook updates/removal |

Source: [broker validation](../../ocdeck/settings.py), [config loading](../../ocdeck/common.py), [startup](../../ocdeck/bootstrap.py), [device behavior](../../ocdeck/device.py). Some internal and legacy files are generated only when their feature is used.

## Related guides

[CLI](../CLI.md) · [Appearance fields](APPEARANCE.md) · [Jelly fields](JELLY.md) · [Startup](../features/STARTUP.md) · [Uninstall](../features/UNINSTALL.md)
