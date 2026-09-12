"""Bounded JSON logs with request correlation and final-output redaction."""

from contextvars import ContextVar
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from collections import deque
from .security import scrub

correlation = ContextVar("correlation", default="background")


class JsonFormatter(logging.Formatter):
    def __init__(self, secrets=()):
        super().__init__()
        self.secrets = secrets

    def format(self, record):
        value = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "correlationId": correlation.get(),
            "message": record.getMessage(),
        }
        if record.exc_info:
            value["exception"] = self.formatException(record.exc_info)
        return json.dumps(scrub(value, self.secrets), ensure_ascii=True)


def configure(root):
    root = Path(root)
    try:
        token = (root / "token").read_text().strip()
    except OSError:
        token = ""
    handler = RotatingFileHandler(root / "broker.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(JsonFormatter((token,)))
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


def tail(root, count=100, errors_only=False):
    count = max(0, min(2000, count))
    rows = deque(maxlen=count)
    try:
        with (Path(root) / "broker.log").open(encoding="utf-8", errors="replace") as stream:
            for line in stream:
                if not errors_only or any(x in line for x in ('"WARNING"', '"ERROR"', '"CRITICAL"')):
                    rows.append(line[:8192].rstrip())
    except OSError:
        pass
    try:
        token = (Path(root) / "token").read_text().strip()
    except OSError:
        token = ""
    return scrub(list(rows), (token,))
