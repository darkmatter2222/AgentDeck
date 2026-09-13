"""Jelly-facing update UX layered onto the existing broker/device classes."""

import logging
import math
import threading

from PIL import Image, ImageDraw, ImageFont

from .common import home
from .coffee import rainbow
from .jelly import free_keys
from .updates import CHECK_INTERVAL, UPDATE_LOCK, check, install, schedule_restart

LOG = logging.getLogger(__name__)
MOVE_INTERVAL = 30.0


def _draw_update_badge(loop, key, image, now):
    """Reserve a footer below Jelly and keep upgrade symbols above his crown."""
    body = rainbow(image, int(now * 6) % 48)
    result = Image.new("RGBA", image.size)
    result.paste(body, (0, -20))
    draw = ImageDraw.Draw(result)
    cx = image.width // 2
    draw.rounded_rectangle((cx - 20, 0, cx + 20, 19), radius=5, fill=(9, 17, 27, 245))
    draw.text((cx - 10, 10), "!", font=ImageFont.load_default(size=16), fill=(255, 65, 83), anchor="mm")
    green = round(215 + 35 * math.sin(now * math.pi))
    draw.polygon(
        ((cx + 10, 2), (cx + 18, 10), (cx + 13, 10), (cx + 13, 17), (cx + 7, 17), (cx + 7, 10), (cx + 2, 10)),
        fill=(65, green, 125),
    )
    draw.rectangle((0, image.height - 20, image.width, image.height), fill=(9, 17, 27, 255))
    lines = ("Updating", "please wait") if getattr(loop, "_jelly_update_installing", False) else ("Update", "available")
    font = ImageFont.load_default(size=9 if image.width < 80 else 10)
    for index, line in enumerate(lines):
        draw.text((cx, image.height - 15 + index * 10), line, font=font, fill=(229, 247, 244), anchor="mm")
    return result


def _install_worker(loop):
    with UPDATE_LOCK:
        if loop.stop.is_set():
            loop._jelly_update_installing = False
            return
        _install_worker_locked(loop)


def _install_worker_locked(loop):
    info = getattr(loop, "_jelly_update_info", None)
    if not info:
        return
    try:
        loop.status["update"] = {"available": True, "state": "installing", **info}
        install(info["version"])
        loop.status["update"] = {"available": False, "state": "restarting", "version": info["version"]}
        schedule_restart(loop.jelly_root or home(), mock=getattr(loop, "mock", False))
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
        if self.jelly is not None:
            if info and not getattr(self.jelly, "update_available", False):
                self._jelly_update_next_move = now + MOVE_INTERVAL
            self.jelly.update_available = bool(info)
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
                self._jelly_update_next_move = now + MOVE_INTERVAL

        frames = original_frames(self, now, views)
        if info and self.jelly is not None:
            self._jelly_update_keys = set(frames)
            for key, image in frames.items():
                frames[key] = _draw_update_badge(self, key, image, now)
                if hasattr(self, "overlay_actions"):
                    self.overlay_actions[key] = {"_action": "update"}
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

    DeviceLoop._start_jelly = start_jelly
    DeviceLoop._jelly_frames = jelly_frames
    DeviceLoop._start_jelly_update = start_update
    DeviceLoop._jelly_update_patch = True
