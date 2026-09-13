"""Original Jelly artwork. All drawing happens on one 40x40 integer grid.

No transformed vector art, antialiasing, network assets or runtime file reads.
The bottom-center contact anchor (20, 34) is identical in every pose.
Cached images are immutable by convention; callers must not draw into them.
"""

from functools import lru_cache
from PIL import Image, ImageDraw

GRID = 40
ANCHOR = (20, 34)
PALETTE = ("#193849", "#267c91", "#40bec0", "#83e6d4", "#dbfff1", "#122b3e", "#f1a5c0")
# width, height, upper-body lean; approximate area stays constant.
POSES = {
    "idle": (24, 19, 0),
    "breathe": (25, 18, 0),
    "bob": (23, 20, 0),
    "squash": (29, 15, 1),
    "deep": (32, 13, 1),
    "launch": (18, 26, 3),
    "stretch": (20, 23, 2),
    "air": (23, 20, 1),
    "apex": (25, 18, 0),
    "fall": (21, 22, 0),
    "impact": (33, 13, 0),
    "rebound": (22, 21, -1),
    "jiggle": (26, 17, 1),
    "puddle": (34, 8, 0),
    "sleep_curl": (27, 14, -2),
    "slump": (28, 15, 3),
    "proud": (22, 23, 0),
    "curious_lean": (25, 18, 4),
    "lean_back": (25, 18, -4),
    "scoot_front": (28, 16, 4),
    "drag_tail": (30, 15, -3),
    "crawl_bridge": (31, 14, 0),
    "tiptoe": (21, 24, 0),
    "rolling_ball": (22, 22, 0),
    "side_flop": (30, 13, -3),
    "twisted": (23, 20, 3),
    "spiral": (23, 21, -2),
    "diagonal_smear": (19, 27, 4),
    "horizontal_smear": (35, 12, 3),
    "vertical_noodle": (16, 30, 0),
    "asym_impact": (33, 12, 4),
    "crown_ripple": (27, 17, -2),
    "double_arch": (24, 20, 0),
}


@lru_cache(maxsize=384)
def logical_sprite(pose="idle", face="neutral", gaze="center", gesture="", step=0):
    """Hand-directed pixel polygons; no scaling/deformation of finished pixels."""
    w, h, lean = POSES[pose]
    im = Image.new("RGBA", (GRID, GRID))
    d = ImageDraw.Draw(im)
    outline, shade, body, light, shine, ink, cheek = PALETTE
    left, right, base = 20 - w // 2, 20 + (w - 1) // 2, ANCHOR[1] - 1
    top = base - h + 1
    crown = 20 + lean
    points = [
        (left, base - 3),
        (left + 1, top + h // 2),
        (left + 4, top + 3),
        (crown - 5, top),
        (crown + 4, top),
        (right - 3, top + 3),
        (right - 1, top + h // 2),
        (right, base - 2),
        (right - 2, base),
        (left + 2, base),
    ]
    d.polygon(points, fill=body, outline=outline)
    if pose == "crawl_bridge":
        d.rectangle((16, base - 3, 24, base), fill=(0, 0, 0, 0))
        d.line((16, base - 4, 24, base - 4), fill=outline)
    if pose == "tiptoe":
        d.rectangle((left, base - 2, right, base), fill=(0, 0, 0, 0))
        d.rectangle((left + 3, base - 2, left + 5, base), fill=outline)
        d.rectangle((right - 5, base - 2, right - 3, base), fill=outline)
    if pose == "crown_ripple":
        d.line([(crown - 4, top + 1), (crown - 1, top + 3), (crown + 3, top + 1)], fill=light)
    if pose == "spiral":
        d.line(
            [(crown - 5, top + 4), (crown + 4, top + 4), (crown + 4, top + 7), (crown, top + 7)], fill=shade, width=2
        )
    d.line(
        [(left + 2, base - 4), (left + 4, base - 2), (right - 3, base - 2), (right - 1, base - 4)], fill=shade, width=2
    )
    d.line(
        [(left + 4, top + h // 2), (left + 5, top + 5), (crown - 4, top + 2), (crown + 2, top + 2)], fill=light, width=2
    )
    d.line((crown - 4, top + 3, crown - 1, top + 3), fill=shine, width=1)
    # Facial features use the same logical grid, tied to the deforming body.
    dx = {"left": -1, "right": 1}.get(gaze, 0)
    fy = min(base - 5, top + max(3, h // 2)) - (1 if gaze == "up" else 0)
    if gaze == "down":
        fy = min(base - 4, fy + 1)
    cx = 20 + lean // 2
    for ex in (cx - 5, cx + 4):
        if face in ("closed", "sleepy"):
            d.line((ex - 1, fy + 1, ex + 2, fy + 1), fill=ink)
        elif face == "half":
            d.rectangle((ex, fy + 1, ex + 2, fy + 2), fill=ink)
        else:
            eh = min(4 if face in ("surprised", "jump", "landing") else 3, max(1, h - 6))
            d.rectangle((ex - 1, fy - 1, ex + 3, fy + eh), fill=shine)
            d.rectangle((ex + dx, fy, ex + dx + 1, fy + eh - 1), fill=ink)
    my = min(base - 3, fy + 5)
    if face in ("jump", "surprised"):
        d.rectangle((cx - 1, my - 1, cx + 1, my + 1), fill=ink)
    elif face == "focused":
        d.line((cx - 1, my, cx + 2, my), fill=ink)
    else:
        d.line([(cx - 2, my - 1), (cx - 1, my), (cx + 1, my), (cx + 2, my - 1)], fill=ink)
    if face in ("happy", "landing"):
        d.point((cx - 7, my - 1), fill=cheek)
        d.point((cx + 7, my - 1), fill=cheek)
    if pose == "double_arch" and not gesture:
        gesture, step = "cheer", 3
    if gesture and step:
        # A growing, thick pseudopod shares the outline and fill of the body.
        length = (2, 4, 7, 8)[min(step, 4) - 1]
        root = (right - 3, base - 7)
        tip = (min(38, root[0] + length), root[1] - (length if gesture == "wave" else 2))
        elbow = (min(36, root[0] + length - 1), root[1] - 2)
        if gesture == "wave" and step == 4:
            tip = (tip[0] - 2, tip[1] - 1)
        if gesture in ("up", "scratch", "cheer", "clap"):
            tip = (30 if gesture != "scratch" else 24, max(2, top - 2))
            if gesture == "clap":
                tip = (22 if step % 2 else 27, max(2, top - 2))
        elif gesture == "down":
            tip = (min(38, right + 1), base - 1)
        d.line([root, elbow, tip], fill=outline, width=5)
        d.line([root, elbow, tip], fill=body, width=3)
        d.point(tip, fill=light)
        if gesture in ("cheer", "clap"):
            d.line([(40 - root[0], root[1]), (40 - elbow[0], elbow[1]), (40 - tip[0], tip[1])], fill=outline, width=5)
            d.line([(40 - root[0], root[1]), (40 - elbow[0], elbow[1]), (40 - tip[0], tip[1])], fill=body, width=3)
    return im


@lru_cache(maxsize=512)
def sprite(pose="idle", face="neutral", gaze="center", gesture="", step=0, scale=2, mirror=False):
    image = logical_sprite(pose, face, gaze, gesture, step)
    if mirror:
        # Flipping about x=20 rather than x=19.5 preserves the contact anchor.
        flipped = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        image = Image.new("RGBA", image.size)
        image.paste(flipped, (1, 0))
    return image.resize((GRID * scale, GRID * scale), Image.Resampling.NEAREST)


# Base body shades, not UI status colors. Outline/eyes retain their contrast.
MOOD_COLORS = {
    "content": "40bec0",
    "curious": "56bdeb",
    "playful": "f49f9e",
    "sleepy": "b09ae0",
    "asleep": "8277ad",
    "waking": "b6abe3",
    "attentive": "64c5d6",
    "thinking": "759fe0",
    "focused": "609cce",
    "excited": "59dfc8",
    "proud": "e4c574",
    "helpful": "79cbbb",
    "concerned": "d6b17e",
    "startled": "c9e9e9",
    "cautious": "c5b2a1",
    "shy": "bbadd0",
    "bored": "92acc0",
    "restless": "9dc6d0",
    "mischievous": "d297c2",
    "overwhelmed": "878ba9",
    "peckish": "e6b39b",
    "overworked": "8b95b8",
    "recovering": "9bbabf",
}


@lru_cache(maxsize=512)
def colored_sprite(pose, face, gaze, gesture, step, scale, mirror, mood, previous="content", blend=3):
    """Four palette steps preserve a single pixel grid, alpha and dark outlines."""
    im = sprite(pose, face, gaze, gesture, step, scale, mirror)
    if mood == previous == "content":
        return im
    old = bytes.fromhex(MOOD_COLORS[previous])
    new = bytes.fromhex(MOOD_COLORS[mood])
    body = tuple(round(a + (b - a) * blend / 3) for a, b in zip(old, new))
    colors = (tuple(round(v * 0.64) for v in body), body, tuple(round(v + (255 - v) * 0.48) for v in body))
    mapping = {tuple(bytes.fromhex(PALETTE[i][1:])): color for i, color in zip((1, 2, 3), colors)}
    # Small palette lookup; cached per held sprite/mood, never resized with smoothing.
    out = im.copy()
    pixels = out.load()
    assert pixels is not None
    for y in range(im.height):
        for x in range(im.width):
            value = pixels[x, y]
            assert isinstance(value, tuple)
            rgb = mapping.get(value[:3])
            if rgb:
                pixels[x, y] = (*rgb, value[3])
    return out
