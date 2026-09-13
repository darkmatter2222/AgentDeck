"""Offline coffee interlude. Scheduling and animation belong to the render thread."""

import colorsys
from functools import lru_cache
import math
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFont

SUPPORT_URL = "https://buymeacoffee.com/j6oiubzfnh"
MIN_INTERVAL, MAX_INTERVAL, DURATION = 3600, 10800, 60


def caption(image, text):
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=10 if image.width >= 80 else 9)
    draw.rounded_rectangle((4, 1, image.width - 5, 17), radius=5, fill=(9, 17, 27, 245))
    draw.text((image.width / 2, 9), text, font=font, fill=(240, 250, 255), anchor="mm")


@lru_cache(maxsize=8)
def cup(size):
    with Image.open(Path(__file__).parent / "assets/logos/buy-me-a-coffee.png") as source:
        image = source.convert("RGBA")
    image.thumbnail((round(size * 0.43), round(size * 0.57)), Image.Resampling.LANCZOS)
    return image


@lru_cache(maxsize=192)
def coffee_frame(width, height, phase):
    image = Image.new("RGBA", (width, height), (15, 21, 31, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2, 2, width - 3, height - 3), radius=11, outline=(255, 221, 0), width=2)
    icon = cup(min(width, height))
    draw.rounded_rectangle(
        (width // 2 - icon.width // 2 - 5, height - icon.height - 13, width // 2 + icon.width // 2 + 5, height - 6),
        radius=7,
        fill=(242, 247, 250),
    )
    image.alpha_composite(icon, ((width - icon.width) // 2, height - icon.height - 10))
    for strand in range(3):
        points = []
        for y in range(12):
            x = width / 2 + (strand - 1) * 9 + math.sin(y / 3 + phase * math.tau / 24 + strand) * 2
            points.append((round(x), round(height * 0.30 - y)))
        draw.line(points, fill=(200, 222, 239, 180), width=2)
    return image


def rainbow(image, phase):
    """Rotate only saturated body shades; eyes, outline and highlights stay crisp."""
    mapping = {}
    pixels = []
    for pixel in image.getdata():
        if pixel not in mapping:
            r, g, b, a = pixel
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if a and s > 0.25 and v > 0.35:
                rgb = colorsys.hsv_to_rgb(phase / 48, s, v)
                mapping[pixel] = (*[round(c * 255) for c in rgb], a)
            else:
                mapping[pixel] = pixel
        pixels.append(mapping[pixel])
    result = image.copy()
    result.putdata(pixels)
    return result


class CoffeeBreak:
    def __init__(self, now, rng=None):
        self.rng = rng or random.Random()
        self.next_at = now + self.rng.uniform(MIN_INTERVAL, MAX_INTERVAL)
        self.key = self.jelly_key = None
        self.until = 0.0
        self.serial = 0

    def finish(self, now):
        self.key = self.jelly_key = None
        self.until = 0.0
        self.next_at = now + self.rng.uniform(MIN_INTERVAL, MAX_INTERVAL)

    def update(self, now, available, jelly, blocked=False):
        if self.key is not None:
            if blocked or now >= self.until or not {self.key, self.jelly_key} <= available:
                self.finish(now)
                if jelly.current in available:
                    jelly.settle(jelly.current, now)
                return
        elif not blocked and now >= self.next_at and len(available) >= 2 and jelly.state != "hop":
            self.jelly_key = jelly.current if jelly.current in available else min(available)
            self.key = self.rng.choice(sorted(available - {self.jelly_key}))
            self.until = now + DURATION
            self.serial += 1
            jelly.settle(self.jelly_key, now)
        if self.key is not None:
            # Keep the pair fixed even when the two keys are not adjacent.
            jelly.deadline = self.until + 1
            jelly.thoughts.clear()

    def decorate(self, now, jelly, frames):
        if self.key is None:
            return frames
        if jelly.current in frames:
            image = frames[jelly.current]
            if jelly.options["coffee_rainbow"]:
                image = rainbow(image, int(now * 8) % 48)
            caption(image, jelly.touch_text if now < jelly.touch_until else "Coffee?")
            frames[jelly.current] = image
        g = jelly.geometry
        frames[self.key] = coffee_frame(g.width, g.height, int(now * 12) % 24).copy()
        return frames
