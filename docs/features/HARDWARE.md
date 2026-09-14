# Stream Deck Mini, Original, MK.2 and XL hardware support

[Project overview](../../README.md) · [Documentation index](../README.md)

The controller uses direct USB HID through the StreamDeck library and packaged hidapi dependency. One broker controls one selected device. An Elgato software plugin is not required.

| Device family | Keys | Layout used by mock previews |
|---|---|---|
| Mini | 6 | 2 rows × 3 columns |
| Original / Original V2 / MK.2 | 15 | 3 rows × 5 columns |
| XL | 32 | 4 rows × 8 columns |

Detection is limited to product IDs mapped in the source. Stream Deck Plus dials/touch strip, pedal and mobile devices are not implemented by this controller. The Mini is the primary physical target; automated 15/32-key coverage does not prove hardware acceptance on every variant.

## Connect your deck

1. Plug in the deck and quit Elgato Stream Deck from its system tray menu.
2. Run `python -m ocdeck devices` and check the detected model, serial and key count.
3. If several supported decks are attached, set the exact `serial` in config; automatic opening expects one matching device.
4. Start the broker and inspect `python -m ocdeck status --json`.
5. Press a physical button and confirm device.input_events increases.

The competing-process guard is conservative: it cannot know which USB device Elgato owns. `allow_elgato: true` only bypasses the guard; it does not provide shared USB ownership. Leave it false for ordinary use.

## Physical diagnostics and recovery

Stop the background task/service and close Elgato before `python -m ocdeck hardware-check`. Follow its printed instructions to verify images and real key events. Start the broker again when finished. A mock broker cannot perform this acceptance check.

The device loop retries after disconnects and monitors the input reader thread. When a deck reconnects with a different supported capacity, assignments resize in registration order. Unchanged images skip USB writes; render timing reports requested/effective loop FPS and composition, conversion and write costs.

Top-level brightness controls the hardware backlight from 0–100. Per-button appearance brightness dims rendered pixels from 0.15–1. For a busy deck, lower fps to 15 if USB throughput makes 24 FPS impractical; the configured target is not a hardware guarantee.

## Printable monitor mount

The [Stream Deck Mini side monitor mount](../../3d-models/side-monitor-mount/README.md) includes the holder, reinforced wing, gravity-held pivot pin, locking pin, fit gauge and pin-fit coupon. The hinge uses five-degree locking positions. Follow its dimension, clearance and print-orientation guidance and inspect the supplied mesh validation; digital validation does not replace a physical fit test.

Source: [device mappings and transport](../../ocdeck/device.py), [hardware diagnostic](../../ocdeck/hardware_check.py).

## Related guides

[First run](../FIRST-RUN.md) · [Focus](FOCUS.md) · [Appearance](../APPEARANCE.md) · [Troubleshooting](../TROUBLESHOOTING.md)
