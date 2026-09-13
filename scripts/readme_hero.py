"""Generate the evergreen README hero without changing documentation."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont

from ocdeck.appearance import Appearance
from ocdeck.art import frame as agent_frame
from ocdeck.jelly import DeckGeometry, Jelly

OUT = ROOT / "docs" / "jelly" / "readme_hero.gif"
W, H, FPS, SECONDS = 1000, 420, 8, 6
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size, bold=False):
    try:
        return ImageFont.truetype(BOLD if bold else FONT, size)
    except OSError:
        return ImageFont.load_default()


def deck_shell(image):
    draw = ImageDraw.Draw(image)
    x, y = 548, 64
    draw.rounded_rectangle((x, y, x + 390, y + 292), 34, fill="#303947", outline="#536172", width=2)
    draw.rounded_rectangle((x + 10, y + 10, x + 380, y + 282), 28, fill="#111925")
    draw.text((x + 195, y + 18), "STREAM DECK", anchor="ma", font=font(10, True), fill="#8494a7")
    return x + 28, y + 52


def background():
    image = Image.new("RGB", (W, H), "#080d18")
    draw = ImageDraw.Draw(image)
    for i in range(8):
        draw.ellipse((655 - i * 12, 20 - i * 8, 1080 + i * 18, 430 + i * 14), fill=(9 + i, 24 + i * 2, 37 + i * 3))
    draw.rectangle((0, 0, 7, H), fill="#61dec3")
    draw.text((50, 48), "AGENTSTREAMDECK", font=font(14, True), fill="#70e7cb")
    draw.text((48, 91), "Mission control for", font=font(42, True), fill="#f4f7fb")
    draw.text((48, 141), "AI coding agents.", font=font(42, True), fill="#f4f7fb")
    draw.text((50, 211), "See the session. Press the key. Get back to code.", font=font(16), fill="#b2c0d2")
    draw.rounded_rectangle((48, 268, 345, 309), 20, fill="#102d31", outline="#2c7168")
    draw.text((196, 289), "MEET JELLY  •  OFFLINE  •  ON BY DEFAULT", anchor="mm", font=font(11, True), fill="#8af0d5")
    draw.text((50, 338), "Your coding companion lives in the keys you are not using.", font=font(13), fill="#8297aa")
    return image


def make_frames():
    base = background()
    jelly = Jelly(DeckGeometry(), 7, "fluid", {"needs": False, "thoughts": "off"})
    jelly.settle(3, 0)
    jelly.deadline = 100
    free = {3, 4, 5}
    frames = []

    for index in range(FPS * SECONDS):
        t = index / FPS
        if index == 5:
            jelly.start_action("nod", t)
        elif index == 13:
            jelly.hop(4, t, free)
        elif index == 28:
            jelly.start_action("dance", t)
        elif index == 36:
            jelly.hop(5, t, free)
        jelly.update(t, free)
        if jelly.state == "idle":
            jelly.deadline = 100

        image = base.copy()
        draw = ImageDraw.Draw(image)
        ox, oy = deck_shell(image)
        crops = jelly.crops(free)
        for key in range(6):
            col, row = key % 3, key // 3
            kx, ky = ox + col * 116, oy + row * 116
            draw.rounded_rectangle((kx - 4, ky - 4, kx + 99, ky + 99), 14, fill="#03060b", outline="#3e4b5a", width=2)
            if key < 3:
                state = ("running", "idle", "input")[key]
                label = ("API", "WEB", "TEST")[key]
                tile = agent_frame(
                    state,
                    label,
                    key,
                    index % 96,
                    style=Appearance(layout="harness"),
                    harness=("opencode", "claude", "codex")[key],
                ).resize((96, 96), Image.Resampling.LANCZOS)
            else:
                tile = Image.new("RGB", (80, 80), "black")
                if key in crops:
                    tile.paste(crops[key], (0, 0), crops[key])
                tile = tile.resize((96, 96), Image.Resampling.NEAREST)
            mask = Image.new("L", (96, 96))
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, 95, 95), 10, fill=255)
            image.paste(tile, (kx, ky), mask)
        frames.append(image)
    return frames


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames = make_frames()
    frames[0].save(
        OUT,
        save_all=True,
        append_images=frames[1:],
        duration=1000 // FPS,
        loop=0,
        optimize=True,
    )
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
