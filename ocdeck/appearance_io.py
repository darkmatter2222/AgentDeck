"""Versioned appearance files contain only visual settings."""

import copy
from dataclasses import asdict
from .appearance import appearance


def validate(value):
    if not isinstance(value, dict):
        raise ValueError("Appearance file must be an object")
    unknown = set(value) - {"schema_version", "appearance", "buttons", "fps"}
    if unknown:
        raise ValueError("Unknown settings: " + ", ".join(sorted(unknown)))
    if type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise ValueError("schema_version must be 1")
    fps = value.get("fps", 24)
    if type(fps) is not int or not 1 <= fps <= 30:
        raise ValueError("fps must be 1..30")
    buttons = value.get("buttons", {})
    if not isinstance(buttons, dict) or any(k not in {str(i) for i in range(1, 33)} for k in buttons):
        raise ValueError("buttons must use slot keys 1..32")
    for slot in range(32):
        appearance(value, slot)
    return copy.deepcopy(value)


def export_settings(config):
    return validate({"schema_version": 1, **{k: config[k] for k in ("appearance", "buttons", "fps") if k in config}})


def import_settings(config, value):
    value = validate(value)
    result = copy.deepcopy(config)
    for key in ("appearance", "buttons", "fps"):
        result[key] = value.get(key, 24 if key == "fps" else {})
    return result


def diff(before, after):
    return {
        k: {"before": before.get(k), "after": after.get(k)}
        for k in ("appearance", "buttons", "fps")
        if before.get(k) != after.get(k)
    }


def preview(config, count=6):
    """In-memory PNG: dry-run emits a data URI and never creates a file."""
    import base64
    import io
    from PIL import Image
    from .art import frame

    columns = {6: 3, 15: 5, 32: 8}[count]
    image = Image.new("RGB", (columns * 90, ((count + columns - 1) // columns) * 90), "black")
    for slot in range(count):
        image.paste(
            frame(
                ("running", "idle", "input")[slot % 3],
                "Preview",
                slot,
                24,
                style=appearance(config, slot),
                pending=3 if slot % 3 == 2 else None,
            ),
            ((slot % columns) * 90, (slot // columns) * 90),
        )
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return "data:image/png;base64," + base64.b64encode(stream.getvalue()).decode("ascii")
