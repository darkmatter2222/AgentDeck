# AgentStreamDeck rename and upgrade

AgentDeck is now **AgentStreamDeck**, starting with version **2.1.1**.
The PyPI distribution is `agentstreamdeck`; the command and Python module remain
`ocdeck`. Existing `.opencode-deck` configuration, `OCDECK_HOME`, `.agentdeck`
receipts/backups, Copilot hook filenames, Windows notification identity and
“OpenCode Deck” scheduled task remain compatible. No hook reinstall is required
solely for this rename. Historical releases and their media keep their original names.

## Rename the GitHub repository

The connected GitHub tools cannot change repository settings. As the repository
owner, open https://github.com/darkmatter2222/AgentDeck/settings and under
**General → Repository name**, enter **AgentStreamDeck**, then click **Rename**.
GitHub redirects old repository URLs. Do not create a new repository at the old
name, because that can break the redirects. Update local checkouts:

```sh
git remote set-url origin https://github.com/darkmatter2222/AgentStreamDeck.git
git pull --ff-only
```

Links in current documentation target the new name and become active after this
settings change. Source history, issues and pull requests stay in this repository.

## Upgrade the package

Stop the broker first. If you installed the old distribution, remove it before
installing the new one because both own the same Python module:

```sh
python -m pip uninstall agentdeck
python -m pip install --upgrade agentstreamdeck==2.1.1
ocdeck --version
```

The install command above requires successful PyPI publication. Until then,
install from this checkout with `python -m pip install .`, after uninstalling the
old distribution. Restart the broker using your existing launcher/task.

## Publish to PyPI

Follow [the exact trusted publisher setup](PYPI.md) after renaming the repository.
Use project `agentstreamdeck`, owner `darkmatter2222`, repository
`AgentStreamDeck`, workflow `pypi.yml`, environment `pypi`. PyPI publication is
not complete until its workflow succeeds. Pending publishers do not reserve names.

GitHub reference: https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository
