# One-touch Windows terminal and editor window switching

[Project overview](../../README.md) · [Documentation index](../README.md)

Press an assigned Stream Deck button to return to its coding session. The broker maps the verified harness process to a Windows top-level window, checks the displayed assignment, and requests both foreground activation and keyboard focus. Minimized agent windows are maximized before activation.

## Set up reliable switching

1. Run the broker and agent as the same desktop user with compatible elevation.
2. Keep one monitored harness per OS window. Separate terminal tabs can share a top-level window and are not individually selected by the current focus implementation.
3. Install the native integration, launch the harness normally, and send a task so the first event registers it.
4. Minimize that window, press its key and confirm both the visible window and keyboard input target change.

The broker prefers a captured HWND, then a legacy exact window token, then a unique visible window owned by the harness or its nearest process ancestor. Ancestor lookup matters because Windows Terminal can own the window while the coding CLI is a child process.

## Separate USB problems from focus problems

```powershell
python -m ocdeck status --json
python -m ocdeck focus 1
```

| Observation | Next check |
|---|---|
| Physical press does not increase device.input_events | USB ownership, reconnect, device input reader |
| Input counter rises but lastFocus reports failure | Window mapping, shared tabs, user/elevation and Windows foreground policy |
| CLI focus succeeds but physical press fails | Physical input path; CLI focus is synthetic |
| Wrong tab remains visible in the right terminal | Use distinct OS windows; exact tab selection is not implemented |
| A delayed press is rejected after a slot changes | Generation protection is working; press the current displayed assignment |

A failed focus operation does not launch a replacement process or send Enter. Windows can refuse foreground activation even when the mapping is correct. Linux has no desktop-focus implementation. Optional managed Windows launchers can provide a dedicated title-pinned window but are not required for the normal integration path.

Source: [focus resolution](../../ocdeck/focus.py), [generation validation](../../ocdeck/model.py), [physical callback](../../ocdeck/device.py).

## Related guides

[Hardware](HARDWARE.md) · [Status](STATUS.md) · [Diagnostics](DIAGNOSTICS.md) · [Launchers](../LAUNCHERS.md)
