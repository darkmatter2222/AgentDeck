"""Read-only diagnostics and an allowlisted, redacted issue bundle."""

import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import zipfile
from . import __version__
from .common import home, read_json, request, load_config
from .observability import tail
from .security import scrub


def versions():
    node = shutil.which("node")
    try:
        node_version = (
            subprocess.run([node, "--version"], capture_output=True, text=True, timeout=3, check=True).stdout.strip()
            if node
            else "missing"
        )
    except (OSError, subprocess.SubprocessError):
        node_version = "unavailable"
    return {
        "agentdeck": __version__,
        "python": platform.python_version(),
        "node": node_version,
        "os": platform.platform(),
    }


def doctor(project=".", no_device=False, root=None):
    root = Path(root or home())
    project = Path(project).resolve()
    rows = []

    def add(check, ok, detail, fix):
        rows.append(
            {
                "check": check,
                "result": "PASS" if ok is True else "FAIL" if ok is False else "MANUAL",
                "detail": detail,
                "fix": fix,
            }
        )

    ver = versions()
    try:
        node_ok = int(ver["node"].lstrip("v").split(".")[0]) >= 20
    except ValueError:
        node_ok = False
    add("node", node_ok, ver["node"], "Install Node.js 20+, then restart the terminal.")
    config_file = root / "config.json"
    try:
        config = load_config(root)
    except (ValueError, OSError):
        config = None
    add(
        "config",
        isinstance(config, dict),
        "JSON configuration",
        "Repair config.json as a JSON object; ocdeck appearance --dry-run",
    )
    from .settings import validate_config

    try:
        validate_config(config)
        add("config-values", True, "Validated broker and appearance settings", "ocdeck appearance --dry-run")
    except (ValueError, TypeError) as error:
        add("config-values", False, str(error), "Repair config.json; ocdeck appearance --dry-run")
    if os.name == "nt":
        add(
            "windows-terminal",
            bool(shutil.which("wt.exe")),
            "Dedicated-window launcher",
            "Install Windows Terminal; restart the terminal.",
        )
    from .harness import SOURCE

    add(
        "runtime-assets",
        (SOURCE / "plugins/harnesses/hook.mjs").is_file() and (SOURCE / "scripts/Run-OpenCode.ps1").is_file(),
        "Packaged adapter and launcher sources",
        "python -m pip install --force-reinstall agentdeck",
    )
    try:
        status = request("GET", "/v1/status", root=root)
        add("broker", True, "Local authenticated API responds", "ocdeck broker")
    except Exception:
        status = {}
        add("broker", False, "Local broker unavailable", "ocdeck broker")
    add(
        "capacity",
        not status.get("overflow"),
        f"Overflow: {status.get('overflow', 0)}",
        "Close unused sessions or attach a larger deck.",
    )
    if not no_device:
        from .device import enumerate_devices, elgato_running

        add(
            "elgato",
            not elgato_running(),
            "Elgato process ownership check",
            "Quit Stream Deck from its tray menu; ocdeck devices",
        )
        try:
            devices = enumerate_devices()
            device_config = config if isinstance(config, dict) else {}
            selected = [
                d
                for d in devices
                if not device_config.get("serial") or d.get("serial_number") == device_config["serial"]
            ]
            add(
                "device",
                len(selected) == 1,
                f"{len(selected)} matching devices",
                "ocdeck devices; select serial in config.json if multiple.",
            )
            if status:
                add(
                    "device-online",
                    status.get("device", {}).get("online") is True,
                    status.get("device", {}).get("error", ""),
                    "Release Elgato ownership and reconnect USB; ocdeck broker",
                )
        except Exception as error:
            add("device", False, str(error), "python -m pip install --upgrade agentdeck; ocdeck devices")
    receipts = list((project / ".agentdeck").glob("*.json"))
    add(
        "hooks-installed",
        bool(receipts),
        f"{len(receipts)} receipts in project",
        "ocdeck harness-install PROFILE --project PROJECT",
    )
    for receipt in receipts:
        saved = read_json(receipt)
        target = Path(saved.get("target", "")) if isinstance(saved, dict) else Path()
        from .harness import PROFILES

        profile = receipt.stem
        expected = {
            "claude": ".claude/settings.local.json",
            "gemini": ".gemini/settings.json",
            "cursor": ".cursor/hooks.json",
            "copilot-cli": ".github/hooks/agentdeck-copilot-cli.json",
            "copilot-vscode": ".github/hooks/agentdeck-copilot-vscode.json",
            "codex": ".codex/hooks.json",
        }.get(profile)
        good = bool(expected) and target == project / expected
        actual = read_json(target) if good else None
        good = good and isinstance(actual, dict) and isinstance(actual.get("hooks"), dict)
        if good and isinstance(saved, dict) and isinstance(actual, dict):
            for event, entries in saved.get("configuration", {}).get("hooks", {}).items():
                good = good and all(entry in actual["hooks"].get(event, []) for entry in entries)
        add(
            "hooks-" + profile,
            bool(good),
            "Receipt target and installed entries",
            f'ocdeck harness-install {profile} --project "{project}" --dry-run',
        )
    details = [s.get("detail", "") for s in status.get("slots", [])]
    add(
        "hook-delivery",
        not any("failed" in d.lower() for d in details),
        "Hook delivery failure latch",
        "Restart the managed session after fixing native hook errors.",
    )
    add(
        "first-hook",
        not any("Waiting for first" in d for d in details),
        "First native hook received",
        "Submit a prompt; review native hooks and workspace trust.",
    )
    focus = status.get("lastFocus")
    add(
        "focus",
        focus.get("ok") if focus else None,
        "Last focus result" if focus else "No focus attempt recorded",
        "ocdeck focus 1; use a dedicated managed window under the same Windows user.",
    )
    # Runtime policy and interactive behavior cannot be proved from static files.
    manual = {
        "approval-coverage": "Inspect HARNESSES.md; unpaired approval notifications cannot establish counts.",
        "stale-native-hooks": "Verify prompt/tool/stop hooks in the native runtime; heartbeat does not prove hook coverage.",
        "bridge-restart": "After a broker restart, verify managed Node bridge and supervisor processes remain alive.",
        "foreground-policy": "Test minimized windows; run broker and agents at the same elevation.",
        "vscode-signin": "Sign in and enable Copilot in the isolated managed VS Code profile.",
        "vscode-trust": "Inspect Chat: Configure Hooks and workspace trust.",
        "vscode-title": "Preserve the managed window.title and launcher suffix.",
        "jsonc": "Preserve comments; reconcile JSONC manually before harness-install.",
        "moved-project": "If moved, reconcile old hooks and receipt; do not blindly rewrite the recorded target.",
        "powershell-policy": "Use the trusted FIRST-RUN.md invocation subject to device policy.",
        "opencode-shim": "Run Get-Command opencode in PowerShell; use ocdeck launch if an alias wins.",
        "deleted-checkout": "Keep the installed source or reinstall hooks to the new source before removing it.",
        "homeailab-focus": "Use the managed wrapper and retain the Windows Terminal managed tab title.",
        "notifications": "Enable AgentDeck notifications in Windows Settings; test a real identified question with Focus Assist on and off.",
    }
    for key, fix in manual.items():
        add(key, None, "Interactive verification required", fix)
    return scrub(rows)


def report(output, lines=100, root=None):
    root = Path(root or home())
    try:
        token = (root / "token").read_text().strip()
    except OSError:
        token = ""
    try:
        status = request("GET", "/v1/status", root=root)
    except Exception:
        status = {"error": "Broker unavailable"}
    values = {
        "status.json": status,
        "versions.json": versions(),
        "config.json": read_json(root / "config.json", {}),
        "logs.json": tail(root, lines),
    }
    # Deliberately exclude token, discovery, launch descriptors and native configs.
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in values.items():
            archive.writestr(name, json.dumps(scrub(value, (token,)), indent=2))
    return str(Path(output).resolve())
