"""Render the real button loop without hardware or opening a browser."""

from pathlib import Path
import queue
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFont
from ocdeck.art import frame
from ocdeck.appearance import Appearance
from ocdeck.device import DeviceLoop
from ocdeck.model import Registry


def main():
    registry = Registry(lambda _: True)
    loop = DeviceLoop(registry, queue.Queue(), threading.Event(),
                      {"jelly": {"needs": False, "thoughts": "off"}}, mock=True)
    loop._start_jelly()
    loop.jelly.settle(3, 0)
    loop.jelly.deadline = 50
    loop.coffee.next_at = 3
    views = registry.view()
    for key in (0, 1, 2, 4):
        views[key] = {**views[key], "id": str(key), "state": "running", "label": "Agent"}
    frames = []
    font = ImageFont.load_default(size=25)
    small = ImageFont.load_default(size=15)
    for i in range(135):
        now = i / 15
        if i == 15:
            loop.press(3, True)
        if i == 105:
            loop.press(loop.coffee.key, True)
        tiles = loop._jelly_frames(now, views)
        for key, view in enumerate(views):
            loop.presented[key] = loop._presented_view(key, view)
        image = Image.new("RGB", (760, 360), "#080d18")
        draw = ImageDraw.Draw(image)
        draw.text((30, 55), "A little coffee break.", font=font, fill="#eaf6ff")
        text = "Tap Jelly. Get a reaction." if now < 3 else "Two free keys. One invitation." if now < 7 else "Tap coffee. Back to coding."
        draw.text((30, 105), text, font=small, fill="#91decf")
        draw.text((30, 220), "Every 1-3 hours · 60 seconds", font=small, fill="#bac8d7")
        draw.text((30, 250), "Agent buttons always come first.", font=small, fill="#bac8d7")
        draw.text((30, 320), "Runtime preview · timing compressed", font=ImageFont.load_default(size=11), fill="#6d849c")
        draw.rounded_rectangle((385, 28, 739, 332), radius=25, fill="#18222f", outline="#35475c", width=2)
        draw.text((562, 45), "STREAM DECK", font=small, fill="#9db0c3", anchor="mm")
        for key in range(6):
            x, y = 403 + (key % 3) * 110, 78 + (key // 3) * 118
            if key in tiles:
                tile = tiles[key].convert("RGB")
            elif views[key]["id"]:
                tile = frame("running", ("API", "WEB", "TEST", "", "CLI")[key], key, i % 96,
                             style=Appearance(layout="harness"), harness=("opencode", "claude", "gemini", "", "cursor")[key])
            else:
                tile = Image.new("RGB", (80, 80))
            image.paste(tile.resize((96, 96), Image.Resampling.NEAREST), (x, y))
        frames.append(image)
    out = Path('docs/jelly/coffee_break.gif')
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=67, loop=0, optimize=True)
    frames[70].save('/tmp/coffee-preview.png')
    print(out)


if __name__ == '__main__':
    main()
