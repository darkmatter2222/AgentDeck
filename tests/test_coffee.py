"""Behavioral coverage of timed interludes and the physical-button routing path."""

import queue
import random
import threading
import unittest
from unittest.mock import patch

from ocdeck.broker import Broker
from ocdeck.coffee import CoffeeBreak, SUPPORT_URL, coffee_frame
from ocdeck.device import DeviceLoop
from ocdeck.jelly import DeckGeometry, Jelly, settings
from ocdeck.model import Registry


class CoffeeTests(unittest.TestCase):
    def setUp(self):
        self.jelly = Jelly(DeckGeometry(), seed=2, options={"thoughts": "off", "needs": False})
        self.jelly.settle(0, 0)
        self.coffee = CoffeeBreak(0, random.Random(1))

    def test_random_initial_delay_and_reschedule_are_one_to_three_hours(self):
        intervals = set()
        for i in range(50):
            self.coffee.finish(i * 20000)
            delay = self.coffee.next_at - i * 20000
            self.assertTrue(3600 <= delay <= 10800)
            intervals.add(delay)
        self.assertGreater(len(intervals), 40)

    def test_waits_for_two_free_keys_and_supports_nonadjacent_pair(self):
        due = self.coffee.next_at
        self.coffee.update(due - 0.01, {0, 5}, self.jelly)
        self.assertIsNone(self.coffee.key)
        for free in (set(), {0}):
            self.coffee.update(due, free, self.jelly)
            self.assertIsNone(self.coffee.key)
        self.coffee.update(due + 10, {0, 5}, self.jelly)
        self.assertEqual((self.coffee.jelly_key, self.coffee.key), (0, 5))
        self.assertEqual(self.coffee.until, due + 70)

    def test_exact_sixty_second_expiry(self):
        due = self.coffee.next_at
        self.coffee.update(due, {0, 1}, self.jelly)
        self.coffee.update(due + 59.999, {0, 1}, self.jelly)
        self.assertEqual(self.coffee.key, 1)
        self.coffee.update(due + 60, {0, 1}, self.jelly)
        self.assertIsNone(self.coffee.key)
        self.assertGreaterEqual(self.coffee.next_at, due + 60 + 3600)

    def test_either_occupied_key_cancels_without_stealing_another(self):
        for occupied in (0, 1):
            c = CoffeeBreak(0, random.Random(1))
            c.update(c.next_at, {0, 1}, self.jelly)
            c.update(c.next_at + 1, {0, 1, 2} - {occupied}, self.jelly)
            self.assertIsNone(c.key)

    def test_disabled_or_update_pending_defers_interlude(self):
        self.coffee.update(self.coffee.next_at, {0, 1}, self.jelly, blocked=True)
        self.assertIsNone(self.coffee.key)
        for option in ("coffee", "coffee_rainbow"):
            self.assertFalse(settings({"jelly": {option: False}})[option])
            with self.assertRaises(ValueError):
                settings({"jelly": {option: "yes"}})

    def test_steam_animates_at_native_sizes(self):
        for size in (72, 80, 96):
            a, b = (coffee_frame(size, size, phase) for phase in (0, 6))
            self.assertEqual(a.size, (size, size))
            self.assertNotEqual(a.tobytes(), b.tobytes())


class ButtonRoutingTests(unittest.TestCase):
    def setUp(self):
        self.registry = Registry(lambda _: True)
        self.presses = queue.Queue()
        self.loop = DeviceLoop(
            self.registry,
            self.presses,
            threading.Event(),
            {"jelly": {"thoughts": "off", "needs": False}, "world": {"enabled": False}},
            mock=True,
        )
        self.loop._start_jelly()
        self.loop.jelly.settle(0, 0)
        self.loop.coffee.next_at = 100

    def render(self, now, views=None):
        views = views or self.registry.view()
        images = self.loop._jelly_frames(now, views)
        for key, view in enumerate(views):
            self.loop.presented[key] = self.loop._presented_view(key, view)
        return images

    def test_jelly_press_reacts_even_with_thoughts_off_and_release_does_nothing(self):
        self.render(1)
        self.loop.press(0, False)
        self.assertTrue(self.loop.jelly_events.empty())
        self.loop.press(0, True)
        self.render(1.1)
        self.assertGreater(self.loop.jelly.touch_until, 1.1)
        self.assertIn(self.loop.jelly.touch_text, ("Ouch!", "Hehe!", "Boop!", "Hey!", "Tickles!"))
        self.assertTrue(self.presses.empty())

    def tap_jelly(self, now):
        key = next(k for k, action in self.loop.overlay_actions.items() if action["_action"] == "tap")
        with patch("ocdeck.device.time.monotonic", return_value=now):
            self.loop.press(key, True)
        self.render(now)

    def test_fifth_tap_spawns_then_either_button_opens_once(self):
        for target in ("jelly_key", "key"):
            with self.subTest(target=target):
                self.setUp()
                self.render(1)
                for now in (2, 3, 4, 5):
                    self.tap_jelly(now)
                    self.assertIsNone(self.loop.coffee.key)
                self.tap_jelly(6)
                self.assertIsNotNone(self.loop.coffee.key)
                self.assertEqual(self.loop.coffee.until, 66)
                self.assertTrue(self.presses.empty())
                key = getattr(self.loop.coffee, target)
                self.loop.press(key, True)
                self.loop.press(key, True)
                self.render(7)
                self.assertIsNone(self.loop.coffee.key)
                self.assertEqual(self.presses.get_nowait(), {"_action": "open_coffee"})
                self.assertTrue(self.presses.empty())
                self.assertGreaterEqual(self.loop.coffee.next_at, 3607)

    def test_taps_use_rolling_window_and_reset_after_invitation(self):
        self.loop.coffee.next_at = 10000
        self.render(1)
        for now in (2, 10, 20, 30, 63):
            self.tap_jelly(now)
        self.assertIsNone(self.loop.coffee.key)
        self.tap_jelly(64)
        self.assertIsNotNone(self.loop.coffee.key)
        self.render(124)
        self.tap_jelly(125)
        self.assertIsNone(self.loop.coffee.key)

    def test_five_taps_require_two_free_keys_and_respect_disable(self):
        for blocked in (False, True):
            with self.subTest(disabled=blocked):
                self.setUp()
                self.loop.jelly.options["coffee"] = not blocked
                views = self.registry.view()
                if not blocked:
                    for i in range(1, len(views)):
                        views[i] = {**views[i], "id": str(i), "state": "running"}
                self.render(1, views)
                for now in range(2, 7):
                    self.loop.press(0, True)
                    self.render(now, views)
                self.assertIsNone(self.loop.coffee.key)
                self.assertTrue(self.presses.empty())

    def test_scheduled_coffee_jelly_press_opens_and_stale_pair_cannot(self):
        self.render(100)
        self.loop.press(self.loop.coffee.jelly_key, True)
        self.render(101)
        self.assertEqual(self.presses.get_nowait(), {"_action": "open_coffee"})
        self.assertIsNone(self.loop.coffee.key)
        for invalid in ("expired", "reassigned", "update"):
            self.setUp()
            self.render(100)
            self.loop.press(self.loop.coffee.jelly_key, True)
            views = self.registry.view()
            if invalid == "reassigned":
                key = self.loop.coffee.key
                views[key] = {**views[key], "id": "agent", "state": "running"}
            if invalid == "update":
                self.loop._jelly_update_info = {"version": "99.0.0"}
            self.render(160 if invalid == "expired" else 101, views)
            self.assertTrue(self.presses.empty())
            self.assertIsNone(self.loop.coffee.key)

    def test_coffee_press_is_one_browser_request_and_dismisses(self):
        self.render(100)
        key = self.loop.coffee.key
        self.loop.press(key, True)
        self.loop.press(key, True)
        self.render(101)
        self.assertIsNone(self.loop.coffee.key)
        self.assertEqual(self.presses.get_nowait(), {"_action": "open_coffee"})
        self.assertTrue(self.presses.empty())
        self.assertLess(self.loop.jelly.deadline, 110)

    def test_expired_or_reassigned_coffee_cannot_open_browser(self):
        for expired in (True, False):
            self.loop.coffee.next_at = 100
            self.render(100)
            key = self.loop.coffee.key
            self.loop.press(key, True)
            views = self.registry.view()
            if not expired:
                views[key] = {**views[key], "id": "new-agent", "state": "running", "generation": 99}
            self.render(160 if expired else 101, views)
            self.assertTrue(self.presses.empty())
            self.assertIsNone(self.loop.coffee.key)

    def test_agent_action_wins_over_stale_update_or_coffee_metadata(self):
        self.loop._jelly_update_info = {"version": "99.0.0"}
        self.loop._jelly_update_keys = {0}
        self.loop.presented[0] = {"id": "agent", "slot": 0, "generation": 5, "_action": "coffee"}
        self.loop.press(0, True)
        self.assertEqual(self.presses.get_nowait()["id"], "agent")
        self.assertTrue(self.loop.jelly_events.empty())

    def test_update_overlay_routes_through_worker_not_hid_callback(self):
        self.loop._jelly_update_info = {"version": "99.0.0"}
        self.render(1)
        key = next(iter(self.loop._jelly_update_keys))
        self.loop.press(key, True)
        self.assertEqual(self.presses.get_nowait()["_action"], "update")
        self.assertFalse(self.loop._jelly_update_installing)

    def test_rainbow_changes_body_and_frames_never_cover_agents(self):
        views = self.registry.view()
        for i in (1, 2, 3, 4):
            views[i] = {**views[i], "id": str(i), "state": "running"}
        first = self.render(100, views)
        second = self.render(101, views)
        self.assertEqual(set(first), {0, 5})
        self.assertEqual(set(second), {0, 5})
        self.assertNotEqual(first[0].tobytes(), second[0].tobytes())

    def test_browser_uses_fixed_support_url_and_synthetic_focus_cannot_open_it(self):
        # No HTTP server or desktop required to exercise the broker worker dispatch.
        broker = object.__new__(Broker)
        broker.device = self.loop
        broker.registry = self.registry
        with patch("webbrowser.open", return_value=True) as browser:
            self.assertTrue(broker.handle_press({"_action": "open_coffee"})["ok"])
            browser.assert_called_once_with(SUPPORT_URL, new=2)
            broker.handle_press({"_action": "open_coffee"}, synthetic=True)
            self.assertEqual(browser.call_count, 1)

    def test_stale_tap_cannot_poke_jelly_after_slot_reuse(self):
        self.render(1)
        self.loop.press(0, True)
        views = self.registry.view()
        views[0]["generation"] += 1
        self.render(1.1, views)
        self.assertEqual(self.loop.jelly.touch_until, 0)
