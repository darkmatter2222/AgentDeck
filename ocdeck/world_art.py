"""World costume overlays and atmosphere, kept separate from Jelly body art."""

import math
from PIL import ImageDraw
from .world_props import prop, cloud, leaf, wave, INK, WHITE, GOLD, PINK, GREEN, BLUE


def costume(image, name, phase, head):
    """Draw on a logical 40px sprite; preserve eyes and floor-contact anatomy."""
    if not name:
        return image
    im = image.copy()
    d = ImageDraw.Draw(im)
    y = max(4, head)
    sway = wave(phase)
    if name in ("santa", "elf", "party", "witch", "nightcap"):
        color = {"santa": PINK, "elf": GREEN, "party": GOLD, "witch": "#8055b9", "nightcap": BLUE}[name]
        if name == "party":
            d.polygon([(13, y), (20, y - 11), (27, y)], fill=color, outline=INK)
            for x, h in ((17, -2), (21, -5), (23, -1)):
                d.point((x, y + h), fill=PINK)
            d.line((20, y - 12, 20 + sway, y - 14), fill=PINK)
        elif name == "witch":
            d.polygon([(12, y), (17, y - 10), (23, y - 11), (22, y - 7), (28, y)], fill=color, outline=INK)
            d.line((8, y + 1, 32, y + 1), fill=INK, width=2)
            d.line((13, y - 1, 27, y - 1), fill="#bd8c50", width=2)
            d.rectangle((19, y - 2, 22, y), outline=GOLD)
        else:
            d.polygon(
                [
                    (11, y),
                    (17, y - 9),
                    (23, y - 10),
                    (28, y - 6),
                    (29 + sway, y - 2),
                    (25 + sway, y - 3),
                    (22, y - 6),
                    (27, y),
                ],
                fill=color,
                outline=INK,
            )
            d.line([(13, y - 2), (18, y - 7), (21, y - 8)], fill=WHITE if name == "santa" else "#a7d4d2")
            d.ellipse((27 + sway, y - 3, 30 + sway, y), fill=WHITE if name != "elf" else GOLD)
            d.line((10, y, 28, y), fill=WHITE if name == "santa" else GOLD, width=2)
            if name == "nightcap":
                d.point((19, y - 4), fill=WHITE)
    elif name in ("beanie", "sunhat", "gardener"):
        if name == "beanie":
            d.pieslice((11, y - 9, 29, y + 7), 180, 360, fill=PINK, outline=INK)
            for x in (15, 19, 23, 27):
                d.line((x, y - 4, x, y - 1), fill="#c76580")
            d.line((11, y, 29, y), fill="#f5c5cd", width=3)
            d.ellipse((18 + sway, y - 11, 22 + sway, y - 7), fill="#f5c5cd")
        else:
            d.pieslice((12, y - 7, 28, y + 5), 180, 360, fill="#d2af71", outline=INK)
            d.line((13, y - 1, 27, y - 1), fill=GREEN if name == "gardener" else PINK, width=2)
            d.line((7, y + 1, 33, y + 1), fill=GOLD, width=2)
            d.line((10, y + 2, 30, y + 2), fill="#a78453")
    elif name == "bunny":
        d.ellipse((12, y - 12, 17, y + 1), fill=WHITE)
        d.ellipse((23, y - 12, 28, y + 1), fill=WHITE)
        d.line((14, y - 9, 14, y - 2), fill=PINK)
        d.line((25, y - 9, 25, y - 2), fill=PINK)
        d.line((12, y - 4, 12, y - 1), fill="#8eacb9")
    elif name == "ghost":
        # A translucent sheet with cutout eyes; hover is applied in the controller.
        d.polygon(
            [
                (8, 32),
                (10, y + 3),
                (16, y - 2),
                (24, y - 2),
                (30, y + 3),
                (33, 32),
                (28, 29),
                (24, 33),
                (20, 30),
                (15, 33),
            ],
            fill="#d5eee8",
        )
        d.ellipse((15, y + 6, 18, y + 10), fill=INK)
        d.ellipse((23, y + 6, 26, y + 10), fill=INK)
        d.line([(11, y + 10), (10, 29), (13, 30)], fill="#9ebdc5")
        d.line([(28, y + 11), (30, 28), (28, 29)], fill="#9ebdc5")
    elif name == "skeleton":
        d.line((20, 25, 20, 32), fill=WHITE)
        for h in (26, 29):
            d.line([(14, h), (17, h + 1), (23, h + 1), (26, h)], fill=WHITE)
    elif name == "reaper":
        d.line([(8, 29), (10, y + 2), (20, y - 4), (30, y + 2), (32, 29)], fill="#8055b9", width=4)
    elif name in ("mask", "shades"):
        d.rectangle((12, y + 7, 28, y + 10), fill="#8055b9" if name == "mask" else INK)
        d.point((15, y + 8), fill=WHITE)
        d.point((24, y + 8), fill=WHITE)
        d.line((13, y + 7, 15, y + 7), fill="#91b6c8")
        d.line((23, y + 7, 25, y + 7), fill="#91b6c8")
    elif name == "scarf":
        d.line((10, 28, 30, 28), fill=PINK, width=3)
        d.line((28, 28, 30 + sway, 33), fill=PINK, width=2)
        d.line((12, 27, 27, 27), fill="#ffc1cb")
        d.point((30 + sway, 34), fill=GOLD)
    elif name == "bow":
        d.polygon([(12, y), (18, y + 3), (12, y + 6), (24, y), (18, y + 3), (24, y + 6)], fill=PINK, outline="#a55c79")
        d.rectangle((17, y + 2, 19, y + 4), fill="#ffc1cb")
    elif name == "sweat":
        drop_y = y + 4 + phase % 4
        d.polygon([(30, drop_y), (28, drop_y + 3), (30, drop_y + 5), (32, drop_y + 3)], fill=BLUE)
        d.point((29, drop_y + 3), fill=WHITE)
    elif name == "umbrella":
        d.pieslice((5, 0, 35, 20), 180, 360, fill="#c4a7ff", outline=INK)
        d.line((20, 9, 20, y + 2), fill=WHITE)
        d.arc((11, 0, 29, 20), 180, 360, fill="#ebe2ff")
        d.line((20, 1, 20, 9), fill="#ebe2ff")
        d.line((6, 9, 34, 9), fill="#826eae")
    elif name == "boots":
        d.rectangle((9, 31, 16, 34), fill=GOLD)
        d.rectangle((24, 31, 31, 34), fill=GOLD)
        d.line((9, 34, 16, 34), fill=INK)
        d.line((24, 34, 31, 34), fill=INK)
        d.point((11, 32), fill=WHITE)
        d.point((26, 32), fill=WHITE)
    else:
        raise ValueError("Missing world costume: " + name)
    return im


def sky(draw, kind, width, height, phase, color, density=1):
    """Sparse atmosphere in continuous deck coordinates; never an opaque backdrop.

    Static stars twinkle, leaves tumble, balloons rise, rain falls. Separate depth
    bands keep large motifs in the sky and fog near the ground, behind the actor.
    """
    p = phase
    count = max(3, width * height // (360 if kind in ("rain", "snow") else 1100)) * density
    if kind in (
        "rain",
        "snow",
        "confetti",
        "petals",
        "leaves",
        "fireflies",
        "butterflies",
        "hearts",
        "stars",
        "balloons",
    ):
        if kind in ("leaves", "butterflies", "balloons", "hearts"):
            count = max(2, width * height // 2600) * density
        for i in range(count):
            drift = wave(p // 3 + i)
            x = (i * 47 + (p // 3 if kind not in ("stars", "fireflies") else 0)) % (width + 12) - 6
            y = (i * 31 + p * (2 if kind == "rain" else 1)) % (height + 16) - 8
            c = (PINK, GOLD, BLUE, GREEN)[i % 4]
            if kind == "rain":
                draw.line((x, y, x - 1, y + 3 + i % 2), fill=BLUE if i % 3 else "#406583")
                if y > height - 6:
                    draw.line((x - 2, height - 3, x + 2, height - 3), fill="#638b9b")
            elif kind == "snow":
                x += drift
                draw.point((x, y), fill=WHITE)
                if i % 5 == 0:
                    draw.line((x - 1, y, x + 1, y), fill="#91b6c8")
                    draw.line((x, y - 1, x, y + 1), fill=WHITE)
            elif kind == "stars":
                # Fixed coordinates are essential: a starfield must not look like rain.
                x, y = (i * 47 + 9) % width, (i * 29 + 6) % max(1, height - 10)
                bright = (p // 2 + i * 3) % 12 < 3
                draw.point((x, y), fill=GOLD if bright else "#61788e")
                if bright and i % 4 == 0:
                    draw.line((x - 1, y, x + 1, y), fill=GOLD)
                    draw.line((x, y - 1, x, y + 1), fill=WHITE)
            elif kind == "fireflies":
                x = (i * 47 + round(3 * math.sin(p / 9 + i))) % width
                y = (i * 29 + round(2 * math.cos(p / 11 + i))) % height
                bright = (p + i * 3) % 16 < 6
                draw.point((x, y), fill=GOLD if bright else "#486649")
                if bright:
                    draw.point((x + 1, y), fill="#9baf65")
            elif kind == "leaves":
                leaf(draw, x + drift, y, ("#cb7945", "#dba351", "#b7593e")[i % 3], drift)
            elif kind == "butterflies":
                x += round(4 * math.sin(p / 6 + i))
                y = (i * 31 + round(5 * math.sin(p / 9 + i))) % max(1, height - 10)
                wing = (3, 2, 1, 2)[(p + i) % 4]
                draw.ellipse((x - wing, y - 2, x - 1, y + 1), fill=color)
                draw.ellipse((x + 1, y - 2, x + wing, y + 1), fill=GOLD)
                draw.line((x, y - 2, x, y + 2), fill="#526b85")
                draw.point((x - 1, y - 3), fill=WHITE)
            elif kind == "balloons":
                y = (i * 31 - p // 2) % (height + 20) - 10
                draw.ellipse((x - 3, y - 5, x + 3, y + 3), fill=c, outline=INK)
                draw.point((x - 1, y - 3), fill=WHITE)
                draw.line([(x, y + 4), (x + drift, y + 7), (x, y + 9)], fill="#71899a")
            elif kind == "hearts":
                y = (i * 31 - p // 2) % (height + 10) - 5
                draw.polygon(
                    [
                        (x, y + 3),
                        (x - 3, y),
                        (x - 3, y - 2),
                        (x - 1, y - 3),
                        (x, y - 1),
                        (x + 1, y - 3),
                        (x + 3, y - 2),
                        (x + 3, y),
                    ],
                    fill=PINK,
                )
                draw.point((x - 2, y - 1), fill="#ffd1d5")
            elif kind == "petals":
                draw.polygon(
                    [(x + drift, y - 1), (x + 3 + drift, y), (x + 2 + drift, y + 2), (x + drift, y + 2)], fill="#d795b0"
                )
                draw.point((x + drift, y), fill="#f4c5d6")
            else:
                draw.line((x, y, x + (2 if (p + i) % 4 < 2 else 0), y + 1), fill=c)
    elif kind == "clouds":
        for i in range(max(2, width // 65)):
            x = (i * 67 + p // 3) % (width + 40) - 20
            cloud(draw, x, 14 + i % 2 * 8)
    elif kind == "fog":
        for i in range(3):
            x = (i * 73 + p // 3) % (width + 60) - 30
            y = height - 9 - i * 6
            draw.line(
                [(x, y), (x + 10, y - 2), (x + 29, y - 2), (x + 42, y)],
                fill=("#314758", "#293b4d", "#233345")[i],
                width=2,
            )
    elif kind == "smoke":
        # Small rising curls, not four solid clouds covering the screen.
        for i in range(max(2, width // 55)):
            age = (p + i * 7) % 28
            x = (i * 59 + 25) % width + round(3 * math.sin(age / 5))
            y = height - 12 - age
            draw.arc(
                (x - 3 - age // 9, y - 3, x + 3 + age // 9, y + 3), 160, 330, fill="#647186" if age < 18 else "#354653"
            )
    elif kind in ("lights", "lanterns", "icicles"):
        for y in range(3, height, 48):
            for x in range(0, width, 24):
                draw.line([(x, y), (x + 6, y + 2), (x + 12, y + 3), (x + 18, y + 2), (x + 24, y)], fill="#43536a")
                if kind == "icicles":
                    for dx, h in ((5, 5), (12, 9), (19, 6)):
                        draw.polygon([(x + dx - 1, y + 2), (x + dx + 2, y + 2), (x + dx, y + h)], fill="#8bb6cc")
                        draw.point((x + dx, y + 3), fill=WHITE)
                    if p % 8 < 2:
                        draw.point((x + 12, y + 8), fill=WHITE)
                elif kind == "lanterns":
                    draw.line((x + 12, y + 3, x + 12, y + 5), fill=GOLD)
                    draw.ellipse((x + 8, y + 5, x + 16, y + 13), fill="#ba5864", outline=INK)
                    draw.line((x + 12, y + 6, x + 12, y + 12), fill=GOLD if p % 8 < 5 else "#dca460", width=2)
                    draw.line((x + 12, y + 14, x + 12 + wave(p), y + 16), fill=GOLD)
                else:
                    for dx in (6, 18):
                        c = (PINK, GOLD, GREEN, BLUE)[(x // 6 + dx // 6) % 4]
                        draw.rectangle((x + dx, y + 3, x + dx + 1, y + 5), fill=c)
                        if (p // 3 + x + dx) % 8 < 2:
                            draw.point((x + dx, y + 4), fill=WHITE)
    elif kind in ("fireworks", "fountain"):
        for i in range(max(1, width // 65)):
            cx = (i * 67 + 27) % width
            age = (p + i * 11) % 32
            cy = height - 5 if kind == "fountain" else 14 + (i * 11) % max(1, height // 2)
            if kind == "fireworks" and age < 8:
                y = height - 5 - round((height - 5 - cy) * age / 8)
                draw.line((cx, y, cx, y + 4), fill=GOLD)
                continue
            r = (age - 8) * 0.7 if kind == "fireworks" else age * 0.55
            if r < 0 or age > 28:
                continue
            for a in range(0, 360 if kind == "fireworks" else 180, 45 if kind == "fireworks" else 25):
                angle = math.radians(a)
                x = round(cx + math.cos(angle) * r)
                y = round(cy - math.sin(angle) * r + (max(0, age - 17) ** 2 / 35 if kind == "fireworks" else 0))
                draw.line(
                    (x, y, x - round(math.cos(angle) * 2), y + round(math.sin(angle) * 2)),
                    fill=(PINK, GOLD, BLUE)[i % 3] if age < 23 else "#795e66",
                )
    elif kind in ("wind", "tornado", "hurricane"):
        if kind == "wind":
            for i in range(max(3, width // 35)):
                x = (i * 43 + p * 2) % (width + 15) - 15
                y = 10 + (i * 17) % max(1, height - 20)
                draw.line([(x, y), (x + 6, y), (x + 8, y - 1), (x + 8, y - 3)], fill="#526c7e")
        else:
            for i in range(9):
                radius = 12 - i if kind == "tornado" else 12
                x = width // 2 + round(math.sin(p / 5 + i / 2) * 2)
                y = 9 + i * 3
                draw.arc((x - radius, y - 2, x + radius, y + 2), 0 if (p + i) % 8 < 4 else 120, 300, fill="#71879d")
            for i in range(3):
                draw.point((width // 2 + round(15 * math.sin(p / 4 + i)), 15 + i * 7), fill=WOOD_COLOR)
    elif kind in ("sun", "sunrise"):
        x, y = width - 13, 10
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill="#d5a563")
        draw.ellipse((x - 5, y - 5, x + 4, y + 4), fill=GOLD)
        draw.line((x - 3, y - 3, x, y - 4), fill="#ffe8aa")
        for i in range(8):
            a = i * math.pi / 4
            r = 9 + (1 if (p // 4 + i) % 8 < 2 else 0)
            draw.line(
                (
                    round(x + r * math.cos(a)),
                    round(y + r * math.sin(a)),
                    round(x + (r + 2) * math.cos(a)),
                    round(y + (r + 2) * math.sin(a)),
                ),
                fill="#b59059",
            )
        if kind == "sunrise":
            for i in range(3):
                draw.line((x - 16 + i * 4, y + 6 + i * 3, x + 16 - i * 4, y + 6 + i * 3), fill="#675264")
    elif kind == "rainbow":
        # A small sky arc, never a full-deck opaque wash.
        cx = width // 2
        for i, c in enumerate(("#b77181", "#b99a62", "#639e85", "#638eaf", "#8b7daa")):
            draw.arc((cx - 28 + i * 2, 5 + i * 2, cx + 28 - i * 2, 49 - i * 2), 180, 360, fill=c, width=2)
        cloud(draw, cx - 27, 29)
        cloud(draw, cx + 27, 29)
        draw.point((cx - 15 + (p // 3) % 4, 33), fill="#719cad")
    elif kind == "meteor":
        sky(draw, "stars", width, height, p, color, density)
        age = p % 48
        if age < 20:
            x = round(width * age / 20)
            y = 5 + age // 2
            for tail in range(9):
                draw.point((x - tail, y - tail // 2), fill=(WHITE, GOLD, "#a98963", "#5e5961")[min(3, tail // 2)])
    elif kind:
        raise ValueError("Missing world sky: " + kind)


WOOD_COLOR = "#a98c68"
