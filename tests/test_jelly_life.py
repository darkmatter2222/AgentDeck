"""Behavioral acceptance of Jelly's expanded life; no hardware or wall-clock sleeps."""

import json
from pathlib import Path
import queue
import random
import tempfile
import threading
import unittest
from unittest.mock import patch
from PIL import Image
from ocdeck.jelly import Jelly, DeckGeometry, free_keys, settings
from ocdeck.jelly_art import POSES, ANCHOR, colored_sprite, logical_sprite
from ocdeck.jelly_catalog import ACTIONS, HOPS, MOODS
from ocdeck.jelly_mind import Mind, NEEDS
from ocdeck.jelly_words import Thoughts, vocabulary
from ocdeck.device import DeviceLoop
from ocdeck.model import Registry


def views(count=6, occupied=None):
    return [
        {"id": f"agent-{k}" if k in (occupied or {}) else None, "state": (occupied or {}).get(k, "off")}
        for k in range(count)
    ]


class LifeTests(unittest.TestCase):
    def test_floor_anchor_all_poses_and_native_sizes(self):
        for size in (72, 80, 96):
            g = DeckGeometry(2, 3, size, size)
            j = Jelly(g, 7, options={"mood_colors": False, "thoughts": "off"})
            j.settle(4, 0)
            for pose in POSES:
                j.pose = pose
                bounds = j.crops({4})[4].getbbox()
                self.assertEqual(bounds[3], size - 3, (size, pose, bounds))
                self.assertEqual(j.y, g.bounds(4)[3] - 3)

    def test_twenty_distinct_new_pose_shapes(self):
        self.assertEqual(len(POSES), 33)
        new = list(POSES)[13:]
        shapes = {logical_sprite(p).tobytes() for p in new}
        self.assertEqual(len(shapes), 20)

    def test_all_new_actions_render_and_move_only_inside_current_key(self):
        self.assertEqual(len(ACTIONS), 20)
        moving = set()
        signatures = set()
        for name in ACTIONS:
            j = Jelly(DeckGeometry(), 7, options={"thoughts": "off"})
            j.settle(1, 0)
            self.assertTrue(j.start_action(name, 0))
            states, positions = [], set()
            for i in range(91):
                t = j.action_duration * i / 90
                j.now = t
                j._local_pose(t)
                self.assertEqual(set(j.crops(set(range(6)))), {1})
                self.assertLessEqual(j.y, j.geometry.anchor(1)[1])
                states.append((j.pose, j.rotation, j.gesture))
                positions.add((j.x, j.y))
            signatures.add(tuple(states))
            if len(positions) > 1:
                moving.add(name)
        self.assertEqual(len(signatures), 20)
        self.assertTrue({"scoot", "crawl", "roll", "tiptoe", "pace", "retreat", "bounce", "somersault"} <= moving)

    def test_every_hop_style_finishes_and_uses_continuous_position(self):
        self.assertEqual(len(HOPS), 14)
        signatures = set()
        for name in HOPS:
            j = Jelly(DeckGeometry(), 7, name)
            j.settle(1, 0)
            j.hop(4 if name == "careful_drop" else 2, 0, {1, 2, 4})
            duration = j.PREPARE + j.FLIGHT + j.LANDING
            trace = []
            previous = (j.x, j.y)
            for i in range(int(duration * 30) + 2):
                j.update(i / 30, {1, 2, 4})
                self.assertLess(abs(j.x - previous[0]) + abs(j.y - previous[1]), 18, name)
                previous = (j.x, j.y)
                trace.append((round(j.x, 2), round(j.y, 2), j.pose))
            self.assertEqual(j.state, "idle")
            signatures.add(tuple(trace))
        self.assertEqual(len(signatures), 14)

    def test_local_offset_is_preserved_at_hop_launch(self):
        j = Jelly(DeckGeometry(), 7)
        j.settle(1, 0)
        j.x += 4
        before = (j.x, j.y)
        j.hop(2, 1, {1, 2})
        j.update(1, {1, 2})
        self.assertEqual((j.x, j.y), before)

    def test_all_moods_have_distinct_palettes_and_keep_alpha(self):
        samples = set()
        source = colored_sprite("idle", "neutral", "center", "", 0, 2, False, "content")
        for mood in MOODS:
            image = colored_sprite("idle", "neutral", "center", "", 0, 2, False, mood)
            self.assertEqual(image.getchannel("A").tobytes(), source.getchannel("A").tobytes())
            samples.add(image.tobytes())
        self.assertEqual(len(samples), len(MOODS))

    def test_palette_transition_is_quantized_and_off_preserves_original(self):
        j = Jelly(DeckGeometry(), 7, options={"mood_colors": False})
        j.settle(1, 0)
        before = j.crops({1})[1].tobytes()
        j.mind.set_mood("sleepy", 0)
        j.now = 10
        self.assertEqual(before, j.crops({1})[1].tobytes())
        j.options["mood_colors"] = True
        frames = set()
        for t in (0, 0.1, 0.3, 0.4, 0.6, 0.7, 0.9, 1):
            j.now = t
            frames.add(j.crops({1})[1].tobytes())
        self.assertEqual(len(frames), 4)

    def test_repeated_snapshots_do_not_feed_as_new_events(self):
        m = Mind(random.Random(7), settings({}))
        v = views(6, {0: "idle"})
        m.observe(0, v)
        fed = m.needs["nourishment"]
        for i in range(1, 101):
            m.observe(i / 30, v)
        self.assertLess(m.needs["nourishment"], fed)
        self.assertEqual(len(m.recent_events), 1)

    def test_burst_feeding_is_rate_limited_and_overwhelmed_is_quiet(self):
        m = Mind(random.Random(7), settings({}))
        v = views(32, {k: "running" for k in range(32)})
        m.observe(0, v)
        self.assertLessEqual(m.needs["nourishment"], 77)
        self.assertEqual(m.mood, "overwhelmed")
        self.assertLessEqual(len(m.recent_events), 64)

    def test_continuous_activity_feeds_and_tires(self):
        m = Mind(random.Random(7), settings({}))
        v = views(6, {0: "running", 1: "running"})
        for t in range(0, 2400, 2):
            m.observe(t, v)
        self.assertEqual(m.needs["nourishment"], 100)
        self.assertLess(m.needs["energy"], 35)
        self.assertEqual(m.mood, "overworked")
        self.assertTrue(all(0 <= n <= 100 for n in m.needs.values()))

    def test_idle_sleep_and_activity_wakes_without_neglect_penalty(self):
        m = Mind(random.Random(7), settings({}))
        for t in range(0, 350, 2):
            m.observe(t, views())
        self.assertEqual(m.mood, "asleep")
        m.observe(360, views(6, {0: "running"}))
        self.assertNotEqual(m.mood, "asleep")
        state = m.snapshot([])
        m.needs["energy"] = 1
        m.restore(state)
        self.assertGreaterEqual(m.needs["energy"], 85)
        self.assertEqual(m.needs["workload"], 0)

    def test_long_elapsed_gap_does_not_apply_hours_of_decay(self):
        m = Mind(random.Random(7), settings({}))
        m.observe(0, views())
        before = m.needs.copy()
        m.observe(100000, views())
        self.assertLess(abs(m.needs["nourishment"] - before["nourishment"]), 1)

    def test_oldest_pending_target_stays_stable(self):
        m = Mind(random.Random(7), settings({}))
        v = views(6, {4: "input"})
        m.observe(0, v)
        v[0] = {"id": "second", "state": "input"}
        m.observe(4, v)
        self.assertEqual(m.target, 4)
        v[4]["state"] = "running"
        m.observe(8, v)
        self.assertEqual(m.target, 0)

    def test_route_uses_only_free_cells_and_never_occupied_target(self):
        g = DeckGeometry(3, 5)
        free = {0, 5, 10, 11, 12, 7, 2, 3}
        route = g.route_beside(0, 4, free)
        self.assertTrue(route)
        previous = 0
        for k in route:
            self.assertIn(k, free)
            self.assertIn(k, g.adjacent(previous))
            previous = k
        self.assertIn(previous, g.adjacent(4))
        self.assertEqual(g.route_beside(0, 4, {0, 5, 10}), [])

    def test_point_direction_for_agents_above_below_left_right(self):
        j = Jelly(DeckGeometry(3, 5), 7)
        j.settle(7, 0)
        for target, gaze, gesture, mirror in (
            (2, "up", "up", False),
            (12, "down", "down", False),
            (6, "right", "point", True),
            (8, "right", "point", False),
        ):
            j._point(target)
            self.assertEqual((j.gaze, j.gesture, j.mirror), (gaze, gesture, mirror))

    def test_input_reaction_reaches_neighbor_using_free_route(self):
        j = Jelly(DeckGeometry(), 7, options={"thoughts": "off"})
        j.settle(3, 0)
        v = views(6, {2: "input"})
        visited = set()
        for i in range(600):
            j.update(i / 30, free_keys(v), v)
            visited.add(j.current)
            self.assertNotIn(2, j.crops(free_keys(v)))
        self.assertIn(j.current, (1, 5))
        self.assertNotIn(2, visited)

    def test_occupied_destination_cancels_thought_and_travel(self):
        j = Jelly(DeckGeometry(), 7)
        j.settle(1, 0)
        j.thoughts.next_at = 0
        j.thoughts.say("quiet", 0)
        j.hop(2, 1, {1, 2})
        self.assertFalse(j.thoughts.text)
        j.update(1.9, {1})
        self.assertEqual(j.state, "hidden")
        self.assertEqual(j.crops({1}), {})

    def test_idle_is_not_success_unknown_is_not_failure(self):
        m = Mind(random.Random(7), settings({}))
        v = views(6, {0: "running"})
        m.observe(0, v)
        v[0]["state"] = "idle"
        m.observe(5, v)
        self.assertEqual(m.consume_reaction()[1], "quiet")
        v[0]["state"] = "unknown"
        m.observe(10, v)
        self.assertEqual(m.consume_reaction()[1], "concern")

    def test_explicit_outcomes_are_deduplicated_and_correct(self):
        m = Mind(random.Random(7), settings({}))
        v = views(6, {0: "idle"})
        m.observe(0, v)
        v[0].update(outcome="success", outcomeId="first")
        m.observe(5, v)
        self.assertEqual(m.consume_reaction()[1], "success")
        m.observe(10, v)
        self.assertIsNone(m.consume_reaction())
        v[0].update(outcome="failure", outcomeId="second")
        m.observe(15, v)
        self.assertEqual(m.consume_reaction()[1], "failure")

    def test_outcome_extension_validates_and_reaches_registry_view(self):
        r = Registry(lambda _: True)
        r.upsert({"id": "a", "process": {"pid": 1}})
        base = {"status": "idle", "seq": 1, "producer": "test"}
        with self.assertRaises(ValueError):
            r.snapshot("a", {**base, "outcome": "success"})
        r.snapshot("a", {**base, "outcome": "success", "outcomeId": "result-1"})
        self.assertEqual(r.view()[0]["outcome"], "success")
        self.assertEqual(r.view()[0]["outcomeId"], "result-1")

    def test_arrival_departure_reconnection_have_separate_words(self):
        m = Mind(random.Random(7), settings({}))
        v = views(6, {0: "running"})
        m.observe(0, v)
        self.assertEqual(m.consume_reaction()[1], "greetings")
        m.observe(5, views())
        self.assertEqual(m.consume_reaction()[1], "departures")
        m.observe(10, views(6, {0: "unknown"}))
        m.observe(15, v)
        self.assertEqual(m.consume_reaction()[1], "reconnected")

    def test_authored_vocabulary_unique_bounded_and_packaged(self):
        groups = vocabulary()
        lines = [s for v in groups.values() for s in v]
        self.assertEqual(len(lines), 1040)
        self.assertEqual(len(set(lines)), 1040)
        self.assertTrue(all(s.isascii() and len(s) <= 52 for s in lines))
        self.assertTrue({"success", "failure", "resolved", "greetings", "departures", "reconnected"} <= set(groups))

    def test_thought_history_avoids_repeat_until_category_exhaustion(self):
        thoughts = Thoughts(random.Random(7), "chatty")
        selected = []
        for i in range(100):
            thoughts.say("quiet", i * 60)
            selected.append(thoughts.text)
        self.assertEqual(len(set(selected)), 100)
        self.assertLessEqual(len(thoughts.recent), 128)

    def test_thought_scrolls_once_and_stays_inside_key(self):
        thoughts = Thoughts(random.Random(7), "chatty")
        thoughts.next_at = 0
        thoughts.say("quiet", 0)
        a, b = thoughts.render(80, 2, 0), thoughts.render(80, 2, 3)
        self.assertEqual(a.size, (80, 18))
        self.assertNotEqual(a.tobytes(), b.tobytes())
        self.assertEqual(thoughts.render(80, 2, 99).tobytes(), thoughts.render(80, 2, 100).tobytes())
        self.assertFalse(thoughts.active(thoughts.until + 1))
        self.assertFalse(thoughts.say("input", 1, event=True))

    def test_thought_is_above_head_and_does_not_cover_neighbor(self):
        j = Jelly(DeckGeometry(), 7)
        j.settle(1, 0)
        without = j.crops({1, 2})[1]
        j.thoughts.next_at = 0
        j.thoughts.say("quiet", 0)
        with_text = j.crops({1, 2})
        self.assertEqual(set(with_text), {1})
        self.assertEqual(with_text[1].crop((0, 25, 80, 80)).tobytes(), without.crop((0, 25, 80, 80)).tobytes())
        j.hide()
        self.assertFalse(j.thoughts.text)

    def test_speech_off_sleep_and_stale_input(self):
        thoughts = Thoughts(random.Random(7), "off")
        self.assertFalse(thoughts.say("quiet", 100))
        j = Jelly(DeckGeometry(), 7)
        j.settle(1, 0)
        j.thoughts.next_at = 0
        j.thoughts.say("input", 0)
        j._talk(1, views())
        self.assertFalse(j.thoughts.text)
        j.thoughts.next_at = 0
        j.thoughts.say("quiet", 2)
        j.mind.set_mood("asleep", 2)
        j._talk(3, views())
        self.assertFalse(j.thoughts.text)

    def test_optional_state_is_bounded_private_and_resilient(self):
        m = Mind(random.Random(7), settings({}))
        v = views(6, {0: "input"})
        v[0]["label"] = "SECRET PROJECT"
        m.observe(0, v)
        saved = m.snapshot(["quiet:1"] * 500)
        raw = json.dumps(saved)
        self.assertNotIn("SECRET", raw)
        self.assertNotIn("agent-", raw)
        self.assertLessEqual(len(saved["recent"]), 128)
        self.assertEqual(set(saved["needs"]), set(NEEDS))
        for invalid in (None, [], {"schema_version": 1, "needs": {"energy": float("nan")}}):
            self.assertEqual(m.restore(invalid), [])
        self.assertEqual(m.restore(saved), ["quiet:1"] * 128)
        saved["recent"] = ["quiet:999", "quiet:-1", "unknown:0", "quiet:1"]
        self.assertEqual(m.restore(saved), ["quiet:1"])

    def test_device_persistence_and_focus_handoff(self):
        with tempfile.TemporaryDirectory() as root:
            loop = DeviceLoop(
                Registry(lambda _: True),
                queue.Queue(),
                threading.Event(),
                {"jelly": {"enabled": True, "persistent": True}},
                mock=True,
                root=Path(root),
            )
            loop._start_jelly()
            loop.jelly.mind.needs["energy"] = 10
            loop._save_jelly()
            state = json.loads((Path(root) / "jelly-state.json").read_text())
            self.assertEqual(state["needs"]["energy"], 10)
            loop._start_jelly()
            self.assertGreaterEqual(loop.jelly.mind.needs["energy"], 85)
            for i in range(100):
                loop.notify_jelly("focus", 1)
            self.assertEqual(loop.jelly_events.qsize(), 32)
            loop._jelly_frames(0, loop.registry.view())
            self.assertEqual(loop.jelly_events.qsize(), 0)
            with patch("ocdeck.common.atomic_json", side_effect=OSError("read only")):
                with self.assertLogs("ocdeck.device", level="WARNING"):
                    loop._save_jelly()
            self.assertIsNotNone(loop.jelly)

    def test_configuration_accepts_presets_rejects_invalid_values(self):
        for style in (*HOPS, "mood"):
            settings({"jelly": {"hop_style": style}})
        for name in ("balanced", "mellow", "curious", "playful"):
            settings({"jelly": {"personality": name}})
        for invalid in (
            {"thoughts": "shout"},
            {"persistent": 1},
            {"needs": "yes"},
            {"travel": "always"},
            {"mood_colors": None},
            {"local_movement": "unlimited"},
        ):
            with self.assertRaises(ValueError):
                settings({"jelly": invalid})


if __name__ == "__main__":
    unittest.main()
