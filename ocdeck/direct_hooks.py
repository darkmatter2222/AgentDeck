\
"""Event-driven native harness hooks that register directly with the local broker."""

import hashlib
import time
from pathlib import Path

from .focus import capture_window

PROFILES = {
    "codex": "Codex",
    "claude": "Claude",
    "copilot-cli": "Copilot CLI",
    "copilot-vscode": "Copilot VS Code",
    "gemini": "Gemini",
    "cursor": "Cursor CLI",
}
ACTIONS = {
    "start",
    "end",
    "idle",
    "busy",
    "tool",
    "result",
    "error",
    "permission",
    "codex-permission",
    "notification",
}


def _identity(pid):
    import psutil

    process = psutil.Process(int(pid))
    return {"pid": process.pid, "created": process.create_time()}


class DirectHooks:
    def __init__(self, registry):
        self.registry = registry
        self.states = {}

    @staticmethod
    def key(profile, session):
        digest = hashlib.sha256(f"{profile}\0{session}".encode()).hexdigest()[:32]
        return f"hook-{profile}-{digest}"

    def _register(self, profile, session, parent_pid, cwd):
        key = self.key(profile, session)
        state = self.states.get(key)
        if state and self.registry.probe(state["process"]) is not True:
            self.registry.remove(key)
            self.states.pop(key, None)
            state = None
        if state:
            self.registry.upsert(state["registration"])
            return key, state
        process = _identity(parent_pid)
        window = capture_window(process["pid"])
        project = Path(str(cwd or ".")).name or PROFILES[profile]
        registration = {
            "id": key,
            "process": process,
            "windowToken": "",
            "harness": profile,
            "label": f"{PROFILES[profile]}:{project}",
            "eventDriven": True,
            **window,
        }
        self.registry.upsert(registration)
        state = {
            "process": process,
            "registration": registration,
            "producer": f"native-{profile}",
            "seq": 0,
            "status": "unknown",
            "pending": set(),
            "input": False,
            "detail": "Waiting for first native hook",
        }
        self.states[key] = state
        return key, state

    def event(self, body):
        profile = body.get("profile")
        event = body.get("event")
        parent_pid = body.get("parentPid")
        if profile not in PROFILES or not isinstance(event, dict):
            raise ValueError("Invalid native hook profile/event")
        action = event.get("action")
        session = event.get("session")
        if action not in ACTIONS or not isinstance(session, str) or not 1 <= len(session) <= 512:
            raise ValueError("Invalid native hook action/session")
        if type(parent_pid) is not int or parent_pid <= 0:
            raise ValueError("Invalid native hook parent process")
        key = self.key(profile, session)
        if action == "end":
            self.registry.remove(key)
            self.states.pop(key, None)
            return {"ok": True, "removed": True}
        key, state = self._register(profile, session, parent_pid, body.get("cwd", "."))
        request = event.get("request") if isinstance(event.get("request"), str) else ""
        question = bool(event.get("question"))
        failed = bool(event.get("failed"))
        if action in ("start", "idle"):
            state["status"] = "idle"
            state["pending"].clear()
            state["input"] = False
            state["detail"] = ""
        elif action == "busy":
            state["status"] = "busy"
            state["pending"].clear()
            state["input"] = False
            state["detail"] = ""
        elif action == "tool":
            state["status"] = "busy"
            state["input"] = False
            if question and request:
                state["pending"].add(request)
            state["detail"] = ""
        elif action == "result":
            state["status"] = "busy"
            if request:
                state["pending"].discard(request)
            state["input"] = False
            state["detail"] = ""
        elif action == "codex-permission":
            state["status"] = "busy"
            state["input"] = True
            state["detail"] = "Approval requested; count unknown"
        elif action == "permission":
            state["status"] = "unknown"
            state["input"] = False
            state["detail"] = "Permission decision; no paired request ID"
        elif action == "notification":
            state["status"] = "unknown"
            state["detail"] = "Permission notification; inspect harness"
        elif action == "error" or failed:
            state["status"] = "unknown"
            state["pending"].clear()
            state["input"] = False
            state["detail"] = "Harness error; inspect terminal"
        request_ids = [
            hashlib.sha256(f"{session}\0{value}".encode()).hexdigest() for value in sorted(state["pending"])
        ]
        snapshot = {
            "status": state["status"],
            "pending": len(state["pending"]),
            "pendingKnown": False,
            "inputNeeded": state["input"],
            "requestIds": request_ids,
            "detail": state["detail"],
            "producer": state["producer"],
            "seq": state["seq"] + 1,
        }
        outcome = event.get("outcome")
        if outcome in ("success", "failure"):
            snapshot["outcome"] = outcome
            snapshot["outcomeId"] = hashlib.sha256(
                f"{session}\0{event.get('event', '')}\0{request}\0{time.time_ns()}".encode()
            ).hexdigest()
        if not self.registry.snapshot(key, snapshot):
            return {"ok": False, "reason": "stale native hook"}
        state["seq"] = snapshot["seq"]
        return {"ok": True, "slot": self.registry.records[key]["slot"]}
