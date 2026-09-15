"""Reproducible native/enlarged object and atmosphere audit from production art."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFont
from ocdeck.world_props import prop
from ocdeck.world_art import sky
from ocdeck.world_catalog import SCENES

OUT = Path(__file__).resolve().parents[1] / "docs/jelly"


def main():
    names = sorted({s.prop for s in SCENES.values() if s.prop} | {"icicles"})
    font = ImageFont.load_default(size=12)
    frames = []
    for phase in range(8):
        sheet = Image.new("RGB", (960, ((len(names) + 7) // 8) * 130), "#09111b")
        d = ImageDraw.Draw(sheet)
        for i, name in enumerate(names):
            x, y = (i % 8) * 120, (i // 8) * 130
            d.text((x + 5, y + 4), name, fill="#dbfff1", font=font)
            im = prop(name, phase, "#dca16b" if name == "leaf" else "#b4a0de")
            sheet.paste(im, (x + 3, y + 66), im)
            enlarged = im.resize((80, 80), Image.Resampling.NEAREST)
            sheet.paste(enlarged, (x + 40, y + 26), enlarged)
        frames.append(sheet)
    frames[0].save(OUT / "world-objects.png")
    frames[0].save(OUT / "world-objects.gif", save_all=True, append_images=frames[1:], duration=250, loop=0)
    kinds = sorted({s.sky for s in SCENES.values() if s.sky})
    frames = []
    for phase in range(48):
        sheet = Image.new("RGB", (800, ((len(kinds) + 4) // 5) * 115), "#09111b")
        d = ImageDraw.Draw(sheet)
        for i, kind in enumerate(kinds):
            x, y = i % 5 * 160, i // 5 * 115
            d.text((x + 5, y + 4), kind, fill="#dbfff1", font=font)
            im = Image.new("RGBA", (76, 42))
            sky(ImageDraw.Draw(im), kind, 76, 42, phase, "#dca16b")
            im = im.resize((152, 84), Image.Resampling.NEAREST)
            sheet.paste(im, (x + 4, y + 24), im)
        frames.append(sheet)
    frames[0].save(OUT / "world-atmosphere.gif", save_all=True, append_images=frames[1:], duration=125, loop=0)


if __name__ == "__main__":
    main()
