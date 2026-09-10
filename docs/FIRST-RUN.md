# Install and verify on your Windows PC

Choose your setup path in [TUTORIALS.md](TUTORIALS.md). The installation steps below
use the original OpenCode installer and scheduled task. For a foreground-only
broker, follow that tutorial first and run the physical checks here with the
installed interpreter (`python -m ocdeck`) instead of relying on command shims.

## Original OpenCode installation

1. Extract the ZIP to a permanent directory, for example `C:\Tools\AgentDeck`. Keep the whole folder: the installed Python package is editable and the global plugin entry imports these sources.
2. Disable only the Mini under Elgato Preferences > Devices > Enabled. Elgato 7.1 introduced that control, so 7.2 should have it. Close any old scripts that also write to the Mini. Leave Elgato running if you want; it must not own this device.
3. Confirm Python and OpenCode run. Use `Get-Command opencode` to record the original path before installing. Use Python 3.11 or later; the installer's `-Python` option accepts a full executable path.
4. Run the installer as the Windows account that will use the device. The default server plugin is the broad-compatibility path. Do not opt into TUI mode until the installed OpenCode API has been checked.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Install.ps1
```

Alternative with explicit paths:

```powershell
.\scripts\Install.ps1 -Python 'C:\Path\To\python.exe' -OpenCodePath 'C:\Path\To\opencode.exe'
```

If the default OpenCode config home is overridden, use `-ConfigDirectory 'C:\actual\config\opencode'`. The installer otherwise honors `OPENCODE_CONFIG_DIR`, then `XDG_CONFIG_HOME`, then `~/.config/opencode`. Avoid installing another copy of the bridge in `.opencode/plugins` within projects.

If Task Scheduler returns access denied, rerun PowerShell elevated as the **same Windows account**. Do not install as SYSTEM or another administrator's account. The installed task deliberately uses Interactive / Limited rather than a different security principal. The script stops with an error if it cannot create the task; it does not silently substitute a startup folder.

5. Open a new terminal. Verify `Get-Command opencode` points to `.opencode-deck\bin\opencode.cmd`. Existing PowerShell functions/aliases and machine PATH entries can take precedence. `oc` or `ocdeck launch` explicitly selects the managed launcher if needed. Do not change the recorded original executable to this new shim.
6. Run `ocdeck status`. Expect `device.online: true` and `device.mock: false`. Verify the physical READY key. READY means the device was opened and images submitted, not that a camera has confirmed the screen or all focus tests have passed.
7. Run `opencode` from two different directories. Expect two separate terminal windows and two amber indicators. Run a real prompt and watch green during the entire work, then amber. Request a structured question and a tool approval to check red. The broker does not approve anything when a key is pressed.
8. With a different application foregrounded, press each physical key. Verify both the correct window and where keyboard input goes. Minimize a window and repeat. `ocdeck focus 1` tests a synthetic focus request; it does not replace a physical button test. `lastFocus` in status records the outcome.
9. Close one OpenCode instance. Its key should go black within approximately one second. Close the last instance: READY returns. Launch six; all six positions must work. A seventh remains off-deck until a slot frees.
10. Restart the broker, restart Elgato, unplug/replug USB, and reboot. Repeat mixed running/idle/input states. Check the task at the root of Task Scheduler after login.

**Standalone physical-key diagnostic**

```powershell
ocdeck stop
ocdeck hardware-check
Start-ScheduledTask -TaskName 'OpenCode Deck' -TaskPath '\'
```

The diagnostic takes the same process lock, draws six numbers, and asks you to press 1 through 6. It saves actual key-down results in `.opencode-deck\hardware-check.json`. It leaves visual confirmation explicitly false until you separately confirm appearance. Stop the broker first; two USB owners are not allowed.

**Configuration:** edit `.opencode-deck\config.json` and restart the task. Defaults: `fps: 10`, `brightness: 45`, `animations: true`, `ready: true`, `serial: null`. Use the serial from `ocdeck devices` when multiple Minis are present. `fps` is capped at 15. Set `animations` false for static status images, or lower FPS for USB load. Set `ready` false for six black keys when empty.

**Troubleshooting:** inspect `.opencode-deck\broker.log` and OpenCode's own logs. LINK ? indicates missing/failing/stale telemetry. A red key requires unresolved request data; the monitor does not interpret ordinary prose questions. A window-mapping error means the direct launch was not a dedicated managed window, its title changed, or a different terminal hosted it. A foreground-denied error is distinct from an absent target. A task with a long-running status is expected while the broker is active.

Before login or device initialization, firmware may display a logo or old image briefly. The application guarantees its initialized state, not a pre-firmware black screen.


## Additional harness and mixed-session acceptance

After the broker works, install project hooks and launch the desired harnesses
using [HARNESSES.md](HARNESSES.md). Record the installed native version and confirm
that its hooks load before treating a key as accurate.

1. Start Claude and Copilot CLI in the same project using their BAT launchers;
   optionally keep an OpenCode window open. Expect one stable key per managed launch.
2. Submit a coding task and a separate text-only prompt in each. Verify running
   during work and idle at completion. A missing completion hook is a real failure.
3. For Claude, exercise `AskUserQuestion`, including answer/cancel. Other adapters
   do not promise red for approvals. Verify the exact capability table instead of
   expecting OpenCode's pending coverage from every harness.
4. From another application, physically press each key, repeat while minimized,
   then test six simultaneous launches and a seventh overflow launch. Confirm
   keyboard focus as well as a successful API response.
5. Restart the broker while agents remain open; inspect rediscovery and state
   restoration. Close each agent, then try forced termination. The key must release.
6. For Copilot VS Code, use its isolated launcher and verify the editor's exact
   title, account sign-in, hook enablement and foreground activation separately.
7. Remove one profile's hooks using `Install-Harness.ps1 -Remove`, confirm other
   settings/hooks remain, and reinstall if continuing to use it.

The local relay does not extend support to WSL, SSH or containers. Record actual
outcomes in [TEST-RESULTS.md](TEST-RESULTS.md); automated fixture tests and synthetic
focus requests do not replace these physical/native-runtime observations.
