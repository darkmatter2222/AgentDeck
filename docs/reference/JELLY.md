# Jelly configuration reference and personality recipes

[Project overview](../../README.md) · [Documentation index](../README.md)

The full default Jelly object below is taken from the current settings validator. Merge this object with existing broker configuration and restart the broker. `animations: false` disables Jelly even when `enabled` is true.

```json
{
  "jelly": {
    "enabled": true,
    "virtual_gap": 8,
    "behavior_seed": null,
    "hop_style": "classic",
    "personality": "balanced",
    "mood_colors": true,
    "needs": true,
    "reactions": true,
    "thoughts": "normal",
    "local_movement": "normal",
    "travel": "normal",
    "persistent": false,
    "coffee": true,
    "coffee_rainbow": true
  }
}
```


| Setting | Accepted values and effect |
|---|---|
| `enabled` | Boolean; shows Jelly on unassigned keys when animations are enabled |
| `virtual_gap` | Integer 0–40; simulated native-pixel distance between key viewports, default 8 |
| `behavior_seed` | Integer or null; deterministic behavior for repeatable previews |
| `hop_style` | One of the fourteen catalog styles, or `mood`; default `classic` |
| `personality` | `balanced`, `mellow`, `curious`, `playful` |
| `mood_colors` | Boolean; mood palette transitions or original turquoise |
| `needs` | Boolean; activity-driven internal needs simulation |
| `reactions` | Boolean; agent-state and successful-focus reactions |
| `thoughts` | `off`, `quiet`, `normal`, `chatty`; ambient frequency, not the tap-response switch |
| `local_movement` | `low`, `normal`, `high`; relative local-action frequency |
| `travel` | `rare`, `normal`, `frequent`; relative cross-key movement frequency |
| `persistent` | Boolean; retain bounded needs, mood and recent phrase IDs in jelly-state.json |
| `coffee` | Boolean; enables both timed and five-tap coffee invitations |
| `coffee_rainbow` | Boolean; rainbow body colors during the coffee invitation |

## Quiet companion recipe

```json
{"jelly":{"personality":"mellow","thoughts":"quiet","local_movement":"low","travel":"rare","coffee":false}}
```

## Playful companion recipe

```json
{"jelly":{"personality":"playful","thoughts":"chatty","hop_style":"mood","local_movement":"high","travel":"frequent"}}
```

The examples change only the listed fields. The complete defaults remain above. With thoughts off, touch reactions can still display a short response. Turning reactions off does not itself disable touch interactions or coffee. Disable coffee explicitly if you want no support invitations.

Persistence saves at approximately one-minute checkpoints and normal shutdown. Returning after a break restores energy to at least 85 and resets workload, with no away-time decay. Corrupt persistence data is ignored. Appearance exports omit Jelly settings and imports preserve them.

Source: [settings and controller](../../ocdeck/jelly.py), [mind](../../ocdeck/jelly_mind.py), [thoughts](../../ocdeck/jelly_words.py), [coffee](../../ocdeck/coffee.py).

## Related guides

[Meet Jelly](../JELLY.md) · [Animation catalog](../jelly/README.md) · [Coffee interactions](../features/COFFEE.md) · [Updates](../features/UPDATES.md)
