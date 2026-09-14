"""Real Node hook -> authenticated HTTP broker -> physical control -> hook JSON."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from test_system import identity

from ocdeck.broker import Broker


class TransportTests(unittest.TestCase):
    def test_claude_native_hook_roundtrip_and_disabled_fallback(self):
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch("ocdeck.broker.identity", identity),
            patch("ocdeck.direct_hooks._identity", identity),
        ):
            root = Path(temporary)
            (root / "config.json").write_text(
                json.dumps({"controls": {"enabled": True, "permissions": True}, "jelly": {"enabled": False}})
            )
            broker = Broker(root, mock=True, probe=lambda _: True, focus=lambda _: {"ok": True})
            thread = threading.Thread(target=broker.serve, daemon=True)
            thread.start()
            child = None
            try:
                deadline = time.monotonic() + 5
                while not (root / "discovery.json").exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                env = dict(os.environ, OCDECK_HOME=str(root))
                env.pop("AGENTDECK_HOOK_BINDING", None)
                script = Path(__file__).resolve().parents[1] / "plugins/harnesses/hook.mjs"
                child = subprocess.Popen(
                    ["node", str(script), "claude", "PermissionRequest"],
                    env=env,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                child.stdin.write(
                    json.dumps(
                        {
                            "session_id": "fixture-session",
                            "tool_name": "Bash",
                            "tool_input": {"command": "echo fixture"},
                        }
                    )
                )
                child.stdin.close()
                deadline = time.monotonic() + 5
                while not broker.permissions.waiting_owners() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(broker.permissions.waiting_owners())
                target = next(v for v in broker.registry.view() if v["id"])
                broker.controls.open(target)
                for action in ("review", "request", "deny"):
                    tile = next(t for t in broker.controls.tiles() if t["command"] == action)
                    self.assertTrue(broker.handle_press(tile)["ok"])
                child.wait(timeout=5)
                output = json.loads(child.stdout.read())
                self.assertEqual(output["hookSpecificOutput"]["decision"]["behavior"], "deny")
                self.assertNotIn("updatedPermissions", output["hookSpecificOutput"]["decision"])
                self.assertEqual(child.stderr.read(), "")
                broker.permissions.enabled = False
                result = subprocess.run(
                    ["node", str(script), "claude", "PermissionRequest"],
                    env=env,
                    input=json.dumps({"session_id": "fixture-session", "tool_name": "Bash"}),
                    text=True,
                    capture_output=True,
                    timeout=5,
                )
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
            finally:
                if child:
                    if child.poll() is None:
                        child.kill()
                        child.wait()
                    for stream in (child.stdin, child.stdout, child.stderr):
                        stream.close()
                broker.stop.set()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
