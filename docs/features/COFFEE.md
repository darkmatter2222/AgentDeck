# Jelly tap reactions and coffee invitations

[Project overview](../../README.md) · [Documentation index](../README.md)

Tap Jelly on an unused key and he reacts with a short wobble, cheer or other touch response. His short touch message can appear even when ambient thoughts are disabled.

![Jelly points to a steaming support cup](../jelly/coffee_break.gif)

## Two ways to invite a coffee break

| Trigger | Behavior |
|---|---|
| Timed invitation | A random 1–3 hour interval, requiring two unassigned keys |
| Five taps | Five Jelly presses within a rolling sixty-second window request the same routine early |

During the invitation Jelly stays on one free key, points toward a steaming cup on another and says “Coffee?” with optional rainbow body colors. The invitation lasts up to sixty seconds. The fifth tap presents it; it does not immediately open a browser. A subsequent press on **either Jelly or the cup** opens [Ryan’s verified Buy Me a Coffee page](https://buymeacoffee.com/j6oiubzfnh) and dismisses the invitation.

The two keys do not have to be adjacent. Agent assignments preempt the presentation, and the update indicator has higher priority. Delayed key events are checked against the displayed invitation and slot generation. After a finished/dismissed break a fresh 1–3 hour interval is scheduled; restarting the broker starts a new delay. Artwork is bundled and the invitation itself works offline.

## Preference controls

```json
{"jelly":{"coffee":false}}
```

This disables both timed and five-tap invitations. `coffee_rainbow: false` keeps the ordinary mood palette during an enabled invitation. `jelly.enabled: false` turns off the companion and its coffee UI. The current runtime support destination is Buy Me a Coffee; a different README support service would not automatically change the runtime URL.

Source: [coffee timing and drawing](../../ocdeck/coffee.py), [tap routing and priority](../../ocdeck/device.py), [coffee regression tests](../../tests/test_coffee.py).

## Related guides

[Jelly guide](../JELLY.md) · [Jelly settings](../reference/JELLY.md) · [Update priority](UPDATES.md) · [Privacy](PRIVACY.md)
