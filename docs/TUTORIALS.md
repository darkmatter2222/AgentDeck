# Practical AgentStreamDeck workflows and customization tutorials

[Project overview](../README.md) · [Documentation index](README.md)

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
