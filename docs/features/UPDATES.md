# Package upgrades, Jelly update button and automatic restart

[Project overview](../../README.md) · [Documentation index](../README.md)

There are two independent mechanisms: discovering a newer published version and noticing that you already installed a newer version locally.

| Mechanism | Trigger | Network | Control |
|---|---|---|---|
| Version discovery | Startup and approximately every five minutes | PyPI JSON lookup | check_updates |
| Jelly install action | Press the marked Jelly after discovery | pip package installation | Explicit physical press |
| Installed-version watcher | A changed package in the broker’s Python environment | No lookup required | auto_restart_on_upgrade |

## Update with Jelly

![Jelly update indicator at native key sizes](../jelly/update_available.gif)

When a newer stable package is found, Jelly shows rainbow colors, a red exclamation point, green arrow and “Update available” footer. He changes keys at most once every thirty seconds so the notice stays readable. Press that marked Jelly to install the detected version into the broker's Python environment and restart it. The display changes to “Updating / please wait.” Discovery alone does not install anything.

Agent assignments take priority and update UI requires a free Jelly key. If every key is occupied, or Jelly/animations are disabled, use the CLI update path. Update mode takes precedence over coffee invitations. Failed updates are reported in device/update status and logs; inspect status before retrying.

## Update with pip

```powershell
python -m pip install --upgrade agentstreamdeck
python -m ocdeck --version
python -m ocdeck status --json
```

Use the same interpreter environment that runs the broker. With the installed-version watcher active, the broker waits for pip to finish and files to stabilize, verifies package records and a fresh import, then schedules a restart. Typical detection/stabilization is around 10–20 seconds after pip completes, plus shutdown/startup time. It preserves the data/config directory.

The watcher excludes source checkouts and editable installs. Reinstalling the same version does not trigger restart. A stopped broker is not started by pip, and a first install still needs `python -m ocdeck install`. If upgrading a broker older than the watcher feature, restart once to load it. Hook clients recover on their next event; conventional producers re-register through their normal heartbeat.

## Control update behavior

```json
{"check_updates":false,"auto_restart_on_upgrade":false}
```

The first field disables online discovery; the second disables automatic restart after a separate local upgrade. To keep manual pip upgrades activating automatically while disabling online checks, change only `check_updates`.

The lookup is bounded to a three-second network timeout and a capped response. Offline failures do not block agent monitoring. Prereleases are excluded from the normal newer-stable comparison.

Source: [lookup/install](../../ocdeck/updates.py), [Jelly update UI](../../ocdeck/jelly_update.py), [installed-version watcher](../../ocdeck/upgrade_watch.py).

## Related guides

[Startup and restart](STARTUP.md) · [Jelly](../JELLY.md) · [Coffee](COFFEE.md) · [Release workflow](../PYPI.md)
