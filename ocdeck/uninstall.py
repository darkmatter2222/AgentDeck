"""Receipt-scoped removal; never delete a project or an environment wholesale."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from .common import home, read_json, request
from .harness import install, PROFILES, SOURCE


def discover(roots):
    found = set()
    for root in roots:
        root = Path(root).expanduser().resolve()
        if not root.is_dir():
            continue
        for directory, children, files in os.walk(root, followlinks=False):
            children[:] = [
                c
                for c in children
                if c not in (".git", "node_modules", ".venv", "venv") and not (Path(directory) / c).is_symlink()
            ]
            if Path(directory).name == ".agentdeck":
                if any(f == p + ".json" for p in PROFILES for f in files):
                    found.add(str(Path(directory).parent))
                children[:] = []
    return sorted(found)


def uninstall(scan=(), dry_run=False):
    root = home().resolve()
    registered = read_json(root / "projects.json", []) or []
    projects = sorted(set([*registered, *discover(scan or [Path.cwd()])]))
    plans = []
    for project in projects:
        for profile in PROFILES:
            if (Path(project) / ".agentdeck" / (profile + ".json")).exists():
                plans.append((profile, project))
    print(
        json.dumps(
            {
                "projects": plans,
                "local": ["scheduled task", "managed OpenCode plugin", "managed shims", "configuration"],
                "backups": "Retained under " + str(root / "backups"),
                "dryRun": dry_run,
            },
            indent=2,
        )
    )
    # Preflight every receipt before changing anything. The native installer refuses
    # moved targets, malformed JSON and shell metacharacters in installed paths.
    for profile, project in plans:
        if install(profile, project, remove=True, dry_run=True):
            raise RuntimeError("Hook removal preflight failed; no uninstall changes applied")
    if dry_run:
        return 0
    try:
        status = request("GET", "/v1/status")
    except Exception:
        status = {}
    if any(v.get("id") for v in status.get("slots", [])) or status.get("overflow"):
        raise RuntimeError("Close managed agent sessions before uninstalling; run ocdeck status")
    for profile, project in plans:
        if install(profile, project, remove=True):
            raise RuntimeError("Project hook removal failed; local installation retained")
    metadata = read_json(root / "install.json", {}) or {}
    if os.name == "nt":
        script = SOURCE / "scripts" / "Remove-Integration.ps1"
        subprocess.run(["powershell.exe", "-NoProfile", "-File", str(script), "-Data", str(root)], check=True)
    try:
        request("POST", "/v1/stop")
    except Exception:
        pass
    # Give the broker time to release discovery/log files; never move its token live.
    for _ in range(30):
        try:
            request("GET", "/v1/status", timeout=0.2)
        except Exception:
            break
        time.sleep(0.1)
    else:
        raise RuntimeError("Broker did not stop; local files retained. Run ocdeck stop")
    backup = root / "backups" / str(time.time_ns())
    backup.mkdir(parents=True, exist_ok=False)
    for name in ("config.json", "install.json", "projects.json", "update.json", "token", "discovery.json"):
        path = root / name
        if path.exists():
            shutil.move(str(path), str(backup / name))
    # Remove only exact known shims after verifying their runtime/command marker.
    runtime = metadata.get("python")
    for name in ("ocdeck.cmd", "oc.cmd", "opencode.cmd"):
        path = root / "bin" / name
        if path.exists() and runtime:
            text = path.read_text(errors="replace")
            if runtime in text and " -m ocdeck " in text:
                shutil.move(str(path), str(backup / name))
    print("Uninstalled managed hooks, integration and configuration. Backups and Python environment retained.")
    return 0
