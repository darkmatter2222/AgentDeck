# Complete button appearance settings

[Project overview](../../README.md) · [Documentation index](../README.md)

Set a default under `appearance`, then override fields by one-based slot string under `buttons`. A per-slot value wins over the global value; missing fields fall back to the defaults below. An alias stays with the physical slot when another agent takes it.

| JSON field | CLI flag | Default | Values |
|---|---|---|---|
| `layout` | `--layout` | `"classic"` | classic, harness, minimal |
| `theme` | `--theme` | `"classic"` | high-contrast, classic, aurora, ocean, accessible, mono |
| `primary` | `--primary` | `"status"` | status, project, harness, detail, custom, alias, none |
| `secondary` | `--secondary` | `"project"` | same choices as primary |
| `custom_text` | `--custom-text` | `""` | 0–100 characters |
| `show_slot` | `--show-slot` | `true` | true / false |
| `effect` | `--effect` | `"breathe"` | breathe, glow, steady |
| `intensity` | `--intensity` | `0.55` | 0–1 |
| `speed` | `--speed` | `1.0` | 0.25–3; 1 = two-second cycle |
| `brightness` | `--brightness` | `1.0` | 0.15–1; image dimming |
| `alias` | `--alias` | `""` | 0–100 characters; empty restores project name |
| `text_effect` | `--text-effect` | `"none"` | none, scroll, shimmer |
| `text_size` | `--text-size` | `"normal"` | small, normal, large |
| `text_align` | `--text-align` | `"center"` | left, center, right |
| `badge` | `--badge` | `"dot"` | dot, ring, pill; harness layout |
| `border` | `--border` | `"solid"` | solid, double, corners, none |
| `background` | `--background` | `"solid"` | solid, gradient, grid |
| `logo_size` | `--logo-size` | `"normal"` | small, normal, large; harness layout |

`--no-show-slot` is the negative form of `--show-slot`. Numeric values must be finite. The hardware backlight is the separate top-level `brightness` setting, 0–100. Badge and logo controls affect the harness layout. Custom text is reused if both text lines select `custom`.

## Presets and precedence

A preset starts from the default appearance, applies the following fields and writes the result at the selected global or slot scope. Existing alias/custom text are preserved. Explicit flags apply last. There is no JSON `preset` field.

| Preset | Field overrides |
|---|---|
| `studio` | `layout=harness`, `theme=aurora`, `primary=alias`, `secondary=status`, `show_slot=False`, `background=gradient` |
| `neon` | `layout=harness`, `theme=ocean`, `effect=glow`, `intensity=0.85`, `border=double`, `background=grid`, `text_effect=shimmer` |
| `focus` | `layout=harness`, `theme=mono`, `effect=steady`, `primary=alias`, `secondary=status`, `border=corners`, `show_slot=False` |
| `readable` | `layout=minimal`, `theme=accessible`, `text_size=large`, `primary=status`, `secondary=alias`, `effect=steady` |
| `marquee` | `layout=harness`, `theme=aurora`, `primary=alias`, `secondary=status`, `text_effect=scroll`, `speed=0.5`, `show_slot=False` |

## Readable labels and static operation

Keep one text line set to `status` when using monochrome or unfamiliar colors. Ring/pill badges add non-color cues. The agent-label bitmap font replaces unsupported characters with `?`; Jelly thoughts use a separate text renderer. Long labels are measured and shortened unless scrolling is selected. Scrolling pauses at each end and clips inside its line; short text remains still.

`effect: steady` freezes agent icon and text motion. `animations: false` disables global motion and Jelly. `speed` controls icon and text phase together. `intensity` adjusts pulsing, not shimmer strength. Actual USB FPS depends on deck model and active keys.

## Export, import and preview

```powershell
python -m ocdeck appearance --preset studio --alias Builder --dry-run
python -m ocdeck preview --preset studio --alias Builder --output studio.gif
python -m ocdeck appearance --preset studio --alias Builder
python -m ocdeck appearance --export my-look.json
python -m ocdeck appearance --import my-look.json --dry-run
python -m ocdeck appearance --import my-look.json
```

Export schema version 1 contains `appearance`, `buttons`, and `fps` only. It excludes device serial, alerts, Jelly settings and credentials. Import replaces those three visual fields, resetting omitted FPS to 24 and omitted visual objects to empty objects. Other broker settings survive. Dry-run produces an in-memory PNG data URI and no files. A GIF preview always uses a sample six-key layout; dry-run uses the configured mock slot count.

Source: [appearance validation](../../ocdeck/appearance.py), [import/export](../../ocdeck/appearance_io.py), [renderer](../../ocdeck/art.py).

## Related guides

[Visual gallery](../GALLERY.md) · [Appearance recipes](../APPEARANCE.md) · [CLI](../CLI.md) · [Configuration](CONFIG.md)
