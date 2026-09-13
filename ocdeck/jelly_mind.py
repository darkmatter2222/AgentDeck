"""Offline temperament and needs, derived only from bounded session metadata."""

from collections import deque
import math
from .jelly_catalog import MOODS

NEEDS = ("energy", "nourishment", "stimulation", "workload", "confidence", "sociability")
PRESETS = {"balanced": (1.0, 1.0), "mellow": (0.55, 0.65), "curious": (1.25, 1.0), "playful": (1.0, 1.5)}


class Mind:
    def __init__(self, rng, options):
        self.rng, self.options = rng, options
        self.needs = dict(zip(NEEDS, (85.0, 75.0, 50.0, 0.0, 65.0, 50.0)))
        self.mood = self.previous_mood = "content"
        self.mood_since = 0.0
        self.hold_until = 0.0
        self.last = None
        self.last_activity = None
        self.previous = {}
        self.pending = {}
        self.recent_events = deque(maxlen=64)
        self.outcomes = {}
        self.reaction = None
        self.target = None
        self.target_id = None
        self.next_reminder = 0.0
        self.last_feed = -100.0
        self.last_reaction = -100.0
        self.next_temperament = 0.0

    def set_mood(self, mood, now, hold=12):
        if mood not in MOODS:
            raise ValueError("Unknown Jelly mood")
        if mood != self.mood:
            self.previous_mood, self.mood = self.mood, mood
            self.mood_since = now
        self.hold_until = max(self.hold_until, now + hold)

    def observe(self, now, views, events=()):
        dt = 0 if self.last is None else max(0, min(2.0, now - self.last))
        self.last = now
        if self.last_activity is None:
            self.last_activity = now
            self.next_temperament = now + 25
        current = {i: (v.get("id"), v["state"]) for i, v in enumerate(views or ()) if v.get("id")}
        running = sum(state == "running" for _, state in current.values())
        signals = []
        for slot, (identity, state) in current.items():
            old = self.previous.get(slot)
            if old != (identity, state):
                self.recent_events.append(now)
                self.last_activity = now
                if state == "input":
                    self.pending[slot] = (identity, now)
                    signals.append((90, "helpful", "point_right", "input", slot))
                elif state == "unknown":
                    signals.append((70, "concerned", "look_up", "concern", slot))
                elif old and old[0] == identity and old[1] == "input":
                    signals.append((60, "content", "nod", "resolved", slot))
                elif old and old[0] == identity and old[1] == "unknown":
                    signals.append((50, "content", "wave", "reconnected", slot))
                elif not old or old[0] != identity:
                    signals.append((45, "curious", "wave", "greetings", slot))
                elif state == "running":
                    signals.append((40, "attentive", "look_right", "running", slot))
                elif state == "idle":
                    signals.append((30, "content", "nod", "quiet", slot))
                # Event bursts cannot feed infinitely; sustained work feeds separately.
                if self.options.get("needs", True) and now - self.last_feed >= 5:
                    self.needs["nourishment"] += 1.5
                    self.needs["stimulation"] += 4
                    self.last_feed = now
            v = views[slot]
            outcome, event_id = v.get("outcome"), v.get("outcomeId")
            if outcome in ("success", "failure") and isinstance(event_id, str) and event_id:
                token = (identity, event_id)
                if self.outcomes.get(slot) != token:
                    self.outcomes[slot] = token
                    good = outcome == "success"
                    signals.append(
                        (
                            65 if good else 80,
                            "proud" if good else "startled",
                            "cheer" if good else "retreat",
                            "success" if good else "failure",
                            slot,
                        )
                    )
                    if self.options.get("needs", True):
                        self.needs["confidence"] += 5 if good else -3
        for slot in self.previous.keys() - current.keys():
            signals.append((20, "curious", "edge_peek", "departures", slot))
        self.pending = {k: v for k, v in self.pending.items() if current.get(k) == (v[0], "input")}
        if self.pending:
            target = min(self.pending, key=lambda k: (self.pending[k][1], k))
            self.target, self.target_id = target, current[target][0]
            if now >= self.next_reminder:
                signals.append((90, "helpful", "point_right", "input", target))
                self.next_reminder = now + 45
        else:
            self.target = self.target_id = None
        for event in events:
            if event.get("kind") == "focus" and event.get("slot") in current:
                slot = event["slot"]
                signals.append((25, "attentive", "nod", "running" if current[slot][1] == "running" else "quiet", slot))
                if self.options.get("needs", True):
                    self.needs["sociability"] += 2
        self.previous = current
        self.outcomes = {k: v for k, v in self.outcomes.items() if k in current and current[k][0] == v[0]}
        while self.recent_events and now - self.recent_events[0] > 10:
            self.recent_events.popleft()
        busy = min(100.0, running * 17 + len(self.pending) * 10 + len(self.recent_events) * 3)
        if self.options.get("needs", True):
            n = self.needs
            n["workload"] += (busy - n["workload"]) * min(1, dt / 12)
            resting = self.mood in ("asleep", "sleepy", "recovering") and not running
            n["energy"] += dt * (0.16 if resting else 0.025 if not running else -0.012 * min(running, 4))
            n["nourishment"] += dt * (0.02 * min(running, 3) if running else -0.007)
            n["stimulation"] += dt * (0.05 * min(running, 3) if running else -0.04)
            n["sociability"] -= dt * 0.006
        self.needs = {k: max(0.0, min(100.0, v)) for k, v in self.needs.items()}
        quiet = now - self.last_activity
        n = self.needs
        if self.options.get("reactions", True) and signals and now - self.last_reaction >= 3:
            signal = max(signals, key=lambda s: (s[0], -s[4]))
            # Input remains the stable attention target even during unrelated changes.
            if self.target is not None:
                signal = (90, "helpful", "point_right", "input", self.target)
            _, mood, action, category, slot = signal
            if self.mood in ("asleep", "sleepy") and category in ("greetings", "running", "reconnected"):
                mood, action = "waking", "reform"
            self.set_mood(mood, now, 3 if mood == "startled" else 10)
            self.reaction = (action, category, slot)
            self.last_reaction = now
        if not self.options.get("needs", True):
            return
        if len(self.recent_events) >= 12 or n["workload"] > 85:
            self.set_mood("overwhelmed", now, 15)
        elif running and n["energy"] < 35:
            self.set_mood("overworked", now, 15)
        elif now >= self.hold_until:
            if self.mood == "startled":
                self.set_mood("concerned", now, 12)
            elif self.mood in ("overworked", "overwhelmed") and n["workload"] < 45:
                self.set_mood("recovering", now, 20)
            elif self.mood == "asleep" and (running or quiet < 5):
                self.set_mood("waking", now, 8)
            elif not running and quiet > 300:
                self.set_mood("asleep", now, 20)
            elif not running and (quiet > 120 or n["energy"] < 25):
                self.set_mood("sleepy", now, 20)
            elif n["nourishment"] < 30:
                self.set_mood("peckish", now, 20)
            elif running:
                self.set_mood("focused" if n["workload"] < 60 else "thinking", now, 15)
            elif now >= self.next_temperament:
                temperament = self.options.get("personality", "balanced")
                choices = {
                    "balanced": (
                        "content",
                        "curious",
                        "playful",
                        "bored",
                        "cautious",
                        "shy",
                        "restless",
                        "mischievous",
                    ),
                    "mellow": ("content", "content", "shy", "cautious", "bored"),
                    "curious": ("curious", "curious", "thinking", "attentive", "mischievous"),
                    "playful": ("playful", "excited", "mischievous", "restless", "curious"),
                }[temperament]
                self.set_mood(self.rng.choice(choices), now, 20)
                self.next_temperament = now + self.rng.uniform(25, 60)

    def consume_reaction(self):
        result, self.reaction = self.reaction, None
        return result

    def snapshot(self, recent):
        return {"schema_version": 1, "needs": self.needs, "mood": self.mood, "recent": list(recent)[-128:]}

    def restore(self, value):
        # Saved values contain no wall-clock debt: returning after a break is restorative.
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            return []
        needs = value.get("needs")
        if not isinstance(needs, dict) or set(needs) != set(NEEDS):
            return []
        if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 100 for v in needs.values()):
            return []
        self.needs = {**needs, "energy": max(85.0, needs["energy"]), "workload": 0.0}
        self.mood = self.previous_mood = "waking"
        recent = value.get("recent", [])
        from .jelly_words import vocabulary

        valid = {f"{category}:{i}" for category, lines in vocabulary().items() for i in range(len(lines))}
        return [s for s in recent[-128:] if isinstance(s, str) and s in valid] if isinstance(recent, list) else []
