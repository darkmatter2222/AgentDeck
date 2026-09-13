"""One cosmetic entity in continuous deck-space, driven by the device loop.

No threads, device access or wall clock inside the controller. Call update with
monotonic time and the current free-key set, then crop its single world sprite.
"""

from dataclasses import dataclass
import math
import random
from PIL import Image
from .jelly_art import ANCHOR, GRID, sprite


def settings(config):
    value = config.get("jelly", {})
    if not isinstance(value, dict) or set(value) - {"enabled", "virtual_gap", "behavior_seed", "hop_style"}:
        raise ValueError("Unknown or invalid jelly configuration")
    result = {"enabled": False, "virtual_gap": 8, "behavior_seed": None, "hop_style": "classic", **value}
    if type(result["enabled"]) is not bool:
        raise ValueError("jelly.enabled must be boolean")
    if type(result["virtual_gap"]) is not int or not 0 <= result["virtual_gap"] <= 40:
        raise ValueError("jelly.virtual_gap must be 0..40 integer pixels")
    if result["behavior_seed"] is not None and type(result["behavior_seed"]) is not int:
        raise ValueError("jelly.behavior_seed must be an integer or null")
    if result["hop_style"] not in ("classic", "fluid"):
        raise ValueError("jelly.hop_style must be classic or fluid")
    return result


def free_keys(views):
    """Off AND unassigned: READY, errors and future functional states all win."""
    return {k for k, view in enumerate(views) if view["state"] == "off" and not view.get("id")}


@dataclass(frozen=True)
class DeckGeometry:
    rows: int = 2
    columns: int = 3
    width: int = 80
    height: int = 80
    gap: int = 8

    def __post_init__(self):
        if min(self.rows, self.columns, self.width, self.height) < 1 or self.gap < 0:
            raise ValueError("Invalid deck geometry")

    @property
    def count(self):
        return self.rows * self.columns

    @property
    def size(self):
        return (self.columns * (self.width + self.gap) - self.gap, self.rows * (self.height + self.gap) - self.gap)

    @property
    def scale(self):
        return max(1, min(self.width, self.height) // GRID)

    def bounds(self, key):
        if key not in range(self.count):
            raise ValueError("Key outside deck")
        row, col = divmod(key, self.columns)
        x, y = col * (self.width + self.gap), row * (self.height + self.gap)
        return x, y, x + self.width, y + self.height

    def anchor(self, key):
        x, y, _, _ = self.bounds(key)
        return x + self.width / 2, y + self.height * 0.8

    def adjacent(self, key):
        self.bounds(key)
        row, col = divmod(key, self.columns)
        return tuple(
            r * self.columns + c
            for r, c in ((row, col - 1), (row, col + 1), (row - 1, col), (row + 1, col))
            if 0 <= r < self.rows and 0 <= c < self.columns
        )


class Jelly:
    PREPARE = 0.6
    FLIGHT = 0.7
    LANDING = 0.5

    def __init__(self, geometry, seed=None, hop_style="classic"):
        self.geometry = geometry
        self.rng = random.Random(seed)
        self.hop_style = hop_style
        self.state = "hidden"
        self.current = None
        self.destination = None
        self.x = self.y = 0.0
        self.since = 0.0
        self.deadline = None
        self.pose = "idle"
        self.face = "neutral"
        self.gaze = "center"
        self.gesture = ""
        self.gesture_step = 0
        self.mirror = False
        self.closed = False

    def close(self):
        self.closed = True
        self.hide()

    def hide(self):
        self.state, self.current, self.destination = "hidden", None, None
        self.deadline = None

    def settle(self, key, now):
        """Place on spawn/landing only; navigation always goes through hop()."""
        self.current, self.destination = key, None
        self.x, self.y = self.geometry.anchor(key)
        self.state, self.since = "idle", now
        self.deadline = now + self.rng.uniform(2.0, 4.5)

    def hop(self, destination, now, available):
        if (
            self.closed
            or self.current is None
            or self.state == "hop"
            or self.current not in available
            or destination not in available
            or destination not in self.geometry.adjacent(self.current)
        ):
            return False
        self.destination, self.state, self.since = destination, "hop", now
        return True

    def update(self, now, available):
        available = set(available) & set(range(self.geometry.count))
        if self.closed:
            return
        if (
            not available
            or (self.current is not None and self.current not in available)
            or (self.destination is not None and self.destination not in available)
        ):
            self.hide()
            return  # Abort the whole entity this frame, including its source crop.
        if self.state == "hidden":
            if self.deadline is None:
                self.deadline = now + self.rng.uniform(0.5, 1.3)
            elif now >= self.deadline:
                self.settle(self.rng.choice(sorted(available)), now)
            return
        self.pose, self.face, self.gaze = "idle", "neutral", "center"
        self.gesture, self.gesture_step, self.mirror = "", 0, False
        if self.state == "hop":
            self._hop_pose(now)
            return
        if self.deadline is not None and now >= self.deadline:
            if self.state != "idle":
                self.state, self.since = "idle", now
                self.deadline = now + self.rng.uniform(2, 5)
            else:
                assert self.current is not None
                neighbors = [k for k in self.geometry.adjacent(self.current) if k in available]
                action = self.rng.choices(
                    ["blink", "look_left", "look_right", "look_up", "wave", "point_left", "point_right", "rest", "hop"],
                    [6, 2, 2, 1, 1, 1, 1, 1, 4 if neighbors else 0],
                )[0]
                if action == "hop":
                    self.hop(self.rng.choice(neighbors), now, available)
                    self._hop_pose(now)
                    return
                self.state, self.since = action, now
                self.deadline = now + (0.5 if action == "blink" else 5 if action == "rest" else 1.4)
        self._idle_pose(now)

    def _idle_pose(self, now):
        elapsed = now - self.since
        if self.state == "idle":
            # Quiet, anchored breathing with long pose holds.
            phase = elapsed % 3.2
            self.pose = "breathe" if 1.6 <= phase < 2.1 else "idle"
        elif self.state == "blink":
            self.face = ("neutral", "half", "closed", "closed", "half", "neutral")[min(5, int(elapsed * 12))]
        elif self.state.startswith("look_"):
            self.gaze, self.face = self.state[5:], "curious"
        elif self.state == "rest":
            self.pose = "breathe"
            self.face = "half" if elapsed < 0.3 or elapsed > 4.6 else "sleepy"
        elif self.state == "wave" or self.state.startswith("point_"):
            self.face = "happy"
            self.mirror = self.state == "point_left"
            self.gaze = "right"
            if elapsed >= 0.25:
                self.gesture = "wave" if self.state == "wave" else "point"
                index = min(11, int((elapsed - 0.25) * 12))
                self.gesture_step = (1, 2, 3, 4, 3, 4, 3, 4, 3, 2, 1, 0)[index]

    def _hop_pose(self, now):
        assert self.current is not None and self.destination is not None
        elapsed = max(0, now - self.since)
        a, b = self.geometry.anchor(self.current), self.geometry.anchor(self.destination)
        dx, dy = b[0] - a[0], b[1] - a[1]
        self.mirror = dx < 0
        self.gaze = "right" if dx else "up" if dy < 0 else "center"
        self.face = "focused"
        if elapsed < self.PREPARE:
            self.x, self.y = a
            self.pose = ("idle", "bob", "idle", "squash", "deep", "deep")[min(5, int(elapsed * 10))]
        elif elapsed < self.PREPARE + self.FLIGHT:
            t = (elapsed - self.PREPARE) / self.FLIGHT
            ease = t * t * (3 - 2 * t)
            # Physical position is continuous at the deck FPS; poses hold 83–100ms.
            self.x = a[0] + dx * ease
            arc = self.geometry.height * (0.17 if dx else 0.09)
            self.y = a[1] + dy * ease - arc * 4 * t * (1 - t)
            poses = (
                ("launch", "launch", "air", "apex", "apex", "fall", "fall")
                if self.hop_style == "classic"
                else ("launch", "stretch", "air", "apex", "apex", "air", "fall", "stretch", "fall")
            )
            self.pose = poses[min(len(poses) - 1, int(t * len(poses)))]
            self.face = "jump"
        elif elapsed < self.PREPARE + self.FLIGHT + self.LANDING:
            self.x, self.y = b
            t = elapsed - self.PREPARE - self.FLIGHT
            self.pose = ("impact", "impact", "rebound", "jiggle", "idle")[min(4, int(t * 10))]
            self.face = "landing"
        else:
            self.settle(self.destination, now)
            self.pose, self.face, self.mirror = "idle", "happy", False

    def crops(self, available):
        """Return only nonempty free-key viewports intersecting the world sprite.

        paste with a negative destination is Pillow's native viewport clipping.
        The bezel has no viewport, so it is never painted onto any physical key.
        """
        if self.closed or self.current is None or self.state == "hidden":
            return {}
        if self.current not in available or (self.destination is not None and self.destination not in available):
            return {}
        g = self.geometry
        im = sprite(self.pose, self.face, self.gaze, self.gesture, self.gesture_step, g.scale, self.mirror)
        x, y = round(self.x - ANCHOR[0] * g.scale), round(self.y - ANCHOR[1] * g.scale)
        result = {}
        for key in sorted(available):
            l, t, r, b = g.bounds(key)
            if x >= r or y >= b or x + im.width <= l or y + im.height <= t:
                continue
            viewport = Image.new("RGBA", (g.width, g.height))
            viewport.paste(im, (x - l, y - t))
            if viewport.getbbox():
                result[key] = viewport
        return result
