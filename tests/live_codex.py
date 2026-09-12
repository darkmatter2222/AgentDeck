"""Explicit interactive Codex acceptance runner; not discovered by unittest/CI."""

import subprocess
import sys
import time
from ocdeck.common import request


def main():
    print("Run from a project with trusted Codex hooks and a running broker.")
    print("Exercise a prompt, a tool requiring approval, then exit Codex.")
    child = subprocess.Popen([sys.executable, "-m", "ocdeck", "start", "--profile", "codex"])
    seen = set()
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        try:
            for slot in request("GET", "/v1/status")["slots"]:
                if slot.get("harness") == "codex":
                    seen.add(slot["state"])
        except Exception:
            pass
        if {"running", "idle", "input"} <= seen:
            break
        if child.poll() not in (None, 0):
            break
        time.sleep(0.25)
    missing = {"running", "idle", "input"} - seen
    print("Observed:", ", ".join(sorted(seen)), "| Missing:", ", ".join(sorted(missing)) or "none")
    print("Physically verify focus and slot removal after closing the managed window.")
    return int(bool(missing))


if __name__ == "__main__":
    raise SystemExit(main())
