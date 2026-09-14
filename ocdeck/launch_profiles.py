"""INI launcher catalog. Paths are cwd values, never shell fragments."""

import configparser
from dataclasses import dataclass
import json
import os
from pathlib import Path

from .harness import PROFILES

HARNESS_NAMES = {
    "opencode": "OpenCode",
    "claude": "Claude Code",
    "codex": "Codex",
    "copilot-cli": "Copilot CLI",
    "copilot-vscode": "Copilot VS Code",
    "gemini": "Gemini CLI",
    "cursor": "Cursor CLI",
}


@dataclass(frozen=True)
class LaunchProfile:
    name: str
    directory: Path
    harnesses: tuple[str, ...]
    args: tuple[str, ...] = ()
    executable: str = ""


def read_profiles(file):
    parser = configparser.ConfigParser(interpolation=None)
    if not Path(file).exists():
        return []
    parser.read(file, encoding="utf-8-sig")
    if parser.defaults():
        raise ValueError("launcher.ini: DEFAULT values are not supported")
    result = []
    for section in parser.sections():
        if not section.startswith("repo:") or not section[5:].strip():
            raise ValueError("Use [repo:Friendly name] sections in launcher.ini")
        value = parser[section]
        if set(value) - {"directory", "harnesses", "args", "executable"}:
            raise ValueError("Unknown launcher.ini option in " + section)
        directory = Path(os.path.expandvars(value.get("directory", ""))).expanduser()
        if not directory.is_absolute():
            raise ValueError("Repository directory must be absolute: " + section)
        harnesses = tuple(x.strip() for x in value.get("harnesses", "opencode,claude").split(","))
        if not harnesses or any(h not in HARNESS_NAMES for h in harnesses) or len(set(harnesses)) != len(harnesses):
            raise ValueError("Invalid or duplicate harness in " + section)
        args = json.loads(value.get("args", "[]"))
        if not isinstance(args, list) or any(not isinstance(x, str) or "\0" in x for x in args):
            raise ValueError("args must be a JSON string array")
        executable = value.get("executable", "")
        if any(c in executable for c in "\r\n\0"):
            raise ValueError("Invalid executable")
        result.append(LaunchProfile(section[5:].strip(), directory, harnesses, tuple(args), executable))
    return result


def launch_profile(profile, harness):
    if harness not in profile.harnesses:
        raise ValueError("Harness not configured for this project")
    if not profile.directory.is_dir():
        raise ValueError("Repository folder is missing: " + str(profile.directory))
    if os.name != "nt":
        raise RuntimeError("Deck launches require Windows Terminal on Windows")
    if harness == "opencode":
        from .launcher import launch

        return launch(list(profile.args), cwd=str(profile.directory), executable=profile.executable or None)
    if harness not in PROFILES:
        raise ValueError("Unsupported harness")
    from .harness import launch

    return launch(harness, list(profile.args), cwd=str(profile.directory), executable=profile.executable or None)
