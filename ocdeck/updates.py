"""One bounded, optional release lookup per broker start; never installs software."""

import json
import logging
import urllib.request
from packaging.version import Version, InvalidVersion
from . import __version__
from .common import read_json, atomic_json
from .security import scrub

URL = "https://api.github.com/repos/darkmatter2222/AgentDeck/releases/latest"
LOG = logging.getLogger(__name__)


def check(root, config, fetch=None):
    if not config.get("check_updates", True):
        return None
    try:
        if fetch is None:
            req = urllib.request.Request(
                URL, headers={"User-Agent": "AgentDeck", "Accept": "application/vnd.github+json"}
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                raw = response.read(262145)
            if len(raw) > 262144:
                raise ValueError("Release response too large")
            release = json.loads(raw)
        else:
            release = fetch()
        version = str(release["tag_name"])
        if release.get("draft") or release.get("prerelease") or Version(version) <= Version(__version__):
            return None
        info = {
            "version": version,
            "url": "https://github.com/darkmatter2222/AgentDeck/releases",
            "notes": scrub(str(release.get("body", ""))[:8000]),
        }
        state = read_json(root / "update.json", {}) or {}
        if state.get("version") != version:
            LOG.info("Update available: %s — %s", version, info["url"])
            print(f"AgentDeck {version} available: {info['url']}\n{info['notes']}", flush=True)
            atomic_json(root / "update.json", info)
        return info
    except (OSError, ValueError, KeyError, TypeError, InvalidVersion):
        LOG.info("Update check unavailable; continuing offline")
        return None
