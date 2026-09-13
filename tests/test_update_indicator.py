import queue
import threading
import unittest
from unittest.mock import patch

from ocdeck.device import DeviceLoop
from ocdeck.jelly import DeckGeometry, Jelly
from ocdeck.model import Registry


class UpdateIndicatorTests(unittest.TestCase):
    def make_loop(self, size=80):
        loop = DeviceLoop(Registry(lambda _: True), queue.Queue(), threading.Event(), {}, mock=True)
        loop._start_jelly()
        loop.jelly = Jelly(DeckGeometry(width=size, height=size), seed=7)
        loop.jelly.settle(1, 0)
        loop._jelly_update_info = {"version": "99.0.0"}
        return loop

    def test_ambient_reactions_do_not_add_extra_hops(self):
        loop = self.make_loop()
        views = loop.registry.view()
        views[0] = {**views[0], "id": "waiting-agent", "state": "input"}
        with patch.object(loop.jelly, "hop", wraps=loop.jelly.hop) as hop:
            for step in range(351):
                loop._jelly_frames(step / 10, views)
            self.assertEqual(hop.call_count, 1)
            self.assertEqual(hop.call_args.args[1], 30)
        self.assertTrue(loop.jelly.update_available)
        loop._jelly_update_info = None
        loop._jelly_frames(36, views)
        self.assertFalse(loop.jelly.update_available)

    def test_badges_and_footer_fit_native_sizes_and_body_animates(self):
        for size in (72, 80, 96):
            loop = self.make_loop(size)
            views = loop.registry.view()
            first = loop._jelly_frames(0, views)[1]
            second = loop._jelly_frames(1, views)[1]
            self.assertEqual(first.size, (size, size))
            self.assertNotEqual(
                first.crop((0, 20, size, size - 20)).tobytes(), second.crop((0, 20, size, size - 20)).tobytes()
            )
            pixels = list(first.crop((0, 0, size, 20)).getdata())
            self.assertTrue(any(r > 200 and g < 100 for r, g, b, a in pixels))
            self.assertTrue(any(g > 180 and r < 100 for r, g, b, a in pixels))
            for top in (size - 20, size - 10):
                self.assertTrue(
                    any(
                        r > 180 and g > 180 and b > 180 for r, g, b, a in first.crop((0, top, size, top + 10)).getdata()
                    )
                )
            self.assertEqual(loop.overlay_actions[1], {"_action": "update"})

    def test_claimed_agent_key_never_receives_update_overlay(self):
        loop = self.make_loop()
        views = loop.registry.view()
        loop._jelly_frames(0, views)
        views[1] = {**views[1], "id": "new-agent", "state": "running"}
        frames = loop._jelly_frames(0.1, views)
        self.assertNotIn(1, frames)
        self.assertNotIn(1, loop.overlay_actions)

    def test_installing_footer_changes_without_changing_action(self):
        loop = self.make_loop()
        views = loop.registry.view()
        first = loop._jelly_frames(0, views)[1]
        loop._jelly_update_installing = True
        second = loop._jelly_frames(0, views)[1]
        self.assertNotEqual(first.crop((0, 60, 80, 80)).tobytes(), second.crop((0, 60, 80, 80)).tobytes())
        self.assertEqual(loop.overlay_actions[1], {"_action": "update"})
