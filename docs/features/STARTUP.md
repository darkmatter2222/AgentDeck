# Install, start, stop and restart the background broker

[Project overview](../../README.md) · [Documentation index](../README.md)

Install the Python package, then explicitly register the per-user background process:

```powershell
python -m pip install --upgrade agentstreamdeck
python -m ocdeck install
```

The install step creates default config only if absent, records the current interpreter/runtime location, registers startup and starts the broker. It installs the OpenCode server plugin when opencode is on PATH. It works without OpenCode for native-hook harnesses.

| Platform | Startup mechanism | Scope |
|---|---|---|
| Windows | AgentStreamDeck Broker Scheduled Task | Current interactive desktop user; limited privilege |
| Linux | agentstreamdeck.service | systemd user service; current user |
| Other platforms | Reports manual broker command | No automatic startup integration promised |

`install --no-start` registers startup without starting immediately. `install --no-opencode-plugin` skips optional OpenCode plugin installation. The process uses the Python environment from which setup was run, so use that same interpreter for future package upgrades.

## Windows service controls

```powershell
Stop-ScheduledTask -TaskName 'AgentStreamDeck Broker'
Start-ScheduledTask -TaskName 'AgentStreamDeck Broker'
```

Use Stop then Start after changing config. Close the Elgato application from the tray before starting the hardware broker. Old owned `OpenCode Deck` tasks are recognized during migration/removal; the current task name is AgentStreamDeck Broker. The legacy Verify-Windows.ps1 script checks the old task/venv and is not the current verification path.

## Linux service controls

```bash
systemctl --user status agentstreamdeck.service
systemctl --user stop agentstreamdeck.service
systemctl --user restart agentstreamdeck.service
```

Linux supports broker startup and rendering subject to local HID access, but no desktop-window focus implementation. A working user systemd session is required for `install` to start its service. In an environment without one, run the foreground broker after setup has established its local metadata or use a normal desktop session.

## Foreground and mock operation

```powershell
python -m ocdeck broker
```

A foreground broker remains tied to that terminal. `broker --mock` avoids USB and is useful for development; it is not a way to control the physical deck. Use a distinct OCDECK_HOME for isolated testing. The broker lock prevents multiple brokers sharing one data directory.

`python -m ocdeck stop` requests broker shutdown. Linux systemd has Restart=always, so stop the service when you need it to stay off for hardware-check or Elgato. Stopping the broker is different from removing startup registration.

Source: [startup implementation](../../ocdeck/bootstrap.py), [broker lifecycle](../../ocdeck/broker.py).

## Related guides

[First run](../FIRST-RUN.md) · [Integrations](../integrations/README.md) · [Updates](UPDATES.md) · [Removal](UNINSTALL.md)
