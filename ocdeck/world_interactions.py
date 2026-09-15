"""Intention, travel, contact and disposition, independent of rendering and scenes."""

from collections import deque
from dataclasses import asdict, dataclass
import math
from .world_objects import DEFINITIONS, ATMOSPHERES, Object

RECIPES = {name: d.action for name, d in DEFINITIONS.items()}
TOOLS = {"rake", "broom", "scythe"}
TRANSFER = {"balloon", "lantern", "kite"}


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


@dataclass(frozen=True)
class PlayFrame:
    key: int
    name: str
    action: str
    stage: str
    progress: float
    elapsed: float
    color: str


class Interaction:
    def __init__(self):
        self.objects = {}
        self.serial = 0
        self.target = None
        self.key = None
        self.home_key = None
        self.work_key = None
        self.scene = ""
        self.sky = ""
        self.frame = None
        self.stage = ""
        self.stage_started = 0.0
        self.next_at = 0.6
        self.owns_actor = False
        self.held = None
        self.history = deque(maxlen=24)
        self.locations = deque(maxlen=12)
        self.events = deque(maxlen=64)
        self.origin_x = 0.0
        self.use_elapsed = 0.0
        self.last = None
        self.visible = False
        self.geometry = None
        self.water = 1.0

    def snapshot(self):
        return {
            "version": 1,
            "serial": self.serial,
            "objects": [asdict(o) for o in list(self.objects.values())[-8:]],
            "history": list(self.history),
            "locations": list(self.locations),
        }

    def restore(self, value):
        if not isinstance(value, dict) or value.get("version") != 1:
            return
        items = value.get("objects", [])
        if not isinstance(items, list):
            return
        restored = {}
        for raw in items[-8:]:
            if not isinstance(raw, dict) or raw.get("name") not in DEFINITIONS:
                continue
            if type(raw.get("id")) is not int or not 0 < raw["id"] < 10**9:
                continue
            if any(
                type(raw.get(k)) not in (int, float) or not math.isfinite(raw[k]) or not 0 <= raw[k] <= 1
                for k in ("progress", "amount")
            ):
                continue
            # Coordinates are intentionally reconciled on the next valid placement.
            obj = Object(raw["id"], raw["name"], None, None, "stored", raw["progress"], raw["amount"])
            obj.applied = raw.get("applied") is True
            obj.result = DEFINITIONS[obj.name].result if obj.applied else ""
            restored[obj.id] = obj
        self.objects = restored
        self.serial = max(restored, default=0)
        history = value.get("history", [])
        if isinstance(history, list):
            self.history.extend(n for n in history[-24:] if isinstance(n, str) and n in DEFINITIONS)

    def cancel(self, now, jelly):
        if self.target is not None:
            obj = self.objects[self.target]
            obj.state = "stored"
            obj.cell = None
            # Completed contact progress survives, carried objects never remain floating.
            self.events.append(("cancel", self.stage, obj.id))
        if self.owns_actor and jelly.state == "world_play":
            jelly.state, jelly.deadline = "idle", now + 2
        self.frame, self.target, self.key = None, None, None
        self.held = None
        self.owns_actor = False
        self.stage = ""
        self.visible = False
        self.next_at = max(self.next_at, now + 3)

    def _choose_cell(self, jelly, free, avoid=None, exclude=None):
        candidates = sorted(
            jelly.geometry.reachable(jelly.current, free) - ({exclude} if exclude is not None else set())
        )
        weights = []
        for k in candidates:
            distance = len(jelly.geometry.route_to(jelly.current, k, free) or [])
            weights.append((1 + min(distance, 3)) / (1 + self.locations.count(k) + (3 if k == avoid else 0)))
        key = jelly.rng.choices(candidates, weights)[0]
        self.locations.append(key)
        return key

    def _begin(self, now, jelly, available, scene_id, scene, options):
        candidates = list(dict.fromkeys([scene.prop, ATMOSPHERES.get(scene.sky, "")]))
        candidates = [n for n in candidates if n in DEFINITIONS]
        if not candidates:
            return
        # An explicit scene override remains a reproducible demo. Normal scenes
        # provide opportunities; existing needs and recent history rank them.
        weights = []
        for name in candidates:
            motive = DEFINITIONS[name].motive
            need = {
                "play": "stimulation",
                "tidy": "confidence",
                "curiosity": "stimulation",
                "rest": "energy",
                "celebrate": "sociability",
                "weather": "energy",
            }.get(motive, motive)
            deficit = 100 - jelly.mind.needs.get(need, 50)
            weights.append((20 + deficit) / (1 + self.history.count(name) * 3))
        name = candidates[0] if options["scene_override"] and scene.prop else jelly.rng.choices(candidates, weights)[0]
        obj = next((o for o in self.objects.values() if o.name == name and not o.applied), None)
        if obj is None:
            self.serial += 1
            obj = Object(self.serial, name, None, None, color=scene.color)
            self.objects[obj.id] = obj
        # Keep bounded logical keepsakes, never unbounded decorations.
        while len(self.objects) > 8:
            del self.objects[next(k for k in self.objects if k != obj.id)]
        reachable = jelly.geometry.reachable(jelly.current, available)
        if obj.cell not in reachable:
            obj.cell = self._choose_cell(jelly, reachable)
            obj.home = obj.cell
        obj.state = "reserved"
        self.target, self.key, self.home_key = obj.id, obj.cell, jelly.current
        self.work_key = self._choose_cell(jelly, reachable, obj.cell) if name in TOOLS | TRANSFER else obj.cell
        if name in TOOLS | TRANSFER and len(reachable) > 1 and self.work_key == obj.cell:
            self.work_key = self._choose_cell(jelly, reachable, exclude=obj.cell)
        self.scene, self.sky = scene_id, scene.sky
        self.use_elapsed = obj.progress * 6
        self.water = max(0.0, 1 - obj.progress)
        self.owns_actor, self.visible = True, True
        self._stage("notice", now, jelly)
        self.events.append(("selected", name, obj.cell))

    def _stage(self, stage, now, jelly):
        self.stage, self.stage_started = stage, now
        self.origin_x = jelly.x
        self.events.append(("stage", stage, jelly.current))

    def _travel(self, now, jelly, free, destination, next_stage):
        if jelly.state == "hop":
            return
        route = jelly.geometry.route_to(jelly.current, destination, free)
        if route is None:
            self.cancel(now, jelly)
        elif route:
            if not jelly.hop(route[0], now, free):
                self.cancel(now, jelly)
        else:
            self.key = destination
            self._stage(next_stage, now, jelly)

    def _outcome(self, jelly, obj):
        if obj.applied:
            return
        obj.applied, obj.result, obj.state = True, DEFINITIONS[obj.name].result, "changed"
        self.history.append(obj.name)
        motive = DEFINITIONS[obj.name].motive
        need = {
            "play": "stimulation",
            "curiosity": "stimulation",
            "tidy": "confidence",
            "rest": "energy",
            "celebrate": "sociability",
            "weather": "energy",
        }.get(motive, motive)
        if jelly.options["needs"] and need in jelly.mind.needs:
            jelly.mind.needs[need] = min(100, jelly.mind.needs[need] + 5)
        if obj.name == "gift":
            self.serial += 1
            toy = Object(self.serial, "beachball", obj.cell, obj.cell, "stored", color=obj.color)
            self.objects[toy.id] = toy
            obj.data["gift_id"] = toy.id
        self.events.append(("outcome", obj.id, obj.result))

    def tick(self, now, jelly, available, scene_id, scene, options, blocked=False):
        dt = 0 if self.last is None else max(0, min(0.25, now - self.last))
        self.last = now
        free = set(available) & set(range(jelly.geometry.count))
        allowed = (
            not blocked
            and options["interactions"]
            and options["props"]
            and not options["reduced_motion"]
            and jelly.current in free
            and not jelly.update_available
            and now >= jelly.touch_until
            and jelly.mind.target is None
            and now >= jelly.look_until
            and jelly.mind.mood not in ("asleep", "overwhelmed", "overworked")
        )
        if self.geometry is not None and self.geometry != jelly.geometry:
            self.cancel(now, jelly)
            for obj in self.objects.values():
                obj.cell = obj.home = None
                obj.state = "stored"
        self.geometry = jelly.geometry
        if not allowed:
            self.cancel(now, jelly)
            return
        if self.target is not None:
            obj = self.objects[self.target]
            if obj.home not in free or self.work_key not in free or jelly.state not in ("world_play", "hop", "idle"):
                self.cancel(now, jelly)
                return
        else:
            if scene is None or now < self.next_at or jelly.state == "hop":
                return
            self._begin(now, jelly, free, scene_id, scene, options)
            if self.target is None:
                return
        obj = self.objects[self.target]
        elapsed = max(0, now - self.stage_started)
        travel_stages = {
            "approach": (obj.home, "position"),
            "carry": (self.work_key, "work_position"),
            "return": (obj.home, "return_position"),
        }
        if self.stage in travel_stages:
            destination, following = travel_stages[self.stage]
            self._travel(now, jelly, free, destination, following)
            if self.target is None:
                return
        else:
            jelly.state, jelly.deadline = "world_play", now + 2
            jelly.rotation, jelly.mirror = 0, False
            jelly.face, jelly.gaze = "focused", "right"
            jelly.pose = "curious_lean" if self.stage in ("reach", "use", "putdown") else "idle"
            jelly.gesture, jelly.gesture_step = ("point", 2) if self.stage in ("reach", "use", "putdown") else ("", 0)
            if self.stage == "notice":
                jelly._point(obj.cell)
                if elapsed >= 0.8:
                    self._stage("approach", now, jelly)
            elif self.stage in ("position", "work_position", "return_position"):
                left = jelly.geometry.bounds(jelly.current)[0]
                goal = left + max(18 * jelly.geometry.scale, jelly.geometry.width / 2 - 7 * jelly.geometry.scale)
                jelly.x = self.origin_x + (goal - self.origin_x) * ease(elapsed / 0.6)
                if elapsed >= 0.6:
                    following = {"position": "reach", "work_position": "use", "return_position": "putdown"}[self.stage]
                    self._stage(following, now, jelly)
            elif self.stage == "reach":
                if elapsed >= 0.8:
                    if DEFINITIONS[obj.name].carry:
                        self.held, obj.state = obj.id, "held"
                        self.events.append(("pickup", obj.id, jelly.current))
                    self._stage("carry" if obj.name in TOOLS | TRANSFER else "use", now, jelly)
            elif self.stage == "use":
                # Only reached contact can mutate material state. Long wall-clock
                # gaps pause the action rather than awarding invisible work.
                self.use_elapsed = min(6.0, self.use_elapsed + dt)
                obj.progress = self.use_elapsed / 6
                obj.state = "in_use"
                action = RECIPES[obj.name]
                if action in ("drink", "lick", "serve", "picnic", "unwrap_eat"):
                    obj.amount = max(0.0, 1 - obj.progress)
                if action in ("water", "fill_water"):
                    self.water = max(0, 1 - obj.progress)
                    obj.amount = obj.progress
                if action in ("rake", "sweep", "harvest"):
                    # Gather on the pulling half of each stroke; never on recovery.
                    cycle = self.use_elapsed % 1.5
                    pulls = int(self.use_elapsed / 1.5) + min(1, cycle / 0.85)
                    obj.data["gathered"] = min(1, pulls / 4)
                if action == "ride":
                    jelly.x = self.origin_x + math.sin(obj.progress * math.pi) * 3 * jelly.geometry.scale
                    jelly.y = jelly.geometry.anchor(jelly.current)[1] - 5 * jelly.geometry.scale
                elif action in ("splash", "snow_angel"):
                    jelly.pose = "puddle" if action == "snow_angel" else "rebound"
                    jelly.y = jelly.geometry.anchor(jelly.current)[1] - (
                        round(5 * abs(math.sin(obj.progress * math.tau))) if action == "splash" else 0
                    )
                elif action in ("aim", "moonwatch", "lullaby", "shelter"):
                    jelly.gaze, jelly.face = "up", "curious"
                if self.use_elapsed >= 6:
                    self._outcome(jelly, obj)
                    self._stage("return" if obj.name in TOOLS else "putdown", now, jelly)
            elif self.stage == "putdown":
                if elapsed >= 0.8:
                    self.held = None
                    obj.cell = self.work_key if obj.name in TRANSFER else obj.home
                    obj.state = "changed"
                    jelly.y = jelly.geometry.anchor(jelly.current)[1]
                    self._stage("admire", now, jelly)
            elif self.stage == "admire":
                jelly.face, jelly.pose = "happy", "proud"
                if elapsed >= 2:
                    self._stage("rest", now, jelly)
                    self.owns_actor = False
                    jelly.state, jelly.deadline = "idle", now + 3
                    self.next_at = now + options["interaction_seconds"]
            elif self.stage == "rest":
                # A result remains observable through theme changes and pauses.
                self.owns_actor = False
                jelly.state = "idle"
                if now >= self.next_at:
                    self.frame = None
                    self.target, self.key = None, None
                    self.stage = ""
                    return
        if self.held == obj.id:
            obj.cell = jelly.current
        self.visible = True
        elapsed = max(0, now - self.stage_started)
        p = obj.progress if self.stage == "use" else min(1, elapsed / 0.8)
        assert self.key is not None
        self.frame = PlayFrame(self.key, obj.name, RECIPES[obj.name], self.stage, p, elapsed, obj.color)

    def render_layers(self, jelly, available):
        from .world_object_art import render_layers

        return render_layers(self, jelly, available)

    def layers(self, jelly):
        if self.frame is None:
            return None
        back, front = self.render_layers(jelly, {self.frame.key})
        from PIL import Image

        blank = lambda: Image.new("RGBA", (jelly.geometry.width, jelly.geometry.height))
        return back.get(self.frame.key, blank()), front.get(self.frame.key, blank())
