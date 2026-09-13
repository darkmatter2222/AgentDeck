"""Original pixel-blob silhouette, with native-pixel inbetweens and tiny pseudopods."""

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
    # Draw crisp pixels at output resolution: half-sized pixels on an 80px key.
    # Smoothness comes from time-based shape inbetweens, never a blur filter.
    unit = size / 40
    s = unit
    im = Image.new("RGBA", (size, size))
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
    if motion == "sway":
        lean += math.sin(progress * math.tau * 2) * 0.8
    if motion == "chew":
        w += pulse * 0.9
    if motion == "stretch":
        h += math.sin(progress * math.pi) * 4
    if motion == "duck":
        h -= math.sin(progress * math.pi) * 5
    cx, base = 20 + lean * 0.4, 34 - 1 / unit
    if motion == "bounce":
        base -= abs(pulse) * 4
    old, new = bytes.fromhex(MOOD_COLORS[previous]), bytes.fromhex(MOOD_COLORS[mood])
    tint = tuple(round(a + (b - a) * blend) for a, b in zip(old, new))
    # Keep the familiar turquoise identity; moods gently tint rather than replace it.
    color = tuple(round(a * 0.7 + b * 0.3) for a, b in zip((64, 190, 192), tint))
    if trick == "rainbow":
        import colorsys

        color = tuple(round(v * 255) for v in colorsys.hsv_to_rgb((now * 0.2) % 1, 0.48, 0.95))
    shade = tuple(round(v * 0.66) for v in color)
    light = tuple(round(v + (255 - v) * 0.55) for v in color)
    left, right, top = 20 - w / 2, 20 + w / 2 - 0.5, base - h + 1
    crown = 20 + lean
    outline, ink, shine = "#193849", "#122b3e", "#dbfff1"

    def polygon(points, fill, edge=None):
        d.polygon(
            [(round(x * s), round(y * s)) for x, y in points], fill=fill, outline=edge, width=max(1, round(0.75 * s))
        )

    # A tiny tapered lobe grows out of the flank only when gesturing.
    # No permanent ears, detached hands, long bones or angular elbows.
    wave = bool(gesture) or motion == "wave"
    if wave:
        lift = 1.5 + math.sin(now * 6) * 1.2
        sides = (-1, 1) if gesture in ("cheer", "clap") else (1,)
        for side in sides:
            root = right - 1 if side == 1 else left + 1
            ay = base - 5
            tipx, tipy = root + side * 3, ay - lift - 1
            ellipse((min(root, tipx) - 1, tipy - 1, max(root, tipx) + 1, ay + 2), outline)
            ellipse((min(root, tipx) - 0.4, tipy - 0.4, max(root, tipx) + 0.4, ay + 1.3), color)

    # Preserve the original broad floor, stepped shoulders and flattened crown.
    polygon(
        [
            (left, base - 3),
            (left + 1, top + h / 2),
            (left + 4, top + 3),
            (crown - 5, top),
            (crown + 4, top),
            (right - 3, top + 3),
            (right - 1, top + h / 2),
            (right, base - 2),
            (right - 2, base),
            (left + 2, base),
        ],
        color,
        outline,
    )
    line([(left + 2, base - 4), (left + 4, base - 2), (right - 3, base - 2), (right - 1, base - 4)], shade, 1.5)
    line([(left + 4, top + h / 2), (left + 5, top + 5), (crown - 4, top + 2), (crown + 2, top + 2)], light, 1.5)
    line([(crown - 4, top + 3), (crown - 1, top + 3)], shine, 0.5)

    # Original square eyes and little smile, slightly finer than the 40px art.
    fy = min(base - 5, top + max(3, h * 0.5))
    fy += {"up": -1, "down": 1}.get(gaze, 0)
    dx = {"left": -0.5, "right": 0.5}.get(gaze, 0)

    def rect(box, fill):
        d.rectangle(tuple(round(v * s) for v in box), fill=fill)

    blink = now % 4.7 < 0.12
    for ex in (cx - 4.5, cx + 4):
        if face in ("closed", "sleepy") or blink:
            line([(ex - 1, fy + 1), (ex + 1.5, fy + 1)], ink, 0.75)
        else:
            eh = 1 if face == "half" else 3
            rect((ex - 1.5, fy - 0.5, ex + 1.8, fy + eh), shine)
            rect((ex - 0.5 + dx, fy, ex + 0.8 + dx, fy + eh - 0.5), ink)
    my = min(base - 3, fy + 5)
    if face in ("jump", "surprised"):
        rect((cx - 0.75, my - 1, cx + 0.75, my + 0.5), ink)
    else:
        line([(cx - 1.8, my - 1), (cx - 0.8, my), (cx + 0.8, my), (cx + 1.8, my - 1)], ink, 0.75)
    if face in ("happy", "landing") or trick in ("hello", "love", "shy_hide"):
        line([(cx - 7, fy + 4), (cx - 5.5, fy + 4)], "#f1a5c0", 0.5)
        line([(cx + 5.5, fy + 4), (cx + 7, fy + 4)], "#f1a5c0", 0.5)
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
    im.paste((0, 0, 0, 0), (0, round(34 * unit), size, size))
    return im
