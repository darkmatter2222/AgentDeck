# Stream Deck user interface and every customization area

[Project overview](../README.md) · [Documentation index](README.md)

The physical deck is the user interface. AgentStreamDeck currently configures that UI through CLI flags and config.json; it does not ship a graphical settings application or Elgato property inspector.

| UI area | Available controls | Detailed guide |
|---|---|---|
| Agent identity | Official harness logo, project name, slot alias, custom text | [Labels and fields](reference/APPEARANCE.md) |
| Status | Running, idle, input, unknown; supported request counts | [Status semantics](features/STATUS.md) |
| Layout | Classic artwork, harness logo/badge, minimal glyph | [Appearance](APPEARANCE.md) |
| Color | Six themes, five presets, per-slot overrides | [Gallery](GALLERY.md) |
| Motion | Breathe/glow/steady, speed, intensity, FPS | [Complete visual settings](reference/APPEARANCE.md) |
| Typography | Two label lines, size, alignment, scrolling/shimmer | [Text options](reference/APPEARANCE.md) |
| Decoration | Dot/ring/pill badge, borders, background, logo size | [Visual settings](reference/APPEARANCE.md) |
| Brightness | Device backlight and per-key image brightness | [Config fields](reference/CONFIG.md) |
| Companion | Personality, moods, thoughts, hops, local movement, travel | [Jelly settings](reference/JELLY.md) |
| Touch | Focus agent; tap Jelly; invite coffee; install marked update | [Interaction table below](#physical-button-actions) |
| Alerts | Sound, toast, mute slots, WAV, cooldown | [Alerts](features/ALERTS.md) |
| Sharing | Validated appearance import/export and dry-run | [Appearance reference](reference/APPEARANCE.md) |

## Physical button actions

| What is displayed | What a press does |
|---|---|
| Assigned agent | Requests Windows foreground and keyboard focus |
| Ordinary Jelly | Touch reaction; five taps within a minute can invite coffee |
| Jelly or cup during coffee presentation | Opens Ryan’s support page and dismisses the invitation |
| Jelly with Update available | Installs detected package version and restarts broker |
| Blank key or READY without an agent | No agent focus action |

The action follows what was actually displayed, and current assignments take priority. Stale generations and expired invitation events are rejected. Ordinary taps never approve tools or send replies. Opt-in [hold menus](features/DECK-CONTROLS.md) provide a separate request-specific native permission review and decision screen.

## Build a look

```powershell
python -m ocdeck preview --preset neon --output neon.gif
python -m ocdeck appearance --preset neon --dry-run
python -m ocdeck appearance --preset neon
python -m ocdeck appearance --slot 2 --alias Reviewer --primary alias --secondary status
```

Preview first, save global preferences, then add a per-slot override. Restart the broker after saving. See the complete CLI reference for every accepted option and the gallery for the actual rendered results.

## Related guides

[CLI reference](CLI.md) · [Visual gallery](GALLERY.md) · [Appearance fields](reference/APPEARANCE.md) · [Jelly](JELLY.md)
