# Managed launchers: HomeAILab, local AI, and cloud

The model endpoint and the window are separate concerns. HomeAILab selects a
backend and launches a CLI; AgentStreamDeck needs a stable association with the desktop
window to focus it. A directly started OpenCode process can report state while
having no usable top-level window: Windows Terminal owns that window, not the
OpenCode PID. This explains why a lit key does not establish a focus mapping.

`Launch-Agent.bat` runs the selected CLI or existing launcher inside AgentStreamDeck's
unique, title-pinned window. Its supervisor owns one registration, and the child
inherits the appropriate plugin/hook binding. Backend selection and tuning remain
inside HomeAILab. Nothing in HomeAILab needs to be copied or edited.

## Setup

1. Update AgentStreamDeck to current main and restart its broker. Run the broker as your
   desktop user, at the same elevation as the agent windows.
2. For OpenCode, run `scripts\Install.ps1` as described in the README. This installs
   the global OpenCode plugin and records the actual CLI path. If requested, supply
   `-OpenCodePath` pointing to the original CLI, not AgentStreamDeck's shim.
3. For Claude and other hook adapters, install their project hooks once, e.g.
   `scripts\Install-Harness.ps1 -Profile claude -Project C:\Projects\MyApp`.
   Follow [tutorials](TUTORIALS.md) for a setup without OpenCode.
4. Close the old unmanaged sessions and relaunch through the wrapper from your
   software project's directory. Restarting the broker alone cannot turn an old
   unmanaged process into a titled managed window.

Use current Windows Terminal. Keep `showTerminalTitleInTitlebar` enabled (the
Terminal default); changing it to false hides the exact title used for mapping.
Do not rename the managed tab or combine multiple agents into it. Deck aliases
are fine: they affect only button text.

## Keep using HomeAILab

From PowerShell:

```powershell
cd C:\Projects\MyApp
C:\Tools\AgentStreamDeck\scripts\Launch-Agent.bat --profile opencode --launcher "C:\Tools\HomeAILab\harness\opencode\opencode-5090.bat" --
C:\Tools\AgentStreamDeck\scripts\Launch-Agent.bat --profile claude --launcher "C:\Tools\HomeAILab\harness\claude\claude-5090.bat" --
```

Or use the short examples:

```powershell
$env:HOMEAILAB_ROOT = "C:\Tools\HomeAILab"
cd C:\Projects\MyApp
C:\Tools\AgentStreamDeck\scripts\examples\HomeAILab-OpenCode-5090.bat
C:\Tools\AgentStreamDeck\scripts\examples\HomeAILab-Claude-Cluster.bat
```

| Example | Existing HomeAILab launcher used |
|---|---|
| `HomeAILab-OpenCode-5090.bat` | `harness/opencode/opencode-5090.bat` |
| `HomeAILab-OpenCode-Spark.bat` | `harness/opencode/opencode-spark.bat` |
| `HomeAILab-Claude-5090.bat` | `harness/claude/claude-5090.bat` |
| `HomeAILab-Claude-Cluster.bat` | `harness/claude/claude-cluster.bat` |

For 3090 or another target, pass its existing file with `--launcher` and choose the
matching `--profile`. Model discovery, context, thinking, provider configuration,
and `.env` loading remain the HomeAILab script's responsibility. In particular,
these wrappers preserve any permission-bypass flags already in that script.
The new standalone examples below do not add permission-bypass flags.

Use interactive scripts, not `opencode-3090-serve.bat`: a headless server has no
interactive agent UI to focus. Wrapping it would only focus its server console.
An unrelated `opencode attach` window is not automatically mapped to it.

HomeAILab scripts must remain in their checkout, where their relative `.env`
loader works. They must run the CLI synchronously rather than detaching it into
another window. AgentStreamDeck does not infer endpoint ports or scan your LAN.

The OpenCode shim detects an inherited `OCDECK_BINDING` and calls the recorded real
CLI directly. This prevents HomeAILab's `where opencode` lookup from nesting a
second managed launch or registering a second button.

## Minimal local Claude example

Provide a backend that implements **Anthropic `/v1/messages`**; an OpenAI-only
`/v1/chat/completions` endpoint requires a compatible gateway first. Use the server
base URL, not a URL ending in `/v1/messages`.

```powershell
$env:AGENTDECK_LOCAL_URL = "http://127.0.0.1:8201"
$env:AGENTDECK_LOCAL_MODEL = "your-served-model-id"
# Set AGENTDECK_LOCAL_TOKEN separately if your server enforces authentication.
cd C:\Projects\MyApp
C:\Tools\AgentStreamDeck\scripts\examples\Claude-Local.bat
```

The file selects the local endpoint/model for Claude and its model roles. It uses
`local-dev` only as a placeholder for a backend without authentication. It does
not discover models or alter your context limits; use HomeAILab when you want its
full tuning. Environment changes use `setlocal` and end with the launcher.

## Cloud examples

```powershell
cd C:\Projects\MyApp
C:\Tools\AgentStreamDeck\scripts\examples\Claude-Cloud.bat
C:\Tools\AgentStreamDeck\scripts\examples\OpenCode-Cloud.bat
C:\Tools\AgentStreamDeck\scripts\Launch-Agent.bat --profile gemini --
C:\Tools\AgentStreamDeck\scripts\Launch-Agent.bat --profile copilot-cli --
```

Claude-Cloud clears local endpoint/model routing and uses normal Anthropic
login or an existing `ANTHROPIC_API_KEY`. OpenCode-Cloud clears temporary config
file overrides and uses your normal provider configuration; select a cloud
provider/model there or forward `--model provider/model`. Neither creates a cloud
account, provisions credentials, or guarantees that your default provider is cloud.
Install the corresponding hooks for Gemini/Copilot and sign in with each CLI first.

For enterprise gateways or other provider settings already in your shell, use
`Launch-Agent.bat --profile claude --` directly so the wrapper preserves them.
Arguments after `--` go to the selected CLI or HomeAILab launcher. Equivalent CLI:

```powershell
python -m ocdeck start --profile claude --launcher "C:\Tools\HomeAILab\harness\claude\claude-spark.bat" -- --resume
```

## Verify a button press

Bring another app forward, press the key, and check that keyboard input reaches
the intended agent. Repeat with the target minimized. `ocdeck status` reports
`lastFocus`: successful activation includes `keyboardFocus: true`; mapping errors
include a match count, and activation failures include foreground and attachment
diagnostics. `ocdeck focus 1` exercises the same activation code without the device.

The focus fallback explicitly creates the worker's message queue, attaches to the
foreground and target GUI threads, preserves a valid input child, and detaches in
all outcomes. It checks both foreground and keyboard focus before reporting success.
It does not simulate typing or relax process identity checks.

Sources: [HomeAILab launchers](https://github.com/darkmatter2222/HomeAILab/tree/main/harness),
[Windows thread input attachment](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-attachthreadinput),
[Terminal title settings](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/appearance).
Windows desktop / physical device acceptance still requires testing on your machine.
