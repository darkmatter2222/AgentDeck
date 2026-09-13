"""HID adapter using the pip hidapi wheel, avoiding a manual hidapi.dll install."""

import logging
import queue
import threading
import time
from .art import frame
from .errors import message
from .appearance import appearance, animation_phase, harness_id
from collections import OrderedDict
from .jelly import DeckGeometry, Jelly, free_keys, settings as jelly_settings

LOG = logging.getLogger(__name__)
MINI_PIDS = {0x0063, 0x0090, 0x00B3, 0x00B8}


class WheelTransport:
    """StreamDeck transport duck type backed by cython-hidapi's bundled library."""

    def __init__(self, info):
        self.info, self.handle = info, None
        self.lock = threading.RLock()

    def open(self):
        import hid

        with self.lock:
            if self.handle is None:
                h = hid.device()
                h.open_path(self.info["path"])
                h.set_nonblocking(True)
                self.handle = h

    def close(self):
        with self.lock:
            if self.handle:
                self.handle.close()
                self.handle = None

    def is_open(self):
        return self.handle is not None

    def connected(self):
        import hid

        return any(x["path"] == self.info["path"] for x in hid.enumerate(0x0FD9, self.product_id()))

    def path(self):
        return self.info["path"]

    def vendor_id(self):
        return self.info["vendor_id"]

    def product_id(self):
        return self.info["product_id"]

    def _call(self, method, *args):
        from StreamDeck.Transport.Transport import TransportError

        try:
            with self.lock:
                if self.handle is None:
                    raise OSError("Device is closed")
                return getattr(self.handle, method)(*args)
        except (OSError, ValueError) as e:
            raise TransportError(str(e)) from e

    def write(self, payload):
        result = self._call("write", bytes(payload))
        if result != len(payload):
            from StreamDeck.Transport.Transport import TransportError

            raise TransportError(f"Short HID write: {result}/{len(payload)}")
        return result

    def write_feature(self, payload):
        return self._call("send_feature_report", bytes(payload))

    def read_feature(self, report_id, length):
        return bytes(self._call("get_feature_report", report_id, length))

    def read(self, length):
        value = self._call("read", length)
        return bytes(value) if value else None


def device_types():
    from StreamDeck.Devices.StreamDeckMini import StreamDeckMini
    from StreamDeck.Devices.StreamDeckOriginal import StreamDeckOriginal
    from StreamDeck.Devices.StreamDeckOriginalV2 import StreamDeckOriginalV2
    from StreamDeck.Devices.StreamDeckXL import StreamDeckXL

    return {
        **{p: StreamDeckMini for p in MINI_PIDS},
        0x60: StreamDeckOriginal,
        **{p: StreamDeckOriginalV2 for p in (0x6D, 0x80, 0xA5, 0xB9)},
        **{p: StreamDeckXL for p in (0x6C, 0x8F, 0xBA)},
    }


def elgato_running():
    import psutil

    for process in psutil.process_iter(["name"]):
        try:
            if (process.info["name"] or "").lower() in ("streamdeck.exe", "stream deck.exe", "stream deck"):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


def enumerate_devices():
    import hid

    types = device_types()
    result = []
    for d in hid.enumerate(0x0FD9, 0):
        if d["product_id"] in types:
            deck = types[d["product_id"]](WheelTransport(d))
            result.append({**d, "model": deck.deck_type(), "keys": deck.key_count()})
    return result


def enumerate_minis():
    import hid

    return [d for d in hid.enumerate(0x0FD9, 0) if d["product_id"] in MINI_PIDS]


class DeviceLoop:
    def __init__(self, registry, presses, stop, config, mock=False, root=None):
        self.registry, self.presses, self.stop, self.config, self.mock = registry, presses, stop, config, mock
        self.status = {"online": False, "mock": mock, "error": "Not connected", "frames": 0}
        self.presented: list[dict | None] = [None] * len(self.registry.slots)
        self.presented_lock = threading.Lock()
        self.deck = None
        self.jelly = None
        self.jelly_events = queue.Queue(maxsize=32)
        self.jelly_root = root
        self.jelly_saved_at = 0.0

    def notify_jelly(self, kind, slot):
        """Metadata-only handoff; workers never touch the animation controller."""
        if kind == "focus":
            try:
                self.jelly_events.put_nowait({"kind": kind, "slot": slot})
            except queue.Full:
                pass

    def _save_jelly(self):
        if self.jelly and self.jelly_root and self.jelly.options["persistent"]:
            from pathlib import Path
            from .common import atomic_json

            try:
                atomic_json(
                    Path(self.jelly_root) / "jelly-state.json", self.jelly.mind.snapshot(self.jelly.thoughts.recent)
                )
            except Exception:
                LOG.warning("Could not save Jelly's optional state", exc_info=True)

    def _start_jelly(self):
        self.jelly = None
        self.status["jelly"] = "disabled"
        try:
            options = jelly_settings(self.config)
            if not options["enabled"] or not self.config.get("animations", True):
                return
            if self.deck:
                rows, columns = self.deck.key_layout()
                width, height = self.deck.key_image_format()["size"]
            else:
                rows, columns = {6: (2, 3), 15: (3, 5), 32: (4, 8)}[len(self.registry.slots)]
                width = height = 80
            geometry = DeckGeometry(rows, columns, width, height, options["virtual_gap"])
            self.jelly = Jelly(geometry, options["behavior_seed"], options["hop_style"], options)
            self.jelly.thoughts.next_at = time.monotonic() + 20
            if options["persistent"] and self.jelly_root:
                from pathlib import Path
                from .common import read_json

                recent = self.jelly.mind.restore(read_json(Path(self.jelly_root) / "jelly-state.json", {}))
                self.jelly.thoughts.recent.extend(recent)
            self.jelly_saved_at = time.monotonic()
            self.status["jelly"] = "enabled"
        except Exception:
            self._fail_jelly()

    def _fail_jelly(self):
        LOG.exception("Experimental Jelly disabled; agent rendering continues")
        if self.jelly:
            self.jelly.close()
        self.jelly = None
        self.status["jelly"] = "failed"

    def _jelly_frames(self, now, views):
        if self.jelly is None:
            return {}
        try:
            available = free_keys(views)
            events = []
            for _ in range(32):
                try:
                    events.append(self.jelly_events.get_nowait())
                except queue.Empty:
                    break
            self.jelly.update(now, available, views, events)
            self.status["jelly_life"] = {
                "mood": self.jelly.mind.mood,
                "action": self.jelly.state,
                "hop_style": self.jelly.active_hop,
                "needs": {k: round(v, 1) for k, v in self.jelly.mind.needs.items()},
            }
            if now - self.jelly_saved_at >= 60:
                self._save_jelly()
                self.jelly_saved_at = now
            return self.jelly.crops(available)
        except Exception:
            self._fail_jelly()
            return {}

    def press(self, key, state):
        if not state or not 0 <= key < len(self.presented):
            return
        with self.presented_lock:
            view = self.presented[key]
            if view:
                try:
                    self.presses.put_nowait(dict(view))
                except queue.Full:
                    LOG.warning("Press queue full; dropping press")

    def run(self):
        from PIL import Image

        while not self.stop.is_set():
            try:
                if not self.mock:
                    from StreamDeck.ImageHelpers import PILHelper

                    devices = enumerate_devices()
                    serial = self.config.get("serial")
                    if serial:
                        devices = [d for d in devices if d.get("serial_number") == serial]
                    if len(devices) != 1:
                        raise RuntimeError(
                            f"Found {len(devices)} matching decks; select serial in config.json if multiple"
                        )
                    if elgato_running() and not self.config.get("allow_elgato", False):
                        raise RuntimeError(
                            "AD001: Elgato is running. Quit Stream Deck from its tray menu, then run ocdeck doctor."
                        )
                    self.deck = device_types()[devices[0]["product_id"]](WheelTransport(devices[0]))
                    self.deck.open()
                    self.registry.resize(self.deck.key_count())
                    self.presented = [None] * self.deck.key_count()
                    self.deck.set_brightness(int(self.config.get("brightness", 45)))
                    blank = PILHelper.to_native_key_format(self.deck, Image.new("RGB", (80, 80), "black"))
                    for k in range(len(self.registry.slots)):
                        self.deck.set_key_image(k, blank)
                    self.deck.set_key_callback(lambda deck, key, state: self.press(key, state))
                    self.status.update(serial=devices[0].get("serial_number"), productId=devices[0]["product_id"])
                self.status.update(online=True, error="", keys=len(self.registry.slots))
                last, native = {}, OrderedDict()
                styles = [appearance(self.config, k) for k in range(len(self.registry.slots))]
                next_probe = time.monotonic() + 2
                fps = max(1, min(30, int(self.config.get("fps", 24))))
                self._start_jelly()
                metrics = {
                    "requested_fps": fps,
                    "ticks": 0,
                    "late_frames": 0,
                    "composition_ms": 0.0,
                    "conversion_ms": 0.0,
                    "write_ms": 0.0,
                }
                metrics_start = time.monotonic()
                while not self.stop.is_set():
                    start = time.monotonic()
                    if not self.mock and start >= next_probe:
                        assert self.deck is not None
                        if not self.deck.is_open() or not self.deck.connected():
                            raise OSError("Mini disconnected")
                        next_probe = start + 2
                    views = self.registry.view()
                    if not any(v["id"] for v in views) and self.config.get("ready", True):
                        views[0] = {**views[0], "state": "ready"}
                    compose_start = time.monotonic()
                    overlays = self._jelly_frames(start, views)
                    metrics["composition_ms"] += (time.monotonic() - compose_start) * 1000
                    for k, v in enumerate(views):
                        style = styles[k]
                        phase = animation_phase(start, style, self.config.get("animations", True))
                        key = (
                            v["state"],
                            v["label"],
                            k,
                            phase if v["state"] != "off" else 0,
                            (self.deck.key_image_format()["size"][0] if self.deck else 80),
                            style,
                            harness_id(v["label"], v.get("harness", "")),
                            v.get("detail", "") if "detail" in (style.primary, style.secondary) else "",
                            v.get("pending"),
                        )
                        base_key = key
                        jelly_image = overlays.get(k)
                        # Bounded shared native cache. Bytes reflect real crop changes,
                        # so blank keys and held poses do not incur device writes.
                        if jelly_image is not None:
                            key = ("jelly", k, jelly_image.tobytes())
                        # Assignment identity must refresh even when the pixels are identical.
                        if last.get(k) == key:
                            with self.presented_lock:
                                self.presented[k] = dict(v)
                            continue
                        if not self.mock:
                            assert self.deck is not None
                            if key not in native:
                                if len(native) >= 768:
                                    native.popitem(last=False)
                                convert_start = time.monotonic()
                                if jelly_image is not None:
                                    try:
                                        native[key] = PILHelper.to_native_key_format(
                                            self.deck, jelly_image.convert("RGB")
                                        )
                                    except Exception:
                                        self._fail_jelly()
                                        overlays = {}
                                        key = base_key
                                        native[key] = PILHelper.to_native_key_format(self.deck, frame(*base_key))
                                else:
                                    native[key] = PILHelper.to_native_key_format(self.deck, frame(*base_key))
                                metrics["conversion_ms"] += (time.monotonic() - convert_start) * 1000
                            native.move_to_end(key)
                            write_start = time.monotonic()
                            self.deck.set_key_image(k, native[key])
                            metrics["write_ms"] += (time.monotonic() - write_start) * 1000
                        with self.presented_lock:
                            self.presented[k] = dict(v)
                        last[k] = key
                        self.status["frames"] += 1
                    metrics["ticks"] += 1
                    if time.monotonic() - start > 1 / fps:
                        metrics["late_frames"] += 1
                    elapsed = time.monotonic() - metrics_start
                    if elapsed >= 1:
                        ticks = metrics["ticks"]
                        self.status["render_timing"] = {
                            "requested_fps": fps,
                            "effective_loop_fps": round(ticks / elapsed, 2),
                            "late_frames": metrics["late_frames"],
                            **{
                                name: round(metrics[name] / ticks, 3)
                                for name in ("composition_ms", "conversion_ms", "write_ms")
                            },
                            "mock": self.mock,
                        }
                    self.stop.wait(max(0, 1 / fps - (time.monotonic() - start)))
            except Exception as error:
                LOG.warning(message("AD002", str(error)))
                self.status.update(online=False, error=message("AD002", str(error)))
            finally:
                if self.jelly:
                    self._save_jelly()
                    self.jelly.close()
                    self.jelly = None
                if self.deck:
                    try:
                        if self.stop.is_set():
                            from StreamDeck.ImageHelpers import PILHelper

                            blank = PILHelper.to_native_key_format(self.deck, Image.new("RGB", (80, 80), "black"))
                            for k in range(len(self.registry.slots)):
                                self.deck.set_key_image(k, blank)
                    except Exception:
                        pass
                    try:
                        self.deck.close()
                    except Exception:
                        pass
                    self.deck = None
                with self.presented_lock:
                    self.presented = [None] * len(self.registry.slots)
            self.stop.wait(2)
