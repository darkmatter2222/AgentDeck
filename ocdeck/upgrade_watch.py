"""Activate externally installed wheels after pip finishes; no installer hooks."""

import base64
import csv
import io
import hashlib
from importlib import metadata
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

from . import __version__
from .updates import UPDATE_LOCK, schedule_restart

LOG = logging.getLogger(__name__)
POLL_SECONDS = 5
SETTLE_SECONDS = 10


def installed():
    dist = metadata.distribution("agentstreamdeck")
    direct = json.loads(dist.read_text("direct_url.json") or "{}")
    if direct.get("dir_info", {}).get("editable"):
        return None
    record = dist.read_text("RECORD")
    if not record:
        return None
    return dist, (dist.version, hashlib.sha256(record.encode()).hexdigest())


def pip_running():
    """Wait for visible pip installers, including their rollback/cleanup phase."""
    for proc in psutil.process_iter(["cmdline"]):
        try:
            args = [str(arg).lower() for arg in proc.info.get("cmdline") or []]
            if not args or "install" not in args:
                continue
            if Path(args[0]).name.startswith("pip") or any(
                args[i] == "-m" and args[i + 1] == "pip" for i in range(len(args) - 1)
            ):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def complete(dist):
    """Check RECORD hashes so an interrupted replacement cannot trigger restart."""
    # Parse RECORD directly: importlib.metadata.files() may filter missing
    # files, which would hide a partially installed runtime or asset.
    rows = list(csv.reader(io.StringIO(dist.read_text("RECORD") or "")))
    if not rows or not any(row and row[0].replace("\\", "/") == "ocdeck/__init__.py" for row in rows):
        return False
    for row in rows:
        if len(row) != 3:
            return False
        name, recorded_hash, _size = row
        if name.endswith(".pyc"):
            continue
        path = Path(str(dist.locate_file(name)))
        if not path.is_file():
            return False
        if not recorded_hash:
            continue
        algorithm, expected = recorded_hash.split("=", 1)
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, algorithm).digest()
        if base64.urlsafe_b64encode(digest).rstrip(b"=").decode() != expected:
            return False
    return True


def importable(version, root, runner=subprocess.run):
    """A fresh interpreter must load the installed version and its dependencies."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["OCDECK_HOME"] = str(Path(root).resolve())
    result = runner(
        [sys.executable, "-c", "import ocdeck, hid, psutil, PIL, StreamDeck; print(ocdeck.__version__)"],
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        **({"creationflags": 0x08000000} if os.name == "nt" else {}),
    )
    return result.returncode == 0 and result.stdout.strip() == version


class UpgradeWatch:
    def __init__(self, running_version=__version__):
        self.running_version = running_version
        self.pending = None
        self.since = 0.0

    def ready(self, now, candidate, busy):
        """Require a stable changed wheel and no running installer for ten seconds."""
        if candidate is None or candidate[0] == self.running_version or busy:
            self.pending = None
            return False
        if candidate != self.pending:
            self.pending, self.since = candidate, now
            return False
        return now - self.since >= SETTLE_SECONDS


def watch(broker):
    monitor = UpgradeWatch()
    broker.device.status["pip_upgrade"] = {"state": "watching", "running_version": monitor.running_version}
    try:
        initial = installed()
        # Editing a checkout must never relaunch a different installed package.
        if (
            initial is None
            or Path(str(initial[0].locate_file("ocdeck/__init__.py"))).resolve()
            != Path(__file__).with_name("__init__.py").resolve()
        ):
            broker.device.status["pip_upgrade"] = {"state": "disabled", "reason": "source or editable installation"}
            return
    except (metadata.PackageNotFoundError, OSError, ValueError):
        # Metadata may be temporarily absent during an in-progress pip uninstall.
        initial = None
    while not broker.stop.wait(POLL_SECONDS):
        if not UPDATE_LOCK.acquire(blocking=False):
            monitor.pending = None
            continue
        try:
            candidate = installed()
            if not monitor.ready(time.monotonic(), candidate[1] if candidate else None, pip_running()):
                continue
            if candidate is None:
                continue
            dist, signature = candidate
            if not complete(dist) or not importable(signature[0], broker.root):
                broker.device.status["pip_upgrade"] = {"state": "waiting", "version": signature[0]}
                continue
            # Recheck metadata and installer state after verification to close the
            # common replacement/rollback race before relinquishing the device.
            latest = installed()
            if latest is None or latest[1] != signature or pip_running() or broker.stop.is_set():
                monitor.pending = None
                continue
            broker.device.status["pip_upgrade"] = {"state": "restarting", "version": signature[0]}
            LOG.info("Pip upgrade ready: %s -> %s; restarting broker", monitor.running_version, signature[0])
            schedule_restart(broker.root, mock=getattr(broker.device, "mock", False))
            broker.stop.set()
            return
        except Exception:
            monitor.pending = None
            LOG.info("Pip upgrade not ready; keeping the current broker running", exc_info=True)
        finally:
            UPDATE_LOCK.release()
