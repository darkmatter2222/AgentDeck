"""Bounded PyPI update checks plus an explicit, user-triggered self update."""

import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

from packaging.version import InvalidVersion, Version

from . import __version__
from .common import atomic_json, read_json
from .security import scrub

PYPI_URL = "https://pypi.org/pypi/agentstreamdeck/json"
RELEASE_URL = "https://github.com/darkmatter2222/AgentStreamDeck/releases"
CHECK_INTERVAL = 300
LOG = logging.getLogger(__name__)


def check(root, config, fetch=None):
    """Return update metadata when PyPI has a newer stable version."""
    if not config.get("check_updates", True):
        return None
    try:
        if fetch is None:
            req = urllib.request.Request(
                PYPI_URL,
                headers={"User-Agent": f"AgentStreamDeck/{__version__}", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                raw = response.read(262145)
            if len(raw) > 262144:
                raise ValueError("PyPI response too large")
            release = json.loads(raw)
        else:
            release = fetch()

        # Production uses PyPI's JSON shape. Keep support for the old injected
        # GitHub-release fixture shape so existing tests and offline callers do not break.
        if isinstance(release.get("info"), dict):
            version = str(release["info"]["version"])
            source = "pypi"
        else:
            version = str(release["tag_name"]).lstrip("v")
            source = "legacy-fixture"

        candidate = Version(version)
        if candidate.is_prerelease or candidate <= Version(__version__):
            return None

        info = {
            "version": version,
            "url": RELEASE_URL,
            "package": f"agentstreamdeck=={version}",
            "source": source,
        }
        state = read_json(Path(root) / "update.json", {}) or {}
        if state.get("version") != version:
            LOG.info("Update available on PyPI: %s", version)
            print(f"AgentStreamDeck {version} available on PyPI: {RELEASE_URL}", flush=True)
            atomic_json(Path(root) / "update.json", info)
        return info
    except (OSError, ValueError, KeyError, TypeError, InvalidVersion, json.JSONDecodeError):
        LOG.info("Update check unavailable; continuing offline")
        return None


def install(version, runner=None):
    """Install one validated AgentStreamDeck version into the running interpreter."""
    parsed = Version(str(version))
    if parsed.is_prerelease:
        raise ValueError("Refusing prerelease self-update")
    package = f"agentstreamdeck=={parsed}"
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-input",
        "--upgrade",
        "--upgrade-strategy",
        "only-if-needed",
        package,
    ]
    execute = runner or subprocess.run
    result = execute(command, capture_output=True, text=True, timeout=300)
    if result.returncode:
        detail = scrub((result.stderr or result.stdout or "pip update failed")[-2000:])
        raise RuntimeError(detail)
    LOG.info("Installed AgentStreamDeck %s from PyPI", parsed)
    return {"ok": True, "version": str(parsed), "package": package}


def schedule_restart(root, parent_pid=None, popen=None):
    """Start a tiny detached worker that restarts the broker after this process exits."""
    parent_pid = int(parent_pid or os.getpid())
    root = str(Path(root))
    code = r"""
import os
import subprocess
import sys
import time

pid = int(sys.argv[1])
root = sys.argv[2]

for _ in range(150):
    alive = False
    if os.name == "nt":
        probe = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True,
            text=True,
            creationflags=0x08000000,
        )
        alive = str(pid) in probe.stdout
    else:
        try:
            os.kill(pid, 0)
            alive = True
        except OSError:
            alive = False
    if not alive:
        break
    time.sleep(0.1)

command = [sys.executable, "-m", "ocdeck", "broker"]
kwargs = {
    "cwd": root,
    "stdin": subprocess.DEVNULL,
    "stdout": subprocess.DEVNULL,
    "stderr": subprocess.DEVNULL,
    "close_fds": True,
}
if os.name == "nt":
    kwargs["creationflags"] = 0x00000008 | 0x00000200
else:
    kwargs["start_new_session"] = True
subprocess.Popen(command, **kwargs)
"""
    env = os.environ.copy()
    # A permanent source checkout on PYTHONPATH would shadow the newly installed wheel.
    env.pop("PYTHONPATH", None)
    command = [sys.executable, "-c", code, str(parent_pid), root]
    launch = popen or subprocess.Popen
    kwargs = {
        "env": env,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if os.name == "nt":
        kwargs["creationflags"] = 0x00000008 | 0x00000200
    else:
        kwargs["start_new_session"] = True
    launch(command, **kwargs)
    return {"ok": True, "parentPid": parent_pid}
