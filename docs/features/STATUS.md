# Live AI agent status, input counts and slot assignment

[Project overview](../../README.md) · [Documentation index](../README.md)

AgentStreamDeck gives each monitored local session or runtime a physical button. Launch your configured coding agent normally, work in its terminal or editor, then glance at the deck to decide which window needs attention. The display follows events; it does not inspect the terminal screen to guess whether work finished.

| Visible state | Default appearance | Meaning | Press action |
|---|---|---|---|
| Running | Green moving indicator | Producer reports busy or retry | Focus agent window |
| Idle | Amber breathing indicator | Producer reports idle/turn end | Focus agent window |
| Input | Red attention indicator | Known pending requests or an observed input-needed state | Focus agent window |
| Unknown | Amber LINK ? | Missing, stale or untrustworthy state | Try focus; inspect terminal |
| READY | Initial system artwork | No active assignments and ready enabled | No agent assignment |
| Off | Black, or available for Jelly | Unassigned slot | Jelly action only if one is displayed |

These colors describe the classic palette. Themes can change colors; keep status text visible for unambiguous identification. **Pressing an agent key never answers a question or approves a tool.**

## Pending requests: known counts and honest uncertainty

OpenCode keeps sets of permission/question identities and can provide a complete count. Supported artwork shows 1–9 or `9+`. Native hook profiles expose `pending: null` in public status because their total is unknown. Paired question IDs may still establish INPUT and support request-specific notifications without proving a complete count.

Codex can report an observed approval request with an unknown count. Claude questions can use paired AskUserQuestion IDs. Unpaired Claude/Gemini permission notifications become unknown. Copilot and Cursor have activity-only limitations. A green key is not a universal guarantee that the agent needs no response.

## Assignment, capacity and cleanup

Mini has six keys, Original/MK.2 fifteen and XL thirty-two. New records take the first free slot. Excess records remain in overflow and take a released slot in registration order. There are no implemented overflow pages to switch through. On device capacity change, records are reassigned in registration order.

Closing an agent releases its slot on a delivered session-end event or confirmed process death. Event-driven hook records retain their last state while the verified local process is alive. Conventional snapshot records become unknown after the default ten-second stale interval without a trustworthy state snapshot. A lost connection is not treated as proof the process exited.

READY is device artwork, not a registry record. It can reserve a free key while the deck is empty, and Jelly uses the other free keys. Assignments immediately take priority over Jelly, coffee and update overlays. Slot-based aliases stay with their slot when it is reassigned.

## Observe a session

```powershell
python -m ocdeck status --json
python -m ocdeck focus 1
```

Status returns zero-based `slot` values in API objects; CLI `focus 1` means the first physical key. A generation counter changes with reassignment so delayed presses cannot focus a different session that inherited the button.

Source: [registry](../../ocdeck/model.py), [device UI](../../ocdeck/device.py), [OpenCode facts](../../plugins/core.mjs), [hook reducer](../../ocdeck/direct_hooks.py).

## Related guides

[Integration coverage](../integrations/README.md) · [Focus](FOCUS.md) · [Alerts](ALERTS.md) · [API](../API.md)
