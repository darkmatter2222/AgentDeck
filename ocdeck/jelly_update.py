"""Jelly-facing update UX layered onto DeviceLoop without changing agent assignment semantics."""

import logging
from pathlib import Path
import threading
import time

from PIL import ImageDraw, ImageFont

from .common import home
from .jelly import free_keys
from .updates import CHECK_INTERVAL, check, install, schedule_restart

LOG = logging.getLogger(__name__)
MOVE_INTERVAL = 1.1


def _draw_update_badge(loop, key, image):
    """Draw a small red exclamation above Jelly using the same Pillow UI font family."""
    geometry = loop.jelly.geometry
    left = geometry.bounds(key)[0]
    local_x = int(round(loop.jelly.x - left))
    local_x = max(9, min(image.width - 9, local_x))
    draw = ImageDraw.Draw(image)
    draw.ellipse(
        (local_x - 7, 1, local_x + 7, 15),
        fill=(205, 25, 45, 255),
        outline=(255, 150, 160, 255),
        width=1,
    )
    draw.text(
        (local_x, 8),
        "!",
        font=ImageFont.load_default(size=12),
        fill=(255, 255, 255, 255),
        anchor="mm",
    )


def _watch(loop):
    """Poll PyPI immediately and every five minutes without blocking rendering."""
    while not loop.stop.is_set():
        try:
            root = Path(loop.jelly_root or home())
            info = check(root, loop.config)
            if info:
                loop._jelly_update_info = info
                loop.status["update"] = {"available": True, **info}
        except Exception:
            LOG.info("Background PyPI update check failed; keeping the current state", exc_info=True)
        if loop.stop.wait(CHECK_INTERVAL):
            return


def _install_worker(loop):
    info = getattr(loop, "_jelly_update_info", None)
    if not info:
        return
    try:
        loop.status["update"] = {"available": True, "state": "installing", **info}
        install(info["version"])
        loop.status["update"] = {"available": False, "state": "restarting", "version": info["version"]}
        schedule_restart(loop.jelly_root or home())
        loop.stop.set()
    except Exception as error:
        LOG.exception("Jelly self-update failed")
        loop.status["update"] = {
            "available": True,
            "state": "failed",
            **info,
            "error": str(error)[-500:],
        }
    finally:
        loop._jelly_update_installing = False


def install_device_patch(DeviceLoop):
    """Install the PyPI/Jelly integration exactly once."""
    if getattr(DeviceLoop, "_jelly_update_patch", False):
        return

    original_start = DeviceLoop._start_jelly
    original_frames = DeviceLoop._jelly_frames
    original_press = DeviceLoop.press

    def start_jelly(self):
        original_start(self)
        if not hasattr(self, "_jelly_update_info"):
            self._jelly_update_info = None
            self._jelly_update_keys = set()
            self._jelly_update_next_move = 0.0
            self._jelly_update_installing = False
            self._jelly_update_thread = None
        if self.config.get("check_updates", True) and (
            self._jelly_update_thread is None or not self._jelly_update_thread.is_alive()
        ):
            self._jelly_update_thread = threading.Thread(
                target=_watch,
                args=(self,),
                name="agentstreamdeck-update-watch",
                daemon=True,
            )
            self._jelly_update_thread.start()

    def jelly_frames(self, now, views):
        info = getattr(self, "_jelly_update_info", None)
        if info and self.jelly is not None:
            # The update indicator replaces ambient speech so the red signal stays legible.
            self.jelly.thoughts.clear()
            available = free_keys(views)
            if self.jelly.state == "idle" and now >= self._jelly_update_next_move:
                current = self.jelly.current
                destinations = (
                    sorted(set(self.jelly.geometry.adjacent(current)) & available) if current is not None else []
                )
                if destinations:
                    self.jelly.hop(self.jelly.rng.choice(destinations), now, available)
                elif current is not None:
                    self.jelly.start_action("pace", now)
                self._jelly_update_next_move = now + MOVE_INTERVAL

        frames = original_frames(self, now, views)
        if info and self.jelly is not None:
            self._jelly_update_keys = set(frames)
            for key, image in frames.items():
                _draw_update_badge(self, key, image)
        else:
            self._jelly_update_keys = set()
        return frames

    def start_update(self):
        if self._jelly_update_installing or not self._jelly_update_info:
            return False
        self._jelly_update_installing = True
        threading.Thread(
            target=_install_worker,
            args=(self,),
            name="agentstreamdeck-self-update",
            daemon=True,
        ).start()
        return True

    def press(self, key, state):
        if (
            state
            and getattr(self, "_jelly_update_info", None)
            and key in getattr(self, "_jelly_update_keys", set())
        ):
            self._start_jelly_update()
            return
        original_press(self, key, state)

    DeviceLoop._start_jelly = start_jelly
    DeviceLoop._jelly_frames = jelly_frames
    DeviceLoop._start_jelly_update = start_update
    DeviceLoop.press = press
    DeviceLoop._jelly_update_patch = True
