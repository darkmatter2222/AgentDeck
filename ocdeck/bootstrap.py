"""Per-user broker startup registration for an installed AgentStreamDeck package."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from .common import atomic_json, home, read_json

WINDOWS_TASK = "AgentStreamDeck Broker"
LINUX_SERVICE = "agentstreamdeck.service"


def _source():
    package = Path(__file__).resolve().parent
    runtime = package / "runtime"
    if (runtime / "plugins").is_dir():
        return runtime
    return package.parent


def _windows(root, start=True, runner=None):
    execute = runner or subprocess.run
    python = Path(sys.executable)
    pythonw = python.with_name("pythonw.exe")
    if not pythonw.exists():
        pythonw = python

    def quote(value):
        return str(value).replace("'", "''")

    script = f"""
$ErrorActionPreference = 'Stop'
$task = Get-ScheduledTask -TaskName '{WINDOWS_TASK}' -TaskPath '\\' -ErrorAction SilentlyContinue
if ($task) {{ Stop-ScheduledTask -TaskName '{WINDOWS_TASK}' -TaskPath '\\' -ErrorAction SilentlyContinue }}
$legacy = Get-ScheduledTask -TaskName 'OpenCode Deck' -TaskPath '\\' -ErrorAction SilentlyContinue
if ($legacy -and $legacy.Description -like 'OpenCode Deck*') {{
  Unregister-ScheduledTask -TaskName 'OpenCode Deck' -TaskPath '\\' -Confirm:$false
}}
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$action = New-ScheduledTaskAction -Execute '{quote(pythonw)}' -Argument '-m ocdeck broker' -WorkingDirectory '{quote(root)}'
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName '{WINDOWS_TASK}' -TaskPath '\\' -Description 'AgentStreamDeck per-user broker' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
"""
    if start:
        script += f"Start-ScheduledTask -TaskName '{WINDOWS_TASK}' -TaskPath '\\'\n"
    result = execute(
        ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "Scheduled Task registration failed")[-2000:])
    return {"kind": "scheduled-task", "name": WINDOWS_TASK}


def _linux(root, start=True, runner=None):
    execute = runner or subprocess.run
    unit_dir = Path.home() / ".config" / "systemd" / "user"
    unit_dir.mkdir(parents=True, exist_ok=True)
    unit = unit_dir / LINUX_SERVICE
    python = str(Path(sys.executable).resolve()).replace('"', '\\"')
    root_value = str(root).replace('"', '\\"')
    unit.write_text(
        "[Unit]\nDescription=AgentStreamDeck per-user broker\nAfter=graphical-session.target\n\n"
        "[Service]\nType=simple\n"
        f'Environment="OCDECK_HOME={root_value}"\n'
        f'ExecStart="{python}" -m ocdeck broker\n'
        "Restart=always\nRestartSec=2\n\n"
        "[Install]\nWantedBy=default.target\n",
        encoding="utf-8",
    )
    commands = [["systemctl", "--user", "daemon-reload"], ["systemctl", "--user", "enable", LINUX_SERVICE]]
    if start:
        commands.append(["systemctl", "--user", "restart", LINUX_SERVICE])
    for command in commands:
        result = execute(command, capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise RuntimeError((result.stderr or result.stdout or "systemd user service setup failed")[-2000:])
    return {"kind": "systemd-user", "name": LINUX_SERVICE, "unit": str(unit)}


def install(start=True, install_opencode=True, runner=None):
    root = home()
    root.mkdir(parents=True, exist_ok=True)
    if not (root / "config.json").exists():
        atomic_json(root / "config.json", {"fps": 24, "brightness": 45, "animations": True, "ready": True})
    existing = read_json(root / "install.json", {}) or {}
    info = {
        **existing,
        "python": sys.executable,
        "source": str(_source()),
        "distribution": "agentstreamdeck",
        "pluginMode": existing.get("pluginMode", "server"),
    }
    atomic_json(root / "install.json", info)
    if os.name == "nt":
        startup = _windows(root, start, runner)
    elif sys.platform.startswith("linux"):
        startup = _linux(root, start, runner)
    else:
        startup = {"kind": "manual", "command": f"{sys.executable} -m ocdeck broker"}
    plugin = None
    if install_opencode and shutil.which("opencode"):
        from .launcher import install_plugin

        install_plugin("server")
        plugin = "opencode"
    result = {"ok": True, "home": str(root), "startup": startup, "plugin": plugin}
    print(json.dumps(result, indent=2))
    return result
