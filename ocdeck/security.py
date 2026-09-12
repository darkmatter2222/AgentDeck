"""Defense in depth for metadata, diagnostics and logs; never collect prompt bodies."""

import re
from typing import Any

REDACTED = "[REDACTED]"
KEY = re.compile(r"token|secret|password|passwd|credential|authorization|api.?key|cookie|private.?key", re.I)
PATTERNS = [
    re.compile(
        r"""(?i)(?:[\w.-]*(?:token|secret|password|passwd|credential|api[_-]?key)[\w.-]*)[\s"']*[:=]\s*(?:"[^"\r\n]*"|'[^'\r\n]*')"""
    ),
    re.compile(r"-----BEGIN [^-]*PRIVATE KEY-----[\s\S]*?-----END [^-]*PRIVATE KEY-----"),
    re.compile(r"\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+", re.I),
    re.compile(
        r"\b(?:sk-[\w-]{8,}|gh[pousr]_[\w]{8,}|github_pat_[\w]{8,}|AKIA[A-Z0-9]{16}|eyJ[\w-]+\.[\w-]+\.[\w-]+)\b"
    ),
    re.compile(
        r"(?i)(?:[\w.-]*(?:token|secret|password|passwd|credential|api[_-]?key)[\w.-]*)[\s\"\']*[:=][\s\"\']*[^\s,;\"\'&}]+"
    ),
    re.compile(r"https?://[^\s/@:]+:[^\s/@]+@"),
]


def scrub_text(value: str, secrets: tuple[str, ...] = ()) -> str:
    for secret in secrets:
        if secret:
            value = value.replace(secret, REDACTED)
    for pattern in PATTERNS:
        value = pattern.sub(REDACTED, value)
    return value


def scrub(value: Any, secrets: tuple[str, ...] = ()) -> Any:
    if isinstance(value, dict):
        return {str(k): REDACTED if KEY.search(str(k)) else scrub(v, secrets) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [scrub(v, secrets) for v in value]
    return scrub_text(value, secrets) if isinstance(value, str) else value
