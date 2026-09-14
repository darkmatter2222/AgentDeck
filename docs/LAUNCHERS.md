# Optional managed launchers, HomeAILab and local model workflows

[Project overview](../README.md) · [Documentation index](README.md)

Normal monitoring uses the global OpenCode plugin or project-native hooks and your existing launch command. A custom local-model BAT file can keep running normally after hook installation. Managed launchers are compatibility helpers when you specifically want a supervisor-owned Windows Terminal window.

## Setup and current limitations

1. Follow [first run](FIRST-RUN.md) to install the broker and your project hooks.
2. Install Windows Terminal for a dedicated managed window. Use one harness per OS window.
3. For hook harnesses, optionally use `python -m ocdeck start --profile claude`, or pass a synchronous existing script through `--launcher`.
4. OpenCode managed launch/route/worker paths still expect legacy install.json metadata with an `opencode` executable entry. Fresh plugin-first setup does not create that entry, and the worker reads it even when a launcher override is supplied. On a fresh install, launch OpenCode or your OpenCode BAT normally. The OpenCode wrapper examples below apply only to a legacy installation that already has valid metadata.

The current scripts/Install.ps1 accepts only -Python; older -OpenCodePath and -ConfigDirectory flags are not present. Use install-plugin --config-dir for an alternate plugin home. Do not point legacy executable metadata at the shim itself. Legacy Verify-Windows.ps1 checks the old task/environment and is not a current setup check.

Hook helper example:

```powershell
python -m ocdeck harness-launch --profile claude --current-window -- --help
```

Options before `--` belong to AgentStreamDeck; arguments after it belong to the harness. `--current-window` is useful for status testing and does not provide a unique managed window title. A local CLI calling a remote model API is still a local process; a CLI running over SSH is a different host boundary.

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


## Related guides

[CLI commands](CLI.md) · [Native integrations](integrations/README.md) · [Focus](features/FOCUS.md) · [Remote boundaries](REMOTE-AND-WSL.md)
