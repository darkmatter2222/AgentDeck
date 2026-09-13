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
