"""Generate the compact README hero and normalize the README opening."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont

from ocdeck.appearance import Appearance
from ocdeck.art import frame as agent_frame
from ocdeck.jelly import DeckGeometry, Jelly

OUT = ROOT / "docs" / "jelly" / "readme_hero.gif"
README = ROOT / "README.md"
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
    draw.text((50, 48), "AGENTSTREAMDECK  •  V3.0", font=font(14, True), fill="#70e7cb")
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


def rewrite_readme():
    text = README.read_text(encoding="utf-8")
    marker = "## New in 3.0 — Meet your coding Jelly"
    _, rest = text.split(marker, 1)
    opening = """# AgentStreamDeck

<p align="center">
  <img src="docs/jelly/readme_hero.gif" alt="AgentStreamDeck mission control with Jelly living across unused Stream Deck keys" width="100%">
</p>

**Mission control for AI coding agents on your Stream Deck.** See activity at a glance, then press a key to focus the right session. Jelly, the offline coding companion introduced in v3.0, lives in the keys you are not using.

[![Tests](https://github.com/darkmatter2222/AgentStreamDeck/actions/workflows/ci.yml/badge.svg)](https://github.com/darkmatter2222/AgentStreamDeck/actions/workflows/ci.yml)
[![GitHub stars](https://img.shields.io/github/stars/darkmatter2222/AgentStreamDeck?style=flat-square&logo=github&color=gold)](https://github.com/darkmatter2222/AgentStreamDeck/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/darkmatter2222/AgentStreamDeck?style=flat-square&logo=github)](https://github.com/darkmatter2222/AgentStreamDeck/forks)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue?style=flat-square)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](pyproject.toml)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat-square)](#requirements)
[![Stream Deck Mini, MK.2 and XL](https://img.shields.io/badge/Stream_Deck-Mini%20%7C%20MK.2%20%7C%20XL-8A2BE2?style=flat-square)](#requirements)

> ⭐ **If AgentStreamDeck is useful, [star the repo](https://github.com/darkmatter2222/AgentStreamDeck).** It helps other developers find the project.

AgentStreamDeck connects OpenCode, Claude Code, GitHub Copilot CLI, Copilot in VS Code, Gemini CLI, Cursor CLI and Codex CLI to one local controller over direct USB HID. No Elgato plugin or MCP server is required.

> **Upgrading from AgentDeck?** The Python distribution is now `agentstreamdeck`; the `ocdeck` command, existing configuration and hook receipts remain compatible. See [rename and upgrade steps](docs/RENAMING.md).

"""
    body = marker + rest
    old_showcase = """![Jelly living on a Stream Deck — AgentStreamDeck 3.0](docs/jelly/jelly_v3_showcase.gif)

*An authored product animation using the actual Jelly and agent renderers;
a simulated Stream Deck Mini, not filmed hardware.*
"""
    body = body.replace(old_showcase, "")
    README.write_text(opening + body, encoding="utf-8")


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
    rewrite_readme()
    print(f"wrote {OUT.relative_to(ROOT)} and refreshed README opening")


if __name__ == "__main__":
    main()
