"""Validate optional broker features before starting background workers."""

import math
from .appearance_io import export_settings
from .jelly import settings as jelly_settings


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError("config.json must contain an object")
    export_settings(config)
    jelly_settings(config)
    if type(config.get("slots", 6)) is not int or config.get("slots", 6) not in (6, 15, 32):
        raise ValueError("slots must be 6, 15 or 32 (mock capacity; physical deck auto-detects)")
    for name in ("check_updates", "auto_restart_on_upgrade", "allow_elgato", "animations", "ready"):
        if name in config and type(config[name]) is not bool:
            raise ValueError(name + " must be boolean")
    if type(config.get("brightness", 45)) is not int or not 0 <= config.get("brightness", 45) <= 100:
        raise ValueError("brightness must be 0..100")
    alerts = config.get("alerts", {})
    if not isinstance(alerts, dict) or set(alerts) - {
        "sound",
        "toast",
        "sound_file",
        "states",
        "cooldown_seconds",
        "muted_slots",
    }:
        raise ValueError("Unknown or invalid alerts configuration")
    for name in ("sound", "toast"):
        if type(alerts.get(name, False)) is not bool:
            raise ValueError("alerts." + name + " must be boolean")
    states = alerts.get("states", ["input"])
    if not isinstance(states, list) or any(x not in ("input", "running", "idle", "unknown") for x in states):
        raise ValueError("alerts.states must contain input, running, idle or unknown")
    cooldown = alerts.get("cooldown_seconds", 10)
    if type(cooldown) not in (int, float) or not math.isfinite(cooldown) or not 0 <= cooldown <= 3600:
        raise ValueError("alerts.cooldown_seconds must be 0..3600")
    muted = alerts.get("muted_slots", [])
    if not isinstance(muted, list) or any(x not in [str(i) for i in range(1, 33)] for x in muted):
        raise ValueError("alerts.muted_slots must be strings 1..32")
    if "sound_file" in alerts and not isinstance(alerts["sound_file"], str):
        raise ValueError("alerts.sound_file must be a WAV file path")
    return config
