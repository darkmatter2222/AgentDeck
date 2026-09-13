"""Curated offline thoughts, bounded repetition history and a clean one-pass marquee."""

from collections import deque
from functools import lru_cache
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Metadata is per category, so every authored line inherits contextual constraints.
CATEGORY_EVENTS = {
    "running": "running",
    "input": "input",
    "success": "success",
    "failure": "failure",
    "concern": "unknown",
    "resolved": "resolved",
    "greetings": "arrival",
    "departures": "departure",
    "reconnected": "reconnected",
}


@lru_cache(maxsize=1)
def vocabulary():
    value = json.loads((Path(__file__).parent / "assets/jelly/thoughts.json").read_text(encoding="utf-8"))
    lines = [line for group in value.values() for line in group]
    if len(lines) < 1000 or len(set(lines)) != len(lines):
        raise ValueError("Jelly vocabulary must contain 1000+ distinct authored lines")
    if any(not isinstance(s, str) or not s.isascii() or not 1 <= len(s) <= 52 for s in lines):
        raise ValueError("Invalid Jelly thought")
    return value


def _font_size(scale):
    # Match the small clean Pillow UI font used by agent status labels. Render at
    # final device resolution instead of enlarging a tiny bitmap with NEAREST.
    return 7 if scale <= 1 else 9


@lru_cache(maxsize=256)
def text_bitmap(text, scale=2):
    font = ImageFont.load_default(size=_font_size(scale))
    box = font.getbbox(text)
    width = max(1, int(box[2] - box[0]))
    height = max(1, int(box[3] - box[1]))
    # L-mode keeps Pillow's antialiasing. This is intentionally not a 1-bit mask.
    image = Image.new("L", (width, height), 0)
    ImageDraw.Draw(image).text((-box[0], -box[1]), text, font=font, fill=255)
    return image


class Thoughts:
    def __init__(self, rng, frequency="normal"):
        self.rng = rng
        self.frequency = frequency
        self.recent = deque(maxlen=128)
        self.text = ""
        self.category = ""
        self.started = 0.0
        self.until = 0.0
        self.next_at = 20.0

    def clear(self):
        self.text = ""
        self.until = 0.0

    def say(self, category, now, width=80, scale=2, event=False):
        if self.frequency == "off" or now < self.next_at or self.text and now < self.until:
            return False
        lines = vocabulary()[category]
        choices = [(f"{category}:{i}", line) for i, line in enumerate(lines) if f"{category}:{i}" not in self.recent]
        if not choices:
            oldest = next(token for token in self.recent if token.startswith(category + ":"))
            choices = [(oldest, lines[int(oldest.split(":")[1])])]
        token, self.text = self.rng.choice(choices)
        self.recent.append(token)
        self.category, self.started = category, now
        pixels = text_bitmap(self.text, scale).width
        self.until = now + 3.5 + max(0, pixels - width + 8) / 24
        interval = {"quiet": 90, "normal": 35, "chatty": 15}[self.frequency]
        self.next_at = max(self.until + 3, now + (max(12, interval / 2) if event else interval))
        return True

    def active(self, now):
        return bool(self.text) and now < self.until

    def render(self, width, scale, now):
        strip_height = 9 * scale
        strip = Image.new("RGBA", (width, strip_height), (9, 17, 27, 235))
        mask = text_bitmap(self.text, scale)
        overflow = max(0, mask.width - width + 8)
        offset = min(overflow, max(0, int((now - self.started - 1.5) * 24)))
        y = max(0, (strip_height - mask.height) // 2)
        strip.paste((230, 249, 247, 255), (4 - offset, y), mask)
        return strip
