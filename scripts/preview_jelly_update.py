"""Preview the actual update tiles at supported native key sizes."""
from pathlib import Path
import queue
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFont
from ocdeck.device import DeviceLoop
from ocdeck.jelly import DeckGeometry, Jelly
from ocdeck.model import Registry


def main():
    loops = []
    for size in (72, 80, 96):
        loop = DeviceLoop(Registry(lambda _: True), queue.Queue(), threading.Event(), {}, mock=True)
        loop._start_jelly()
        loop.jelly = Jelly(DeckGeometry(width=size, height=size), seed=7)
        loop.jelly.settle(0, 0)
        loop._jelly_update_info = {"version": "99.0.0"}
        loops.append(loop)
    frames = []
    for index in range(72):
        image = Image.new("RGB", (600, 280), "#080d18")
        draw = ImageDraw.Draw(image)
        draw.text((300, 25), "A calmer way to say: update available.",
                  font=ImageFont.load_default(size=19), anchor="mm", fill="#e8f5ff")
        for i, loop in enumerate(loops):
            tile = loop._jelly_frames(index / 12, loop.registry.view())[0]
            tile = tile.resize((160, 160), Image.Resampling.NEAREST).convert("RGB")
            image.paste(tile, (30 + i * 190, 65))
            draw.text((110 + i * 190, 246), f"{loop.jelly.geometry.width}px key",
                      font=ImageFont.load_default(size=13), anchor="mm", fill="#95acbf")
        frames.append(image)
    frames[0].save("docs/jelly/update_available.gif", save_all=True, append_images=frames[1:],
                   duration=83, loop=0, optimize=True)
    frames[10].save("/tmp/jelly-update-preview.png")


if __name__ == "__main__":
    main()
