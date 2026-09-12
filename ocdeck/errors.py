"""Stable user-facing errors, actionable commands and documentation anchors."""

CATALOG = {
    "AD001": ("Elgato Stream Deck may own the device", "Quit Stream Deck from the tray; ocdeck doctor"),
    "AD002": ("Device unavailable or disconnected", "ocdeck devices"),
    "AD003": ("Broker unavailable", "ocdeck broker"),
    "AD004": ("Invalid configuration or request", "ocdeck doctor --no-device"),
    "AD005": ("Stale session registration", "ocdeck status --json; restart the managed agent launcher"),
    "AD006": ("Focus failed", "ocdeck doctor; ocdeck focus 1"),
    "AD007": (
        "Local authentication rejected",
        "ocdeck doctor --no-device; restart the managed launcher under the broker user",
    ),
    "AD008": ("Broker lock unavailable", "ocdeck status --json"),
    "AD500": ("Unexpected broker error", "ocdeck report --output agentdeck-report.zip"),
}
DOC = "https://github.com/darkmatter2222/AgentDeck/blob/main/docs/TROUBLESHOOTING.md"


def message(code: str, detail: str = "") -> str:
    title, fix = CATALOG[code]
    return f"{code}: {title}. {detail} Fix/check: {fix}. {DOC}"
