import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from PIL import Image
from ocdeck.art import frame, harness_logo
from ocdeck.appearance import Appearance, PRESETS, appearance, animation_phase, harness_id


class CustomizationTests(unittest.TestCase):
    def test_assets_exist_match_sources_and_never_substitute_a_wrong_brand(self):
        root = Path(__file__).resolve().parents[1] / "ocdeck/assets/logos"
        sources = json.loads((root / "sources.json").read_text())
        for name, source in sources.items():
            self.assertEqual(hashlib.sha256((root / (name + ".png")).read_bytes()).hexdigest(), source["png_sha256"])
            self.assertIsNotNone(harness_logo(name, 56))
        self.assertIsNone(harness_logo("../claude", 56))
        self.assertIsNone(harness_logo("other-harness", 56))
        self.assertEqual(harness_logo("copilot-cli", 56).tobytes(), harness_logo("copilot", 56).tobytes())
        self.assertEqual(harness_id("copilot-cli:project"), "copilot-cli")

    def test_alias_replaces_project_but_never_status(self):
        a = Appearance(alias="Reviewer", show_slot=False)
        self.assertEqual(
            frame("input", "Original", 0, 24, 80, a).tobytes(),
            frame("input", "Reviewer", 0, 24, 80, replace(a, alias="")).tobytes(),
        )
        self.assertNotEqual(
            frame("input", "Original", 0, 24, 80, a).tobytes(), frame("idle", "Original", 0, 24, 80, a).tobytes()
        )

    def test_text_effects_are_clipped_and_change_pixels(self):
        for effect in ("scroll", "shimmer"):
            a = Appearance(
                layout="harness",
                intensity=0,
                primary="alias",
                alias="Long project alias for scrolling",
                text_effect=effect,
            )
            x = frame("running", "Project", 0, 0, 160, a, "claude")
            y = frame("running", "Project", 0, 40, 160, a, "claude")
            self.assertEqual(x.crop((0, 0, 160, 85)).tobytes(), y.crop((0, 0, 160, 85)).tobytes())
            self.assertNotEqual(x.crop((0, 87, 160, 115)).tobytes(), y.crop((0, 87, 160, 115)).tobytes())
            self.assertEqual(animation_phase(0, a, False), animation_phase(10, a, False))

    def test_new_choices_and_presets_render(self):
        for field, values in {
            "text_size": ["small", "normal", "large"],
            "text_align": ["left", "center", "right"],
            "badge": ["dot", "ring", "pill"],
            "border": ["solid", "double", "corners", "none"],
            "background": ["solid", "gradient", "grid"],
            "logo_size": ["small", "normal", "large"],
        }.items():
            for value in values:
                a = appearance({"appearance": {"layout": "harness", field: value}})
                for state in ("running", "idle", "input", "unknown", "ready", "off"):
                    im = frame(state, "Project", 0, 24, 80, a, "gemini")
                    if state == "off":
                        self.assertIsNone(im.getbbox())
                    else:
                        self.assertIsNotNone(im.getbbox())
            with self.assertRaises(ValueError):
                appearance({"appearance": {field: "bogus"}})
        for options in PRESETS.values():
            appearance({"appearance": options})
        with self.assertRaises(ValueError):
            appearance({"appearance": {"alias": "x" * 101}})
        with self.assertRaises(ValueError):
            appearance({"appearance": {"theme": []}})

    def test_cli_presets_override_precedence_and_preserve_labels(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = dict(os.environ, OCDECK_HOME=td)

            def cli(*args):
                return subprocess.run([sys.executable, "-m", "ocdeck", *args], env=env, capture_output=True, text=True)

            p = root / "config.json"
            p.write_text(
                json.dumps(
                    {
                        "serial": "KEEP",
                        "appearance": {"alias": "Main"},
                        "buttons": {"2": {"alias": "Review", "custom_text": "Keep"}},
                    }
                )
            )
            self.assertEqual(cli("appearance", "--slot", "2", "--preset", "neon", "--theme", "mono").returncode, 0)
            data = json.loads(p.read_text())
            self.assertEqual(data["serial"], "KEEP")
            self.assertEqual(data["appearance"]["alias"], "Main")
            self.assertEqual(data["buttons"]["2"]["alias"], "Review")
            self.assertEqual(data["buttons"]["2"]["custom_text"], "Keep")
            self.assertEqual(data["buttons"]["2"]["theme"], "mono")
            before = p.read_bytes()
            self.assertEqual(cli("appearance", "--alias", "x" * 101).returncode, 1)
            self.assertEqual(p.read_bytes(), before)
            output = root / "preview.gif"
            result = cli("preview", "--preset", "focus", "--alias", "Demo", "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(p.read_bytes(), before)
            with Image.open(output) as im:
                self.assertGreater(im.width, 0)
