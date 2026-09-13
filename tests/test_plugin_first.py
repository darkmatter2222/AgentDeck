import os
import unittest
from unittest import mock

from ocdeck.device import WheelTransport
from ocdeck.direct_hooks import DirectHooks
from ocdeck.jelly_art import POSES, logical_sprite
from ocdeck.model import Registry


class _Handle:
    def __init__(self, value):
        self.value = value

    def read(self, _length):
        return self.value


class PluginFirstTests(unittest.TestCase):
    def test_hid_report_without_report_id_is_normalized(self):
        transport = WheelTransport({"path": b"x", "vendor_id": 1, "product_id": 1})
        transport.handle = _Handle([1, 0, 1, 0, 1, 0])
        self.assertEqual(transport.read(7), b"\x00\x01\x00\x01\x00\x01\x00")

    def test_every_jelly_gesture_stays_blob_sized_and_below_crown(self):
        gestures = ("wave", "point", "up", "down", "scratch", "cheer", "clap")
        for pose, (width, height, _lean) in POSES.items():
            top = 33 - height + 1
            for gesture in gestures:
                for step in range(1, 5):
                    with self.subTest(pose=pose, gesture=gesture, step=step):
                        image = logical_sprite(pose, "neutral", "center", gesture, step)
                        alpha = image.getchannel("A").getbbox()
                        self.assertIsNotNone(alpha)
                        left, upper, right, _bottom = alpha
                        self.assertGreaterEqual(upper, max(0, top - 1))
                        self.assertLessEqual(right - left, min(40, width + 9))

    def test_direct_hook_record_does_not_stale_between_events(self):
        clock = [0.0]
        process = {"pid": os.getpid(), "created": 1.0}
        registry = Registry(lambda value: value == process, clock=lambda: clock[0], stale_after=10)
        hooks = DirectHooks(registry)
        with (
            mock.patch("ocdeck.direct_hooks._identity", return_value=process),
            mock.patch("ocdeck.direct_hooks.capture_window", return_value={}),
        ):
            result = hooks.event(
                {
                    "profile": "claude",
                    "parentPid": os.getpid(),
                    "cwd": "/tmp/project",
                    "event": {
                        "event": "SessionStart",
                        "action": "start",
                        "session": "session-1",
                        "request": "",
                        "question": False,
                        "failed": False,
                    },
                }
            )
        self.assertTrue(result["ok"])
        clock[0] = 100.0
        self.assertEqual(registry.view()[0]["state"], "idle")

    def test_direct_hook_question_becomes_input_and_end_removes_slot(self):
        process = {"pid": os.getpid(), "created": 1.0}
        registry = Registry(lambda value: value == process)
        hooks = DirectHooks(registry)
        base = {"profile": "claude", "parentPid": os.getpid(), "cwd": "/tmp/project"}
        with (
            mock.patch("ocdeck.direct_hooks._identity", return_value=process),
            mock.patch("ocdeck.direct_hooks.capture_window", return_value={}),
        ):
            hooks.event(
                {
                    **base,
                    "event": {
                        "event": "SessionStart",
                        "action": "start",
                        "session": "s",
                        "request": "",
                        "question": False,
                        "failed": False,
                    },
                }
            )
            hooks.event(
                {
                    **base,
                    "event": {
                        "event": "PreToolUse",
                        "action": "tool",
                        "session": "s",
                        "request": "req-1",
                        "question": True,
                        "failed": False,
                    },
                }
            )
            self.assertEqual(registry.view()[0]["state"], "input")
            hooks.event(
                {
                    **base,
                    "event": {
                        "event": "SessionEnd",
                        "action": "end",
                        "session": "s",
                        "request": "",
                        "question": False,
                        "failed": False,
                    },
                }
            )
        self.assertIsNone(registry.view()[0]["id"])


if __name__ == "__main__":
    unittest.main()
