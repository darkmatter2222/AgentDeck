"""Jelly-facing update UX layered onto the existing broker/device classes."""

import logging
import threading

from PIL import ImageDraw, ImageFont

from .common import home
from .jelly import free_keys
from .updates import CHECK_INTERVAL, check, install, schedule_restart

LOG = logging.getLogger(__name__)
MOVE_INTERVAL = 1.1


def _draw_update_badge(loop, key, image):
    """Draw a red exclamation above Jelly using the same Pillow UI font family."""
    geometry = loop.jelly.geometry
    left = geometry.bounds(key)[0]
    local_x = int(round(loop.jelly.x - left))
    local_x = max(9, min(image.width - 9, local_x))
    ImageDraw.Draw(image).text(
        (local_x, 8),
        "!",
        font=ImageFont.load_default(size=14),
        fill=(255, 45, 65, 255),
        stroke_width=1,
        stroke_fill=(70, 0, 8, 255),
        anchor="mm",
    )


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


def install_broker_patch(Broker):
    """Turn the broker's existing update worker into a five-minute PyPI watcher."""
    if getattr(Broker, "_pypi_update_patch", False):
        return

    def check_update(self):
        while not self.stop.is_set():
            try:
                info = check(self.root, self.config)
                if info:
                    self.update = info
                    self.device._jelly_update_info = info
                    self.device.status["update"] = {"available": True, **info}
            except Exception:
                LOG.info("Background PyPI update check failed; keeping the current state", exc_info=True)
            if self.stop.wait(CHECK_INTERVAL):
                return

    Broker.check_update = check_update
    Broker._pypi_update_patch = True


def install_device_patch(DeviceLoop):
    """Install Jelly's visual update signal and button action exactly once."""
    if getattr(DeviceLoop, "_jelly_update_patch", False):
        return

    original_start = DeviceLoop._start_jelly
    original_frames = DeviceLoop._jelly_frames
    original_press = DeviceLoop.press

    def start_jelly(self):
        original_start(self)
        if not hasattr(self, "_jelly_update_info"):
            self._jelly_update_info = None
        if not hasattr(self, "_jelly_update_keys"):
            self._jelly_update_keys = set()
        if not hasattr(self, "_jelly_update_next_move"):
            self._jelly_update_next_move = 0.0
        if not hasattr(self, "_jelly_update_installing"):
            self._jelly_update_installing = False

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
