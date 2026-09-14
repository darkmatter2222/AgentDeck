# Migrate from AgentDeck to AgentStreamDeck

[Project overview](../README.md) · [Documentation index](README.md)

The project was renamed from AgentDeck to AgentStreamDeck. The distribution is now `agentstreamdeck`; the CLI and Python module remain `ocdeck`. The compatibility data directory remains `.opencode-deck` and project receipts remain `.agentdeck`. Old filenames in hooks and historical media are intentional compatibility names.

## Update an older installation

If the old agentdeck distribution is installed, stop its broker and remove that distribution before installing agentstreamdeck because they own the same Python module. Preserve the data directory and native hook configuration.

```powershell
python -m pip uninstall agentdeck
python -m pip install --upgrade agentstreamdeck
python -m ocdeck install
python -m ocdeck --version
```

Run install in the same intended environment to register the current AgentStreamDeck Broker task or Linux user service. The Windows setup recognizes an owned legacy OpenCode Deck task. Rerun native project hook installation after adapter updates and restart the harness; the rename alone is not evidence that an old hook runtime is current.

If you already use agentstreamdeck, a normal pip upgrade is sufficient when the current broker watcher is active. See [update behavior](features/UPDATES.md).

## Update an old checkout remote

The repository rename is already complete. Preserve local changes and point the existing checkout at its current URL:

```bash
git remote set-url origin https://github.com/darkmatter2222/AgentStreamDeck.git
git pull --ff-only
```

An editable/source installation is excluded from automatic installed-version restart. Restart the broker after updating source and reinstall dependencies when necessary. The current package-install path does not require a checkout.

## Old instructions to retire

Older pages referred to a required OpenCode shim, managed launchers, the OpenCode Deck scheduled task or a pinned 2.1.1 install. Current setup is plugin-first and supports other harnesses without OpenCode. Compatibility launchers still exist but are optional and may require legacy metadata. Use [first run](FIRST-RUN.md) and [the current release workflow](PYPI.md) instead of historical release setup commands.

## Related guides

[First run](FIRST-RUN.md) · [Updates](features/UPDATES.md) · [Startup](features/STARTUP.md) · [Legacy launchers](LAUNCHERS.md)
