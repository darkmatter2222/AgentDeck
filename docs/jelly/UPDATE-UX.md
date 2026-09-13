# Jelly update indicator

AgentStreamDeck checks the published `agentstreamdeck` package on PyPI when the broker starts and every five minutes while it is running.

When a newer stable package is available:

- Jelly suppresses ambient thoughts so the alert remains clear.
- A red exclamation point stays above Jelly while he moves between available buttons more frequently.
- Pressing the button Jelly currently occupies explicitly starts the update.
- The updater installs the exact version detected on PyPI into the broker's current Python environment, then restarts the broker.
- Agent buttons keep priority. Jelly and the update action only occupy otherwise free buttons.

No package is installed merely because an update exists. The physical button press is the user approval to update. Set `"check_updates": false` in the existing configuration to disable update checks and this Jelly behavior.
