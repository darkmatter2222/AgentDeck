import copy
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import queue
import random
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile

from ocdeck.alerts import Alerts
from ocdeck.appearance_io import validate, import_settings, export_settings
from ocdeck.art import frame
from ocdeck.appearance import Appearance, THEMES
from ocdeck.broker import Broker
from ocdeck.device import DeviceLoop, device_types, WheelTransport
from ocdeck.model import Registry
from ocdeck.observability import JsonFormatter, correlation, tail
from ocdeck.security import scrub, scrub_text
from ocdeck.updates import check
from ocdeck.uninstall import discover


class NextTests(unittest.TestCase):
    def test_uninstall_preserves_unrelated_hooks_and_backs_up_config(self):
        from ocdeck.harness import install
        from ocdeck.uninstall import uninstall

        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "home"
            project = Path(d) / "project"
            project.mkdir()
            root.mkdir()
            target = project / ".codex" / "hooks.json"
            target.parent.mkdir()
            unrelated = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo keep"}]}]}}
            target.write_text(json.dumps(unrelated))
            (root / "config.json").write_text('{"fps":24}')
            with (
                patch.dict(os.environ, {"OCDECK_HOME": str(root)}),
                patch("ocdeck.uninstall.request", side_effect=ConnectionError),
                patch("ocdeck.uninstall.subprocess.run") as integration,
            ):
                self.assertEqual(install("codex", project), 0)
                before = target.read_bytes()
                with patch("builtins.print"):
                    self.assertEqual(uninstall([project], dry_run=True), 0)
                    self.assertEqual(target.read_bytes(), before)
                    self.assertTrue((root / "config.json").is_file())
                    self.assertEqual(uninstall([project]), 0)
                self.assertEqual(json.loads(target.read_text()), unrelated)
                self.assertFalse((project / ".agentdeck/codex.json").exists())
                self.assertFalse((root / "config.json").exists())
                self.assertEqual(len(list((root / "backups").glob("*/config.json"))), 1)

    def test_malformed_config_never_silently_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            config = root / "config.json"
            config.write_text("{broken")
            with self.assertRaises(ValueError):
                Broker(root, mock=True)
            result = subprocess.run(
                [sys.executable, "-m", "ocdeck", "appearance", "--theme", "mono"],
                env={**os.environ, "OCDECK_HOME": d},
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(config.read_text(), "{broken")

    def test_errors_have_actionable_commands(self):
        from ocdeck.errors import CATALOG, message

        for code in CATALOG:
            value = message(code)
            self.assertIn(code, value)
            self.assertIn("ocdeck ", value)
            self.assertIn("TROUBLESHOOTING.md", value)

    def test_configuration_rejects_invalid_optional_values(self):
        from ocdeck.settings import validate_config

        for value in (
            {"slots": True},
            {"alerts": {"sound": "yes"}},
            {"alerts": {"states": "input"}},
            {"alerts": {"cooldown_seconds": float("nan")}},
            {"alerts": {"muted_slots": ["33"]}},
        ):
            with self.assertRaises(ValueError):
                validate_config(value)

    def test_log_rotation_is_bounded_and_redacts(self):
        from logging.handlers import RotatingFileHandler

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "broker.log"
            handler = RotatingFileHandler(path, maxBytes=300, backupCount=3)
            handler.setFormatter(JsonFormatter())
            for i in range(40):
                handler.handle(
                    logging.LogRecord("t", logging.ERROR, "", 1, 'password="two word secret" %s', (i,), None)
                )
            handler.close()
            files = list(Path(d).glob("broker.log*"))
            self.assertLessEqual(len(files), 4)
            for file in files:
                text = file.read_text()
                self.assertNotIn("word secret", text)
                for line in text.splitlines():
                    json.loads(line)

    def test_layout_resize_overflow_and_stale_presses(self):
        for count in (6, 15, 32):
            r = Registry(lambda _: True, slots=count)
            for i in range(count + 2):
                r.upsert({"id": str(i), "process": {"pid": i}})
            self.assertEqual(len(r.view()), count)
            last = r.view()[-1]
            self.assertIsNotNone(r.resolve(last["slot"], last["generation"], last["id"]))
            r.remove(last["id"])
            self.assertEqual(r.view()[-1]["id"], str(count))
            self.assertIsNone(r.resolve(last["slot"], last["generation"], last["id"]))
            r.resize(32 if count != 32 else 6)
            self.assertIsNone(r.resolve(last["slot"], last["generation"], last["id"]))

    def test_device_models_use_correct_driver_and_key_count(self):
        for pid, count in ((0x63, 6), (0x80, 15), (0x6C, 32), (0xB9, 15), (0xBA, 32)):
            deck = device_types()[pid](WheelTransport({"product_id": pid}))
            self.assertEqual(deck.key_count(), count)

    def test_mock_render_and_press_last_key_all_sizes(self):
        for count in (6, 15, 32):
            r = Registry(lambda _: True, slots=count)
            for i in range(count):
                r.upsert({"id": str(i), "process": {"pid": i}})
            stop, presses = threading.Event(), queue.Queue()
            loop = DeviceLoop(r, presses, stop, {"fps": 30}, mock=True)
            thread = threading.Thread(target=loop.run)
            thread.start()
            try:
                import time

                deadline = time.monotonic() + 2
                while loop.presented[-1] is None and time.monotonic() < deadline:
                    time.sleep(0.01)
                loop.press(count - 1, True)
                self.assertEqual(presses.get(timeout=1)["id"], str(count - 1))
            finally:
                stop.set()
                thread.join(3)

    def test_alert_dedup_rate_limit_and_slot_suppression(self):
        now = [0]
        a = Alerts(
            {"alerts": {"sound": True, "toast": True, "cooldown_seconds": 10, "muted_slots": ["2"]}},
            clock=lambda: now[0],
        )
        q = hashlib.sha256(b"q").hexdigest()
        v = {"id": "a", "slot": 0, "state": "input", "requestIds": [q]}
        a.observe([v])
        a.observe([v])
        self.assertEqual(a.queue.qsize(), 1)
        self.assertTrue(a.queue.get()["toast"])
        # Unknown refresh/recovery cannot duplicate the toast for this request.
        a.observe([{**v, "state": "unknown"}])
        a.observe([v])
        self.assertTrue(a.queue.empty())
        a.observe([{**v, "requestIds": [hashlib.sha256(b"q2").hexdigest()]}])
        self.assertTrue(a.queue.get()["toast"])
        a.observe([{**v, "id": "b", "slot": 1}])
        self.assertTrue(a.queue.empty())
        now[0] = 11
        a.observe([{**v, "state": "idle"}])
        a.observe([v])
        self.assertTrue(a.queue.get()["sound"])

    def test_unknown_counts_and_verified_counts(self):
        r = Registry(lambda _: True)
        r.upsert({"id": "a", "process": {}})
        snap = {"producer": "p", "seq": 1, "status": "busy", "pending": 3, "pendingKnown": True}
        r.snapshot("a", snap)
        self.assertEqual(r.view()[0]["pending"], 3)
        r.snapshot("a", {**snap, "seq": 2, "pendingKnown": False, "inputNeeded": True, "pending": 0})
        self.assertEqual(r.view()[0]["state"], "input")
        self.assertIsNone(r.view()[0]["pending"])
        with self.assertRaises(ValueError):
            r.snapshot("a", {**snap, "seq": 3, "requestIds": ["raw secret"]})

    def test_snapshot_scrubbing_and_pixels(self):
        random.seed(72)
        for _ in range(30):
            secret = "sk-" + "".join(random.choices("abcdef0123456789", k=40))
            r = Registry(lambda _: True, secrets=(secret,))
            r.upsert({"id": "a", "process": {}, "label": secret})
            r.snapshot("a", {"producer": "p", "seq": 1, "status": "busy", "detail": secret})
            view = r.view()[0]
            self.assertNotIn(secret, json.dumps(view))
            self.assertEqual(frame("running", secret, 0, 24).tobytes(), frame("running", "[REDACTED]", 0, 24).tobytes())
            record = logging.LogRecord("test", logging.ERROR, "", 1, "failure %s", (secret,), None)
            self.assertNotIn(secret, JsonFormatter().format(record))

    def test_redaction_report_and_nested_config(self):
        from ocdeck.diagnostics import report

        secret = "unique_local_broker_credential"
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "token").write_text(secret)
            (root / "config.json").write_text(json.dumps({"nested": {"API_KEY": "hunter2"}, "alias": secret}))
            (root / "broker.log").write_text("Bearer plain_secret\npassword=hunter2\n" + secret)
            output = root / "report.zip"
            with patch("ocdeck.diagnostics.request", side_effect=ConnectionError):
                report(output, root=root)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(set(z.namelist()), {"status.json", "versions.json", "config.json", "logs.json"})
                payload = b"".join(z.read(n) for n in z.namelist()).decode()
            for value in (secret, "hunter2", "plain_secret"):
                self.assertNotIn(value, payload)

    def test_json_log_correlation_and_exception_scrub(self):
        token = correlation.set("test-request")
        try:
            record = logging.LogRecord("test", logging.ERROR, "", 1, "password=hunter2", (), None)
            value = json.loads(JsonFormatter().format(record))
            self.assertEqual(value["correlationId"], "test-request")
            self.assertNotIn("hunter2", value["message"])
        finally:
            correlation.reset(token)

    def test_import_export_roundtrip_and_rejection(self):
        before = {
            "serial": "keep",
            "alerts": {"toast": True},
            "appearance": {"theme": "ocean"},
            "buttons": {"32": {"alias": "XL"}},
        }
        payload = export_settings(before)
        self.assertNotIn("serial", payload)
        self.assertEqual(import_settings(before, payload)["alerts"], before["alerts"])
        for bad in (
            {**payload, "token": "no"},
            {**payload, "buttons": {"33": {}}},
            {**payload, "appearance": {"bad": 1}},
            {**payload, "fps": True},
        ):
            with self.assertRaises(ValueError):
                validate(bad)

    def test_dry_run_creates_no_files_even_with_export(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "ocdeck",
                    "appearance",
                    "--theme",
                    "high-contrast",
                    "--dry-run",
                    "--export",
                    str(root / "out.json"),
                ],
                env={**os.environ, "OCDECK_HOME": d},
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertIn("appearance", data["diff"])
            self.assertTrue(data["preview"].startswith("data:image/png;base64,"))
            self.assertEqual(list(root.iterdir()), [])

    def test_update_offline_disabled_and_once_per_version(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)

            def fail():
                raise OSError("offline")

            self.assertIsNone(check(root, {}, fail))
            with patch("builtins.print") as printed:
                release = lambda: {"tag_name": "v99.0.0", "body": "Notes"}
                check(root, {}, release)
                check(root, {}, release)
                self.assertEqual(printed.call_count, 1)

            def forbidden():
                self.fail("Network used while disabled")

            self.assertIsNone(check(root, {"check_updates": False}, forbidden))

    def test_receipt_discovery_excludes_dependencies(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for prefix in ("project", "node_modules/other"):
                directory = root / prefix / ".agentdeck"
                directory.mkdir(parents=True)
                (directory / "codex.json").write_text("{}")
            self.assertEqual(discover([root]), [str((root / "project").resolve())])

    def test_high_contrast_state_colors(self):
        for color in THEMES["high-contrast"]:
            channels = [int(color[i : i + 2], 16) / 255 for i in (0, 2, 4)]
            linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
            luminance = sum(a * b for a, b in zip(linear, (0.2126, 0.7152, 0.0722)))
            self.assertGreater((luminance + 0.05) / 0.05, 4.5)
        self.assertNotEqual(
            frame("input", "x", 0, 24, pending=3).tobytes(), frame("input", "x", 0, 24, pending=None).tobytes()
        )

    def test_doctor_no_device_never_enumerates(self):
        from ocdeck.diagnostics import doctor

        with (
            tempfile.TemporaryDirectory() as d,
            patch("ocdeck.device.enumerate_devices", side_effect=AssertionError("hardware used")),
            patch("ocdeck.diagnostics.request", side_effect=ConnectionError),
        ):
            rows = doctor(project=d, no_device=True, root=d)
            self.assertTrue(any(r["check"] == "broker" and r["result"] == "FAIL" for r in rows))
            self.assertGreater(len(rows), 20)


if __name__ == "__main__":
    unittest.main()
