import argparse
import json
from pathlib import Path
import queue
import tempfile
import unittest
from unittest.mock import patch

from ocdeck.broker import Broker
from ocdeck.controls_cli import add_parser, run
from ocdeck.launch_profiles import HARNESS_NAMES, LaunchProfile, launch_profile, read_profiles
from ocdeck.model import Registry
from ocdeck.permissions import Permissions


class PermissionTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.registry = Registry(lambda _: True)
        self.registry.upsert({"id": "agent", "process": {"pid": 1}, "label": "project"})
        self.permissions = Permissions(self.registry, True, lambda: self.now)

    def offer(self):
        return self.permissions.offer({"owner": "agent", "tool": "Bash", "summary": "pytest"})["ticket"]

    def test_decision_is_delivered_once_and_old_click_cannot_approve_next(self):
        ticket = self.offer()
        self.assertTrue(self.permissions.decide(ticket, "allow"))
        self.assertFalse(self.permissions.decide(ticket, "deny"))
        self.assertEqual(self.permissions.poll({"ticket": ticket}), {"state": "decision", "decision": "allow"})
        self.assertEqual(self.permissions.poll({"ticket": ticket}), {"state": "delivered"})
        next_ticket = self.offer()
        self.assertFalse(self.permissions.decide(ticket, "allow"))
        self.assertEqual(self.permissions.poll({"ticket": next_ticket}), {"state": "pending"})

    def test_dead_adapter_and_reused_slot_invalidate_requests(self):
        ticket = self.offer()
        self.now += 3.1
        self.assertFalse(self.permissions.decide(ticket, "allow"))
        ticket = self.offer()
        self.registry.remove("agent")
        self.registry.upsert({"id": "agent", "process": {"pid": 1}})
        self.assertFalse(self.permissions.decide(ticket, "allow"))

    def test_polling_cannot_extend_deadline(self):
        ticket = self.offer()
        for _ in range(109):
            self.now += 1
            self.permissions.poll({"ticket": ticket})
        self.now += 1
        self.assertFalse(self.permissions.decide(ticket, "allow"))

    def test_success_requires_delivered_decision_and_live_lease(self):
        ticket = self.offer()
        self.assertFalse(self.permissions.finish({"ticket": ticket, "ok": True})["ok"])
        self.assertEqual(self.permissions.status(ticket), "pending")
        self.permissions.decide(ticket, "allow")
        self.assertFalse(self.permissions.finish({"ticket": ticket, "ok": True})["ok"])
        self.permissions.poll({"ticket": ticket})
        self.assertTrue(self.permissions.finish({"ticket": ticket, "ok": True})["ok"])
        self.assertEqual(self.permissions.status(ticket), "finished")
        ticket = self.offer()
        self.now += 4
        self.permissions.finish({"ticket": ticket, "ok": True})
        self.assertEqual(self.permissions.status(ticket), "expired")

    def test_disabled_and_queue_bound(self):
        self.assertEqual(Permissions(self.registry).offer({}), {"enabled": False})
        for _ in range(64):
            self.offer()
        with self.assertRaises(ValueError):
            self.offer()


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "config.json").write_text(json.dumps({"controls": {"enabled": True, "permissions": True}}))
        self.broker = Broker(self.root, mock=True, probe=lambda _: True, focus=lambda _: {"ok": True})
        self.controls = self.broker.controls
        self.addCleanup(self.temp.cleanup)

    def click(self, command):
        tile = next(t for t in self.controls.tiles() if t["command"] == command)
        return self.controls.handle(tile)

    def test_cli_roundtrip_preserves_spaces_percent_args_and_configuration(self):
        parser = argparse.ArgumentParser()
        add_parser(parser.add_subparsers(dest="command"))
        folder = self.root / "project with % spaces"
        folder.mkdir()
        with patch("ocdeck.controls_cli.home", return_value=self.root):
            run(
                parser.parse_args(
                    [
                        "controls",
                        "repo",
                        "set",
                        "My project",
                        "--directory",
                        str(folder),
                        "--harness",
                        "claude",
                        "--arg=--model",
                        "--arg",
                        "a b",
                    ]
                )
            )
            run(parser.parse_args(["controls", "repo", "set", "My project", "--harness", "gemini"]))
            run(parser.parse_args(["controls", "configure", "--hold-ms", "900", "--request-timeout", "60"]))
        profile = read_profiles(self.root / "launcher.ini")[0]
        self.assertEqual(profile.directory, folder)
        self.assertEqual(profile.harnesses, ("gemini",))
        self.assertEqual(profile.args, ("--model", "a b"))
        config = json.loads((self.root / "config.json").read_text())
        self.assertTrue(config["controls"]["permissions"])
        self.assertEqual(config["controls"]["hold_ms"], 900)

    def test_picker_confirm_and_stale_double_press(self):
        (self.root / "launcher.ini").write_text(f"[repo:Example]\ndirectory={self.root}\nharnesses=claude\n")
        self.controls.open(self.broker.registry.view()[0])
        old = self.controls.tiles()[0]
        self.click("repo")
        self.assertFalse(self.controls.handle(old)["ok"])
        self.click("agent")
        self.assertEqual(self.controls.page, "confirm")
        launched = []
        import threading

        done = threading.Event()

        def launch(profile, harness):
            launched.append((profile.directory, harness))
            done.set()

        self.controls.launch = launch
        launch_tile = next(t for t in self.controls.tiles() if t["command"] == "launch")
        self.controls.handle(launch_tile)
        self.controls.handle(launch_tile)
        self.assertTrue(done.wait(2))
        self.assertEqual(launched, [(self.root, "claude")])

    def test_physical_only_permission_review_and_no_synthetic_decision_route(self):
        self.broker.registry.upsert({"id": "agent", "process": {"pid": 1}, "label": "Project"})
        ticket = self.broker.permissions.offer({"owner": "agent", "tool": "Bash"})["ticket"]
        self.controls.open(self.broker.registry.view()[0])
        self.click("review")
        self.click("request")
        accept = next(t for t in self.controls.tiles() if t["command"] == "allow")
        self.assertFalse(self.broker.handle_press(accept, synthetic=True)["ok"])
        self.assertEqual(self.broker.permissions.poll({"ticket": ticket})["state"], "pending")
        self.assertTrue(self.broker.handle_press(accept)["ok"])
        self.assertEqual(self.broker.permissions.poll({"ticket": ticket})["decision"], "allow")

    def test_hold_opens_menu_but_tap_focuses_and_stale_release_drops(self):
        device = self.broker.device
        self.broker.registry.upsert({"id": "agent", "process": {"pid": 1}})
        device.presented[0] = self.broker.registry.view()[0]
        with patch("ocdeck.device.time.monotonic", side_effect=[1, 1.1]):
            device.press(0, True)
            device.press(0, False)
        self.assertNotEqual(self.broker.presses.get_nowait().get("_action"), "open_controls")
        with patch("ocdeck.device.time.monotonic", side_effect=[2, 3]):
            device.press(0, True)
            device.press(0, False)
        self.assertEqual(self.broker.presses.get_nowait()["_action"], "open_controls")
        device.press(0, True)
        device.presented[0] = {**device.presented[0], "generation": 100}
        device.press(0, False)
        with self.assertRaises(queue.Empty):
            self.broker.presses.get_nowait()

    def test_ini_refuses_relative_directories_and_unknown_options(self):
        file = self.root / "launcher.ini"
        for value in ("[repo:A]\ndirectory=relative", f"[repo:A]\ndirectory={self.root}\nshell=oops"):
            file.write_text(value)
            with self.assertRaises(ValueError):
                read_profiles(file)

    def test_every_harness_receives_explicit_cwd_and_literal_arguments(self):
        import os
        from types import SimpleNamespace

        before = os.getcwd()
        for harness in HARNESS_NAMES:
            profile = LaunchProfile("fixture", self.root, (harness,), ("--model", "literal & value"))
            with (
                patch("ocdeck.launch_profiles.os", SimpleNamespace(name="nt")),
                patch("ocdeck.launcher.launch") as opencode,
                patch("ocdeck.harness.launch") as other,
            ):
                launch_profile(profile, harness)
                called = opencode if harness == "opencode" else other
                self.assertEqual(called.call_args.kwargs["cwd"], str(self.root))
                self.assertEqual(called.call_args.args[-1], ["--model", "literal & value"])
        self.assertEqual(os.getcwd(), before)

    def test_full_deck_blocks_launch_and_menu_expiry_rejects_press(self):
        (self.root / "launcher.ini").write_text(f"[repo:Example]\ndirectory={self.root}\nharnesses=claude\n")
        self.controls.open(self.broker.registry.view()[0])
        self.click("repo")
        self.click("agent")
        for index in range(6):
            self.broker.registry.upsert({"id": str(index), "process": {"pid": index + 1}})
        with patch.object(self.controls, "launch") as launch:
            self.assertFalse(self.click("launch")["ok"])
            launch.assert_not_called()
        self.assertIn("full", self.controls.message)
        self.controls.until = 0
        self.assertFalse(self.controls.handle({"revision": self.controls.revision, "command": "close"})["ok"])


if __name__ == "__main__":
    unittest.main()
