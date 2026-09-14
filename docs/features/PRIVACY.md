# Local architecture, metadata privacy and offline operation

[Project overview](../../README.md) · [Documentation index](../README.md)

AgentStreamDeck observes coding-agent lifecycle metadata on your computer and renders physical keys. It is not a cloud agent service and does not require a language model to animate Jelly. Your chosen coding harness still has its own provider, network and privacy behavior.

| Data or action | Project behavior |
|---|---|
| Native hook payload | Normalized profile/event/session/tool/request identity, flags, working directory and parent PID |
| Prompts, commands, arguments, results, source and transcripts | Not forwarded in normal lifecycle transport; opt-in permission controls send bounded, scrubbed input previews in a separate ephemeral handoff |
| Request identifiers in public status | Hashed metadata identities |
| Process ownership | Local PID plus exact creation timestamp |
| Jelly personality | Offline session activity metadata and authored phrases |
| Appearance assets | Bundled icons and local renderers |
| Update discovery | PyPI lookup when check_updates is enabled |
| World location and weather | Enabled by default; approximate IP lookup and coordinate-based weather requests, independently disableable |
| World help | Explicit second hold opens the fixed GitHub documentation page |
| Coffee link | Browser opens only after a displayed invitation is pressed |

The broker binds an automatically selected loopback port. Its per-user discovery file identifies the port and a separate token authenticates requests. Browser Origin requests are refused, JSON bodies are capped at 64 KiB, and clients reread discovery so restarts can change ports. These assumptions describe a trusted local application protocol, not a public network API.

The direct hook process reads native input to normalize it. Default lifecycle transport forwards only allowlisted metadata. Explicit permission-control enablement additionally allows bounded native input previews in memory through a separate authenticated endpoint; previews are not included in status or logs. Lifecycle metadata still includes project labels and identifiers. Reports scrub known credential patterns but cannot guarantee that arbitrary custom label text is non-sensitive.

## Offline preferences

```json
{"check_updates":false}
```

This disables online package discovery. Also run `ocdeck world configure --no-weather --no-auto-location` and restart the broker to disable world provider requests. See [weather data and privacy](../jelly/world.md#weather-and-location). Local status, drawing, Jelly personality and installed-version monitoring can continue offline. Separately installed coding agents may still use cloud model endpoints; their network behavior is outside AgentStreamDeck. Disable coffee invitations separately with `jelly.coffee: false` if you do not want a support-link interaction.

Ordinary taps focus agent windows. Opt-in [deck controls](DECK-CONTROLS.md) add explicit session launch and native permission decisions from a separate review screen. Jelly’s marked update button explicitly installs an update, and its displayed coffee action opens the support page. There is no automatic tool approval, keystroke injection or arbitrary macro UI.

Source: [hook normalizer](../../plugins/harnesses/profiles.mjs), [transport](../../plugins/harnesses/hook.mjs), [security scrubber](../../ocdeck/security.py), [API contract](../API.md).

## Related guides

[Architecture](../ARCHITECTURE.md) · [API](../API.md) · [Remote boundary](../REMOTE-AND-WSL.md) · [Diagnostics](DIAGNOSTICS.md)
