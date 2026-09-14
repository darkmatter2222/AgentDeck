"""Rebuild living-world documentation previews from the production renderer."""

from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFont
from ocdeck.world_cli import preview
from ocdeck.world_catalog import SCENES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/jelly"


def main():
    chosen = [
        "sky_fireworks",
        "thanksgiving_table",
        "christmas_lights",
        "ghost_hover",
        "holi_colors",
        "rain",
        "hot",
        "winter_snowball",
    ]
    frames = []
    with tempfile.TemporaryDirectory() as root:
        for scene in chosen:
            file = Path(root) / (scene + ".gif")
            preview(scene, file)
            with Image.open(file) as gif:
                for n in range(0, gif.n_frames, 2):
                    gif.seek(n)
                    im = Image.new("RGB", (560, 390), "#09111b")
                    draw = ImageDraw.Draw(im)
                    draw.text((16, 12), SCENES[scene].title, font=ImageFont.load_default(size=20), fill="#dbfff1")
                    im.paste(gif.convert("RGB").resize((528, 336), Image.Resampling.NEAREST), (16, 44))
                    frames.append(im)
        frames[0].save(
            OUT / "world-showcase.gif", save_all=True, append_images=frames[1:], duration=166, loop=0, optimize=True
        )
        # Native-size scene cards cover every recipe, including all fifty extras.
        sheet = Image.new("RGB", (1000, ((len(SCENES) + 4) // 5) * 125), "#09111b")
        draw = ImageDraw.Draw(sheet)
        from ocdeck.world import World
        from ocdeck.world_weather import WeatherService
        from ocdeck.world_settings import settings
        from ocdeck.jelly import Jelly, DeckGeometry

        for i, scene in enumerate(SCENES):
            o = settings(dict(scene_override=scene, auto_location=False, weather=False, captions=False))
            world = World(o, WeatherService(o))
            jelly = Jelly(DeckGeometry(), seed=2, options={"thoughts": "off"})
            jelly.settle(0, 0)
            world.tick(1, jelly)
            crops = world.decorate(1, jelly, jelly.crops({0, 1}), {0, 1})
            x, y = (i % 5) * 200, (i // 5) * 125
            draw.text((x + 6, y + 3), scene, font=ImageFont.load_default(size=10), fill="#dbfff1")
            for key in (0, 1):
                bg = Image.new("RGBA", (80, 80), "#050910")
                if key in crops:
                    bg.alpha_composite(crops[key])
                sheet.paste(bg.convert("RGB"), (x + 6 + key * 88, y + 25))
        sheet.save(OUT / "world-catalog.png")


if __name__ == "__main__":
    main()
