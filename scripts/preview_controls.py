"""Render the production six-key controls with fixture data; no USB or agent launch."""

import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw, ImageFont
from ocdeck.broker import Broker
from ocdeck.controls import control_frame


def compose(tiles, phase, heading):
    im = Image.new("RGB", (760, 590), "#080e19")
    draw = ImageDraw.Draw(im)
    draw.text((40, 28), "AGENTSTREAMDECK", font=ImageFont.load_default(size=20), fill="#58c6ff")
    draw.text((40, 61), heading, font=ImageFont.load_default(size=29), fill="#f2f6fc")
    draw.rounded_rectangle((28, 115, 732, 533), radius=40, fill="#171f2d", outline="#334255", width=2)
    for k, tile in enumerate(tiles):
        im.paste(control_frame(tile["title"], tile["subtitle"], tile["tone"], phase, 180),
                 (70 + (k % 3) * 220, 136 + (k // 3) * 194))
    draw.text((40, 556), "Production UI renderer / simulated deck / fixture requests", font=ImageFont.load_default(size=15), fill="#9bafc5")
    return im


def main():
    output = Path(__file__).resolve().parents[1] / "docs/controls"
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / "config.json").write_text(json.dumps({"controls": {"enabled": True, "permissions": True}}))
        (root / "launcher.ini").write_text("".join(
            f"[repo:{name}]\ndirectory=/projects/{name.replace(' ', '-')}\nharnesses=claude,opencode,codex,gemini\n"
            for name in ("AgentStreamDeck", "Home AI Lab", "API Worktree", "Website")))
        broker = Broker(root, mock=True, probe=lambda _: True)
        controls = broker.controls
        controls.open(broker.registry.view()[0])
        scenes = [("Pick a project. Choose your agent.", controls.tiles())]
        controls.handle(controls.tiles()[0])
        scenes.append(("Your familiar harnesses, one picker.", controls.tiles()))
        broker.registry.upsert({"id": "fixture", "process": {"pid": 1}, "label": "Claude / AgentStreamDeck"})
        broker.permissions.offer({"owner": "fixture", "tool": "Bash", "summary": "python -m unittest discover -s tests"})
        controls.open(broker.registry.view()[0])
        for action in ("review", "request"):
            controls.handle(next(t for t in controls.tiles() if t["command"] == action))
        scenes.append(("One request. One deliberate decision.", controls.tiles()))
        frames = []
        for heading, tiles in scenes:
            for phase in range(24):
                frames.append(compose(tiles, phase, heading))
        frames[0].save(output / "preview.gif", save_all=True, append_images=frames[1:], duration=125, loop=0)
        compose(scenes[-1][1], 0, scenes[-1][0]).save(output / "permission-review.png")
        print(output)


if __name__ == "__main__":
    main()
