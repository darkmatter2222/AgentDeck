"""Supersampled, continuously deforming Jelly and pocket-sized play props."""

import math
from PIL import Image, ImageDraw
from .jelly_art import MOOD_COLORS

# label, motion, prop: each is selectable through touch and spontaneous play.
TRICKS = {
    "hello": ("Hi!", "wave", "heart"),
    "kiss": ("Mwah", "wave", "heart"),
    "tickle": ("Hehe", "wiggle", "stars"),
    "rainbow": ("Wow", "wiggle", "rainbow"),
    "cookie": ("Yum", "chew", "cookie"),
    "pizza": ("Pizza", "chew", "pizza"),
    "bagel": ("Bagel", "chew", "bagel"),
    "donut": ("Donut", "chew", "donut"),
    "pogo": ("Boing", "bounce", "pogo"),
    "bubbles": ("Pop", "wave", "bubbles"),
    "juggle": ("Ta-da", "wave", "orbs"),
    "stargaze": ("Dream", "sway", "stars"),
    "confetti": ("Yay!", "bounce", "confetti"),
    "love": ("Love", "sway", "heart"),
    "magic": ("Magic", "wave", "stars"),
    "rain": ("Cozy", "sway", "rain"),
    "sunshine": ("Sunny", "sway", "sun"),
    "peekaboo": ("Boo!", "duck", "none"),
    "meditate": ("Zen", "sway", "orbs"),
    "disco": ("Groove", "wiggle", "confetti"),
    "stretchy": ("Stretch", "stretch", "none"),
    "sneeze": ("Achoo", "duck", "stars"),
    "proud_sign": ("Nice!", "wave", "sign"),
    "break_sign": ("Break", "sway", "sign"),
    "thanks": ("Thanks", "wave", "heart"),
    "rocket": ("Zoom", "bounce", "confetti"),
    "shy_hide": ("Oh hi", "duck", "heart"),
    "balance": ("Steady", "sway", "orb"),
}
FOODS = ("cookie", "pizza", "bagel", "donut")


def render(dimensions, size, now, face, gaze, gesture, mirror, mood, previous, blend, trick="", progress=0.0):
    # Draw at 3x native resolution, then filter once. Geometry is in logical units.
    unit = size / 40
    s = unit * 3
    im = Image.new("RGBA", (size * 3, size * 3))
    d = ImageDraw.Draw(im)

    def ellipse(box, fill):
        d.ellipse(tuple(round(v * s) for v in box), fill=fill)

    def line(points, fill, width=1.0):
        d.line([(round(x * s), round(y * s)) for x, y in points], fill=fill, width=max(1, round(width * s)))

    w, h, lean = dimensions
    breath = math.sin(now * 2.7)
    h += breath * 0.45
    w -= breath * 0.4
    motion, prop = TRICKS.get(trick, ("", "", ""))[1:]
    pulse = math.sin(progress * math.pi * 6)
    if motion == "wiggle":
        lean += pulse * 1.8
    if motion == "chew":
        w += pulse * 0.9
    if motion == "stretch":
        h += math.sin(progress * math.pi) * 4
    if motion == "duck":
        h -= math.sin(progress * math.pi) * 5
    cx, base = 20 + lean * 0.45, 33.5
    if motion == "bounce":
        base -= abs(pulse) * 4
    old, new = bytes.fromhex(MOOD_COLORS[previous]), bytes.fromhex(MOOD_COLORS[mood])
    color = tuple(round(a + (b - a) * blend) for a, b in zip(old, new))
    if trick == "rainbow":
        import colorsys

        color = tuple(round(v * 255) for v in colorsys.hsv_to_rgb((now * 0.2) % 1, 0.48, 0.95))
    shade = tuple(round(v * 0.66) for v in color)
    light = tuple(round(v + (255 - v) * 0.55) for v in color)
    left, right, top = cx - w / 2, cx + w / 2, base - h
    # Rounded domed body with a broad, floor-anchored jelly skirt.
    ellipse((left, top, right, base), "#193849")
    ellipse((left + 0.6, top + 0.6, right - 0.6, base - 0.5), color)
    ellipse((left + 2, base - 3, right - 2, base - 0.6), shade)
    ellipse((left + 3, top + 2, left + 7, top + 4), light)
    # Small rounded lobes merge with the body; no stick elbows.
    wave = gesture or motion == "wave"
    for side in (-1, 1):
        lift = (1 + math.sin(now * 7)) * 1.2 if wave and side == 1 else 0.3 * math.sin(now * 3 + side)
        ax = cx + side * (w / 2 - 1)
        ay = top + h * 0.65 - lift
        ellipse((ax - 2.4, ay - 2, ax + 2.4, ay + 2.3), shade)
        ellipse((ax - 1.9, ay - 1.7, ax + 1.9, ay + 1.7), color)
    fy = top + h * 0.52
    dx = {"left": -0.6, "right": 0.6}.get(gaze, 0)
    for ex in (cx - 4, cx + 4):
        if face in ("closed", "sleepy", "half") or now % 4.7 < 0.13:
            line([(ex - 1, fy), (ex + 1, fy)], "#122b3e", 0.7)
        else:
            ellipse((ex - 1.25, fy - 1.7, ex + 1.25, fy + 1.5), "#eafff8")
            ellipse((ex - 0.65 + dx, fy - 1.1, ex + 0.65 + dx, fy + 1.2), "#122b3e")
    line([(cx - 1.4, fy + 3), (cx, fy + 3.7), (cx + 1.4, fy + 3)], "#122b3e", 0.65)
    if prop in FOODS:
        px, py = cx + 4, base - 4 + abs(pulse) * 0.5
        if prop == "pizza":
            d.polygon(
                [(int(x * s), int(y * s)) for x, y in [(px - 4, py - 5), (px + 4, py - 5), (px, py + 2)]],
                fill="#ffd278",
            )
            ellipse((px - 1, py - 4, px + 1, py - 2), "#db5a55")
        else:
            ellipse((px - 4, py - 5, px + 4, py + 2), "#e6ad68" if prop != "donut" else "#f4a9c9")
            if prop in ("bagel", "donut"):
                ellipse((px - 1.4, py - 3, px + 1.4, py - 0.5), color)
            else:
                for ox, oy in [(-2, -3), (1, -2), (0, 0)]:
                    ellipse((px + ox - 0.5, py + oy - 0.5, px + ox + 0.5, py + oy + 0.5), "#694530")
    elif prop == "pogo":
        line([(cx, base - 1), (cx, 34)], "#d7e9f2", 1.5)
        line([(cx - 3, 34), (cx + 3, 34)], "#f1a5c0", 1)
    elif prop != "none" and prop:
        for i in range(5):
            angle = now * 1.5 + i * math.tau / 5
            px, py = 20 + math.cos(angle) * 14, max(4, top - 3) + math.sin(angle) * 2
            c = ("#f1a5c0", "#83e6d4", "#ffe095")[i % 3]
            if prop in ("heart", "sign"):
                line([(px - 1, py), (px, py + 1), (px + 1, py)], c, 1)
            elif prop == "rain":
                line([(px, py), (px - 1, py + 2)], c, 0.6)
            else:
                ellipse((px - 1, py - 1, px + 1, py + 1), c)
    if mirror:
        im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    out = im.resize((size, size), Image.Resampling.LANCZOS)
    # Filtering must never put stray alpha below the floor contact anchor.
    out.paste((0, 0, 0, 0), (0, round(34 * unit), size, size))
    return out
