"""Managed hook-harness supervisor. The existing broker and identity rules are unchanged."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
from .common import home, identity, atomic_json, read_json, request

PROFILES = {
    "codex": "codex",
    "claude": "claude",
    "copilot-cli": "copilot",
    "copilot-vscode": "code",
    "gemini": "gemini",
    "cursor": "agent",
}
SOURCE = Path(__file__).resolve().parent.parent
if not (SOURCE / "plugins/harnesses/install.mjs").is_file():
    SOURCE = Path(__file__).resolve().parent / "runtime"


def install(profile, project, remove=False, dry_run=False):
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js 20+ must be on PATH for hook adapters")
    result = subprocess.call(
        [
            node,
            str(SOURCE / "plugins/harnesses/install.mjs"),
            "--cli",
            profile,
            str(Path(project).resolve()),
            *(["--remove"] if remove else []),
            *(["--dry-run"] if dry_run else []),
        ]
    )
    if result == 0 and not dry_run:
        projects = read_json(home() / "projects.json", []) or []
        resolved = str(Path(project).resolve())
        if resolved not in projects:
            projects.append(resolved)
            atomic_json(home() / "projects.json", projects)
    return result


def launch(profile, args, executable=None, current_window=False, cwd=None):
    executable = shutil.which(executable or PROFILES[profile])
    if not executable:
        raise RuntimeError("Harness executable not found; install it or pass --executable")
    if not shutil.which("node"):
        raise RuntimeError("Node.js 20+ must be on PATH")
    key = str(uuid.uuid4())
    spec = {
        "id": key,
        "profile": profile,
        "executable": executable,
        "cwd": str(Path(cwd).resolve()) if cwd else os.getcwd(),
        "args": args,
        "windowToken": "" if current_window or os.name != "nt" else f"AgentDeck [{key}]",
    }
    if os.name != "nt" or current_window:
        return worker(spec)
    wt = shutil.which("wt.exe")
    if not wt:
        raise RuntimeError("Windows Terminal required; use --current-window for status-only testing")
    file = home() / "launches" / (key + ".harness.json")
    atomic_json(file, spec)
    try:
        terminal_title = spec["windowToken"] + (" launcher" if profile == "copilot-vscode" else "")
        subprocess.Popen(
            [
                wt,
                "-w",
                key,
                "new-tab",
                "--title",
                terminal_title,
                "--suppressApplicationTitle",
                "--inheritEnvironment",
                sys.executable,
                "-m",
                "ocdeck",
                "harness-worker",
                str(file),
            ]
        )
    except Exception:
        file.unlink(missing_ok=True)
        raise
    return 0


def worker(spec):
    spec_file = None
    if not isinstance(spec, dict):
        spec_file = Path(spec)
        spec = read_json(spec_file)
    if not isinstance(spec, dict):
        raise ValueError("Invalid managed launch specification")
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Install Node.js 20+ and restart the terminal")
    root = home().resolve()
    directory = root / "launches" / (spec["id"] + ".hooks")
    directory.mkdir(parents=True, mode=0o700)
    binding, descriptor = directory / "binding.json", directory / "hook.json"
    reg = {
        "id": spec["id"],
        "process": identity(),
        "windowToken": spec["windowToken"],
        "harness": spec["profile"],
        "label": spec["profile"] + ":" + Path(spec["cwd"]).name,
        "managed": True,
    }
    atomic_json(binding, reg)
    env = dict(os.environ, OCDECK_HOME=str(root), AGENTDECK_HOOK_BINDING=str(descriptor))
    # Do not let nested OpenCode instances claim an unrelated managed launch.
    env.pop("OCDECK_BINDING", None)
    bridge = child = None
    try:
        bridge = subprocess.Popen(
            [
                node,
                str(SOURCE / "plugins/harnesses/bridge.mjs"),
                "--worker",
                spec["profile"],
                str(binding),
                str(descriptor),
            ],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 5
        while not descriptor.exists():
            if bridge.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError("Hook bridge did not start")
            time.sleep(0.025)
        command = [spec["executable"], *spec["args"]]
        if spec["profile"] == "copilot-vscode":
            # A separate VS Code application instance is required for environment inheritance.
            # Unique data avoids silently reusing an existing editor with a stale binding.
            editor_key = spec["id"]
            editor_data = root / "editors" / editor_key
            if spec["windowToken"]:
                atomic_json(editor_data / "User/settings.json", {"window.title": spec["windowToken"]})
            command += ["--new-window", "--wait", "--user-data-dir", str(editor_data), spec["cwd"]]
        # Native executables use CreateProcess argv quoting directly. Legacy
        # PowerShell argument binding drops embedded quotes on Windows.
        if os.name == "nt" and Path(command[0]).suffix.lower() in (".bat", ".cmd", ".ps1"):
            launch_file = directory / "command.json"
            atomic_json(launch_file, {"executable": command[0], "args": command[1:], "cwd": spec["cwd"]})
            command = [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(SOURCE / "scripts/Run-OpenCode.ps1"),
                "-LaunchFile",
                str(launch_file),
            ]
        child = subprocess.Popen(command, cwd=spec["cwd"], env=env)
        warned = False
        while child.poll() is None:
            if bridge.poll() is not None and not warned:
                print(
                    "AgentStreamDeck bridge exited; status will become unknown. Restart this launch to reconnect.",
                    file=sys.stderr,
                )
                warned = True
            try:
                time.sleep(0.2)
            except KeyboardInterrupt:
                pass  # Child shares console and receives Ctrl+C; keep watching until it exits.
        return child.returncode
    finally:
        if child and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        if bridge:
            if bridge.stdin:
                bridge.stdin.close()
            try:
                bridge.wait(timeout=4)
            except subprocess.TimeoutExpired:
                bridge.kill()
                bridge.wait()
        try:
            request("DELETE", "/v1/instances/" + reg["id"], root=root)
        except Exception:
            pass
        shutil.rmtree(directory, ignore_errors=True)
        if spec_file:
            spec_file.unlink(missing_ok=True)
