import queue
import threading
import unittest
from unittest.mock import patch

from PIL import Image
from ocdeck.appearance_io import export_settings, import_settings
from ocdeck.device import DeviceLoop
from ocdeck.jelly import DeckGeometry, Jelly, free_keys, settings
from ocdeck.jelly_art import ANCHOR, GRID, POSES, logical_sprite, sprite
from ocdeck.model import Registry
from ocdeck.settings import validate_config


class JellyTests(unittest.TestCase):
    def test_mini_corner_edge_adjacency(self):
        g = DeckGeometry()
        self.assertEqual([set(g.adjacent(k)) for k in range(6)], [{1, 3}, {0, 2, 4}, {1, 5}, {0, 4}, {1, 3, 5}, {2, 4}])

    def test_other_grids_do_not_wrap_rows(self):
        for rows, cols in ((1, 1), (3, 5), (4, 8), (2, 4)):
            g = DeckGeometry(rows, cols, 72, 72, 12)
            for key in range(g.count):
                for neighbor in g.adjacent(key):
                    self.assertIn(key, g.adjacent(neighbor))
                    r, c = divmod(key, cols)
                    nr, nc = divmod(neighbor, cols)
                    self.assertEqual(abs(r - nr) + abs(c - nc), 1)
            self.assertEqual(g.bounds(g.count - 1)[2:], g.size)

    def test_free_filter_respects_all_functional_states(self):
        views = [
            {"state": state, "id": None} for state in ("running", "idle", "input", "ready", "unknown", "error", "off")
        ]
        views.append({"state": "off", "id": "reserved"})
        self.assertEqual(free_keys(views), {6})

    def test_zero_keys_hide_then_delayed_respawn(self):
        j = Jelly(DeckGeometry(), 1)
        for i in range(100):
            j.update(i, set())
            self.assertEqual(j.crops(set()), {})
            self.assertIsNone(j.deadline)
        j.update(100, {2})
        self.assertEqual(j.state, "hidden")
        j.update(102, {2})
        self.assertEqual(j.current, 2)

    def test_one_free_key_never_travels(self):
        j = Jelly(DeckGeometry(), 7)
        for i in range(6000):
            j.update(i / 30, {4})
            self.assertIn(j.current, (None, 4))
            self.assertIsNone(j.destination)

    def test_valid_destinations_only(self):
        j = Jelly(DeckGeometry(), 7)
        j.settle(0, 0)
        for dest, available in ((5, {0, 5}), (2, {0, 2}), (1, {0}), (3, {3})):
            self.assertFalse(j.hop(dest, 0, available))
        self.assertTrue(j.hop(1, 0, {0, 1}))

    def test_seeded_behavior_is_deterministic_and_adjacent(self):
        a, b = Jelly(DeckGeometry(), 42), Jelly(DeckGeometry(), 42)
        states = set()
        for i in range(18000):
            now = i / 30
            free = {1, 2, 4, 5}
            a.update(now, free)
            b.update(now, free)
            self.assertEqual(
                (a.state, a.current, a.destination, a.x, a.y, a.pose),
                (b.state, b.current, b.destination, b.x, b.y, b.pose),
            )
            if a.destination is not None:
                self.assertIn(a.destination, a.geometry.adjacent(a.current))
                self.assertIn(a.destination, free)
            states.add(a.state)
        self.assertTrue({"hop", "blink", "wave", "rest", "point_left", "point_right"} <= states)

    def test_immediate_eviction_during_all_actions(self):
        for state in ("idle", "blink", "wave", "rest", "point_left"):
            j = Jelly(DeckGeometry(), 7)
            j.settle(1, 0)
            j.state = state
            j.update(0.1, {2, 4})
            self.assertEqual(j.state, "hidden")
            self.assertEqual(j.crops({2, 4}), {})

    def test_midflight_source_or_destination_invalidation(self):
        for available in ({1}, {2}, set()):
            j = Jelly(DeckGeometry(), 7)
            j.settle(1, 0)
            j.hop(2, 0, {1, 2})
            j.update(0.95, {1, 2})
            self.assertEqual(set(j.crops({1, 2})), {1, 2})
            self.assertEqual(j.crops(available), {})
            j.update(0.96, available)
            self.assertEqual(j.state, "hidden")

    def test_all_direction_hops_are_continuous_and_land(self):
        for source, dest in ((1, 2), (2, 1), (1, 4), (4, 1)):
            j = Jelly(DeckGeometry(), 7)
            free = {source, dest}
            j.settle(source, 0)
            j.hop(dest, 0, free)
            points = []
            intersected = False
            for i in range(55):
                j.update(i / 30, free)
                points.append((j.x, j.y))
                intersected |= len(j.crops(free)) == 2
            self.assertTrue(intersected)
            self.assertEqual(j.current, dest)
            self.assertEqual(points[-1], j.geometry.anchor(dest))
            for a, b in zip(points, points[1:]):
                self.assertLess(abs(a[0] - b[0]) + abs(a[1] - b[1]), 12)

    def test_world_clipping_equals_full_canvas_reference(self):
        g = DeckGeometry()
        j = Jelly(g, 7)
        j.settle(1, 0)
        j.hop(2, 0, {1, 2})
        j.update(0.95, {1, 2})
        im = sprite(j.pose, j.face, j.gaze, j.gesture, j.gesture_step, g.scale, j.mirror)
        world = Image.new("RGBA", g.size)
        world.paste(im, (round(j.x - ANCHOR[0] * g.scale), round(j.y - ANCHOR[1] * g.scale)))
        crops = j.crops({1, 2})
        for key in (1, 2):
            self.assertEqual(crops[key].tobytes(), world.crop(g.bounds(key)).tobytes())
        visible = sum(sum(px != 0 for px in crop.getchannel("A").tobytes()) for crop in crops.values())
        total = sum(px != 0 for px in world.getchannel("A").tobytes())
        self.assertLess(visible, total)  # Missing pixels are behind the bezel.

    def test_logical_grid_integer_scaling_anchor_and_cache(self):
        for pose in POSES:
            im = logical_sprite(pose)
            self.assertEqual(im.size, (40, 40))
            self.assertEqual(im.getbbox()[3], ANCHOR[1])
            large = sprite(pose, scale=2)
            self.assertEqual(large.tobytes(), im.resize((80, 80), Image.Resampling.NEAREST).tobytes())
            self.assertIs(large, sprite(pose, scale=2))
        idle, blink = logical_sprite(), logical_sprite(face="closed")
        self.assertEqual(idle.getchannel("A").tobytes(), blink.getchannel("A").tobytes())

    def test_pose_holds_while_position_advances(self):
        for variant in ("classic", "fluid"):
            j = Jelly(DeckGeometry(), 7, variant)
            j.settle(1, 0)
            j.hop(2, 0, {1, 2})
            j.update(0.72, {1, 2})
            pose, x = j.pose, j.x
            j.update(0.74, {1, 2})
            self.assertEqual(j.pose, pose)
            self.assertGreater(j.x, x)

    def test_close_is_final_and_starts_no_threads(self):
        before = set(threading.enumerate())
        j = Jelly(DeckGeometry(), 7)
        j.settle(1, 0)
        j.close()
        j.update(20, {1, 2})
        self.assertFalse(j.hop(2, 21, {1, 2}))
        self.assertEqual(j.crops({1, 2}), {})
        self.assertEqual(set(threading.enumerate()), before)

    def test_config_defaults_validation_and_appearance_preservation(self):
        self.assertFalse(settings({})["enabled"])
        for value in (
            None,
            [],
            {"enabled": 1},
            {"fps": 60},
            {"virtual_gap": True},
            {"virtual_gap": -1},
            {"virtual_gap": 41},
            {"behavior_seed": False},
            {"hop_style": "bad"},
        ):
            with self.assertRaises(ValueError):
                validate_config({"jelly": value})
        config = {"jelly": {"enabled": True, "behavior_seed": 7}, "fps": 30}
        validate_config(config)
        exported = export_settings(config)
        self.assertNotIn("jelly", exported)
        self.assertEqual(import_settings(config, exported)["jelly"], config["jelly"])

    def test_disabled_animation_and_geometry(self):
        for count in (6, 15, 32):
            loop = DeviceLoop(
                Registry(lambda _: True, slots=count),
                queue.Queue(),
                threading.Event(),
                {"jelly": {"enabled": True}},
                mock=True,
            )
            loop._start_jelly()
            self.assertEqual(loop.jelly.geometry.count, count)
            loop.config["animations"] = False
            loop._start_jelly()
            self.assertIsNone(loop.jelly)

    def test_exception_disables_jelly_without_harming_agents(self):
        loop = DeviceLoop(
            Registry(lambda _: True), queue.Queue(), threading.Event(), {"jelly": {"enabled": True}}, mock=True
        )
        loop._start_jelly()
        with patch.object(Jelly, "update", side_effect=RuntimeError("test cosmetic failure")):
            with self.assertLogs("ocdeck.device", level="ERROR"):
                self.assertEqual(loop._jelly_frames(0, loop.registry.view()), {})
        self.assertIsNone(loop.jelly)
        self.assertEqual(loop.status["jelly"], "failed")
        self.assertEqual(loop._jelly_frames(1, loop.registry.view()), {})

    def test_device_loop_changed_keys_priority_eviction_and_shutdown(self):
        # Execute the actual sole writer with a fake clock/transport, capturing RGB.
        clock = [0.0]
        views = [{"id": None, "state": "off", "label": "", "pending": None} for _ in range(6)]
        writes = []

        class Stop:
            ticks = 0

            def is_set(self):
                return self.ticks >= 70

            def wait(self, seconds):
                self.ticks += 1
                clock[0] += max(seconds, 1 / 30)
                if self.ticks == 60:
                    views[1] = {**views[1], "id": "new-agent", "state": "input", "label": "Agent"}

        stop = Stop()

        class Deck:
            def open(self):
                pass

            def close(self):
                pass

            def set_brightness(self, value):
                pass

            def set_key_callback(self, value):
                pass

            def key_count(self):
                return 6

            def key_layout(self):
                return (2, 3)

            def key_image_format(self):
                return {"size": (80, 80)}

            def is_open(self):
                return True

            def connected(self):
                return True

            def set_key_image(self, key, im):
                writes.append((stop.ticks, key, im.copy()))

        deck = Deck()
        registry = Registry(lambda _: True)
        loop = DeviceLoop(registry, queue.Queue(), stop, {"fps": 30, "ready": False, "jelly": {"enabled": True}})
        original = loop._start_jelly

        def start():
            original()
            loop.jelly.settle(1, 0)
            loop.jelly.deadline = 100

        with (
            patch("ocdeck.device.enumerate_devices", return_value=[{"product_id": 1}]),
            patch("ocdeck.device.device_types", return_value={1: lambda _: deck}),
            patch("ocdeck.device.elgato_running", return_value=False),
            patch("ocdeck.device.time.monotonic", side_effect=lambda: clock[0]),
            patch("StreamDeck.ImageHelpers.PILHelper.to_native_key_format", side_effect=lambda _, im: im),
            patch.object(registry, "view", side_effect=lambda: [dict(v) for v in views]),
            patch.object(loop, "_start_jelly", side_effect=start),
        ):
            loop.run()
        self.assertIsNone(loop.jelly)
        # Other free keys get initial blanking only, never animation refreshes.
        self.assertFalse(any(1 <= tick < 60 and key != 1 for tick, key, _ in writes))
        replacement = next(im for tick, key, im in writes if tick == 60 and key == 1)
        from ocdeck.art import frame
        from ocdeck.appearance import animation_phase, appearance

        style = appearance(loop.config, 1)
        expected = frame("input", "Agent", 1, animation_phase(2.0, style), 80, style, "opencode", "", None)
        self.assertEqual(replacement.tobytes(), expected.tobytes())
        self.assertNotEqual(replacement.tobytes(), Image.new("RGB", (80, 80)).tobytes())
        self.assertGreater(sum(replacement.getchannel("R").tobytes()), sum(replacement.getchannel("G").tobytes()))
        self.assertIsNone(loop.deck)
        self.assertEqual(loop.presented, [None] * 6)


if __name__ == "__main__":
    unittest.main()
