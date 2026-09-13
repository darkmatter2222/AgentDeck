# Documentation

[AgentStreamDeck overview and quick start](../README.md)

## Set up your deck

| Goal | Guide |
|---|---|
| Install the broker and launch agents normally | [Plugin-first setup](PLUGIN-FIRST.md) |
| Connect a specific coding agent | [Supported integrations](HARNESSES.md) |
| Use remote sessions or WSL | [Remote and WSL](REMOTE-AND-WSL.md) |
| Change colors, labels, logos or layouts | [Appearance](APPEARANCE.md) |
| Customize Jelly or disable coffee invitations | [Jelly](JELLY.md) |
| Configure alerts, update, troubleshoot logs or uninstall | [Configuration and maintenance](CONFIGURATION.md) |
| Diagnose a problem | [Troubleshooting](TROUBLESHOOTING.md) |
| Migrate an older AgentDeck installation | [Rename and migration](RENAMING.md) |

The pip distribution is `agentstreamdeck`; run the CLI as `python -m ocdeck`.
A source checkout is needed only for development, not normal installation.

## Develop and contribute

| Topic | Guide |
|---|---|
| Contribution workflow and tests | [Contributing](../CONTRIBUTING.md) |
| Broker and integration design | [Architecture](ARCHITECTURE.md) |
| Local broker endpoints | [API](API.md) |
| Jelly implementation and rendering | [Engineering report](jelly/ENGINEERING.md) |
| Automated evidence and hardware checks | [Test results](TEST-RESULTS.md) |
| Package publishing | [PyPI and releases](PYPI.md) |
| Release history | [GitHub releases](https://github.com/darkmatter2222/AgentStreamDeck/releases) |

Additional references: [extended feature guide](NEXT.md), [tutorials](TUTORIALS.md),
and [compatibility launchers](LAUNCHERS.md). Some examples in those references
use a source checkout or older compatibility commands; start with the setup guide above.
