# Practical AgentStreamDeck workflows and customization tutorials

[Project overview](../README.md) · [Documentation index](README.md)

## Launch a new agent without leaving the deck

This tutorial uses the controls feature branch. Until merged and released, install that branch with Git installed:

```powershell
python -m pip install --upgrade "git+https://github.com/darkmatter2222/AgentStreamDeck.git@feature/deck-launcher-permission-controls"
python -m ocdeck install
```

1. Choose an existing project folder. Substitute your real path in the commands below.
2. Register a friendly name and the harnesses you want in its picker. Repeating `--harness` sets their order.
3. Install the relevant project hooks. OpenCode uses the global server plugin installed by `ocdeck install`.

```powershell
python -m ocdeck controls repo set "My App" --directory "C:\Projects\MyApp" --harness claude --harness opencode --harness gemini
python -m ocdeck harness-install claude --project "C:\Projects\MyApp"
python -m ocdeck harness-install gemini --project "C:\Projects\MyApp"
python -m ocdeck controls configure --enabled --hold-ms 650 --menu-timeout 45
python -m ocdeck controls show
python -m ocdeck controls validate
Stop-ScheduledTask -TaskName 'AgentStreamDeck Broker'
Start-ScheduledTask -TaskName 'AgentStreamDeck Broker'
```

4. Hold an unused key until **RELEASE** appears, then release it. Choose **My App**, then your harness. If all keys are occupied, hold a session and choose **NEW**; you will need to close a session before launching when the deck is full.
5. Check the project, folder and agent on the confirmation screen, then press **LAUNCH**. A dedicated Windows Terminal window is requested. BACK returns to the dashboard while the adapter registers its live session.
6. Send a task in the new window. Check that the correct project key appears and a normal tap returns to it.

No manual INI editing is needed. To change folders, repeat `controls repo set "My App" --directory "..."`. To remove a profile, run `controls repo remove "My App"`. The picker rereads the catalog on its next open. [Full feature behavior](features/DECK-CONTROLS.md).

## Review and answer a permission request

1. Enable the feature explicitly, reinstall the updated Claude hooks, and restart both broker and Claude. Existing unrelated hooks remain intact.

```powershell
python -m ocdeck controls configure --enabled --permissions --request-timeout 90
python -m ocdeck harness-install claude --project "C:\Projects\MyApp"
Stop-ScheduledTask -TaskName 'AgentStreamDeck Broker'
Start-ScheduledTask -TaskName 'AgentStreamDeck Broker'
```

2. In Claude, request a harmless action that your current native rules require permission for. Do not weaken your rules just to make a test prompt appear. If no permission is needed, the deck correctly has nothing to review.
3. When a live native request arrives, its key shows input state. Hold and release that session, choose **REVIEW**, then select the specific request.
4. Read the tool/project and **DETAIL** pages. These are bounded previews. Choose **TERMINAL** if you need the complete command or arguments; this releases the hook back to native handling and focuses its window.
5. Press **ACCEPT** or **REJECT** once for the displayed request. Watch the handoff result. “Decision sent to harness” confirms the adapter response, not successful tool execution.
6. Use **REVIEW** on the result screen for another request, or **BACK** for live sessions. A stale key press cannot decide a replacement request.

OpenCode's server plugin follows the same deck flow when its SDK exposes a supported reply method and the request was observed live. For Codex, Copilot, Gemini and Cursor, use native prompt focus. A red indicator alone does not guarantee a decision-capable request. The [coverage matrix](features/DECK-CONTROLS.md#harness-coverage) explains the exact limits.

To keep launch menus but disable decisions, run `python -m ocdeck controls configure --no-permissions` and restart the broker. To restore the original press-down interaction entirely, use `--no-enabled` and restart.

## Keep custom model launchers and isolated worktrees

Use separate named profiles when arguments or executables are specific to a harness. Each `--arg` is one exact argv element; use `--arg=--flag` for a value beginning with a dash.

```powershell
python -m ocdeck controls repo set "Local OpenCode" --directory "C:\Projects\MyApp" --harness opencode --executable "C:\HomeAI\opencode-local.bat"
python -m ocdeck controls repo set "Claude Review" --directory "C:\Projects\MyApp-review" --harness claude --arg=--model --arg sonnet
python -m ocdeck harness-install claude --project "C:\Projects\MyApp-review"
python -m ocdeck controls launch "Claude Review" --harness claude
```

The review directory should already exist, for example as a Git worktree you created for isolated changes. AgentStreamDeck passes it as the child process's working directory without changing the broker's cwd. It does not create a worktree or change branches for you. The last command launches the same saved profile from the CLI, useful for diagnosing a launch before using the deck.

```powershell
python -m ocdeck controls repo set "Claude Review" --clear-args
python -m ocdeck controls repo set "Local OpenCode" --clear-executable
python -m ocdeck controls configure --hold-ms 900 --menu-timeout 60
```

Clearing the custom executable restores that harness's default PATH lookup. Use `controls show` to inspect your effective configuration. Restart for timing changes; profile edits need only a new picker open.

## Monitor Claude Code and Codex together

Install the broker once using the first-run guide. From a software project, install both project profiles:

```powershell
python -m ocdeck harness-install claude
python -m ocdeck harness-install codex
```

Review/trust Codex hooks in its native /hooks UI. Open Claude in one OS window and Codex in another, then send each a task. Both can share the same physical deck. Press their keys to switch windows. Follow the separate integration pages for the difference between Claude questions, Codex approvals and unknown counts.

## Set up a readable review station

```powershell
python -m ocdeck preview --preset readable --output readable.gif
python -m ocdeck appearance --preset readable --dry-run
python -m ocdeck appearance --preset readable
python -m ocdeck appearance --slot 2 --alias Reviewer --secondary alias
```

The preset uses a minimal layout, accessible palette, large text and steady effect. A slot alias remains attached to key 2 even when another session takes it. Restart after saving. To restore global inheritance for key 2, remove that slot's override object from buttons in config.json.

## Make long project names readable

```powershell
python -m ocdeck preview --preset marquee --alias "Backend integration review" --output labels.gif
python -m ocdeck appearance --slot 1 --preset marquee --alias "Backend integration review"
```

The marquee preset scrolls long labels with pauses. Prefer a concise alias on smaller native keys. Keep the secondary status line so you can identify the state without interpreting color.

## Share a visual setup

```powershell
python -m ocdeck appearance --export team-look.json
python -m ocdeck appearance --import team-look.json --dry-run
python -m ocdeck appearance --import team-look.json
```

The export shares appearance/buttons/FPS only, so it does not overwrite another person's serial, alerts or Jelly settings. Import replaces visual settings; it is not a merge of each incoming field. Inspect the dry-run diff and restart afterward.

## Keep local-model launch scripts

Install the native hook profile once and launch your existing local-model script normally. AgentStreamDeck observes the harness, so changing a model endpoint in your own launcher does not require a new adapter. Model compatibility and provider configuration remain the harness's responsibility. See the compatibility launcher guide for optional dedicated-window examples and their prerequisites.

## Quiet evenings with Jelly

Merge `{"jelly":{"personality":"mellow","thoughts":"quiet","local_movement":"low","travel":"rare","coffee":false}}` into config and restart. This keeps a quiet companion without support invitations. Use `jelly.enabled: false` to disable Jelly entirely. To also suppress the empty-deck READY key, set ready false.

## Prepare a useful bug report

```powershell
python -m ocdeck doctor --project C:\Projects\MyApp --no-device --json
python -m ocdeck status --json
python -m ocdeck report --output agentstreamdeck-report.zip --lines 200
```

Record whether device.input_events changes on a press and whether synthetic focus succeeds. Inspect the ZIP before sharing. Include the harness name/version and exact failed step; never label a mock result as physical hardware verification.

## Related guides

[First run](FIRST-RUN.md) · [CLI](CLI.md) · [Appearance](APPEARANCE.md) · [Launchers](LAUNCHERS.md) · [Jelly settings](reference/JELLY.md)
