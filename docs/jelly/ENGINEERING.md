# Living Jelly — expanded companion engineering report

Repository: https://github.com/darkmatter2222/AgentStreamDeck

Branch: `feature/living-jelly-prototype`. This expansion builds on `c0a465f`.
Use `git rev-parse HEAD` for the source SHA. The v3.0.0 release promotes this
implementation to main with Jelly enabled by default.
Released in v3.0.0 and enabled by default. Explicit opt-outs and the global
animations setting remain respected. Physical-device acceptance remains a separate
manual check; the included showcase is a rendered demonstration.

## Delivered scope

| Component | Implemented |
| --- | --- |
| Visible actions | Original 13 plus 20 new local actions: **33 total** (directional hops counted separately). |
| Logical body poses | Original 13 plus 20 new distinct shapes: **33 total**. |
| Hop styles | Original classic/fluid plus 12 variants: **14**, with optional mood-based selection. |
| Mood states | **23** moods, including the proposed 20 plus peckish, overworked and recovering. |
| Temperament presets | Balanced, mellow, curious, playful. |
| Needs | Energy, nourishment, stimulation, workload, confidence, sociability. |
| Thoughts | **1,040 unique authored lines** in 15 contextual categories; no generated word salad or network service. |
| Persistence | Optional bounded state, no session identifiers/content, restorative resume. |

Catalogs are machine-readable in [`catalog.json`](catalog.json). Original artwork,
all animation recipes, metadata handling and phrase selection run locally.

## Floor, artwork, movement and animation

`DeckGeometry.anchor()` now places the contact anchor exactly **three native
pixels above the bottom of each button**. The artwork is on one 40×40 logical
grid with stable `(20,34)` bottom-center anchor. Integer nearest-neighbor scaling
keeps crisp pixels: 80/96px keys use 2×, 72px keys use smaller 1× artwork.
No interpolated scaling, game engine, or additional runtime dependency is added.

Local actions use continuous floor coordinates, with left/center/right resting
positions. The horizontal span leaves room for the widest pose. Local artwork
and thoughts are restricted to the current key. Scoot, crawl, roll, tiptoe, pace,
edge peek, retreat and somersault move horizontally; bounce/dance/cheer provide
local vertical motion. Turn, spin, scratch, applause, nod and head shake use
expressive poses/gestures. Yawn, melt and reform provide quieter activity.
Roll/spin/somersault use crisp quarter-turns, reanchored after rotation.

Twenty new pose names: `puddle`, `sleep_curl`, `slump`, `proud`, `curious_lean`,
`lean_back`, `scoot_front`, `drag_tail`, `crawl_bridge`, `tiptoe`, `rolling_ball`,
`side_flop`, `twisted`, `spiral`, `diagonal_smear`, `horizontal_smear`,
`vertical_noodle`, `asym_impact`, `crown_ripple`, `double_arch`.

Across keys, one entity moves through continuous world coordinates. Key
rectangles are viewports, separated by an adjustable default 8px virtual bezel.
Pillow crops the same world sprite into intersecting free keys. The current
local x-offset is retained at takeoff, preventing a snap back to center.
Positions use elapsed time; deliberate poses are held independently.

Styles: classic, fluid, tiny, bunny, heavy, floaty, nervous, excited, sleepy,
running, sideways, tuck_roll, vault, careful_drop. Each has its own timing,
arc and pose sequence. Bunny/excited add anticipatory bounces; running adds a
run-up; vault uses a tendril; tuck_roll rotates and lands asymmetrically; sideways
keeps the face toward the viewer. Careful drop uses a downward-oriented peek
and fall (upward requests use classic). Tiny is a low arc; `bounce` is the
separate same-button hop action. `mood` chooses an appropriate travel style.

Normal movement remains in the existing 24 FPS device loop, configurable up to
30 FPS. Local pose time is quantized at 12Hz before applying the authored holds;
hop pose rates vary with style and phase. Stillness remains part of the design.
Global `animations=false` disables the companion, including text motion.

## Moods, color and needs

Moods: content, curious, playful, sleepy, asleep, waking, attentive, thinking,
focused, excited, proud, helpful, concerned, startled, cautious, shy, bored,
restless, mischievous, overwhelmed, peckish, overworked and recovering.

Each mood has a distinct body palette. Shade/body/highlight transition in four
quantized steps over about 0.9s, preserving alpha, dark outlines and contrasting
eyes. Palette changes affect Jelly only; functional UI colors are unchanged.

A local seeded RNG selects mood-biased actions with quiet/local/travel group
weights initially 70/20/10. These are selection weights, not guaranteed time
percentages; mood and preset modify them. Calm/busy moods suppress travel.
Low stimulation adds exploratory or idle actions; low confidence favors cautious
movement; high sociability adds greetings and glances.

`Mind.observe()` consumes only IDs, state, optional explicit outcome IDs and
successful-focus notifications, never labels, source code, prompts, commands,
transcripts or keystrokes. Duplicate snapshots do not count as new activity.
Meaningful event feeding is limited to once per five seconds. Continuous
running activity nourishes and stimulates Jelly but gradually reduces energy.
Energy recovers during quiet/rest. Every need is bounded to 0–100, and elapsed
updates are capped at two seconds so suspension does not apply hours of decay.

After roughly two minutes without activity Jelly becomes sleepy, and after five
minutes he can sleep. New activity wakes him; explicit errors can startle him
before concern. Sustained work with low energy becomes overworked; many changes
or high workload become overwhelmed. Reduced workload allows recovery. These
are deliberately lightweight simulated needs, not biological or productivity
measurements. Ordinary coding outside connected sessions is not observed.

No death, streaks, guilt, feeding obligation, or neglect penalty exists. Quiet
time is valid activity for this companion.

## Agent events and priority

Only unassigned `off` keys are free. READY/system/error/agent buttons always win.
Loss of either source or destination hides the whole entity on the next ordinary
render tick, canceling the thought. Zero free keys stay hidden; one free key
still supports local life. Free space permits delayed reappearance.

Input requests receive oldest-first stable attention. A breadth-first search
finds the shortest route through free keys to a free neighbor of the target.
It never enters the agent key or crosses occupied cells. Routes are recomputed
from current occupancy; blocked targets get a directional look/point from the
current location. Jelly scoots toward a neighboring target at a time-based
speed, then points left/right/up/down. Overwhelmed/overworked Jelly avoids travel.

Arrivals wave, running changes attract attention, input requests point, resolved
input nods, departures attract an exploratory glance, unknown connections produce
concern, and reconnection waves. Successful focus notifications arrive through a
bounded 32-item queue; callbacks never modify the animation controller.
Reactions coalesce with a minimum three-second interval; pending reminders are
at most once per 45 seconds. Cosmetic input pointing never consumes a functional
button press. There is no special empty-key feeding/press action.

Explicit outcomes are separate from normal state. An idle/Stop event **does not
mean success**, and unknown/link loss **does not mean failure**. The normal
snapshot API accepts optional:

```json
{
  "status": "idle",
  "producer": "existing-producer-id",
  "seq": 42,
  "outcome": "success",
  "outcomeId": "stable-unique-completion-id"
}
```

The ordinary authenticated instance-update route and producer/sequence rules
still apply. Outcome must be `success` or `failure`, paired with an ID of 1–128
characters. IDs deduplicate heartbeat snapshots and remain bounded to current
visible slots inside Jelly. The registry retains the last outcome until a new
explicit outcome; the companion does not repeatedly react to that retained value.

The native hook normalizer forwards explicit error/failure hooks and status error.
It forwards success only for explicit `status: "success"` on Stop/stop/agentStop/
AfterAgent events. Interruptions, aborted status and ordinary idle do not create
success outcomes. Outcomes carry only a generated/hash ID, never tool output.
Availability depends on the native harness supplying these events/fields;
OpenCode's separate adapter currently has normal state reactions but no new
explicit success mapping. No live/native-harness compatibility claim is made.

## Offline speech

`ocdeck/assets/jelly/thoughts.json` contains 1,040 individually authored, unique,
ASCII lines, each 1–52 characters. Categories have context constraints in code:
quiet, curiosity, play, running, input, success, concern, sleep, food, workload,
greetings, departures, reconnected, resolved and failure.

Arrival/departure/reconnect lines are separated to prevent contradictory text.
Success/failure lines require explicit events; ambient proud mood does not
invent a result. Stale input/running/unknown observations are cleared when the
corresponding state disappears. Text never includes session names or content.
A deque of the last 128 phrase IDs avoids repeats until a small category is
exhausted, then reuses its oldest selection. Different contexts keep separate
line identities. No runtime language model is used.

Text is drawn into a one-bit bitmap and nearest-neighbor scaled in a reserved
strip above the resting head. It remains inside the current key. Long lines
scroll once at 32 native pixels/second after a brief initial hold; short lines
hold without scrolling. The strip disappears after the pass. Movement/eviction
cancels it, sleeping is silent, and quiet actions hold long enough for reading.
The first ambient opportunity is after 20 seconds. Approximate ambient cooldowns
are 90/35/15 seconds for quiet/normal/chatty, with event speech also rate-limited.
No speech thread or repeated paragraph marquee exists.

## Configuration and persistence

The README has the full enable/disable example and defaults. All new options are
strictly validated: personality, mood_colors, needs, reactions, thoughts,
local_movement, travel and persistent. Existing enabled/gap/seed/hop options
remain compatible. Default hop style stays classic; `mood` is an explicit choice.
Version-1 appearance export/import stays compatible and preserves broker options.

Optional `jelly-state.json` resides next to broker configuration. Only schema
version, six bounded needs, mood and at most 128 phrase IDs are stored. It contains
no session IDs, labels, code, paths or transcripts. Checkpoints occur at most once
per minute and on ordinary close; saving failure logs a warning without disabling
agent monitoring. Invalid state is ignored. Resume restores at least 85 energy,
resets workload and wakes Jelly, with no offline decay penalty. Persistence is
false by default; it is independently configurable.

## Rendering, performance and failure isolation

One device connection and one existing device writer remain authoritative.
Jelly creates no timers, threads or busy-wait loop. Cached logical, scaled and
colored poses have bounded LRUs, as does the existing native frame cache.
Only intersecting/cosmetically changed free keys refresh; agent-render caching
and assignment-generation handling remain intact. Thoughts add updates only to
Jelly's own key. Controller/render exceptions disable Jelly and let normal
agent rendering continue; optional persistence errors only disable that save.

`device.jelly_life` reports mood/action/hop and bounded needs.
`device.render_timing` reports requested/effective loop FPS, over-budget ticks
and mean composition/conversion/write time. It is not an LCD refresh counter.

The refreshed [`benchmark.json`](benchmark.json) evaluates **all 14 styles at
24 and 30 FPS**, each simulating 30 seconds of work with two running-agent states
and actual StreamDeckMini native conversion, without HID writes. Composition
includes observation/controller/cropping. This is unpaced CPU measurement,
not a hardware throughput guarantee or full-app CPU measurement.

| Requested FPS | Mean composition range across styles | Mean native conversion range |
| --- | ---: | ---: |
| 24 | 0.039–0.117 ms/tick | 0.045–0.053 ms/tick |
| 30 | 0.033–0.042 ms/tick | 0.044–0.060 ms/tick |

Cold caches and host scheduling affect individual rows. Both have substantial
CPU headroom against 41.67ms/33.33ms budgets. USB delivery, physical dropped
frames, actual display smoothness and machine-wide application CPU remain
unmeasured. Default stays 24 FPS until a real Mini is reviewed.

## Verification and reproduction

The previous prototype had 79 Python and 25 Node tests. This expansion passes
**108 Python tests** (29 additional behavioral tests) and **26 Node tests**
(one additional hook-outcome test). Existing tests were retained. Ruff lint and
format, Pyright, wheel/sdist building, and installed-wheel vocabulary/rendering
are checked. Host validation is Linux/Python 3.12; remote Windows matrix results
are separate from these local claims.

New tests cover all action trajectories, all 33 floor anchors and distinct new
poses, all 14 hop styles, mood palettes, event feeding limits, sustained exercise,
sleep/wake, restorative persistence, workload, safe routes and directional points,
input priority, outcome deduplication and schema, honest event categories,
1,040-line uniqueness, one-pass scrolling, own-key clipping, no-repeat history,
config validation and bounded metadata-only state. Earlier eviction, agent
priority, single-writer, shutdown and baseline behavior tests continue to pass.

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
node --test tests/facts.test.mjs tests/harnesses.test.mjs tests/next.test.mjs
python -m ruff check ocdeck tests
python -m ruff format --check ocdeck tests
python -m pyright
python -m build
python scripts/preview_jelly.py --benchmark
python scripts/preview_jelly_life.py
python scripts/preview_jelly_life.py --fps 30 --output docs/jelly-30
```

Generated artifacts include the original sprite sheet/metadata, idle and four
directional hop GIFs, full-deck demo, personality demo and hop contact sheet;
plus new action GIF/PNG, mood PNG, all-pose PNG, all-hop GIF, thought GIF,
agent-reaction GIF and catalog JSON. Visual inspection checks floor anchoring,
expressive silhouettes, mood contrast and the above-head scrolling strip.
Previews simulate screens and gaps, not a measured physical chassis.

After enabling the README config, close Elgato's app, stop any existing broker,
and run `python -m ocdeck broker`. Use `--mock` for a hardware-free broker.
From another terminal use `python -m ocdeck status --json` and
`python -m ocdeck stop`.

## Files and limitations

New runtime modules: `jelly_catalog.py`, `jelly_mind.py`, `jelly_words.py`; new
packaged data: `assets/jelly/thoughts.json`. Existing `jelly.py` and `jelly_art.py`
contain the expanded controller and pixel art. Device/broker integration adds
persistence, telemetry and the focus handoff; model/hook normalization adds
explicit outcome metadata. `pyproject.toml` packages the vocabulary. New preview
script: `scripts/preview_jelly_life.py`. New Python tests: `tests/test_jelly_life.py`;
Node coverage extends `tests/next.test.mjs`. README, this report and visual assets
are updated. No new runtime dependency is required.

Physical Mini/other-model testing is still pending. 72px displays use smaller
1× art; the bezel gap is uncalibrated. Rotation is deliberately discrete pixel
rotation, not a smooth vector spin. Palette/glyph readability and quiet/chatty
timing should be reviewed on the actual LCDs. Larger layouts and outcome payloads
have automated coverage, not physical/native-harness certification. Agent
behavior is inferred from metadata, not semantic understanding of the task.
Direct coding outside connected sessions is invisible. No manual feeding,
keypress game, multi-pet system or diagonal travel is added.

Recommended next step: test the floor, thought strip and input-approach behavior
on a real Mini at 24 and 30 FPS, including mid-flight assignment, full occupancy,
rapid session churn, long work/rest periods and disconnect/shutdown.
