"""Reproduce Jelly artwork, directional GIFs and CPU-only timing without HID.

python scripts/preview_jelly.py --fps 30 --output docs/jelly
python scripts/preview_jelly.py --benchmark --output docs/jelly
"""

import argparse
import json
from pathlib import Path
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw
from ocdeck.jelly import DeckGeometry, Jelly
from ocdeck.jelly_art import ANCHOR, GRID, POSES, logical_sprite
from ocdeck.jelly_catalog import HOPS


def deck_frame(jelly, available, debug=False):
    g = jelly.geometry
    margin, footer = 18, 25
    image = Image.new("RGB", (g.size[0] + margin * 2, g.size[1] + margin * 2 + footer), "#141a24")
    d = ImageDraw.Draw(image)
    crops = jelly.crops(available)
    for key in range(g.count):
        x, y, r, b = g.bounds(key)
        x, y, r, b = x + margin, y + margin, r + margin, b + margin
        d.rectangle((x - 2, y - 2, r + 1, b + 1), fill="#303c4d")
        d.rectangle((x, y, r - 1, b - 1), fill="black")
        if key not in available:
            color = "#60efb1" if key % 2 == 0 else "#ffd074"
            d.ellipse((x + 29, y + 15, x + 49, y + 35), fill=color)
            d.text((x + 14, y + 48), "AGENT", fill=color)
        elif key in crops:
            image.paste(crops[key], (x, y), crops[key])
    caption = f"{jelly.state} / {jelly.pose}" if debug else "LIVING JELLY  /  EXPERIMENTAL"
    d.text((margin, image.height - 20), caption, fill="#adc0d6")
    return image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST)


def save_gif(frames, path, fps):
    # GIF uses 10ms ticks: distribute rounding instead of silently making 30fps 33fps.
    durations = [10 * (round((i + 1) * 100 / fps) - round(i * 100 / fps)) for i in range(len(frames))]
    frames[0].save(
        path, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=False, disposal=2
    )


def hop_frames(source, destination, fps, variant, debug=False):
    jelly = Jelly(DeckGeometry(), seed=7, hop_style=variant)
    free = {source, destination}
    jelly.settle(source, 0)
    jelly.hop(destination, 0.5, free)
    frames = []
    for i in range(round(3 * fps)):
        jelly.update(i / fps, free)
        frames.append(deck_frame(jelly, free, debug))
    return frames


def sprite_sheet(output):
    frames = [(pose, "neutral", "center", "", 0) for pose in POSES]
    frames += [
        ("idle", face, "center", "", 0)
        for face in ("happy", "curious", "focused", "surprised", "sleepy", "jump", "landing", "half", "closed")
    ]
    frames += [("idle", "curious", gaze, "", 0) for gaze in ("left", "right", "up")]
    frames += [("idle", "happy", "right", gesture, step) for gesture in ("wave", "point") for step in range(5)]
    sheet = Image.new("RGBA", (GRID * 8, GRID * ((len(frames) + 7) // 8)))
    metadata = {
        "grid": GRID,
        "anchor": ANCHOR,
        "copyright": "Original AgentStreamDeck Jelly; repository MIT license",
        "frames": [],
    }
    for i, args in enumerate(frames):
        x, y = i % 8 * GRID, i // 8 * GRID
        sheet.paste(logical_sprite(*args), (x, y))
        metadata["frames"].append(
            {
                "name": "_".join(map(str, args)),
                "rect": [x, y, GRID, GRID],
                "duration_ms": 100,
                "group": args[3] or args[0],
                "anchor": ANCHOR,
            }
        )
    sheet.save(output / "jelly_sprite_sheet.png")
    (output / "jelly_sprite_sheet.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return sheet


def benchmark():
    from StreamDeck.Devices.StreamDeckMini import StreamDeckMini
    from StreamDeck.ImageHelpers import PILHelper

    # Driver metadata/conversion only: no transport or connected hardware.
    class NoTransport:
        def connected(self):
            return False

        def close(self):
            pass

    deck = StreamDeckMini(NoTransport())
    results = []
    for style in HOPS:
        for fps in (24, 30):
            jelly = Jelly(DeckGeometry(), seed=7, hop_style=style)
            free = {1, 2, 4, 5}
            jelly.settle(1, 0)
            composition, conversion = [], []
            cpu_start = time.process_time()
            for i in range(fps * 30):
                now = i / fps
                if jelly.state == "idle":
                    destination = next(k for k in jelly.geometry.adjacent(jelly.current) if k in free)
                    jelly.hop(destination, now, free)
                t = time.perf_counter()
                jelly.update(
                    now,
                    free,
                    [
                        {"id": None if k in free else str(k), "state": "off" if k in free else "running"}
                        for k in range(6)
                    ],
                )
                crops = jelly.crops(free)
                composition.append((time.perf_counter() - t) * 1000)
                t = time.perf_counter()
                for crop in crops.values():
                    PILHelper.to_native_key_format(deck, crop.convert("RGB"))
                conversion.append((time.perf_counter() - t) * 1000)
            results.append(
                {
                    "style": style,
                    "requested_fps": fps,
                    "simulated_seconds": 30,
                    "composition_mean_ms": statistics.mean(composition),
                    "composition_p95_ms": sorted(composition)[int(len(composition) * 0.95)],
                    "native_conversion_mean_ms": statistics.mean(conversion),
                    "cpu_seconds": time.process_time() - cpu_start,
                    "hardware_delivered_fps": None,
                    "device_write_ms": None,
                    "note": "Unpaced CPU simulation; native Mini conversion; no USB hardware.",
                }
            )
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/jelly"))
    parser.add_argument("--fps", type=int, choices=(24, 30), default=24)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    sprite_sheet(args.output)
    logical_sprite().resize((320, 320), Image.Resampling.NEAREST).save(args.output / "jelly_static.png")
    jelly = Jelly(DeckGeometry(), seed=7)
    jelly.settle(1, 0)
    jelly.deadline = 100
    frames = []
    for i in range(args.fps * 4):
        if i == args.fps * 2:
            jelly.state, jelly.since, jelly.deadline = "blink", i / args.fps, i / args.fps + 0.5
        jelly.update(i / args.fps, {1})
        frames.append(deck_frame(jelly, {1}, args.debug))
    save_gif(frames, args.output / "jelly_idle.gif", args.fps)
    frames = []
    for action in ("look_left", "look_right", "look_up", "wave", "point_left", "point_right", "rest"):
        jelly.settle(1, 0)
        jelly.state, jelly.since, jelly.deadline = action, 0, 5 if action == "rest" else 1.4
        for i in range(args.fps * (6 if action == "rest" else 2)):
            jelly.update(i / args.fps, {1})
            frames.append(deck_frame(jelly, {1}, True))
    save_gif(frames, args.output / "jelly_personality.gif", args.fps)
    for name, source, destination in (("right", 1, 2), ("left", 2, 1), ("up", 4, 1), ("down", 1, 4)):
        save_gif(
            hop_frames(source, destination, args.fps, "classic", args.debug),
            args.output / f"jelly_hop_{name}.gif",
            args.fps,
        )
    classic = hop_frames(1, 2, args.fps, "classic", True)
    fluid = hop_frames(1, 2, args.fps, "fluid", True)
    comparison = []
    for a, b in zip(classic, fluid):
        im = Image.new("RGB", (a.width * 2, a.height + 24), "#141a24")
        im.paste(a, (0, 24))
        im.paste(b, (a.width, 24))
        d = ImageDraw.Draw(im)
        d.text((20, 6), "A: CLASSIC KEY POSES", fill="white")
        d.text((a.width + 20, 6), "B: FLUID POSES", fill="white")
        comparison.append(im)
    save_gif(comparison, args.output / "jelly_hop_comparison.gif", args.fps)
    jelly = Jelly(DeckGeometry(), seed=7)
    jelly.settle(1, 0)
    free = {1, 2, 4, 5}
    schedule = {1: 2, 4: 5, 7: 4, 10: 1}
    frames = []
    for i in range(args.fps * 14):
        now = i / args.fps
        if i % args.fps == 0 and i // args.fps in schedule:
            jelly.hop(schedule[i // args.fps], now, free)
        # Keep scripted pauses quiet while showing the same runtime controller.
        if jelly.state == "idle":
            jelly.deadline = now + 10
        jelly.update(now, free)
        frames.append(deck_frame(jelly, free, args.debug))
    save_gif(frames, args.output / "jelly_full_deck_demo.gif", args.fps)
    # Contact sheet for inspecting actual clipping/anticipation/impact poses.
    selected = [frames[int(t * args.fps)] for t in (1, 1.4, 1.65, 1.85, 1.95, 2.15, 2.35, 2.55)]
    contact = Image.new("RGB", (selected[0].width * 4, selected[0].height * 2))
    for i, im in enumerate(selected):
        contact.paste(im, (i % 4 * im.width, i // 4 * im.height))
    contact.save(args.output / "jelly_hop_contact_sheet.png")
    if args.benchmark:
        result = benchmark()
        (args.output / "benchmark.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
    print(f"Previews written to {args.output}")


if __name__ == "__main__":
    main()
