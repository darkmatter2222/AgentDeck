"""External pip upgrades must finish and verify before the broker is stopped."""

import base64
import hashlib
from importlib import metadata
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ocdeck.upgrade_watch import UpgradeWatch, complete, importable, pip_running, watch
from ocdeck.updates import schedule_restart


class UpgradeWatchTests(unittest.TestCase):
    def test_requires_ten_seconds_of_stable_changed_installation(self):
        monitor = UpgradeWatch("1.0")
        self.assertFalse(monitor.ready(0, ("2.0", "record"), False))
        self.assertFalse(monitor.ready(9.9, ("2.0", "record"), False))
        self.assertTrue(monitor.ready(10, ("2.0", "record"), False))

    def test_uninstall_rollback_installer_and_record_changes_reset_wait(self):
        for reset, busy in (
            (None, False),
            (("1.0", "old"), False),
            (("2.0", "new"), True),
            (("2.0", "changed"), False),
        ):
            monitor = UpgradeWatch("1.0")
            monitor.ready(0, ("2.0", "new"), False)
            self.assertFalse(monitor.ready(10, reset, busy))
            self.assertFalse(monitor.ready(11, ("2.0", "new"), False))
            self.assertTrue(monitor.ready(21, ("2.0", "new"), False))

    def test_unchanged_version_never_restarts(self):
        monitor = UpgradeWatch("1.0")
        for t in (0, 10, 10000):
            self.assertFalse(monitor.ready(t, ("1.0", "record"), False))

    def test_record_hashes_detect_missing_or_partial_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "ocdeck").mkdir()
            data = b'__version__ = "2.0"\n'
            (root / "ocdeck/__init__.py").write_bytes(data)
            info = root / "agentstreamdeck-2.0.dist-info"
            info.mkdir()
            (info / "METADATA").write_text("Name: agentstreamdeck\nVersion: 2.0\n")
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
            (info / "RECORD").write_text(f"ocdeck/__init__.py,sha256={digest},{len(data)}\n")
            dist = metadata.Distribution.at(info)
            self.assertTrue(complete(dist))
            with (info / "RECORD").open("a") as record:
                record.write("ocdeck/missing-asset.png,sha256=missing,4\n")
            self.assertFalse(complete(dist))
            (info / "RECORD").write_text(f"ocdeck/__init__.py,sha256={digest},{len(data)}\n")
            (root / "ocdeck/__init__.py").write_bytes(b"partial")
            self.assertFalse(complete(dist))
            (root / "ocdeck/__init__.py").unlink()
            self.assertFalse(complete(dist))

    def test_fresh_probe_uses_same_interpreter_clean_path_and_custom_home(self):
        with tempfile.TemporaryDirectory() as td, patch.dict("os.environ", {"PYTHONPATH": "/old/checkout"}):
            runner = Mock(return_value=SimpleNamespace(returncode=0, stdout="2.0\n"))
            self.assertTrue(importable("2.0", td, runner))
            kwargs = runner.call_args.kwargs
            self.assertEqual(kwargs["cwd"], td)
            self.assertNotIn("PYTHONPATH", kwargs["env"])
            self.assertEqual(kwargs["env"]["OCDECK_HOME"], str(Path(td).resolve()))
            runner.return_value.stdout = "1.0\n"
            self.assertFalse(importable("2.0", td, runner))
            runner.return_value.returncode = 1
            self.assertFalse(importable("2.0", td, runner))

    def test_pip_processes_are_detected_without_matching_other_python_scripts(self):
        for args, expected in (
            (["python", "-m", "pip", "install", "agentstreamdeck"], True),
            (["pip3", "install", "agentstreamdeck"], True),
            (["python", "example.py", "install"], False),
            (["python", "-m", "pip", "--version"], False),
        ):
            with patch(
                "ocdeck.upgrade_watch.psutil.process_iter", return_value=[SimpleNamespace(info={"cmdline": args})]
            ):
                self.assertEqual(pip_running(), expected)

    def test_source_checkout_skips_watcher(self):
        broker = SimpleNamespace(device=SimpleNamespace(status={}), stop=Mock())
        dist = Mock()
        dist.locate_file.return_value = "/another/location/ocdeck/__init__.py"
        with patch("ocdeck.upgrade_watch.installed", return_value=(dist, ("2.0", "hash"))):
            watch(broker)
        broker.stop.wait.assert_not_called()
        self.assertEqual(broker.device.status["pip_upgrade"]["state"], "disabled")

    def test_watcher_schedules_before_stopping_and_survives_verification_failure(self):
        broker = SimpleNamespace(root=Path("."), device=SimpleNamespace(status={}), stop=Mock())
        broker.stop.wait.side_effect = [False, False, False, True]
        broker.stop.is_set.return_value = False
        dist = Mock()
        import ocdeck.upgrade_watch as module

        dist.locate_file.return_value = Path(module.__file__).with_name("__init__.py")
        order = []
        broker.stop.set.side_effect = lambda: order.append("stop")
        with (
            patch.object(module, "installed", return_value=(dist, ("99.0", "hash"))),
            patch.object(module, "pip_running", return_value=False),
            patch.object(module.time, "monotonic", side_effect=[0, 10, 20]),
            patch.object(module, "complete", side_effect=[False, True]),
            patch.object(module, "importable", return_value=True),
            patch.object(module, "schedule_restart", side_effect=lambda _, **kwargs: order.append("schedule")),
        ):
            watch(broker)
        self.assertEqual(order, ["schedule", "stop"])

    def test_failed_restart_launch_does_not_stop_running_broker(self):
        broker = SimpleNamespace(root=Path("."), device=SimpleNamespace(status={}), stop=Mock())
        broker.stop.wait.side_effect = [False, False, True]
        broker.stop.is_set.return_value = False
        dist = Mock()
        import ocdeck.upgrade_watch as module

        dist.locate_file.return_value = Path(module.__file__).with_name("__init__.py")
        with (
            patch.object(module, "installed", return_value=(dist, ("99.0", "hash"))),
            patch.object(module, "pip_running", return_value=False),
            patch.object(module.time, "monotonic", side_effect=[0, 10]),
            patch.object(module, "complete", return_value=True),
            patch.object(module, "importable", return_value=True),
            patch.object(module, "schedule_restart", side_effect=OSError("cannot launch")),
        ):
            watch(broker)
        broker.stop.set.assert_not_called()

    def test_restart_preserves_custom_home(self):
        popen = Mock()
        with tempfile.TemporaryDirectory() as td:
            schedule_restart(td, parent_pid=123, popen=popen)
            self.assertEqual(popen.call_args.kwargs["env"]["OCDECK_HOME"], str(Path(td).resolve()))
