"""Real wheel-to-wheel pip upgrade while an isolated mock broker stays running."""

import base64
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
import zipfile


def wheel(destination, version):
    package = Path(__file__).resolve().parents[1] / "ocdeck"
    info = f"agentstreamdeck-{version}.dist-info"
    files = {}
    for path in package.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            files["ocdeck/" + path.relative_to(package).as_posix()] = path.read_bytes()
    files["ocdeck/__init__.py"] = re.sub(
        rb'__version__ = "[^"]+"', f'__version__ = "{version}"'.encode(), files["ocdeck/__init__.py"], count=1
    )
    files[info + "/METADATA"] = f"Metadata-Version: 2.1\nName: agentstreamdeck\nVersion: {version}\n".encode()
    files[info + "/WHEEL"] = (
        b"Wheel-Version: 1.0\nGenerator: integration-test\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    )
    record = io.StringIO(newline="")
    writer = csv.writer(record)
    for name, data in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        writer.writerow((name, "sha256=" + digest, len(data)))
    writer.writerow((info + "/RECORD", "", ""))
    files[info + "/RECORD"] = record.getvalue().encode()
    target = destination / f"agentstreamdeck-{version}-py3-none-any.whl"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return target


def request(root, path="status"):
    discovery = json.loads((root / "discovery.json").read_text())
    token = (root / "token").read_text().strip()
    req = urllib.request.Request(
        f"http://127.0.0.1:{discovery['port']}/v1/{path}",
        headers={"Authorization": "Bearer " + token},
        method="POST" if path == "stop" else "GET",
        data=b"{}" if path == "stop" else None,
    )
    with urllib.request.urlopen(req, timeout=2) as response:
        return json.load(response)


class PipRestartIntegrationTests(unittest.TestCase):
    def test_real_pip_update_restarts_broker_in_same_home(self):
        if sys.platform == "linux" and int(Path("/proc/self/stat").read_text().split()[0]) != os.getpid():
            self.skipTest("Sandbox /proc exposes host PIDs; run real process lifecycle test on CI")
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "custom-home"
            root.mkdir()
            (root / "config.json").write_text(
                json.dumps(
                    {
                        "auto_restart_on_upgrade": True,
                        "check_updates": False,
                        "jelly": {"enabled": False},
                    }
                )
            )
            subprocess.run(
                [sys.executable, "-m", "venv", "--system-site-packages", str(base / "venv")],
                check=True,
                capture_output=True,
                timeout=60,
            )
            python = base / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            old, new = wheel(base, "90.0.1"), wheel(base, "90.0.2")
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            env["OCDECK_HOME"] = str(root)

            def install(path):
                subprocess.run(
                    [str(python), "-m", "pip", "install", "--no-index", "--no-deps", str(path)],
                    cwd=root,
                    env=env,
                    capture_output=True,
                    check=True,
                    timeout=60,
                )

            install(old)
            log = (base / "process.log").open("w")
            process = subprocess.Popen(
                [str(python), "-m", "ocdeck", "broker", "--mock"], cwd=root, env=env, stdout=log, stderr=log
            )
            try:

                def wait_version(expected):
                    deadline = time.monotonic() + 60
                    while time.monotonic() < deadline:
                        process.poll()  # Reap the original process so the restart helper observes its exit.
                        if expected == "90.0.1" and process.returncode is not None:
                            break
                        try:
                            status = request(root)
                            if status["device"].get("pip_upgrade", {}).get("running_version") == expected:
                                return status
                        except (OSError, ValueError, KeyError):
                            pass
                        time.sleep(0.25)
                    diagnostic = subprocess.run(
                        [
                            str(python),
                            "-c",
                            "import sys,ocdeck; print(sys.executable, ocdeck.__version__, ocdeck.__file__)",
                        ],
                        cwd=root,
                        env=env,
                        capture_output=True,
                        text=True,
                    )
                    self.fail(
                        f"broker exit={process.poll()} interpreter={diagnostic.stdout} stderr={diagnostic.stderr}\n"
                        + ((root / "broker.log").read_text()[-4000:] if (root / "broker.log").exists() else "")
                        + (base / "process.log").read_text()[-4000:]
                    )

                before = wait_version("90.0.1")
                install(new)
                after = wait_version("90.0.2")
                self.assertNotEqual(before["brokerPid"], after["brokerPid"])
                self.assertTrue(after["device"]["mock"])
                process.wait(timeout=10)
            finally:
                try:
                    request(root, "stop")
                except (OSError, ValueError, KeyError):
                    pass
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)
                log.close()
                # Let the detached replacement finish its normal device shutdown.
                deadline = time.monotonic() + 8
                while (root / "discovery.json").exists() and time.monotonic() < deadline:
                    time.sleep(0.1)
