"""Curated offline thoughts, bounded repetition history and a crisp one-pass marquee."""

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


@lru_cache(maxsize=128)
def text_bitmap(text, scale=2):
    # Same Pillow sans family as agent labels, drawn directly at native size.
    font = ImageFont.load_default(size=max(10, 6 * scale))
    box = font.getbbox(text)
    im = Image.new("L", (max(1, int(box[2] - box[0])), max(1, int(box[3] - box[1]))))
    ImageDraw.Draw(im).text((-box[0], -box[1]), text, font=font, fill=255)
    return im


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
        self.until = now + 3.5 + (max(0, pixels - width / 2) / 24 if pixels > width - 8 else 0)
        interval = {"quiet": 90, "normal": 35, "chatty": 15}[self.frequency]
        self.next_at = max(self.until + 3, now + (max(12, interval / 2) if event else interval))
        return True

    def active(self, now):
        return bool(self.text) and now < self.until

    def show(self, text, now, width=80, scale=2):
        self.text, self.category, self.started = text, "interaction", now
        self.until = now + 3.2

    def render(self, width, scale, now):
        mask = text_bitmap(self.text, scale)
        strip = Image.new("RGBA", (width, max(14, 9 * scale)), (9, 17, 27, 255))
        if mask.width <= width - 8:
            x = (width - mask.width) // 2
        else:
            # Let the final character reach the midpoint, then hold for two seconds.
            travel = max(0, mask.width - width / 2)
            offset = min(travel, max(0, (now - self.started - 1.5) * 24))
            x = round(4 - offset)
        strip.paste((230, 249, 247, 255), (x, (strip.height - mask.height) // 2), mask)
        return strip
