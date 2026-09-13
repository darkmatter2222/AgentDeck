"""Show every expanded action, pose, mood and hop, plus a scripted agent encounter."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw
from ocdeck.jelly import Jelly, DeckGeometry
from ocdeck.jelly_catalog import ACTIONS, HOPS, MOODS
from ocdeck.jelly_art import POSES, colored_sprite
from preview_jelly import deck_frame, save_gif


def tile(jelly, name):
    im = Image.new("RGB", (112, 112), "#142030")
    ImageDraw.Draw(im).rectangle((16, 8, 95, 87), fill="black")
    crop = jelly.crops({0}).get(0)
    if crop is not None:
        im.paste(crop, (16, 8), crop)
    ImageDraw.Draw(im).text((5, 94), name, fill="#d8e4ed")
    return im


def gallery(output, fps):
    # Actual runtime poses/motion rendered into independent one-key worlds.
    actors = []
    for action in ACTIONS:
        j = Jelly(DeckGeometry(1, 1), 7, options={"thoughts": "off", "needs": False})
        j.settle(0, 0)
        j.start_action(action, 0)
        actors.append((action, j))
    frames = []
    for frame in range(fps * 4):
        im = Image.new("RGB", (112 * 5, 112 * 4))
        for index, (name, j) in enumerate(actors):
            t = frame / fps
            # Hold the final pose for comparison; next loop replays each action.
            j.now = t
            j._local_pose(min(t, j.action_duration))
            im.paste(tile(j, name), (index % 5 * 112, index // 5 * 112))
        frames.append(im)
    save_gif(frames, output / "jelly_actions.gif", fps)
    frames[fps].save(output / "jelly_actions.png")
    im = Image.new("RGB", (112 * 6, 112 * 4))
    for i, mood in enumerate(MOODS):
        j = Jelly(DeckGeometry(1, 1), 7, options={"thoughts": "off"})
        j.settle(0, 0)
        j.mind.set_mood(mood, 0)
        j.now = 2
        j.pose = {
            "asleep": "sleep_curl",
            "sleepy": "slump",
            "overworked": "slump",
            "overwhelmed": "puddle",
            "proud": "proud",
            "curious": "curious_lean",
        }.get(mood, "idle")
        j.face = "sleepy" if mood in ("asleep", "sleepy") else "happy"
        im.paste(tile(j, mood), (i % 6 * 112, i // 6 * 112))
    im.save(output / "jelly_moods.png")
    im = Image.new("RGB", (112 * 6, 112 * 6))
    for i, pose in enumerate(POSES):
        j = Jelly(DeckGeometry(1, 1), 7, options={"thoughts": "off"})
        j.settle(0, 0)
        j.pose = pose
        im.paste(tile(j, pose), (i % 6 * 112, i // 6 * 112))
    im.save(output / "jelly_poses.png")


def hops(output, fps):
    actors = []
    for name in HOPS:
        j = Jelly(DeckGeometry(1, 2), 7, name, {"thoughts": "off", "needs": False})
        j.settle(0, 0)
        j.hop(1, 0.3, {0, 1})
        actors.append((name, j))
    frames = []
    for frame in range(fps * 4):
        im = Image.new("RGB", (200 * 4, 110 * 4), "#142030")
        d = ImageDraw.Draw(im)
        for i, (name, j) in enumerate(actors):
            j.update(frame / fps, {0, 1})
            x, y = i % 4 * 200 + 8, i // 4 * 110 + 5
            d.rectangle((x, y, x + 79, y + 79), fill="black")
            d.rectangle((x + 88, y, x + 167, y + 79), fill="black")
            for k, crop in j.crops({0, 1}).items():
                im.paste(crop, (x + k * 88, y), crop)
            d.text((x, y + 86), name, fill="white")
        frames.append(im)
    save_gif(frames, output / "jelly_hop_styles.gif", fps)


def encounter(output, fps):
    j = Jelly(DeckGeometry(), 12, "mood", {"thoughts": "chatty"})
    j.settle(3, 0)
    j.thoughts.next_at = 0
    views = [{"id": None, "state": "off"} for _ in range(6)]
    views[2] = {"id": "demo", "state": "running"}
    frames = []
    for i in range(fps * 24):
        t = i / fps
        if i == fps * 4:
            views[2]["state"] = "input"
        if i == fps * 14:
            views[2]["state"] = "running"
        if i == fps * 18:
            views[2].update(state="idle", outcome="success", outcomeId="demo-success")
        free = {k for k, v in enumerate(views) if v["state"] == "off"}
        j.update(t, free, views)
        im = deck_frame(j, free, True)
        # State label distinguishes the scripted input/success phases in this demo.
        ImageDraw.Draw(im).text((36, im.height - 20), views[2]["state"] + " / " + j.mind.mood, fill="white")
        frames.append(im)
    save_gif(frames, output / "jelly_agent_reactions.gif", fps)
    # Single-key readable thought, with the same rendering and scrolling implementation.
    j = Jelly(DeckGeometry(1, 1), 7, options={"thoughts": "chatty", "needs": False})
    j.settle(0, 0)
    j.thoughts.next_at = 0
    j.thoughts.say("quiet", 0)
    j.deadline = 100
    frames = []
    for i in range(int((j.thoughts.until + 1) * fps)):
        j.now = i / fps
        frames.append(tile(j, "floor + thought").resize((336, 336), Image.Resampling.NEAREST))
    save_gif(frames, output / "jelly_thoughts.gif", fps)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/jelly"))
    parser.add_argument("--fps", type=int, choices=(24, 30), default=24)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    gallery(args.output, args.fps)
    hops(args.output, args.fps)
    encounter(args.output, args.fps)
    (args.output / "catalog.json").write_text(
        json.dumps(
            {"actions": list(ACTIONS), "poses": list(POSES), "hop_styles": list(HOPS), "moods": list(MOODS)}, indent=2
        )
        + "\n"
    )
    print("Expanded previews:", args.output)


if __name__ == "__main__":
    main()
