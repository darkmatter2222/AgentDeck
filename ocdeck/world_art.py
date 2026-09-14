"""Original pixel motifs. Logical pixels, nearest-neighbor scaling, bounded caches."""

from functools import lru_cache
import math
from PIL import Image, ImageDraw

INK = "#193849"
WHITE = "#dbfff1"
GOLD = "#ffd280"
PINK = "#ff8090"
GREEN = "#59f3c2"
BLUE = "#69bfff"


@lru_cache(maxsize=512)
def prop(name, phase=0, color=GREEN):
    im = Image.new("RGBA", (40, 40))
    d = ImageDraw.Draw(im)
    p = phase % 8

    def box(rect, fill):
        d.rectangle(rect, fill=fill, outline=INK)

    def orb(rect, fill):
        d.ellipse(rect, fill=fill, outline=INK)

    if name in ("gift", "letter"):
        box((8, 17, 31, 33), color)
        if name == "gift":
            d.rectangle((18, 17, 21, 33), fill=GOLD)
            d.line((8, 23, 31, 23), fill=GOLD, width=2)
            d.line([(20, 17), (14, 12), (12, 16), (27, 16), (25, 12), (20, 17)], fill=GOLD)
        else:
            d.line([(9, 18), (20, 26), (30, 18)], fill=WHITE)
            orb((18, 24, 22, 28), PINK)
    elif name in ("tree", "seedling", "flower", "grass", "clover"):
        d.line((20, 33, 20, 20), fill=GREEN, width=2)
        if name == "tree":
            for y, w in ((9, 7), (16, 11), (23, 14)):
                d.polygon([(20, y), (20 - w, y + 9), (20 + w, y + 9)], fill=GREEN, outline=INK)
            for x, y in ((17, 16), (24, 23), (13, 27)):
                d.rectangle((x, y, x + 1, y + 1), fill=GOLD if p < 4 else PINK)
        elif name == "clover":
            for x, y in ((14, 16), (21, 16), (14, 23), (21, 23)):
                orb((x, y, x + 6, y + 6), GREEN)
        elif name == "flower":
            for x, y in ((15, 12), (22, 17), (17, 22), (11, 18)):
                orb((x, y, x + 7, y + 7), color)
            orb((17, 17, 23, 23), GOLD)
        else:
            d.polygon([(20, 26), (10, 20), (11, 26), (20, 29), (29, 19), (28, 25)], fill=GREEN)
            if name == "grass":
                for x in range(6, 34, 4):
                    d.line((x, 34, x + 2, 28 - p % 3), fill=GREEN)
    elif name in ("feast", "pie", "cake", "sweets"):
        box((4, 29, 36, 32), "#e5a15c")
        d.line((7, 32, 7, 38), fill=INK, width=2)
        d.line((33, 32, 33, 38), fill=INK, width=2)
        if name == "feast":
            orb((11, 18, 29, 29), "#c78356")
            orb((26, 23, 33, 29), "#e5a15c")
            for x in (5, 30):
                orb((x, 26, x + 5, 29), GREEN)
        elif name == "cake":
            box((11, 20, 29, 29), PINK)
            d.line((12, 22, 28, 22), fill=WHITE, width=3)
            for x in (14, 20, 26):
                d.line((x, 19, x, 14), fill=BLUE)
                d.point((x, 12 + p % 2), fill=GOLD)
        elif name == "pie":
            orb((9, 22, 31, 29), GOLD)
            for x in range(13, 29, 5):
                d.line((x, 23, x - 2, 27), fill="#a46648")
        else:
            for x in (9, 18, 27):
                orb((x, 24, x + 5, 29), color)
    elif name in ("snowman", "snowball", "snowangel", "snowflake", "icicles"):
        if name == "snowman":
            orb((12, 22, 29, 36), WHITE)
            orb((14, 12, 27, 25), WHITE)
            d.point((18, 17), fill=INK)
            d.point((23, 17), fill=INK)
            d.line((19, 22, 26, 22), fill=PINK, width=2)
            d.polygon([(21, 18), (28, 19), (21, 20)], fill=GOLD)
        elif name == "snowball":
            orb((12 + p, 23 - p, 23 + p, 34 - p), WHITE)
        elif name == "snowangel":
            for rect in ((7, 22, 20, 31), (20, 22, 33, 31), (15, 26, 25, 37), (16, 18, 24, 26)):
                orb(rect, WHITE)
        else:
            for angle in range(0, 360, 60):
                a = math.radians(angle)
                d.line((20, 24, 20 + 12 * math.cos(a), 24 + 12 * math.sin(a)), fill=WHITE)
    elif name in ("pumpkin", "acorn"):
        orb((9, 20, 31, 35), "#ef995c" if name == "pumpkin" else "#c78356")
        d.line((20, 20, 21, 15), fill=GREEN, width=2)
        if name == "pumpkin":
            d.polygon([(14, 24), (12, 28), (17, 28)], fill=INK)
            d.polygon([(25, 24), (22, 28), (28, 28)], fill=INK)
            d.line([(14, 31), (18, 33), (25, 31)], fill=INK)
        else:
            box((9, 19, 31, 25), "#875e47")
    elif name in ("rocket", "fountain", "canister"):
        if name == "rocket":
            d.line((20, 24, 20, 36), fill=WHITE)
            box((16, 14 - p, 24, 25 - p), color)
            d.polygon([(15, 14 - p), (20, 7 - p), (25, 14 - p)], fill=PINK)
            d.line((19, 26 - p, 20, 29), fill=GOLD, width=2)
        else:
            box((16, 28, 24, 35), color)
            for i in range(5):
                d.line((20, 28, 10 + i * 5, 18 + (i + p) % 5), fill=GOLD if name == "fountain" else color)
    elif name in ("fan", "pinwheel", "windsock", "kite", "beachball"):
        d.line((20, 22, 20, 36), fill=WHITE)
        if name in ("fan", "pinwheel"):
            for i in range(4):
                a = (i / 4 + p / 16) * math.tau
                x, y = 20 + 12 * math.cos(a), 21 + 12 * math.sin(a)
                d.polygon([(20, 21), (x, y), (x - 4, y + 3)], fill=(color, GOLD, PINK, BLUE)[i])
            orb((18, 19, 22, 23), WHITE)
        elif name == "windsock":
            d.line((8, 12, 8, 36), fill=WHITE)
            d.polygon([(8, 12), (32, 16 + p % 3), (30, 23 + p % 3), (8, 22)], fill=color, outline=INK)
            d.line((16, 14, 15, 22), fill=WHITE, width=2)
        elif name == "kite":
            d.polygon([(20, 7), (30, 18), (20, 28), (10, 18)], fill=color, outline=INK)
            d.line((10, 18, 30, 18), fill=WHITE)
            d.line((20, 7, 20, 28), fill=WHITE)
        else:
            orb((9, 13, 31, 35), WHITE)
            d.pieslice((9, 13, 31, 35), p * 20, p * 20 + 120, fill=PINK)
            d.pieslice((9, 13, 31, 35), p * 20 + 180, p * 20 + 270, fill=BLUE)
    elif name in ("lantern", "lamp", "diya", "menorah"):
        if name == "menorah":
            d.line((5, 29, 35, 29), fill=GOLD, width=2)
            d.line((20, 28, 20, 36), fill=GOLD, width=2)
            for i, x in enumerate(range(4, 37, 4)):
                y = 15 if i == 4 else 20
                d.line((x, y, x, 29), fill=GOLD)
                d.point((x, y - 2 - p % 2), fill=WHITE)
        elif name == "diya":
            d.pieslice((8, 22, 32, 35), 0, 180, fill=GOLD)
            d.polygon([(20, 14 - p % 2), (16, 24), (23, 24)], fill=GOLD)
            d.point((20, 21), fill=WHITE)
        else:
            d.line((20, 6, 20, 12), fill=GOLD)
            box((12, 12, 28, 31), color)
            d.rectangle((17, 15, 23, 28), fill=GOLD if p < 4 else WHITE)
            d.line((20, 31, 20, 36), fill=GOLD)
    elif name in ("heart", "powder", "rangoli", "eggs", "candy"):
        if name == "heart":
            d.polygon([(20, 32), (8, 20), (8, 15), (13, 12), (20, 17), (27, 12), (32, 15), (32, 20)], fill=PINK)
        elif name == "eggs":
            for x, c in ((8, PINK), (17, BLUE), (26, GOLD)):
                orb((x, 20, x + 8, 33), c)
                d.line((x + 1, 27, x + 7, 27), fill=WHITE)
        elif name == "candy":
            for x, c in ((9, PINK), (22, BLUE)):
                d.polygon([(x - 3, 23), (x + 12, 31), (x + 12, 23), (x - 3, 31)], fill=c)
                orb((x, 22, x + 9, 32), c)
        else:
            for i, c in enumerate((PINK, BLUE, GOLD, GREEN)):
                a = i * math.pi / 2 + p / 20
                x, y = 20 + 8 * math.cos(a), 27 + 5 * math.sin(a)
                orb((x - 5, y - 4, x + 5, y + 4), c)
    elif name in ("lemonade", "cocoa", "popsicle", "pot"):
        if name == "popsicle":
            box((14, 13, 26, 28), color)
            d.line((20, 29, 20, 36), fill=GOLD, width=2)
        else:
            box((12, 22, 27, 34), GOLD if name == "lemonade" else "#c78356")
            d.arc((25, 24, 32, 31), 270, 90, fill=WHITE, width=2)
            if name == "lemonade":
                d.line((23, 27, 25, 15), fill=PINK, width=2)
            if name == "pot":
                orb((11, 18, 28, 25), GOLD)
            if name == "cocoa":
                d.line([(17, 19), (15 + p % 3, 16), (17, 12)], fill=WHITE)
    elif name in ("cloud", "puddle", "window"):
        if name == "window":
            box((7, 10, 33, 35), BLUE)
            d.line((20, 10, 20, 35), fill=WHITE, width=2)
            d.line((7, 23, 33, 23), fill=WHITE, width=2)
        elif name == "puddle":
            d.ellipse((5 - p % 3, 30, 35, 36), fill="#267c91", outline=BLUE)
            d.arc((10, 30, 28, 35), 0, 180, fill=WHITE)
        else:
            for x, y in ((8, 20), (16, 14), (23, 20)):
                orb((x, y, x + 12, y + 10), WHITE)
    elif name in ("crescent", "globe", "clock", "balloon"):
        orb((10, 12, 30, 32), color)
        if name == "crescent":
            d.ellipse((16, 8, 33, 27), fill=(0, 0, 0, 0))
        elif name == "globe":
            d.polygon([(13, 16), (23, 14), (22, 20), (17, 22), (19, 27), (15, 28)], fill=GREEN)
        elif name == "clock":
            d.line((20, 15, 20, 22, 25, 22), fill=INK, width=2)
        else:
            d.line([(20, 32), (18, 35), (20, 39)], fill=WHITE)
    elif name in ("broom", "rake", "scythe", "telescope"):
        d.line((13, 36, 26, 12), fill=GOLD, width=2)
        if name == "broom":
            d.polygon([(12, 26), (21, 30), (16, 38), (6, 34)], fill=GOLD)
        elif name == "rake":
            d.line((19, 15, 31, 20), fill=WHITE, width=2)
            for x in (20, 24, 28):
                d.line((x, 16, x - 3, 21), fill=WHITE)
        elif name == "scythe":
            d.arc((10, 9, 35, 29), 190, 320, fill=WHITE, width=3)
        else:
            d.line((8, 23, 29, 12), fill=BLUE, width=7)
            d.line((20, 25, 28, 36), fill=WHITE)
    elif name in ("sled", "train", "sandcastle"):
        if name == "sled":
            d.line([(5, 32), (29, 32), (34, 28)], fill=WHITE, width=2)
            box((8, 25, 29, 29), PINK)
        elif name == "train":
            box((4 + p, 24, 22 + p, 32), color)
            box((5 + p, 18, 13 + p, 24), GOLD)
            for x in (9 + p, 20 + p):
                orb((x - 3, 30, x + 3, 36), INK)
            box((28, 26, 37, 32), GREEN)
        else:
            box((8, 23, 32, 35), GOLD)
            for x in (9, 18, 27):
                box((x, 17, x + 4, 24), GOLD)
            d.arc((17, 28, 24, 40), 180, 360, fill=INK, width=3)
    elif name == "dreidel":
        box((15, 17, 27, 27), BLUE)
        d.polygon([(15, 27), (27, 27), (21, 34)], fill=BLUE)
        d.line((21, 12, 21, 17), fill=GOLD, width=2)
        d.line((19 + p % 3, 21, 24, 21), fill=WHITE)
    elif name == "leaf":
        d.polygon([(6, 23), (15, 21), (19, 10), (23, 20), (34, 21), (25, 28), (19, 33), (12, 29)], fill=color)
        d.line((19, 22, 19, 36), fill=GOLD)
    elif name == "mittens":
        for x in (7, 23):
            orb((x, 19, x + 9, 32), PINK)
            box((x, 29, x + 9, 35), WHITE)
            orb((x - 3, 24, x + 3, 30), PINK)
    elif name == "music":
        d.line([(15, 29), (15, 13), (28, 10), (28, 26)], fill=color, width=2)
        orb((8, 27, 16, 33), color)
        orb((21, 24, 29, 30), color)
    elif name:
        raise ValueError("Missing world prop: " + name)
    return im


def costume(image, name, phase, head):
    """Draw on a logical 40px sprite; preserve eyes and floor-contact anatomy."""
    if not name:
        return image
    im = image.copy()
    d = ImageDraw.Draw(im)
    y = max(4, head)
    if name in ("santa", "elf", "party", "witch", "nightcap"):
        color = {"santa": PINK, "elf": GREEN, "party": GOLD, "witch": "#8055b9", "nightcap": BLUE}[name]
        d.polygon([(10, y + 1), (20, y - 10), (29, y + 1)], fill=color, outline=INK)
        d.line((10, y + 1, 29, y + 1), fill=WHITE if name == "santa" else GOLD, width=2)
        d.rectangle((19, y - 10, 21, y - 8), fill=WHITE)
    elif name in ("beanie", "sunhat", "gardener"):
        d.pieslice((11, y - 8, 29, y + 6), 180, 360, fill=GOLD if name != "beanie" else PINK)
        d.line((8, y, 32, y), fill=GREEN if name == "gardener" else GOLD, width=2)
    elif name == "bunny":
        d.ellipse((12, y - 12, 17, y + 1), fill=WHITE)
        d.ellipse((23, y - 12, 28, y + 1), fill=WHITE)
        d.line((14, y - 9, 14, y - 2), fill=PINK)
        d.line((25, y - 9, 25, y - 2), fill=PINK)
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
    elif name == "skeleton":
        d.line((20, 25, 20, 32), fill=WHITE)
        for h in (26, 29):
            d.line((14, h, 26, h), fill=WHITE)
    elif name == "reaper":
        d.line([(8, 29), (10, y + 2), (20, y - 4), (30, y + 2), (32, 29)], fill="#8055b9", width=4)
    elif name in ("mask", "shades"):
        d.rectangle((12, y + 7, 28, y + 10), fill="#8055b9" if name == "mask" else INK)
        d.point((15, y + 8), fill=WHITE)
        d.point((24, y + 8), fill=WHITE)
    elif name == "scarf":
        d.line((10, 28, 30, 28), fill=PINK, width=3)
        d.line((28, 28, 30 + phase % 2, 33), fill=PINK, width=2)
    elif name == "bow":
        d.polygon([(12, y), (18, y + 3), (12, y + 6), (24, y), (18, y + 3), (24, y + 6)], fill=PINK)
    elif name == "sweat":
        d.line((30, y + 4 + phase % 4, 30, y + 7 + phase % 4), fill=BLUE, width=2)
    elif name == "umbrella":
        d.pieslice((5, 0, 35, 20), 180, 360, fill="#c4a7ff", outline=INK)
        d.line((20, 9, 20, y + 2), fill=WHITE)
    elif name == "boots":
        d.rectangle((9, 31, 16, 34), fill=GOLD)
        d.rectangle((24, 31, 31, 34), fill=GOLD)
    else:
        raise ValueError("Missing world costume: " + name)
    return im


def sky(draw, kind, width, height, phase, color, density=1):
    """Continuous logical deck-space; renderer crops only currently free keys."""
    p = phase
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
        for i in range(max(4, width // 7) * density):
            x = (i * 37 + (p // 2 if kind not in ("rain", "snow") else p // 4)) % width
            y = (i * 19 + (p * (2 if kind == "rain" else 1))) % height
            c = ("#ff8090", "#ffd280", "#69bfff", "#59f3c2")[i % 4] if kind == "confetti" else color
            if kind == "rain":
                draw.line((x, y, x - 1, y + 3), fill=BLUE)
            elif kind in ("snow", "stars", "fireflies"):
                if kind != "fireflies" or (i + p // 4) % 3:
                    draw.point((x, y), fill=WHITE if kind == "snow" else GOLD)
            elif kind == "hearts":
                draw.line([(x - 1, y), (x, y + 1), (x + 1, y)], fill=PINK)
            elif kind == "butterflies":
                draw.line((x - 2, y - 1, x + 2, y + 1), fill=c, width=2 if p % 4 < 2 else 1)
            elif kind == "balloons":
                draw.ellipse((x, y, x + 4, y + 6), fill=c)
                draw.line((x + 2, y + 6, x + 2, y + 9), fill=WHITE)
            else:
                draw.line((x, y, x + 2, y + 1), fill=c)
    elif kind in ("clouds", "fog", "smoke"):
        for i in range(4):
            x = (i * 43 + p // 2) % (width + 25) - 25
            y = 7 + i % 2 * 9
            draw.ellipse(
                (x, y, x + 24, y + 7), fill=("#506479" if kind == "fog" else color if kind == "smoke" else "#91aabb")
            )
    elif kind in ("lights", "lanterns", "icicles"):
        for y in range(4, height, 44):
            draw.line((0, y, width, y), fill="#506479")
            for x in range(5, width, 10):
                if kind == "icicles":
                    draw.polygon([(x, y), (x + 4, y), (x + 2, y + 7)], fill=WHITE)
                else:
                    draw.rectangle(
                        (x, y + 1, x + 2, y + (6 if kind == "lanterns" else 3)),
                        fill=(PINK, GOLD, GREEN, BLUE)[(x // 10 + p // 8) % 4],
                    )
    elif kind in ("fireworks", "fountain"):
        for i in range(max(1, width // 45)):
            cx = (i * 53 + 23) % width
            cy = 12 + (i * 13) % max(1, height - 30)
            r = (p + i * 7) % 24
            if kind == "fountain":
                cy = height - 4
            for angle in range(0, 360 if kind == "fireworks" else 180, 30):
                a = math.radians(angle)
                x = cx + math.cos(a) * r
                y = cy - math.sin(a) * r
                draw.line((x, y, x - math.cos(a) * 3, y + math.sin(a) * 3), fill=(PINK, GOLD, BLUE)[i % 3])
    elif kind in ("wind", "tornado", "hurricane"):
        for i in range(10):
            y = 5 + i * 3
            if kind == "wind":
                x = (i * 29 + p * 2) % width
                draw.line((x, y, x + 8, y), fill="#91aabb")
            else:
                radius = 12 - i if kind == "tornado" else 14
                x = width // 2 + math.sin(p / 5 + i) * radius
                draw.line((x - radius, y, x + radius, y), fill="#91aabb")
    elif kind in ("sun", "sunrise"):
        x = width - 15
        y = 12 + (3 if kind == "sunrise" else 0)
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=GOLD)
        for i in range(8):
            a = i * math.pi / 4 + p / 70
            draw.line((x + 9 * math.cos(a), y + 9 * math.sin(a), x + 11 * math.cos(a), y + 11 * math.sin(a)), fill=GOLD)
    elif kind == "rainbow":
        for i, c in enumerate((PINK, GOLD, GREEN, BLUE, "#c4a7ff")):
            draw.arc((3 + i * 2, 3 + i * 2, width - 3 - i * 2, height + 20 - i * 2), 180, 360, fill=c, width=2)
    elif kind == "meteor":
        x = (p * 3) % (width + 15) - 15
        draw.line((x, 4, x + 12, 12), fill=GOLD, width=2)
    elif kind:
        raise ValueError("Missing world sky: " + kind)
