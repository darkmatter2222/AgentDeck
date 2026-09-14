"""CLI is the supported configuration interface; INI remains human-readable."""

import configparser
from dataclasses import asdict
import io
import json
import os
from pathlib import Path
import shutil
import tempfile

from .common import atomic_json, home, load_config
from .launch_profiles import HARNESS_NAMES, read_profiles, launch_profile
from .settings import validate_config


def add_parser(sub):
    parser = sub.add_parser("controls", help="Configure the on-deck launcher and permission review")
    actions = parser.add_subparsers(dest="controls_command", required=True)
    settings = actions.add_parser("configure", help="Save controls settings; restart broker to apply")
    import argparse

    for name in ("enabled", "permissions"):
        settings.add_argument("--" + name, action=argparse.BooleanOptionalAction, default=None)
    settings.add_argument("--hold-ms", type=int)
    settings.add_argument("--menu-timeout", type=int)
    settings.add_argument("--request-timeout", type=int)
    actions.add_parser("show", help="Print settings and repository profiles as JSON")
    actions.add_parser("validate", help="Check folders, executables and adapter setup")
    repo = actions.add_parser("repo", help="Add, update or remove a named repository profile")
    repos = repo.add_subparsers(dest="repo_command", required=True)
    put = repos.add_parser("set", help="Create/update a profile; omitted fields keep their previous value")
    put.add_argument("name")
    put.add_argument("--directory")
    put.add_argument("--harness", choices=HARNESS_NAMES, action="append")
    put.add_argument("--arg", action="append", help="Repeat for launch argv; use --arg=--flag for options")
    put.add_argument("--clear-args", action="store_true")
    put.add_argument("--executable", help="Optional executable or existing BAT/CMD path")
    put.add_argument("--clear-executable", action="store_true")
    repos.add_parser("remove").add_argument("name")
    launch = actions.add_parser("launch", help="Launch the same saved profile from the CLI")
    launch.add_argument("name")
    launch.add_argument("--harness", choices=HARNESS_NAMES, required=True)


def _save(file, parser):
    output = io.StringIO()
    parser.write(output)
    file.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=file.parent, prefix=".launcher-", suffix=".ini")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(output.getvalue())
        read_profiles(temporary)
        os.replace(temporary, file)
    finally:
        Path(temporary).unlink(missing_ok=True)


def run(args):
    root = home()
    file = root / "launcher.ini"
    action = args.controls_command
    if action == "configure":
        config = load_config(root)
        value = config.setdefault("controls", {})
        for key in ("enabled", "permissions", "hold_ms", "menu_timeout", "request_timeout"):
            if getattr(args, key) is not None:
                value[key] = getattr(args, key)
        validate_config(config)
        atomic_json(root / "config.json", config)
        print("Controls saved. Restart the broker to apply settings. Repository edits apply on the next picker open.")
    elif action == "repo":
        parser = configparser.ConfigParser(interpolation=None)
        read_profiles(file)  # Do not overwrite malformed user configuration.
        parser.read(file, encoding="utf-8-sig")
        if any(c in args.name for c in "\r\n[]") or not args.name.strip():
            raise ValueError("Profile name must be nonempty and contain no brackets or newlines")
        section = "repo:" + args.name
        if args.repo_command == "remove":
            if not parser.remove_section(section):
                raise ValueError("Unknown repository profile")
        else:
            if section not in parser:
                parser.add_section(section)
            entry = parser[section]
            if args.directory is not None:
                entry["directory"] = str(Path(os.path.expandvars(args.directory)).expanduser().resolve())
            if "directory" not in entry:
                raise ValueError("New profiles require --directory")
            if args.harness:
                entry["harnesses"] = ",".join(args.harness)
            if args.arg is not None:
                entry["args"] = json.dumps(args.arg)
            elif args.clear_args:
                entry["args"] = "[]"
            if args.executable is not None:
                entry["executable"] = args.executable
            elif args.clear_executable:
                entry.pop("executable", None)
        _save(file, parser)
        print("Repository profiles saved. Open the deck picker to use the updated catalog.")
    elif action == "show":
        print(
            json.dumps(
                {
                    "controls": {
                        "enabled": False,
                        "permissions": False,
                        "hold_ms": 650,
                        "menu_timeout": 45,
                        "request_timeout": 110,
                        **load_config(root).get("controls", {}),
                    },
                    "profiles": [asdict(p) for p in read_profiles(file)],
                },
                default=str,
                indent=2,
            )
        )
    elif action == "launch":
        profile = next((p for p in read_profiles(file) if p.name == args.name), None)
        if profile is None:
            raise ValueError("Unknown repository profile")
        launch_profile(profile, args.harness)
    elif action == "validate":
        from .harness import PROFILES

        validate_config(load_config(root))
        rows = []
        for profile in read_profiles(file):
            rows.append({"profile": profile.name, "check": "directory", "ok": profile.directory.is_dir()})
            for harness in profile.harnesses:
                executable = profile.executable or PROFILES.get(harness, "opencode")
                rows.append(
                    {"profile": profile.name, "check": harness + " executable", "ok": bool(shutil.which(executable))}
                )
                if harness != "opencode":
                    rows.append(
                        {
                            "profile": profile.name,
                            "check": harness + " adapter manifest",
                            "ok": (profile.directory / ".agentdeck" / (harness + ".json")).is_file(),
                        }
                    )
        rows.append({"check": "Windows Terminal launcher", "ok": os.name == "nt" and bool(shutil.which("wt.exe"))})
        print(json.dumps(rows, indent=2))
        return int(any(not row["ok"] for row in rows))
    return 0
