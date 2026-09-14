# Remove integrations, preserve settings and uninstall AgentStreamDeck

[Project overview](../../README.md) · [Documentation index](../README.md)

Close monitored sessions first so they do not keep sending events during removal. Preview the removal plan and include every project root that contains older hook installations:

```powershell
python -m ocdeck uninstall --all --scan C:\Projects --scan D:\Work --dry-run
python -m ocdeck uninstall --all --scan C:\Projects --scan D:\Work
```

The command consults recorded projects and scans supplied roots for receipts, skipping symlinks and dependency folders. All receipts are preflighted before writes. A moved project or malformed native config can stop removal so its ownership can be reconciled.

| Component | Removal behavior |
|---|---|
| Native project hooks | Removes entries matching owned receipts; preserves unrelated hooks/settings |
| Startup | Removes owned Windows task or Linux user service |
| OpenCode integration | Removes owned server/TUI integration and applicable legacy shims |
| Notification identity | Removes the owned Windows registration |
| Local config/token metadata | Moves under timestamped backups |
| Logs and backups | Retained |
| Python environment/package | Retained until you uninstall the distribution separately |

To remove only one profile in one project:

```powershell
python -m ocdeck harness-install claude --project C:\Projects\MyApp --remove --dry-run
python -m ocdeck harness-install claude --project C:\Projects\MyApp --remove
```

After complete integration removal, optionally remove the Python distribution:

```powershell
python -m pip uninstall agentstreamdeck
```

Use the same interpreter as the installed broker. Deleting the checkout or Python environment before removing hooks can leave native configs pointing at missing runtime scripts. If an owned entry was manually edited, compare the receipt and backup rather than overwriting unrelated changes. Re-enable Elgato’s software when you want it to own the hardware again.

For recovery, inspect timestamped backups and merge the specific settings you need. Do not blindly replace a newer native config with an old complete backup. Reinstalling the package and running install recreates startup; rerun project hook installation as needed.

Source: [uninstaller](../../ocdeck/uninstall.py), [hook ownership and backups](../../plugins/harnesses/install.mjs).

## Related guides

[Startup](STARTUP.md) · [Config reference](../reference/CONFIG.md) · [Integration guides](../integrations/README.md)
