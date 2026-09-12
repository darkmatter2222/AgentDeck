import json
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from ocdeck import launcher


class WrapperTests(unittest.TestCase):
    def test_existing_opencode_launcher_is_saved_in_managed_spec(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "install.json").write_text(json.dumps({"opencode": "real-opencode", "source": str(root)}))
            with (
                patch.object(launcher, "home", return_value=root),
                patch.object(launcher, "os", SimpleNamespace(name="nt")),
                patch.object(launcher.shutil, "which", side_effect=lambda x: x),
                patch.object(launcher.subprocess, "Popen") as popen,
                patch.object(launcher, "Path", Path),
            ):
                launcher.launch(
                    ["--model", "local/test"], cwd="C:/Project", executable="C:/Home AI/harness/opencode-5090.bat"
                )
            spec = json.loads(next((root / "launches").glob("*.json")).read_text())
            self.assertEqual(spec["executable"], "C:/Home AI/harness/opencode-5090.bat")
            self.assertEqual(spec["args"], ["--model", "local/test"])
            command = popen.call_args.args[0]
            self.assertIn(spec["windowToken"], command)
            self.assertIn("--suppressApplicationTitle", command)

    def test_nested_shim_calls_real_cli_without_new_managed_window(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "install.json").write_text(json.dumps({"opencode": "real-opencode", "source": td}))
            seen = []

            def call(command):
                seen.append(json.loads(Path(command[-1]).read_text()))
                return 7

            with (
                patch.object(launcher, "home", return_value=root),
                patch.dict(os.environ, {"OCDECK_BINDING": "existing-binding"}),
                patch.object(launcher, "launch") as launch,
                patch.object(launcher.subprocess, "call", side_effect=call),
            ):
                self.assertEqual(launcher.route(["--model", "local/test"]), 7)
            launch.assert_not_called()
            self.assertEqual(seen[0]["executable"], "real-opencode")
            self.assertEqual(seen[0]["args"], ["--model", "local/test"])
