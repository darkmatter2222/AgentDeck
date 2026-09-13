import os
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageFont

from ocdeck.jelly_update import CHECK_INTERVAL, install_device_patch
from ocdeck.jelly_words import Thoughts, text_bitmap
from ocdeck.updates import check, install, schedule_restart


class UpdateTests(unittest.TestCase):
    def test_thought_text_uses_clean_final_resolution_ui_font(self):
        mask = text_bitmap("IDLE", 2)
        font = ImageFont.load_default(size=9)
        box = font.getbbox("IDLE")
        self.assertEqual(mask.mode, "L")
        self.assertEqual(mask.width, box[2] - box[0])
        self.assertLess(mask.height, 18)

        thoughts = Thoughts(random.Random(7), "chatty")
        thoughts.next_at = 0
        self.assertTrue(thoughts.say("quiet", 0))
        image = thoughts.render(80, 2, 0)
        self.assertEqual(image.size, (80, 18))

    def test_pypi_check_finds_newer_stable_version(self):
        with tempfile.TemporaryDirectory() as td:
            info = check(
                Path(td),
                {"check_updates": True},
                fetch=lambda: {"info": {"version": "99.1.2"}},
            )
            self.assertEqual(info["version"], "99.1.2")
            self.assertEqual(info["source"], "pypi")
            self.assertEqual(info["package"], "agentstreamdeck==99.1.2")

    def test_pypi_check_ignores_prerelease(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(
                check(
                    Path(td),
                    {"check_updates": True},
                    fetch=lambda: {"info": {"version": "99.1.2rc1"}},
                )
            )

    def test_install_pins_exact_validated_version(self):
        calls = []

        class Result:
            returncode = 0
            stdout = "ok"
            stderr = ""

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return Result()

        result = install("4.5.6", runner=runner)
        self.assertTrue(result["ok"])
        self.assertIn("agentstreamdeck==4.5.6", calls[0][0])
        self.assertIn("--no-input", calls[0][0])
        self.assertEqual(calls[0][1]["timeout"], 300)

    def test_restart_worker_drops_source_pythonpath(self):
        calls = []

        def popen(command, **kwargs):
            calls.append((command, kwargs))
            return object()

        with patch.dict(os.environ, {"PYTHONPATH": "C:/old/source"}, clear=False):
            result = schedule_restart(Path("."), parent_pid=123, popen=popen)
        self.assertTrue(result["ok"])
        self.assertNotIn("PYTHONPATH", calls[0][1]["env"])
        self.assertEqual(calls[0][0][0], os.sys.executable)

    def test_update_mode_marks_jelly_and_intercepts_its_button(self):
        class Geometry:
            def bounds(self, key):
                return (key * 88, 0, key * 88 + 80, 80)

            def adjacent(self, key):
                return (1,) if key == 0 else (0,)

        class ThoughtsStub:
            def __init__(self):
                self.cleared = 0

            def clear(self):
                self.cleared += 1

        class JellyStub:
            def __init__(self):
                self.geometry = Geometry()
                self.x = 40
                self.current = 0
                self.state = "idle"
                self.rng = random.Random(7)
                self.thoughts = ThoughtsStub()
                self.hops = []

            def hop(self, destination, now, available):
                self.hops.append(destination)
                self.state = "hop"
                return True

            def start_action(self, action, now):
                return True

        class Loop:
            def __init__(self):
                import threading

                self.stop = threading.Event()
                self.config = {"check_updates": False}
                self.status = {}
                self.jelly_root = None
                self.original_presses = []
                self.jelly = None

            def _start_jelly(self):
                self.jelly = JellyStub()

            def _jelly_frames(self, now, views):
                return {0: Image.new("RGBA", (80, 80), (0, 0, 0, 255))}

            def press(self, key, state):
                self.original_presses.append((key, state))

        install_device_patch(Loop)
        loop = Loop()
        loop._start_jelly()
        loop._jelly_update_info = {"version": "9.9.9"}
        views = [{"id": None, "state": "off"} for _ in range(6)]
        frames = loop._jelly_frames(10, views)
        self.assertTrue(loop.jelly.thoughts.cleared)
        self.assertTrue(loop.jelly.hops)
        red_pixels = [pixel for pixel in frames[0].getdata() if pixel[0] > 180 and pixel[1] < 100]
        self.assertTrue(red_pixels)

        called = []
        loop._start_jelly_update = lambda: called.append(True)
        loop.press(0, True)
        self.assertEqual(called, [True])
        self.assertEqual(loop.original_presses, [])

    def test_update_check_interval_is_five_minutes(self):
        self.assertEqual(CHECK_INTERVAL, 300)


if __name__ == "__main__":
    unittest.main()
