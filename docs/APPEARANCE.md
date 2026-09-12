# Make the deck yours

![Harness layout with Aurora colors](appearance-preview.gif)

Use the installed `ocdeck` command (or `python -m ocdeck` from the checkout).
Preferences are saved to `%USERPROFILE%\.opencode-deck\config.json` (or
`OCDECK_HOME`). Restart the AgentDeck broker after changing them. Existing
configuration, including an explicitly selected FPS, is preserved.

```powershell
ocdeck appearance --layout harness --theme aurora --effect glow --fps 24
ocdeck appearance --primary project --secondary status --no-show-slot
ocdeck appearance --slot 2 --theme ocean --secondary custom --custom-text "Code review"
ocdeck appearance --slot 3 --speed 0.7 --intensity 0.8 --brightness 0.65
ocdeck preview --layout harness --theme aurora --effect glow --output preview.gif
```

`ocdeck appearance` alone displays saved settings. Global changes are inherited
by buttons without a corresponding override. Remove a key from `buttons` in the
JSON file to restore inheritance for that key. Preview reads saved preferences;
explicit preview flags override them temporarily without saving changes.

| Setting | Choices |
|---|---|
| Layout | `classic` existing state artwork; `harness` brand-inspired glyph + upper-right state dot; `minimal` state glyph in a dot |
| Theme | `classic`, `aurora`, `ocean`, `accessible`, `mono` |
| Primary / secondary text | `status`, `project`, `harness`, `detail`, `custom`, `none` |
| Effect | `breathe` border/status pulse; `glow` adds whole-image brightness breathing; `steady` freezes motion |
| Speed | 0.25–3; 1 is a two-second cycle |
| Intensity | 0–1; strength of brightness modulation |
| Brightness | 0.15–1; per-button rendered brightness |
| FPS | 1–30; new installations default to 24 |

Text is measured and shortened to fit. Slot numbers can be hidden. Keep a status
text line if you want the clearest state identification, especially with the mono
palette or harness layout. `accessible` uses a distinct palette but does not
replace the need for textual state labels. Custom text is shared by both lines
when both select `custom`.

The five harness glyphs are original procedural approximations, not official
logo assets. Claude, Copilot (including VS Code), Gemini, Cursor and OpenCode
are recognized by explicit registration metadata, with compatibility fallback
for existing harness-prefixed labels. Unknown harnesses use a terminal glyph.

## Advanced JSON example

Merge these fields into your existing config, retaining serial and other settings:

```json
{
  "fps": 24,
  "animations": true,
  "appearance": {
    "layout": "harness",
    "theme": "aurora",
    "primary": "project",
    "secondary": "status",
    "show_slot": false,
    "effect": "glow",
    "speed": 1,
    "intensity": 0.55,
    "brightness": 1
  },
  "buttons": {
    "2": {"theme": "ocean", "secondary": "custom", "custom_text": "Code review"},
    "6": {"layout": "minimal", "effect": "steady", "brightness": 0.6}
  }
}
```

Top-level `brightness` remains the device-wide hardware setting (0–100).
Appearance brightness is pixel dimming, not independent hardware backlighting.
`animations: false` disables all motion, including glow. Empty keys remain black.
A 96-step time-based cycle replaces the old 24-step cycle. Late frames are skipped
naturally; no queue of stale animation frames builds up. Actual FPS depends on USB
throughput and the number of active keys. Try 15 FPS if six active keys saturate
an older Mini. Hardware throughput and Windows appearance still need live testing.
