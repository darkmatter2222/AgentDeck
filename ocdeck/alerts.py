"""State transitions are processed independently of USB rendering."""

import hashlib
import logging
import os
import queue
import subprocess
import threading
import time
from pathlib import Path

LOG = logging.getLogger(__name__)


def quiet_hours():
    """Conservative Windows shell interruption check; failure suppresses sound."""
    if os.name != "nt":
        return False
    try:
        import ctypes

        state = ctypes.c_int()
        result = ctypes.windll.shell32.SHQueryUserNotificationState(ctypes.byref(state))
        return result != 0 or state.value != 5  # QUNS_ACCEPTS_NOTIFICATIONS
    except Exception:
        return True


def deliver(event, config):
    if os.name != "nt":
        LOG.info("Alerts require Windows: slot %s state %s", event["slot"] + 1, event["state"])
        return
    if quiet_hours():
        return
    if event["sound"]:
        import winsound

        file = config.get("sound_file")
        winsound.PlaySound(
            str(Path(file).expanduser()) if file else "SystemExclamation",
            winsound.SND_ASYNC | (winsound.SND_FILENAME if file else winsound.SND_ALIAS),
        )
    if event["toast"]:
        # Native WinRT notification; default priority, no alarm scenario or bypass.
        # User labels/prompts never enter either the shell script or notification.
        import winreg

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\AppUserModelId\AgentDeck") as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "AgentDeck")
        text = f"AgentDeck slot {event['slot'] + 1} needs input"
        script = """$ErrorActionPreference='Stop'
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] > $null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] > $null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml('<toast><visual><binding template="ToastGeneric"><text>TEXT</text></binding></visual><audio silent="true"/></toast>')
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('AgentDeck').Show($toast)
""".replace("TEXT", text)
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            timeout=5,
            check=True,
            capture_output=True,
            creationflags=0x08000000,
        )


class Alerts:
    def __init__(self, config, clock=time.monotonic, sink=deliver):
        self.config = config.get("alerts", {})
        self.clock, self.sink = clock, sink
        self.previous = {}
        self.seen = set()
        self.last_sound = -float("inf")
        self.lock = threading.Lock()
        self.queue = queue.Queue(maxsize=64)

    def observe(self, views):
        with self.lock:
            live = {v["id"] for v in views if v["id"]}
            self.previous = {k: v for k, v in self.previous.items() if k in live}
            self.seen = {x for x in self.seen if x[0] in live}
            for view in views:
                identity = view["id"]
                if not identity:
                    continue
                state = view["state"]
                previous = self.previous.get(identity)
                self.previous[identity] = state
                muted = str(view["slot"] + 1) in self.config.get("muted_slots", [])
                requests = view.get("requestIds", []) if state == "input" else []
                fresh = [r for r in requests if (identity, r) not in self.seen]
                self.seen.update((identity, r) for r in requests)
                transition = state != previous
                sound = (
                    not muted
                    and self.config.get("sound", False)
                    and transition
                    and state in self.config.get("states", ["input"])
                    and self.clock() - self.last_sound >= self.config.get("cooldown_seconds", 10)
                )
                toast = not muted and self.config.get("toast", False) and bool(fresh)
                if sound or toast:
                    if sound:
                        self.last_sound = self.clock()
                    try:
                        self.queue.put_nowait({"slot": view["slot"], "state": state, "sound": sound, "toast": toast})
                    except queue.Full:
                        LOG.warning("Alert queue full; alert dropped")

    def run(self, stop):
        while not stop.is_set():
            try:
                event = self.queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self.sink(event, self.config)
            except Exception:
                LOG.exception("Alert delivery failed; run ocdeck doctor")
