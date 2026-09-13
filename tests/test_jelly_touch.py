import unittest
from ocdeck.jelly import Jelly, DeckGeometry
from ocdeck.jelly_smooth import TRICKS, FOODS
from ocdeck.jelly_words import Thoughts, text_bitmap
import random


class TouchTests(unittest.TestCase):
    def test_occupied_and_inflight_taps_do_not_feed_or_move(self):
        j = Jelly(DeckGeometry(), 1)
        j.settle(1, 0)
        before = dict(j.mind.needs)
        self.assertFalse(j.interact(1, 1, {2}))
        self.assertFalse(j.interact(2, 1, {1, 2}))
        j.hop(2, 1, {1, 2})
        self.assertFalse(j.interact(1, 2, {1, 2}))
        self.assertEqual(before, j.mind.needs)

    def test_hungry_touch_feeds_and_debounces(self):
        j = Jelly(DeckGeometry(), 1)
        j.settle(1, 0)
        j.mind.needs["nourishment"] = 20
        j.update(1, {1}, events=({"kind": "touch", "slot": 1},))
        self.assertIn(j.trick, FOODS)
        self.assertGreater(j.mind.needs["nourishment"], 20)
        before = dict(j.mind.needs)
        self.assertFalse(j.interact(1, 1.1, {1}))
        self.assertEqual(before, j.mind.needs)

    def test_all_tricks_render_and_expire(self):
        for trick in TRICKS:
            j = Jelly(DeckGeometry(), 1)
            j.settle(1, 0)
            j.play(trick, 0)
            frames = []
            for t in (0, 0.3, 1, 2):
                j.update(t, {1})
                frames.append(j.crops({1})[1].tobytes())
            self.assertGreater(len(set(frames)), 2, trick)
            j.update(3.3, {1})
            self.assertFalse(j.trick)

    def test_marquee_has_time_to_reach_midpoint_and_hold(self):
        t = Thoughts(random.Random(1))
        t.next_at = 0
        t.say("quiet", 0, 72, 1)
        pixels = text_bitmap(t.text, 1).width
        if pixels > 64:
            arrival = 1.5 + (pixels - 36) / 24
            self.assertGreaterEqual(t.until - arrival, 1.9)
            self.assertEqual(t.render(72, 1, arrival + 0.1).tobytes(), t.render(72, 1, t.until - 0.1).tobytes())

    def test_device_routes_empty_key_touches_and_keeps_agent_focus(self):
        import queue
        import threading
        from ocdeck.device import DeviceLoop

        loop = DeviceLoop.__new__(DeviceLoop)
        loop.presented = [{"state": "off", "id": None}, {"state": "running", "id": "agent"}]
        loop.presented_lock = threading.Lock()
        loop.jelly_events = queue.Queue(maxsize=32)
        loop.presses = queue.Queue()
        loop.press(0, True)
        self.assertEqual(loop.jelly_events.get_nowait(), {"kind": "touch", "slot": 0})
        self.assertTrue(loop.presses.empty())
        loop.press(1, True)
        self.assertEqual(loop.presses.get_nowait()["id"], "agent")
        loop.press(0, False)
        self.assertTrue(loop.jelly_events.empty())

    def test_pixel_art_has_crisp_alpha_and_broad_original_base(self):
        from ocdeck.jelly_smooth import render

        im = render((24, 19, 0), 80, 0.5, "neutral", "center", "", False, "content", "content", 1)
        self.assertEqual(set(im.getchannel("A").tobytes()), {0, 255})
        # The original blob has a broad floor, unlike the rejected oval silhouette.
        floor = [x for x in range(80) if im.getpixel((x, 66))[3]]
        self.assertGreater(max(floor) - min(floor), 32)
        self.assertLessEqual(im.getbbox()[2], 64)  # No permanent side ears/arms.

    def test_wave_is_a_small_attached_lobe(self):
        from ocdeck.jelly_smooth import render

        args = ((24, 19, 0), 80, 0.5, "neutral", "center")
        idle = render(*args, "", False, "content", "content", 1)
        wave = render(*args, "wave", False, "content", "content", 1)
        self.assertGreater(wave.getbbox()[2], idle.getbbox()[2])
        self.assertLessEqual(wave.getbbox()[2] - idle.getbbox()[2], 7)
