# Setup, upgrade and removal tutorials

Start with a permanent checkout, such as `C:\Tools\AgentDeck`. Examples use
PowerShell and `C:\Projects\MyApp` as the software project; substitute real paths.
Do not confuse the AgentDeck source directory with the project your agent will edit.
See [HARNESSES.md](HARNESSES.md) for the profile/capability matrix.

## Existing install: add a harness

1. Close affected managed agents. Update the existing permanent checkout with
   `git pull --ff-only` while on `main`; inspect local changes before pulling.
   If testing a separate checkout, the BAT launchers load that checkout via
   `PYTHONPATH`, while the existing broker/OpenCode plugin keep their installed paths.
2. Verify `node --version` reports 20 or newer. Confirm the desired harness starts
   and authenticates normally. Run `ocdeck status`; the existing broker should be
   active. Release the Mini in Elgato if it is still owned there.
3. Preview and install hooks for your project:

```powershell
C:\Tools\AgentDeck\scripts\Install-Harness.ps1 -Profile claude -Project C:\Projects\MyApp -DryRun
C:\Tools\AgentDeck\scripts\Install-Harness.ps1 -Profile claude -Project C:\Projects\MyApp
C:\Tools\AgentDeck\scripts\Install-Harness.ps1 -Profile copilot-cli -Project C:\Projects\MyApp
```

4. Launch from that project:

```powershell
cd C:\Projects\MyApp
C:\Tools\AgentDeck\scripts\Launch-Claude.bat
C:\Tools\AgentDeck\scripts\Launch-Copilot.bat
```

5. Verify the native harness accepts the generated hook config. Submit a task and
   check running -> idle in `ocdeck status` and on the Mini. Follow
   [FIRST-RUN.md](FIRST-RUN.md) for physical focus and multi-agent checks.

Use these exact profile names for other adapters:

| Install profile | Launcher |
|---|---|
| `codex` | `scripts\Launch-Codex.bat` (review/trust hooks using `/hooks`) |
| `gemini` | `scripts\Launch-Gemini.bat` |
| `cursor` | `scripts\Launch-Cursor.bat` (Cursor CLI `agent`) |
| `copilot-vscode` | `scripts\Launch-Copilot-VSCode.bat` |

VS Code opens an isolated profile and may require sign-in on every launch. Read
[its setup notes](HARNESSES.md#copilot-in-vs-code-preview) before testing. Hooks
installed in one project do not instrument every other project automatically.

## Fresh install with OpenCode

This path installs the broker's automatic logon startup and the global OpenCode
integration. It also supports adding any of the project-hook adapters above.

1. Install Python 3.11+, Windows Terminal and OpenCode. Add Node 20+ if using hook
   adapters or running the JavaScript tests. Check `python --version`,
   `opencode --version`, `node --version`, and `Get-Command wt`.
2. Quit Elgato Stream Deck from the tray and close competing controllers.
3. Clone/extract this repository into a permanent directory; enter it:

```powershell
cd C:\Tools\AgentDeck
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Install.ps1
```

For a nonstandard Python/OpenCode executable or config home, use the documented
`-Python`, `-OpenCodePath`, and `-ConfigDirectory` flags in [FIRST-RUN.md](FIRST-RUN.md).
The installer records the original OpenCode executable. Never set that path to
its own `.opencode-deck\bin\opencode.cmd` wrapper.

4. Open a fresh terminal, run `Get-Command opencode` and `ocdeck status`. The shim
   should resolve from `.opencode-deck\bin`; the real device should be online and
   `mock` should be false. Use `oc` if another alias shadows the shim.
5. Launch OpenCode from a software project and complete the physical checklist.
   Add other harnesses using the existing-install tutorial above.

The task is named `OpenCode Deck` and runs at this desktop user's logon. If task
registration is denied, follow the same-user elevation instructions in FIRST-RUN;
do not switch to SYSTEM or another account. `Verify-Windows.ps1` checks this
installation path specifically; it is not a generic hook installer check.

## Fresh install without OpenCode

The original installer requires OpenCode. To use only Claude, Copilot, Gemini, Cursor or
Codex, set up the Python environment and run the broker in a foreground terminal.
This path **does not create a scheduled task or global command shims**.

After installing Python 3.11+, Node 20+, Windows Terminal and your desired harness,
quit Elgato Stream Deck. In PowerShell:

```powershell
$agentDeckSource = 'C:\Tools\AgentDeck'
$agentDeckData = Join-Path $env:USERPROFILE '.opencode-deck'
New-Item -ItemType Directory -Force -Path $agentDeckData | Out-Null
$agentDeckUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
icacls.exe $agentDeckData /inheritance:r /grant:r "${agentDeckUser}:(OI)(CI)F" 'SYSTEM:(OI)(CI)F'
if ($LASTEXITCODE -ne 0) { throw 'Could not secure the per-user state directory.' }
python -m venv (Join-Path $agentDeckData 'venv')
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
$agentDeckPython = Join-Path $agentDeckData 'venv\Scripts\python.exe'
& $agentDeckPython -m pip install -e $agentDeckSource
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $agentDeckPython -m ocdeck broker
```

Keep that terminal open. Use `broker --mock` instead for software-only testing;
mock mode does not open or draw on the Mini. Do not run a mock and real broker
against the same state directory simultaneously.

In a second terminal, follow the project install/launch examples above. The BAT
files automatically use this per-user virtual environment. To inspect status:

```powershell
& "$env:USERPROFILE\.opencode-deck\venv\Scripts\python.exe" -m ocdeck status
```

Use the same interpreter with `-m ocdeck stop` to stop the broker. Relaunch it after
logging in again. Automated non-OpenCode installation/startup is not yet supplied.
If an existing AgentDeck environment is present, use the existing-install path
rather than recreating it.

## Upgrade

Close managed sessions and stop the broker before modifying the source checkout.
Inspect `git status`, switch to `main` when appropriate, then `git pull --ff-only`.
Do not discard local changes to make an update work.

- Existing editable Python installations use source updates in the same folder;
  reinstall dependencies with the installed interpreter's `-m pip install -e .`
  from the source checkout if `pyproject.toml` changed.
- Rerun each project's `Install-Harness.ps1` command after adapter updates. It
  removes entries recorded in its receipt and installs the current definitions.
  Repeated installation is idempotent. Restart the agents afterward.
- For the scheduled broker, use `Start-ScheduledTask -TaskName 'OpenCode Deck'`.
  For a foreground broker, rerun the interpreter command from the previous section.
- If moving the checkout or software project, uninstall hooks first and reinstall
  from the new location. Receipts bind to the target config's absolute path; moved
  project receipts need manual cleanup as described in HARNESSES.md.

Run `scripts\Test.ps1`, inspect hook loading, and repeat one actual task and focus
check after upgrades. Do not treat fixture tests as native compatibility proof.

## Remove a harness or the whole installation

Close affected agent windows. Remove project hooks while the checkout and receipts
still exist, once for each installed profile in each software project:

```powershell
C:\Tools\AgentDeck\scripts\Install-Harness.ps1 -Profile claude -Project C:\Projects\MyApp -Remove
C:\Tools\AgentDeck\scripts\Install-Harness.ps1 -Profile copilot-cli -Project C:\Projects\MyApp -Remove
```

This removes matching recorded entries and preserves other settings/hooks. It may
leave an empty hooks object/file; that's harmless. If you edited an installed
AgentDeck command yourself, it may no longer match the receipt: inspect and remove
that edited command manually. Keep unrelated hooks. Timestamped backups are for
manual recovery; do not overwrite newer unrelated edits with an old whole file.

For complete integration removal, preview the plan first:

```powershell
ocdeck uninstall --all --scan C:\Projects --dry-run
ocdeck uninstall --all --scan C:\Projects
```

Add `--scan` for other project roots. `scripts\Uninstall.ps1` delegates to that command and supports
`-DryRun`/`-Scan`. It removes owned integration entries, including the managed TUI
URI, and backs up local configuration. Logs, backups and the Python environment
remain. See [complete removal behavior](NEXT.md#uninstall). Re-enable your device
in Elgato afterward if desired.
