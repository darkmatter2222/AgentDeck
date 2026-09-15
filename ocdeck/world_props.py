"""Hand-authored world objects on Jelly's 40px grid, with a shared (20, 34) floor.

Sizes belong to the object, not its viewport: an acorn is 11px high, a tree 30px.
Eight held frames describe material motion; stationary furniture stays grounded.
"""

from functools import lru_cache
import math
from PIL import Image, ImageDraw

INK = "#193849"
WHITE = "#dbfff1"
GOLD = "#ffd280"
PINK = "#ff8090"
GREEN = "#59c99b"
BLUE = "#69bfff"
WOOD = "#a36a45"
DARK = "#684832"

# Freely suspended objects have no contact shadow. Everything else meets y=34.
AIRBORNE = frozenset(("cloud", "crescent", "heart", "balloon", "music", "kite", "snowflake", "icicles"))


def wave(phase):
    return (0, 1, 1, 1, 0, -1, -1, -1)[phase % 8]


def leaf(d, x, y, color, tilt=0):
    """Lobed maple silhouette, lit edge, central vein and a separate stem."""
    d.polygon(
        [
            (x, y - 5),
            (x + 2, y - 2),
            (x + 4, y - 3),
            (x + 3, y),
            (x + 5, y),
            (x + 2, y + 3),
            (x, y + 4),
            (x - 3, y + 2),
            (x - 5, y - 1),
            (x - 2, y - 1),
            (x - 2, y - 3),
        ],
        fill=color,
        outline="#9b5837",
    )
    d.line([(x + tilt, y - 3), (x, y + 2), (x - 1, y + 6)], fill=GOLD)
    d.line((x - 2, y, x, y + 2, x + 2, y), fill="#f4b665")


def cloud(d, x, y, storm=False):
    """One continuous silhouette, with rounded lobes and a shaded flat underside."""
    shade, body, light = ("#42566f", "#71879d", "#a5b6c6") if storm else ("#647e98", "#adc5d6", "#e0edf1")
    d.polygon(
        [
            (x - 13, y + 4),
            (x - 15, y + 1),
            (x - 14, y - 2),
            (x - 10, y - 4),
            (x - 7, y - 4),
            (x - 6, y - 8),
            (x - 2, y - 10),
            (x + 3, y - 9),
            (x + 6, y - 5),
            (x + 10, y - 5),
            (x + 14, y - 2),
            (x + 15, y + 2),
            (x + 12, y + 5),
            (x - 10, y + 5),
        ],
        fill=shade,
        outline=INK,
    )
    d.polygon(
        [
            (x - 13, y),
            (x - 10, y - 3),
            (x - 6, y - 3),
            (x - 4, y - 7),
            (x, y - 8),
            (x + 3, y - 7),
            (x + 5, y - 3),
            (x + 10, y - 3),
            (x + 13, y),
            (x + 11, y + 2),
            (x - 11, y + 2),
        ],
        fill=body,
    )
    d.line([(x - 5, y - 4), (x - 3, y - 7), (x, y - 8), (x + 2, y - 7)], fill=light)
    d.line((x - 11, y - 1, x - 8, y - 2), fill=light)


def prop(name, phase=0, color=GREEN):
    # Normalize before caching so callers cannot grow an unbounded timeline cache.
    return _prop(name, phase % 8, color)


@lru_cache(maxsize=512)
def _prop(name, p, color):
    im = Image.new("RGBA", (40, 40))
    d = ImageDraw.Draw(im)
    sway = wave(p)

    def box(rect, fill, outline=INK):
        d.rectangle(rect, fill=fill, outline=outline)

    def orb(rect, fill, outline: str | None = INK):
        d.ellipse(rect, fill=fill, outline=outline)

    def line(points, fill=WHITE, width=1):
        d.line(points, fill=fill, width=width)

    def flame(x, y):
        d.polygon([(x + sway, y - 4), (x - 2, y), (x, y + 2), (x + 2, y)], fill="#e99547")
        line((x, y - 1, x, y + 1), WHITE)

    def steam(x, y):
        for i in range(2):
            h = (p + i * 4) % 8
            line([(x + i * 5, y - h), (x + i * 5 + sway, y - h - 2), (x + i * 5 + 1, y - h - 4)], "#9cabb5")

    if name in ("gift", "letter"):
        if name == "gift":
            box((11, 22, 29, 33), color)
            box((10, 19, 30, 23), color)
            line((13, 25, 13, 31), WHITE)
            box((19, 20, 21, 33), GOLD, GOLD)
            d.polygon(
                [(20, 19), (14, 15 + sway), (12, 16 + sway), (14, 19), (26, 19), (28, 16 - sway), (26, 15 - sway)],
                fill=GOLD,
                outline=DARK,
            )
        else:
            box((11, 23, 29, 33), "#f2dfb3")
            line([(12, 32), (20, 26), (28, 32)], "#b49a80")
            line([(12, 24), (20, 29), (28, 24)], WOOD)
            orb((18, 27, 22, 31), PINK)
            if p in (2, 3):
                line((25, 21, 27, 19), GOLD)
    elif name in ("tree", "seedling", "flower", "grass", "clover"):
        if name == "tree":
            box((18, 28, 22, 34), WOOD)
            for y, w in ((5, 6), (12, 10), (20, 13)):
                d.polygon([(20, y), (20 - w, y + 10), (20 + w, y + 10)], fill="#267a63", outline=INK)
                d.polygon([(20, y + 1), (20 - w + 2, y + 8), (20, y + 6)], fill=GREEN)
                line((20 - w + 2, y + 9, 20 + w - 2, y + 9), "#194f49")
            for i, (x, y) in enumerate(((17, 12), (23, 18), (13, 27), (26, 28))):
                orb((x, y, x + 2, y + 2), GOLD if (p + i) % 8 < 3 else PINK)
            d.polygon([(20, 2), (21, 5), (24, 5), (21, 7), (20, 9), (19, 7), (16, 5), (19, 5)], fill=GOLD)
        elif name == "grass":
            for i, x in enumerate(range(7, 34, 4)):
                d.polygon(
                    [(x, 34), (x - 2 + sway, 26 - i % 3), (x + 1, 31), (x + 3 + sway, 28), (x + 2, 34)],
                    fill=GREEN if i % 2 else "#34795b",
                )
        else:
            x = 20 + sway
            line([(20, 34), (19, 28), (x, 21)], "#34856b", 2)
            d.polygon([(19, 29), (12, 24), (13, 28), (19, 31)], fill=GREEN, outline="#34856b")
            d.polygon([(20, 27), (27, 22), (26, 27), (20, 29)], fill=GREEN, outline="#34856b")
            if name == "seedling":
                orb((12, 32, 28, 35), DARK)
                line((15, 32, 24, 32), WOOD)
            elif name == "flower":
                for dx, dy in ((-3, -3), (3, -3), (-4, 2), (4, 2), (0, 4)):
                    orb((x + dx - 3, 18 + dy - 3, x + dx + 3, 18 + dy + 3), color, "#967eac")
                orb((x - 2, 16, x + 2, 20), GOLD)
                d.point((x - 1, 17), WHITE)
            else:
                for dx, dy in ((-4, -4), (1, -4), (-4, 1), (1, 1)):
                    orb((x + dx, 18 + dy, x + dx + 5, 23 + dy), GREEN)
                line((x, 18, x, 24), "#b5e9a5")
    elif name in ("feast", "pie", "cake", "sweets"):
        # Plate instead of an oversized table attached to every snack.
        orb((6, 30, 34, 34), "#91aabb")
        line((9, 31, 31, 31), WHITE)
        if name == "feast":
            orb((10, 21, 29, 31), WOOD)
            orb((12, 22, 25, 28), "#d99754", None)
            orb((23, 27, 30, 31), WOOD)
            line((29, 29, 33, 26), WHITE, 2)
            d.point((33, 25), WHITE)
            for x in (8, 30):
                line([(x, 30), (x - 2, 27), (x + 2, 29)], GREEN, 2)
            steam(17, 20)
        elif name == "pie":
            box((10, 28, 30, 31), WOOD)
            orb((9, 24, 31, 29), GOLD)
            for x in range(12, 30, 4):
                line((x, 25, x - 2, 28), WOOD)
            line((12, 25, 27, 28), "#e5a15c")
            steam(17, 23)
        elif name == "cake":
            box((11, 23, 29, 31), "#a85d70")
            box((11, 21, 29, 25), PINK)
            line([(12, 23), (14, 24), (16, 23), (18, 24), (20, 23), (22, 24), (24, 23), (27, 24)], WHITE, 2)
            line((12, 28, 28, 28), "#f9cda6")
            for x in (15, 20, 25):
                line((x, 20, x, 16), BLUE)
                flame(x, 14)
        else:
            for i, x in enumerate((11, 19, 27)):
                box((x - 3, 26 - i % 2 * 3, x + 3, 31), "#c58a58")
                line((x - 2, 27 - i % 2 * 3, x + 2, 27 - i % 2 * 3), GOLD, 2)
                d.point((x, 28), GREEN)
            if p in (2, 3):
                d.point((28, 24), WHITE)
    elif name in ("snowman", "snowball", "snowangel", "snowflake", "icicles"):
        if name == "snowman":
            orb((11, 20, 29, 34), "#91bdd0")
            orb((12, 20, 27, 32), WHITE, None)
            orb((14, 10, 27, 22), WHITE)
            box((15, 7, 25, 12), "#334a64")
            line((12, 12, 29, 12), INK, 2)
            line((16, 10, 24, 10), PINK)
            d.point((18, 16), INK)
            d.point((23, 16), INK)
            d.polygon([(21, 17), (28, 18), (21, 19)], fill="#ed9652")
            line((14, 22, 27, 22), PINK, 2)
            line((25, 23, 26 + sway, 27), PINK, 2)
            line((11, 25, 6, 21, 5, 18 + sway), WOOD)
            line((29, 25, 34, 20 - sway), WOOD)
            for y in (26, 30):
                d.point((20, y), INK)
        elif name == "snowball":
            h = (0, 2, 4, 5, 4, 2, 0, 0)[p]
            orb((15, 24 - h, 25, 34 - h), "#91bdd0")
            orb((16, 25 - h, 23, 31 - h), WHITE, None)
            d.point((18, 26 - h), WHITE)
        elif name == "snowangel":
            for rect in ((8, 25, 20, 31), (20, 25, 32, 31), (16, 25, 24, 34), (17, 20, 23, 26)):
                orb(rect, "#6b98ad", "#a9cfdf")
            line((13, 28, 17, 29), WHITE)
            line((24, 29, 28, 28), WHITE)
            d.point((12 + p * 2, 33), WHITE)
        elif name == "icicles":
            line((10, 10, 30, 10), WHITE, 2)
            for i, x in enumerate((12, 18, 24, 29)):
                d.polygon([(x - 2, 11), (x + 2, 11), (x, 22 + i % 2 * 6)], fill="#80b7d2")
                line((x - 1, 12, x, 19 + i % 2 * 5), WHITE)
            d.point((18, 29 + p // 2), BLUE)
        else:
            for i in range(6):
                a = i * math.tau / 6
                x, y = round(20 + 8 * math.cos(a)), round(18 + 8 * math.sin(a))
                line((20, 18, x, y), "#a3d2e5")
                for side in (-1, 1):
                    line(
                        (
                            round(20 + 5 * math.cos(a)),
                            round(18 + 5 * math.sin(a)),
                            round(x + 3 * math.cos(a + side * 2.4)),
                            round(y + 3 * math.sin(a + side * 2.4)),
                        ),
                        WHITE,
                    )
            d.point((20, 18), GOLD if p == 3 else WHITE)
    elif name == "acorn":
        d.polygon([(15, 27), (25, 27), (24, 31), (20, 34), (16, 31)], fill="#b97b48", outline=DARK)
        line((17, 28, 18, 31), GOLD)
        orb((14, 23, 26, 28), DARK)
        line([(15, 25), (18, 24), (22, 24), (25, 25)], "#d4a36a")
        for x, y in ((16, 26), (20, 25), (23, 26)):
            d.point((x, y), "#b78555")
        line((20, 23, 20, 21, 22, 20), WOOD)
        # A brief edge glint, not a hopping nut.
        if p in (2, 3):
            d.point((17, 29), WHITE)
    elif name == "pumpkin":
        orb((10, 21, 30, 34), "#b66032")
        for x in (12, 17, 22):
            orb((x, 22, x + 7, 33), "#e99547", "#bd6738")
        line((20, 21, 21, 17, 24, 17), "#659564", 2)
        for x in (15, 24):
            d.polygon([(x, 25), (x - 2, 28), (x + 2, 28)], fill=GOLD if p < 4 else "#d7a653")
        line([(15, 30), (18, 31), (23, 31), (26, 29)], GOLD)
    elif name in ("rocket", "fountain", "canister"):
        if name == "rocket":
            lift = (0, 0, 1, 3, 5, 7, 4, 1)[p]
            line((20, 27 - lift, 20, 34), WOOD)
            box((17, 17 - lift, 23, 28 - lift), "#e9e6d5")
            d.polygon([(16, 17 - lift), (20, 12 - lift), (24, 17 - lift)], fill=PINK, outline=INK)
            line((18, 22 - lift, 22, 24 - lift), PINK, 2)
            flame(20, 31 - lift)
        elif name == "canister":
            box((16, 25, 24, 33), "#65768a")
            line((17, 28, 23, 28), color, 3)
            line((18, 24, 22, 24), WHITE)
            for i in range(3):
                y = 22 - i * 5 - (p % 3)
                orb((17 + sway - i, y, 23 + sway + i, y + 4), color, None)
        else:
            d.polygon([(17, 34), (19, 28), (23, 28), (25, 34)], fill=PINK, outline=INK)
            for i in range(5):
                x = 11 + i * 5
                y = 18 + (p + i * 2) % 7
                line([(21, 28), (x, y), (x + sway, y + 2)], GOLD)
                d.point((x, y - 2), WHITE)
    elif name in ("fan", "pinwheel", "windsock", "kite", "beachball"):
        if name in ("fan", "pinwheel"):
            line((20, 24, 20, 33), "#91aabb", 2)
            if name == "fan":
                box((14, 32, 26, 34), "#637d94")
                orb((9, 10, 31, 30), "#344c61", "#91b6c8")
            for i in range(4):
                a = i * math.tau / 4 + p * math.tau / 8
                pts = [
                    (20, 20),
                    (round(20 + 9 * math.cos(a)), round(20 + 9 * math.sin(a))),
                    (round(20 + 6 * math.cos(a + 0.65)), round(20 + 6 * math.sin(a + 0.65))),
                ]
                d.polygon(pts, fill=(BLUE if name == "fan" else (color, GOLD, PINK, BLUE)[i]))
            if name == "fan":
                d.arc((12, 13, 28, 27), 0, 360, fill="#89acbe")
            orb((18, 18, 22, 22), WHITE)
        elif name == "windsock":
            line((11, 10, 11, 34), "#91b6c8", 2)
            d.polygon([(12, 12), (31, 15 + sway), (29, 21 + sway), (12, 20)], fill=PINK, outline=INK)
            for x in (16, 23):
                line((x, 14, x - 1, 20), WHITE, 2)
            orb((10, 12, 14, 20), "#8b4e63")
        elif name == "kite":
            x = 20 + sway
            d.polygon([(x, 7), (x + 7, 14), (x, 23), (x - 7, 14)], fill=color, outline=INK)
            d.polygon([(x, 7), (x, 14), (x - 7, 14)], fill=GOLD)
            d.polygon([(x, 14), (x + 7, 14), (x, 23)], fill=BLUE)
            line((x, 7, x, 23), WHITE)
            line([(x, 23), (x - 2, 27), (x + 1, 30), (x + sway, 34)], "#91aabb")
            for y in (27, 32):
                line((x - 3, y, x + 2, y), PINK)
        else:
            h = (0, 1, 3, 4, 3, 1, 0, 0)[p]
            orb((12, 18 - h, 28, 34 - h), "#e6e6d5")
            d.pieslice((13, 19 - h, 27, 33 - h), 35, 150, fill=PINK)
            d.pieslice((13, 19 - h, 27, 33 - h), 205, 315, fill=BLUE)
            orb((18, 24 - h, 21, 27 - h), GOLD, None)
            line((16, 21 - h, 18, 20 - h), WHITE)
    elif name in ("lantern", "lamp", "diya", "menorah"):
        if name == "menorah":
            line((13, 34, 27, 34), GOLD, 2)
            line((20, 15, 20, 34), GOLD, 2)
            for i, x in enumerate(range(4, 37, 4)):
                y = 17 if i == 4 else 22
                line([(x, y), (x, y + 5), (20, 31)], GOLD)
                flame(x, y - 3)
        elif name == "diya":
            d.polygon([(11, 28), (29, 28), (26, 33), (16, 33)], fill=WOOD, outline=DARK)
            orb((11, 26, 29, 29), GOLD)
            flame(21, 24)
            line((16, 31, 24, 31), "#d39259")
        elif name == "lamp":
            box((16, 33, 24, 34), "#8498a2")
            line((20, 14, 20, 33), "#8498a2", 2)
            d.polygon([(15, 12), (25, 12), (29, 21), (11, 21)], fill=GOLD, outline=INK)
            line((16, 14, 14, 19), WHITE)
            line((17, 22, 23, 22), "#bd8c50" if p < 4 else GOLD)
        else:
            d.arc((16, 9, 24, 18), 180, 360, fill=GOLD)
            orb((12, 16, 28, 30), color)
            for x in (16, 20, 24):
                line((x, 18, x, 28), GOLD)
            box((15, 14, 25, 16), WOOD)
            box((15, 29, 25, 31), WOOD)
            line((20, 32, 20 + sway, 35), GOLD)
            line((18, 19, 18, 26), WHITE if p < 4 else GOLD)
    elif name in ("heart", "powder", "rangoli", "eggs", "candy"):
        if name == "heart":
            y = 20 + sway
            d.polygon(
                [
                    (20, y + 7),
                    (12, y),
                    (12, y - 4),
                    (15, y - 6),
                    (18, y - 6),
                    (20, y - 3),
                    (22, y - 6),
                    (25, y - 6),
                    (28, y - 4),
                    (28, y),
                ],
                fill=PINK,
                outline="#a34d69",
            )
            line((14, y - 3, 16, y - 4), "#ffd4d8", 2)
        elif name == "eggs":
            orb((9, 29, 31, 34), WOOD)
            for x, c in ((12, PINK), (19, BLUE), (26, GOLD)):
                orb((x - 3, 22, x + 3, 32), c)
                line((x - 2, 27, x + 2, 27), WHITE)
                d.point((x - 1, 24), WHITE)
            line((11, 32, 29, 32), GOLD)
            if p in (4, 5):
                d.point((27, 24), WHITE)
        elif name == "candy":
            for x, c in ((14, PINK), (26, BLUE)):
                d.polygon([(x - 7, 26), (x - 7, 32), (x + 7, 26), (x + 7, 32)], fill=c, outline=INK)
                orb((x - 4, 25, x + 4, 32), c)
                line((x - 1, 26, x + 1, 30), WHITE)
            if p in (2, 3):
                d.point((12, 26), GOLD)
        elif name == "powder":
            for x, c in ((10, PINK), (20, BLUE), (30, GOLD)):
                d.polygon([(x - 5, 32), (x, 27), (x + 5, 32)], fill=c, outline=INK)
                d.arc((x - 5, 29, x + 5, 34), 0, 180, fill=WHITE)
                d.point((x + sway, 24 - p % 3), c)
        else:
            orb((6, 22, 34, 34), "#874f72")
            for i in range(8):
                a = i * math.tau / 8
                x, y = round(20 + 9 * math.cos(a)), round(28 + 4 * math.sin(a))
                orb((x - 3, y - 2, x + 3, y + 2), (PINK, BLUE, GOLD, GREEN)[i % 4], None)
            orb((17, 26, 23, 30), GOLD)
            d.point((20, 28), WHITE if p < 2 else PINK)
    elif name in ("lemonade", "cocoa", "popsicle", "pot"):
        if name == "popsicle":
            line((20, 29, 20, 34), WOOD, 2)
            d.rounded_rectangle((15, 16, 25, 29), radius=3, fill=color, outline=INK)
            line((17, 19, 17, 25), WHITE)
            d.point((24, 30 + p // 3), color)
        elif name == "pot":
            orb((12, 23, 28, 34), "#334454")
            orb((12, 22, 28, 26), GOLD)
            for i, x in enumerate((15, 20, 25)):
                orb((x - 2, 20 + i % 2, x + 2, 24 + i % 2), "#e7b55d")
            line((15, 27, 15, 30), "#73869a")
            if p in (2, 3):
                line((20, 18, 20, 21), WHITE)
        elif name == "lemonade":
            d.polygon([(14, 20), (26, 20), (24, 34), (16, 34)], fill="#879fa3", outline=INK)
            d.polygon([(15, 24), (25, 24), (23, 32), (17, 32)], fill="#e9c967")
            line((22, 29, 24, 17, 27, 17), PINK)
            orb((11, 20, 17, 26), GOLD)
            line((14, 21, 14, 25), WHITE)
            d.point((19, 26 + p % 4), WHITE)
        else:
            d.arc((24, 24, 32, 32), 270, 90, fill="#b4c5c9", width=2)
            box((13, 23, 26, 33), "#b56850")
            line((15, 25, 15, 31), "#f0b58b")
            orb((13, 21, 26, 25), DARK)
            line((16, 23, 22, 23), "#e6d2b4")
            steam(17, 20)
    elif name in ("cloud", "puddle", "window"):
        if name == "cloud":
            cloud(d, 20 + sway, 17, True)
            for x in (13, 22, 27):
                y = 26 + (p + x) % 5
                line((x, y, x - 1, y + 2), BLUE)
        elif name == "puddle":
            d.polygon(
                [(7, 31), (12, 29), (24, 29), (29, 31), (34, 32), (29, 34), (11, 34), (5, 33)],
                fill="#275976",
                outline="#548cab",
            )
            r = 2 + p % 4
            d.ellipse((20 - r, 31 - r // 2, 20 + r, 32 + r // 2), outline="#a0cbd8")
            line((10, 31, 15, 31), BLUE)
        else:
            box((9, 9, 31, 34), WOOD)
            box((11, 11, 29, 31), "#27465c")
            for i, x in enumerate((14, 18, 25, 27)):
                y = 13 + (p + i * 3) % 15
                line((x, y, x - 1, y + 3), BLUE)
            line((20, 11, 20, 31), "#d1a876", 2)
            line((11, 21, 29, 21), "#d1a876", 2)
            box((7, 32, 33, 34), "#d1a876")
    elif name in ("crescent", "globe", "clock", "balloon"):
        if name == "crescent":
            orb((13, 8, 28, 25), GOLD)
            d.ellipse((18, 5, 30, 20), fill=(0, 0, 0, 0))
            d.point((15, 18), WHITE if p < 3 else GOLD)
        elif name == "globe":
            orb((11, 13, 29, 31), "#337aad")
            d.polygon([(14, 17), (18, 15), (22, 16), (21, 20), (17, 21), (19, 25), (16, 27), (14, 23)], fill=GREEN)
            d.polygon([(24, 23), (27, 24), (26, 28), (23, 27)], fill=GREEN)
            d.arc((8, 11, 31, 33), 285, 100, fill=GOLD)
            line((20, 32, 20, 34), GOLD)
            line((15, 34, 25, 34), GOLD)
            d.point((14 + p // 3, 17), WHITE)
        elif name == "clock":
            orb((10, 13, 30, 33), WOOD)
            orb((12, 15, 28, 31), "#f0e5c5")
            for x, y in ((20, 17), (26, 23), (20, 29), (14, 23)):
                d.point((x, y), INK)
            line((20, 19, 20, 23, 24, 24), INK)
            a = p * math.tau / 8
            line((20, 23, round(20 + 5 * math.cos(a)), round(23 + 5 * math.sin(a))), PINK)
            line((13, 34, 15, 32), WOOD, 2)
            line((25, 32, 27, 34), WOOD, 2)
        else:
            x = 20 + sway
            orb((x - 6, 8, x + 6, 23), color)
            line((x - 3, 11, x - 4, 14), WHITE)
            d.polygon([(x, 23), (x - 1, 25), (x + 1, 25)], fill=color)
            line([(x, 26), (x - 2, 29), (x + 1, 32), (20, 35)], "#91aabb")
    elif name in ("broom", "rake", "scythe", "telescope"):
        if name == "telescope":
            line((20, 24, 13, 34), "#92a8b8", 2)
            line((20, 24, 28, 34), "#92a8b8", 2)
            d.polygon([(10, 19), (27, 11), (30, 18), (13, 26)], fill=BLUE, outline=INK)
            line((12, 20, 27, 13), WHITE)
            line((28, 12, 31, 18), "#a6c6d9", 3)
            line((9, 23, 12, 22), INK, 3)
            d.point((29, 14), WHITE if p < 3 else BLUE)
        else:
            line((13, 33, 25, 12), WOOD, 2)
            line((15, 29, 24, 13), GOLD)
            if name == "broom":
                d.polygon([(13, 25), (20, 29), (17, 34), (7, 34)], fill="#c89d57", outline=DARK)
                for x in (10, 13, 16):
                    line((x + 3, 28, x, 33), GOLD)
                line((13, 27, 18, 29), PINK)
                if p in (2, 3):
                    d.point((6, 33), WOOD)
            elif name == "rake":
                line((19, 12, 30, 18), "#94adb3", 2)
                for x, y in ((20, 13), (23, 15), (27, 17), (30, 18)):
                    line((x, y, x - 3, y + 4), "#94adb3")
                if p in (2, 3):
                    d.point((23, 14), WHITE)
            else:
                d.polygon([(24, 11), (18, 11), (12, 14), (8, 20), (15, 16), (23, 14)], fill="#94adb3", outline=INK)
                line((13, 14, 18, 12, 23, 12), WHITE if p < 3 else "#b0c5cb")
    elif name in ("sled", "train", "sandcastle"):
        if name == "sled":
            line([(7, 33), (28, 33), (32, 30)], "#94adb3", 2)
            for x in (12, 25):
                line((x, 27, x, 32), WOOD, 2)
            box((9, 25, 29, 28), PINK)
            line((11, 26, 26, 26), "#ffd3c4")
            line([(29, 25), (33, 21 + sway), (30, 20 + sway)], GOLD)
        elif name == "train":
            # Chassis stays on its rails; wheel spokes and chimney provide movement.
            line((3, 35, 37, 35), "#61798a")
            box((5, 22, 24, 30), color)
            box((6, 16, 15, 25), color)
            box((8, 18, 12, 22), "#b8e3e4")
            box((18, 18, 21, 23), WOOD)
            line((4, 16, 16, 16), GOLD, 2)
            box((27, 25, 36, 31), PINK)
            line((24, 29, 27, 29), "#91aabb")
            for x in (10, 21, 30, 35):
                orb((x - 3, 29, x + 3, 35), "#344c61")
                a = p * math.tau / 8
                line((x, 32, round(x + 2 * math.cos(a)), round(32 + 2 * math.sin(a))), GOLD)
            steam(18, 17)
        else:
            box((9, 25, 31, 34), "#c29c63")
            for x in (10, 26):
                box((x, 20, x + 5, 33), "#e8c68a")
                for dx in (0, 4):
                    box((x + dx, 18, x + dx + 1, 21), GOLD, GOLD)
            box((17, 22, 23, 33), "#e8c68a")
            d.arc((17, 28, 23, 38), 180, 360, fill=DARK, width=3)
            line((20, 21, 20, 12), WOOD)
            d.polygon([(21, 12), (28, 13 + sway), (21, 17)], fill=PINK)
            line((11, 27, 13, 27), GOLD)
    elif name == "dreidel":
        w = (6, 5, 3, 5, 6, 5, 3, 5)[p]
        line((20, 14, 20, 19), GOLD, 2)
        d.polygon([(20 - w, 20), (20, 18), (20 + w, 20), (20 + w, 28), (20, 34), (20 - w, 28)], fill=BLUE, outline=INK)
        d.polygon([(20, 19), (20 + w - 1, 21), (20 + w - 1, 28), (20, 32)], fill="#387eaf")
        if w > 3:
            line((17, 22, 17, 27, 19, 27, 19, 24), WHITE)
    elif name == "leaf":
        leaf(d, 20 + sway, 27, color, sway)
    elif name == "mittens":
        line([(13, 25), (15, 19 + sway), (24, 19 + sway), (27, 25)], "#7896a8")
        for x in (12, 26):
            orb((x - 4, 23, x + 4, 32), PINK)
            orb((x - 6, 27, x - 1, 31), PINK)
            box((x - 4, 31, x + 4, 34), "#f1d5c4")
            line((x - 2, 26, x + 2, 26), WHITE)
    elif name == "music":
        y = 20 + sway
        line([(16, y + 7), (16, y - 6), (27, y - 9), (27, y + 4)], BLUE, 2)
        line((17, y - 3, 26, y - 6), BLUE, 2)
        orb((10, y + 5, 16, y + 9), BLUE)
        orb((21, y + 2, 27, y + 6), BLUE)
    elif name:
        raise ValueError("Missing world prop: " + name)
    return im
