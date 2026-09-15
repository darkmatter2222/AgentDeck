"""Production director previews, including real approach hops and prop outcomes."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFont
from ocdeck.jelly import Jelly, DeckGeometry
from ocdeck.world import World
from ocdeck.world_settings import settings
from ocdeck.world_weather import WeatherService

OUT = Path(__file__).resolve().parents[1] / "docs/jelly"
SCENES = [
    "autumn_rake",
    "halloween_witch",
    "autumn_cocoa",
    "christmas_elf",
    "spring_seedling",
    "summer_beachball",
    "valentine_letter",
    "birthday_cake",
    "night_stargazing",
    "christmas_train",
    "winter_snowball",
    "autumn_acorn",
]


def render(scene, size=80):
    g = DeckGeometry(2, 3, size, size)
    o = settings(dict(scene_override=scene, weather=False, auto_location=False, captions=False))
    world = World(o, WeatherService(o))
    jelly = Jelly(g, seed=2, options={"thoughts": "off", "needs": False, "travel": "rare"})
    jelly.settle(0, 0)
    frames = []
    stages = []
    for n in range(168):
        now = n / 12
        free = {0, 1}
        jelly.update(now, free)
        world.tick(now, jelly, free)
        crops = world.decorate(now, jelly, jelly.crops(free), free)
        im = Image.new("RGB", (size * 2 + 8, size), "#09111b")
        for key in free:
            tile = Image.new("RGBA", (size, size), "#050910")
            if key in crops:
                tile.alpha_composite(crops[key])
            im.paste(tile.convert("RGB"), (key * (size + 8), 0))
        frames.append(im)
        stages.append(world.interaction.stage or "ambient")
    return frames, stages


def main():
    reels = [render(s) for s in SCENES]
    frames = []
    for n in range(168):
        sheet = Image.new("RGB", (760, 4 * 125), "#09111b")
        d = ImageDraw.Draw(sheet)
        for i, scene in enumerate(SCENES):
            x, y = i % 3 * 252, i // 3 * 125
            d.text((x + 6, y + 4), scene, fill="#dbfff1", font=ImageFont.load_default(size=13))
            sheet.paste(reels[i][0][n], (x + 6, y + 25))
            d.text((x + 180, y + 60), reels[i][1][n], fill="#8ea8b5", font=ImageFont.load_default(size=10))
        frames.append(sheet)
    frames[0].save(OUT / "world-interactions.gif", save_all=True, append_images=frames[1:], duration=83, loop=0)
    rake, _ = reels[0]
    rake[0].resize((504, 240), Image.Resampling.NEAREST).save(
        OUT / "world-raking.gif",
        save_all=True,
        append_images=[im.resize((504, 240), Image.Resampling.NEAREST) for im in rake[1:]],
        duration=83,
        loop=0,
    )


if __name__ == "__main__":
    main()
