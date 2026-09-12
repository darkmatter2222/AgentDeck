"""Manual six-key diagnostic with actual USB events, isolated from the broker."""

import json
import queue
import time
from PIL import Image, ImageDraw, ImageFont
from .broker import InstanceLock
from .common import home, read_json, atomic_json
from .device import enumerate_devices, device_types, elgato_running, WheelTransport


def run():
    from StreamDeck.ImageHelpers import PILHelper

    root = home()
    root.mkdir(parents=True, exist_ok=True)
    with InstanceLock(root):
        if elgato_running():
            raise RuntimeError("Quit Elgato Stream Deck, then run ocdeck doctor")
        devices = enumerate_devices()
        serial = read_json(root / "config.json", {}).get("serial")
        if serial:
            devices = [d for d in devices if d.get("serial_number") == serial]
        if len(devices) != 1:
            raise RuntimeError("Expected one deck; select a serial in config.json")
        deck = device_types()[devices[0]["product_id"]](WheelTransport(devices[0]))
        count = deck.key_count()
        presses = queue.Queue()
        observed = []
        try:
            deck.open()
            deck.set_brightness(45)
            for key in range(count):
                im = Image.new("RGB", (80, 80), "#123b5c")
                ImageDraw.Draw(im).text(
                    (40, 40), str(key + 1), font=ImageFont.load_default(size=36), fill="white", anchor="mm"
                )
                deck.set_key_image(key, PILHelper.to_native_key_format(deck, im))
            deck.set_key_callback(lambda d, k, pressed: presses.put(k + 1) if pressed else None)
            print(f"{count} numbered images submitted. Confirm physical key order.")
            print(f"Press physical keys 1 through {count} in order within 60 seconds.")
            deadline = time.monotonic() + 60
            while len(observed) < count and time.monotonic() < deadline:
                try:
                    key = presses.get(timeout=min(1, max(0.01, deadline - time.monotonic())))
                    observed.append(key)
                    print(f"Physical key-down received: {key}", flush=True)
                except queue.Empty:
                    pass
            result = {
                "time": time.time(),
                "serial": devices[0].get("serial_number"),
                "physicalKeys": observed,
                "keyOrderPass": observed == list(range(1, count + 1)),
                "displayVisuallyConfirmed": False,
                "note": "Display appearance requires human confirmation; API writes are not camera evidence.",
            }
            atomic_json(root / "hardware-check.json", result)
            print(json.dumps(result, indent=2))
        finally:
            try:
                blank = PILHelper.to_native_key_format(deck, Image.new("RGB", (80, 80), "black"))
                for key in range(count):
                    deck.set_key_image(key, blank)
            finally:
                deck.close()
