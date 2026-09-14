"""Check repository-local documentation links, media and public reference coverage.

Run from any directory with the project's installed dependencies. No network,
USB access, broker startup or configuration writes are performed.
"""

import argparse
from dataclasses import fields
import html
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image
from ocdeck.appearance import Appearance
from ocdeck.jelly import settings as jelly_settings
from ocdeck.settings import validate_config


def prose(text):
    return re.sub(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1\s*$", "", text)


def anchors(text):
    found, counts = set(), {}
    for title in re.findall(r"(?m)^#{1,6}\s+(.+?)(?:\s+#+)?$", prose(text)):
        title = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", title)
        title = re.sub(r"<[^>]+>", "", title).replace("`", "")
        slug = re.sub(r"[^\w\- ]", "", html.unescape(title).lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        found.add(slug if count == 0 else f"{slug}-{count}")
    found.update(re.findall(r'(?:id|name)=["\']([^"\']+)["\']', text))
    return found


def cli_parser():
    # Capture parser construction before parse_args can dispatch a command.
    from ocdeck import __main__

    class Captured(Exception):
        pass

    result = {}
    original = argparse.ArgumentParser.parse_args

    def capture(self, *args, **kwargs):
        result["parser"] = self
        raise Captured

    argparse.ArgumentParser.parse_args = capture
    try:
        __main__.main()
    except Captured:
        pass
    finally:
        argparse.ArgumentParser.parse_args = original
    return result["parser"]


def main():
    docs = sorted(
        p
        for p in ROOT.rglob("*.md")
        if not any(
            part in {".git", ".venv", "venv", "node_modules", "build", "dist"} for part in p.relative_to(ROOT).parts
        )
    )
    texts = {p.resolve(): p.read_text(encoding="utf-8") for p in docs}
    errors, links = [], 0
    for path, text in texts.items():
        content = prose(text)
        targets = re.findall(r"\[[^\]\n]*\]\(([^\s)]+)(?:\s+\"[^\"]*\")?\)", content)
        targets += re.findall(r'(?:src|href)=["\']([^"\']+)["\']', content)
        for target in targets:
            url = urlsplit(html.unescape(target.strip("<>")))
            if url.scheme or url.netloc:
                continue
            links += 1
            local = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not local.exists():
                errors.append(f"{path.relative_to(ROOT)}: missing {target}")
            elif url.fragment and local.suffix.lower() == ".md":
                target_text = texts.get(local, local.read_text(encoding="utf-8"))
                if unquote(url.fragment) not in anchors(target_text):
                    errors.append(f"{path.relative_to(ROOT)}: missing heading {target}")
        # Only explicitly marked JSON config examples, not API bodies/exports.
        if path.parent.name in {"reference", "features"}:
            for block in re.findall(r"(?ms)^```json\s*\n(.*?)^```", text):
                try:
                    value = json.loads(block)
                    validate_config(value)
                except (ValueError, TypeError) as exc:
                    errors.append(f"{path.relative_to(ROOT)}: invalid config example: {exc}")

    cli = (ROOT / "docs/CLI.md").read_text()
    parser = cli_parser()
    commands = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction)).choices
    for name, command in commands.items():
        match = re.search(rf"(?ms)^## {re.escape(name)}\n(.*?)(?=^## |\Z)", cli)
        if not match:
            errors.append(f"CLI reference missing command: {name}")
            continue
        def check_arguments(command, prefix):
            for action in command._actions:
                if isinstance(action, argparse._HelpAction):
                    continue
                if isinstance(action, argparse._SubParsersAction):
                    for child_name, child in action.choices.items():
                        if child_name not in match[1]:
                            errors.append(f"CLI reference missing {prefix} subcommand: {child_name}")
                        check_arguments(child, prefix + " " + child_name)
                    continue
                for option in action.option_strings or [action.dest]:
                    if option not in match[1]:
                        errors.append(f"CLI reference missing {prefix} argument: {option}")

        check_arguments(command, name)

    for filename, names in (
        ("APPEARANCE.md", [field.name for field in fields(Appearance)]),
        ("JELLY.md", list(jelly_settings({}))),
    ):
        reference = (ROOT / "docs/reference" / filename).read_text()
        for name in names:
            if f"`{name}`" not in reference:
                errors.append(f"{filename} missing setting: {name}")

    media = sorted(p for p in (ROOT / "docs").rglob("*") if p.suffix.lower() in {".png", ".gif"})
    for path in media:
        try:
            with Image.open(path) as image:
                # Load the final frame as well as the opening frame of animations.
                image.load()
                image.seek(getattr(image, "n_frames", 1) - 1)
                image.load()
        except Exception as exc:
            errors.append(f"Invalid media {path.relative_to(ROOT)}: {exc}")

    if errors:
        print("\n".join(errors))
        return 1
    print(
        f"PASS: {len(docs)} Markdown files, {links} local links, {len(commands)} CLI commands, "
        f"{len(fields(Appearance))} appearance fields, {len(jelly_settings({}))} Jelly fields, "
        f"{len(media)} decoded PNG/GIF assets; config examples valid."
    )
    print("External links, native harness behavior, USB timing and Windows focus require separate verification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
