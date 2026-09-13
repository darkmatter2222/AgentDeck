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
    d.line(
        [(left + 2, base - 4), (left + 4, base - 2), (right - 3, base - 2), (right - 1, base - 4)], fill=shade, width=2
    )
    d.line(
        [(left + 4, top + h // 2), (left + 5, top + 5), (crown - 4, top + 2), (crown + 2, top + 2)], fill=light, width=2
    )
    d.line((crown - 4, top + 3, crown - 1, top + 3), fill=shine, width=1)
    # Facial features use the same logical grid, tied to the deforming body.
    dx = {"left": -1, "right": 1}.get(gaze, 0)
    fy = top + max(5, h // 2) - (1 if gaze == "up" else 0)
    cx = 20 + lean // 2
    for ex in (cx - 5, cx + 4):
        if face in ("closed", "sleepy"):
            d.line((ex - 1, fy + 1, ex + 2, fy + 1), fill=ink)
        elif face == "half":
            d.rectangle((ex, fy + 1, ex + 2, fy + 2), fill=ink)
        else:
            eh = 4 if face in ("surprised", "jump", "landing") else 3
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
    if gesture and step:
        # A growing, thick pseudopod shares the outline and fill of the body.
        length = (2, 4, 7, 8)[min(step, 4) - 1]
        root = (right - 3, base - 7)
        tip = (min(38, root[0] + length), root[1] - (length if gesture == "wave" else 2))
        elbow = (min(36, root[0] + length - 1), root[1] - 2)
        if gesture == "wave" and step == 4:
            tip = (tip[0] - 2, tip[1] - 1)
        d.line([root, elbow, tip], fill=outline, width=5)
        d.line([root, elbow, tip], fill=body, width=3)
        d.point(tip, fill=light)
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
