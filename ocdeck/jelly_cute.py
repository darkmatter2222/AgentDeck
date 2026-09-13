"""Small visual polish layer for Jelly's original integer-grid artwork."""

from functools import lru_cache

from PIL import ImageDraw


def install(art):
    """Keep Jelly's renderer API intact while softening silhouette and face."""
    art.POSES.update(
        {
            "idle": (26, 18, 0),
            "breathe": (27, 17, 0),
            "bob": (25, 19, 0),
            "squash": (30, 14, 1),
            "deep": (33, 12, 1),
            "launch": (19, 25, 3),
            "stretch": (21, 22, 2),
            "air": (24, 19, 1),
            "apex": (26, 17, 0),
            "fall": (22, 21, 0),
            "impact": (34, 12, 0),
            "rebound": (23, 20, -1),
            "jiggle": (27, 16, 1),
        }
    )
    base = art.logical_sprite
    body, shine, ink, cheek = art.PALETTE[2], art.PALETTE[4], art.PALETTE[5], art.PALETTE[6]

    @lru_cache(maxsize=384)
    def cute(pose="idle", face="neutral", gaze="center", gesture="", step=0):
        image = base(pose, face, gaze, gesture, step).copy()
        w, h, lean = art.POSES[pose]
        if h < 10:
            return image

        draw = ImageDraw.Draw(image)
        bottom = art.ANCHOR[1] - 1
        top = bottom - h + 1
        cx = 20 + lean // 2
        fy = min(bottom - 7, top + max(4, h // 2)) - (1 if gaze == "up" else 0)
        if gaze == "down":
            fy = min(bottom - 6, fy + 1)

        # Clear the old compact face without touching the outline, then redraw
        # larger low-set eyes. The proportions read clearly on 72-96 px keys.
        draw.rectangle((cx - 7, fy - 2, cx + 7, min(bottom - 2, fy + 7)), fill=body)
        dx = {"left": -1, "right": 1}.get(gaze, 0)
        eye_h = 4 if face in ("surprised", "jump", "landing", "curious") and h >= 15 else 3

        for ex in (cx - 4, cx + 3):
            if face in ("closed", "sleepy"):
                draw.line((ex - 1, fy + 1, ex + 2, fy + 1), fill=ink)
                draw.point((ex + 2, fy), fill=ink)
                continue
            if face == "half":
                draw.rectangle((ex - 1, fy, ex + 3, fy + 1), fill=shine)
                draw.line((ex - 1, fy, ex + 3, fy), fill=ink)
                continue

            eb = fy + eye_h
            draw.rectangle((ex - 1, fy, ex + 3, eb), fill=shine)
            for point in ((ex - 1, fy), (ex + 3, fy), (ex - 1, eb), (ex + 3, eb)):
                draw.point(point, fill=body)
            px = max(ex - 1, min(ex + 2, ex + dx))
            draw.rectangle((px, fy + 1, px + 1, min(eb - 1, fy + 3)), fill=ink)
            draw.point((px, fy + 1), fill=shine)

        my = min(bottom - 3, fy + 6)
        if face in ("jump", "surprised"):
            draw.rectangle((cx - 1, my - 1, cx + 1, my + 1), outline=ink)
        elif face == "focused":
            draw.line((cx - 2, my, cx + 2, my), fill=ink)
        elif face == "curious":
            draw.line([(cx - 1, my), (cx, my + 1), (cx + 1, my)], fill=ink)
        elif face in ("closed", "sleepy"):
            draw.line((cx - 1, my, cx + 1, my), fill=ink)
        else:
            draw.line([(cx - 2, my - 1), (cx - 1, my), (cx + 1, my), (cx + 2, my - 1)], fill=ink)

        if face in ("happy", "landing", "curious"):
            draw.rectangle((cx - 8, my - 1, cx - 7, my), fill=cheek)
            draw.rectangle((cx + 7, my - 1, cx + 8, my), fill=cheek)
        elif face == "neutral" and pose in ("idle", "breathe", "bob"):
            draw.point((cx - 7, my), fill=cheek)
            draw.point((cx + 7, my), fill=cheek)
        return image

    art.logical_sprite = cute
