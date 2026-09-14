# Optional Windows sound alerts and desktop notifications

[Project overview](../../README.md) · [Documentation index](../README.md)

AgentStreamDeck can chime when a selected state changes and show a Windows notification for a newly identified request. Both channels default off. This lets you keep watching your code while hearing that another agent needs a response.

Merge this into the existing config, then restart the broker:

```json
{"alerts":{"sound":true,"toast":true,"states":["input"],"cooldown_seconds":10,"muted_slots":["2"]}}
```

| Control | Effect |
|---|---|
| sound | Enables Windows SystemExclamation or a selected WAV |
| sound_file | Optional WAV path, e.g. `C:\Sounds\input.wav`; escape backslashes in JSON |
| states | Sound transitions: input, running, idle, unknown |
| cooldown_seconds | Global sound rate limit, 0–3600 seconds |
| toast | Request-specific desktop notifications |
| muted_slots | One-based strings; suppress sound and toast for those slots |

## Sound and toast are different signals

Sound is eligible when a slot enters a selected state. Repeated identical snapshots do not retrigger it. The cooldown is global across slots, not a separate timer per agent. INPUT without an identified request can still trigger sound.

Toast delivery requires a newly identified request. Several new IDs in one snapshot produce one slot notification; repeated delivery and stale-state recovery do not repeat it during the broker lifetime. Restarting the broker resets deduplication history. Changing `states` does not convert toasts into generic running/idle notifications.

The first opted-in toast registers the per-user AgentStreamDeck notification identity. Windows notification preferences, Do Not Disturb/Focus Assist and fullscreen or presentation conditions can suppress delivery. Delivery is normal priority with silent toast audio. Sounds and toasts run independently of USB rendering; Linux mock tests exercise decision logic without delivering Windows notifications.

## Verify your preference

Start with a supported identified OpenCode question. Verify one notification, leave it pending across snapshots, and verify it does not repeat. Mute that slot and create another request. Test with and without Do Not Disturb. An activity-only integration cannot supply request-specific notifications for IDs it never reports.

Source: [alert transitions and delivery](../../ocdeck/alerts.py), [validation](../../ocdeck/settings.py).

## Related guides

[Input coverage](STATUS.md) · [Config fields](../reference/CONFIG.md) · [Diagnostics](DIAGNOSTICS.md)
