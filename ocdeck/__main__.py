import argparse
import json
from pathlib import Path
import sys
from .common import home, identity, request, load_config


def main():
    parser = argparse.ArgumentParser(prog="ocdeck")
    from . import __version__

    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    from .controls_cli import add_parser

    add_parser(sub)
    broker = sub.add_parser("broker")
    broker.add_argument("--mock", action="store_true")
    install_cmd = sub.add_parser("install", help="Install the per-user broker startup service/task")
    install_cmd.add_argument("--no-start", action="store_true")
    install_cmd.add_argument("--no-opencode-plugin", action="store_true")
    sub.add_parser("status").add_argument("--json", action="store_true")
    sub.add_parser("stop")
    sub.add_parser("devices")
    sub.add_parser("hardware-check")
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--project", default=".")
    doctor.add_argument("--no-device", action="store_true")
    doctor.add_argument("--json", action="store_true")
    report = sub.add_parser("report")
    report.add_argument("--output", default="agentdeck-report.zip")
    report.add_argument("--lines", type=int, default=100)
    uninstall = sub.add_parser("uninstall")
    uninstall.add_argument("--all", action="store_true", required=True)
    uninstall.add_argument("--scan", action="append", default=[])
    uninstall.add_argument("--dry-run", action="store_true")
    launch = sub.add_parser("launch")
    launch.add_argument("args", nargs=argparse.REMAINDER)
    route = sub.add_parser("route")
    route.add_argument("args", nargs=argparse.REMAINDER)
    worker = sub.add_parser("worker")
    worker.add_argument("spec")
    ident = sub.add_parser("identity")
    ident.add_argument("pid", type=int)
    plug = sub.add_parser("install-plugin")
    plug.add_argument("--mode", choices=["server", "tui"], default="server")
    plug.add_argument("--config-dir")
    from .harness import PROFILES

    hp = sub.add_parser("harness-install")
    hp.add_argument("profile", choices=PROFILES)
    hp.add_argument("--project", default=".")
    hp.add_argument("--remove", action="store_true")
    hp.add_argument("--dry-run", action="store_true")
    hl = sub.add_parser("harness-launch")
    hl.add_argument("--profile", required=True, choices=PROFILES)
    hl.add_argument("--executable")
    hl.add_argument("--current-window", action="store_true")
    hl.add_argument("args", nargs=argparse.REMAINDER)
    hw = sub.add_parser("harness-worker")
    hw.add_argument("spec")
    start = sub.add_parser("start", help="Managed local/cloud CLI or existing BAT launcher")
    start.add_argument("--profile", required=True, choices=["opencode", *PROFILES])
    start.add_argument("--launcher", help="Path to existing BAT/CMD/EXE; defaults to the installed CLI")
    start.add_argument("args", nargs=argparse.REMAINDER)
    preview = sub.add_parser("preview")
    preview.add_argument("--output", default="animation-preview.gif")
    from .appearance import THEMES, PRESETS

    customize = sub.add_parser("appearance", help="Save button appearance; restart broker to apply")
    customize.add_argument("--slot", type=int, choices=range(1, 33))
    for target in (customize, preview):
        target.add_argument("--preset", choices=list(PRESETS))
        target.add_argument("--alias")
        for name, choices in {
            "text-effect": ["none", "scroll", "shimmer"],
            "text-size": ["small", "normal", "large"],
            "text-align": ["left", "center", "right"],
            "badge": ["dot", "ring", "pill"],
            "border": ["solid", "double", "corners", "none"],
            "background": ["solid", "gradient", "grid"],
            "logo-size": ["small", "normal", "large"],
        }.items():
            target.add_argument("--" + name, choices=choices)
        target.add_argument("--layout", choices=["classic", "harness", "minimal"])
        target.add_argument("--theme", choices=list(THEMES))
        target.add_argument("--effect", choices=["breathe", "glow", "steady"])
        for name in ("primary", "secondary"):
            target.add_argument(
                "--" + name, choices=["status", "project", "harness", "detail", "custom", "alias", "none"]
            )
        target.add_argument("--custom-text")
        target.add_argument("--show-slot", action=argparse.BooleanOptionalAction, default=None)
        target.add_argument("--speed", type=float)
        target.add_argument("--intensity", type=float)
        target.add_argument("--brightness", type=float, help="Per-button image brightness, 0.15..1")
    customize.add_argument("--dry-run", action="store_true")
    customize.add_argument("--export", dest="export_file")
    customize.add_argument("--import", dest="import_file")
    customize.add_argument("--fps", type=int, choices=range(1, 31))
    focus = sub.add_parser("focus")
    focus.add_argument("slot", type=int)
    args = parser.parse_args()
    try:
        if args.command == "controls":
            from .controls_cli import run

            return run(args)
        elif args.command == "doctor":
            from .diagnostics import doctor

            rows = doctor(args.project, args.no_device)
            if args.json:
                print(json.dumps(rows, indent=2))
            else:
                for row in rows:
                    print(f"{row['result']:6} {row['check']}: {row['detail']} | Fix/check: {row['fix']}")
            return int(any(r["result"] == "FAIL" for r in rows))
        elif args.command == "report":
            from .diagnostics import report

            print(report(args.output, args.lines))
        elif args.command == "uninstall":
            from .uninstall import uninstall

            return uninstall(args.scan, args.dry_run)
        elif args.command == "broker":
            from .broker import run

            run(mock=args.mock)
        elif args.command == "install":
            from .bootstrap import install

            install(start=not args.no_start, install_opencode=not args.no_opencode_plugin)
        elif args.command in ("status", "stop"):
            print(json.dumps(request("GET" if args.command == "status" else "POST", "/v1/" + args.command), indent=2))
        elif args.command == "identity":
            print(json.dumps(identity(args.pid)))
        elif args.command == "launch":
            from .launcher import launch

            launch(args.args[1:] if args.args[:1] == ["--"] else args.args)
        elif args.command == "route":
            from .launcher import route

            return route(args.args[1:] if args.args[:1] == ["--"] else args.args)
        elif args.command == "worker":
            from .launcher import worker

            return worker(args.spec)
        elif args.command == "install-plugin":
            from .launcher import install_plugin

            install_plugin(args.mode, args.config_dir)
        elif args.command == "harness-install":
            from .harness import install

            return install(args.profile, args.project, args.remove, args.dry_run)
        elif args.command == "harness-launch":
            from .harness import launch

            return launch(
                args.profile,
                args.args[1:] if args.args[:1] == ["--"] else args.args,
                args.executable,
                args.current_window,
            )
        elif args.command == "start":
            forwarded = args.args[1:] if args.args[:1] == ["--"] else args.args
            if args.profile == "opencode":
                from .launcher import launch

                launch(forwarded, executable=args.launcher)
            else:
                from .harness import launch

                return launch(args.profile, forwarded, executable=args.launcher)
        elif args.command == "harness-worker":
            from .harness import worker

            return worker(args.spec)
        elif args.command == "devices":
            from .device import enumerate_devices

            print(
                json.dumps(
                    [
                        {k: (v.decode(errors="replace") if isinstance(v, bytes) else v) for k, v in d.items()}
                        for d in enumerate_devices()
                    ],
                    indent=2,
                )
            )
        elif args.command == "hardware-check":
            from .hardware_check import run

            run()
        elif args.command == "focus":
            slots = request("GET", "/v1/status")["slots"]
            if not 1 <= args.slot <= len(slots):
                raise ValueError(f"Slot must be 1..{len(slots)}")
            view = slots[args.slot - 1]
            print(json.dumps(request("POST", "/v1/focus", view), indent=2))
        elif args.command == "appearance":
            from .appearance import Appearance, appearance, animation_phase
            from dataclasses import fields, asdict
            from .common import read_json, atomic_json

            config = load_config()
            if not isinstance(config, dict):
                raise ValueError("config.json must contain an object")
            from .appearance_io import import_settings, export_settings, diff, preview as render_preview
            import copy

            before = copy.deepcopy(config)
            if args.import_file:
                config = import_settings(config, json.loads(Path(args.import_file).read_text(encoding="utf-8-sig")))
            changes = {f.name: getattr(args, f.name) for f in fields(Appearance) if getattr(args, f.name) is not None}
            if args.preset:
                preset = asdict(Appearance(**PRESETS[args.preset]))
                # Applying a visual preset should not erase the user's labels.
                preset.pop("alias")
                preset.pop("custom_text")
                changes = {**preset, **changes}
            if changes:
                target = (
                    config.setdefault("appearance", {})
                    if args.slot is None
                    else config.setdefault("buttons", {}).setdefault(str(args.slot), {})
                )
                target.update(changes)
            if args.fps is not None:
                config["fps"] = args.fps
            for slot in range(32):
                appearance(config, slot)
            if args.dry_run:
                print(
                    json.dumps(
                        {"diff": diff(before, config), "preview": render_preview(config, config.get("slots", 6))},
                        indent=2,
                    )
                )
                return 0
            if args.export_file:
                atomic_json(Path(args.export_file), export_settings(config))
            if changes or args.fps is not None or args.import_file:
                atomic_json(home() / "config.json", config)
                print("Appearance saved. Restart the AgentStreamDeck broker to apply.")
            print(json.dumps(config, indent=2))
        elif args.command == "preview":
            from .art import frame
            from PIL import Image, ImageDraw
            from .appearance import Appearance, appearance, animation_phase
            from .common import read_json
            from dataclasses import fields, asdict

            config = load_config()
            if not isinstance(config, dict):
                raise ValueError("config.json must contain an object")
            changes = {f.name: getattr(args, f.name) for f in fields(Appearance) if getattr(args, f.name) is not None}
            if args.preset:
                preset = asdict(Appearance(**PRESETS[args.preset]))
                # Applying a visual preset should not erase the user's labels.
                preset.pop("alias")
                preset.pop("custom_text")
                changes = {**preset, **changes}
            config["appearance"] = {**config.get("appearance", {}), **changes}
            # Explicit preview flags override saved per-button preferences.
            styles = [
                appearance(
                    {
                        "appearance": {
                            **config.get("appearance", {}),
                            **config.get("buttons", {}).get(str(k + 1), {}),
                            **changes,
                        }
                    },
                    k,
                )
                for k in range(6)
            ]
            images = []
            states = ["running", "idle", "input", "running", "unknown", "ready"]
            count = min(192, max(48, round(48 / min(style.speed for style in styles))))
            for phase in range(count):
                im = Image.new("RGB", (532, 370), "#10141d")
                d = ImageDraw.Draw(im)
                d.text((22, 12), "AGENTDECK / APPEARANCE PREVIEW", fill="white")
                for k, state in enumerate(states):
                    im.paste(
                        frame(
                            state,
                            "HomeAILab",
                            k,
                            animation_phase(phase / 24, styles[k], config.get("animations", True)),
                            150,
                            styles[k],
                            ["opencode", "claude", "copilot", "gemini", "cursor", "opencode"][k],
                            "Review changes",
                        ),
                        (22 + (k % 3) * 170, 40 + (k // 3) * 160),
                    )
                images.append(im)
            images[0].save(
                args.output,
                save_all=True,
                append_images=images[1:],
                duration=[50 if n % 6 == 5 else 40 for n in range(count)],
                loop=0,
            )
            print(str(Path(args.output).resolve()))
    except Exception as error:
        from .security import scrub_text

        print(scrub_text(f"ocdeck: {error} | Diagnose: ocdeck doctor"), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
