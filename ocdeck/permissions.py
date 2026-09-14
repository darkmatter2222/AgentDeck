"""Ephemeral, single-use permission handoff. Only physical controls decide."""

import secrets
import threading
import time

from .security import scrub_text


class Permissions:
    def __init__(self, registry, enabled=False, clock=time.monotonic, timeout=110):
        self.registry, self.enabled, self.clock = registry, enabled, clock
        self.lock = threading.RLock()
        self.items = {}
        self.timeout = timeout

    def _live(self, item):
        return self.registry.resolve(item["slot"], item["generation"], item["owner"]) is not None

    def sweep(self):
        with self.lock:
            now = self.clock()
            for key, item in list(self.items.items()):
                terminal = item["state"] in ("finished", "failed")
                if now >= item["expires"] or (not terminal and (now - item["seen"] > 3 or not self._live(item))):
                    del self.items[key]

    def offer(self, body):
        if not self.enabled:
            return {"enabled": False}
        owner, tool, summary = body.get("owner"), body.get("tool"), body.get("summary", "")
        if not isinstance(owner, str) or not isinstance(tool, str) or not 1 <= len(tool) <= 100:
            raise ValueError("Invalid permission owner/tool")
        if not isinstance(summary, str) or len(summary) > 2000:
            raise ValueError("Invalid permission summary")
        with self.lock:
            self.sweep()
            views = self.registry.view()
            view = next((v for v in views if v["id"] == owner), None)
            if view is None or not self.registry.resolve(view["slot"], view["generation"], owner):
                raise ValueError("Permission owner must have a live deck slot")
            if len(self.items) >= 64:
                raise ValueError("Permission queue full; use terminal")
            key = secrets.token_hex(24)
            now = self.clock()
            self.items[key] = dict(
                owner=owner,
                slot=view["slot"],
                generation=view["generation"],
                tool=scrub_text(tool, self.registry.secrets),
                summary=scrub_text(summary, self.registry.secrets),
                label=view["label"],
                state="pending",
                seen=now,
                expires=now + self.timeout,
            )
            return {"enabled": True, "ticket": key}

    def poll(self, body):
        with self.lock:
            self.sweep()
            item = self.items.get(body.get("ticket"))
            if not item:
                return {"state": "expired"}
            item["seen"] = self.clock()
            if item["state"] == "queued":
                item["state"] = "delivered"
                return {"state": "decision", "decision": item.pop("decision")}
            return {"state": item["state"]}

    def finish(self, body):
        with self.lock:
            self.sweep()
            item = self.items.get(body.get("ticket"))
            if item:
                if body.get("ok") is True and item["state"] != "delivered":
                    return {"ok": False}
                item["state"] = "finished" if body.get("ok") is True else "failed"
                item["expires"] = self.clock() + 15
            return {"ok": True}

    def status(self, ticket):
        with self.lock:
            self.sweep()
            return self.items.get(ticket, {}).get("state", "expired")

    def pending(self, owner):
        with self.lock:
            self.sweep()
            return [
                {"ticket": k, **v} for k, v in self.items.items() if v["owner"] == owner and v["state"] == "pending"
            ]

    def waiting_owners(self):
        with self.lock:
            self.sweep()
            return {v["owner"] for v in self.items.values() if v["state"] == "pending"}

    def decide(self, ticket, decision):
        if decision not in ("allow", "deny", "terminal"):
            raise ValueError("Invalid permission decision")
        with self.lock:
            self.sweep()
            item = self.items.get(ticket)
            if not item or item["state"] != "pending":
                return False
            item.update(state="queued", decision=decision)
            return True
