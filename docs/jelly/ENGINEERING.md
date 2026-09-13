# Living Jelly prototype — engineering report

Repository: https://github.com/darkmatter2222/AgentStreamDeck

Branch: `feature/living-jelly-prototype`, based on main commit
`804531a` (Document successful AgentStreamDeck PyPI publication).
Run `git rev-parse HEAD` for the final branch commit. This report is committed
with the implementation; it does not embed its own self-referential commit hash.
No release or main-branch merge is part of this experiment.

## Implementation

| Concern | Implementation |
| --- | --- |
| Architecture | One `Jelly` controller, one continuous `(x,y)` bottom-center anchor, rectangular `DeckGeometry` viewports. |
| Logical art | Original 40×40 RGBA, seven colors plus transparency, integer-coordinate polygons and face details. No borrowed game artwork. |
| Scale | Integer nearest-neighbor only: 80px keys use 2×; 72px keys use 1×. |
| Contact anchor | `(20,34)` logical pixels; bottom contour ends at y=33. Blinks leave silhouette and anchor unchanged. Mirroring preserves x=20. |
| Physical FPS | Existing device-loop `fps`: default 24, supported 1–30; this experiment evaluates 24 and 30. |
| Pose rate | Classic airborne sequence: 7 holds over 0.7s (10Hz); fluid: 9 holds over 0.7s (~12.9Hz). Preparation/landing 10Hz; gestures/blink 12Hz. Idle holds are longer. |
| Geometry | Live `key_layout()` and `key_image_format()`; mock geometry 2×3, 3×5, 4×8. Orthogonal adjacency never wraps rows. |
| Bezel | Default 8 native pixels between viewports; configurable 0–40. Gap has no display surface. Physical calibration remains pending. |
| Clipping | One scaled world sprite, pasted at relative coordinates into intersecting free-key RGBA viewports. Negative paste offsets clip it; source/destination crops derive from identical pose and position. No special exit/entry sprites. |
| Trajectory | Smoothstep interpolation plus a parabolic upward offset; smaller arc for vertical travel. Position advances at device FPS independently of held artwork. |
| Jump timing | 600ms look/bob/compress/hold, 700ms flight, 500ms impact/rebound/jiggle/recovery. |
| Occupancy | Only `state == off` with no assignment ID is free. READY/system/error/agent UI takes priority. |
| Eviction | On the next ordinary render tick, invalidated source or destination hides the entire entity immediately. No animation completion delay. |
| Reappearance | Randomized 0.5–1.3s delay after free space exists. Hiding/respawning is allowed for eviction; normal travel is always adjacent. |
| Threading | No new timers, threads, connections, writer or busy loop. Existing stop-event wait drives all updates; close clears the entity. |
| Failure handling | Initialization/update/crop/native Jelly conversion errors are logged once and disable the entity. Existing agent render path continues. Reconnection or restart reconstructs it. Hardware write errors retain normal device reconnect behavior. |
| Configuration | Validated `jelly.enabled`, `virtual_gap`, `behavior_seed`, `hop_style`; enabled defaults false. Existing global `fps` is authoritative. `animations=false` disables Jelly. |
| Appearance I/O | Version-1 appearance exports stay compatible and omit broker-level Jelly options. Imports preserve existing Jelly configuration. |

Controller actions: hidden, idle/breathing, blink (half/closed/open), look left,
right and up, wave, point left/right, and rest/sleep/wake. Hopping contains distinct
preparation, squash, launch/stretch, airborne/apex/fall and landing/recovery phases
in all four directions. Pseudopods extend, reach, wave/point, then retract. Facial
recipes cover neutral, happy, curious, focused, surprised, sleepy, jump and
landing; some share base eye geometry with gaze or body deformation providing
the expression. `surprised` is available in the art/sprite sheet, not a separate
randomly scheduled behavior.

Behavior uses a local seeded `random.Random`, quiet 2–5s action intervals, and
weighted choices. With only one free key, all non-travel behavior remains
available. With no free keys, no crops or behavior actions are produced.

## Caching and integration

`logical_sprite` has a bounded 384-entry cache; scaled/mirrored sprites have a
512-entry cache. Images are immutable by convention. Per-key crop bytes form
the changed-image identity and reuse the existing bounded 768-entry native
frame LRU. There is no unbounded per-timestamp cache. Only intersecting free
keys are composed; held crops do not trigger a device write, and departed keys
are cleared through the ordinary off-state path. Normal agent frames retain
their existing cache and appearance behavior.

Native conversion is not a CPU bottleneck in this simulation, so no separate
precomputed native animation bank was added. The main render loop exposes
`render_timing`: requested FPS, effective loop FPS, over-budget ticks, and mean
composition/conversion/device-write ms per tick. These are cumulative since
connection, not USB delivery acknowledgements or a physical display FPS counter.
`frames` remains the existing changed-key write count, not deck FPS.

## Visual review

Inspected original sprite sheet and sampled horizontal and vertical GIF frames:
anticipation, elongated launch, split crops behind the bezel, full emergence,
impact compression and recovery. Both horizontal and vertical flights intersect
two viewports. Logical-grid and alpha-bound tests protect anchor/palette behavior
without brittle full-image goldens. The idle GIF's first and last RGB frames are
identical, avoiding a loop seam. Individual directional demo GIFs deliberately
restart their one-way demonstration; the four-direction full-deck demo returns
to its starting key.

The side-by-side `jelly_hop_comparison.gif` uses the same path and timing for both
styles. Classic's longer, distinct launch/apex/fall holds make the silhouette
easier to read at key size; fluid adds intermediate shape changes. Classic is
the provisional default. Neither style is claimed hardware-validated. No
bilinear, bicubic or LANCZOS scaling is used for Jelly. Existing agent UI retains
its own renderer. The simulated key outlines are illustrative, not a measured
Mini chassis model.

## Validation

Baseline (before source edits, after installing declared project dependencies):
**61/61 Python tests**, **25/25 Node tests**. The initial Python attempt in the
bare environment failed because project dependencies, including psutil, were
missing; installing `.[dev]` resolved that baseline setup issue.

Final local validation: **79/79 Python tests**, including **18/18 new Jelly tests**;
**25/25 Node tests**. Ruff lint/format and Pyright pass. Wheel and source package
build successfully. The wheel's Jelly imports and bundled preview script are
checked from outside the source checkout. Host: Linux, Python 3.12.

New tests cover adjacency/corners/edges/multiple grids; filtering functional UI;
zero/one/multiple free keys; seeded behavior; destination selection; immediate
eviction in idle/gesture/rest; mid-flight source/destination invalidation;
continuous movement and two-key intersections in all directions; full-world
reference clipping and missing bezel pixels; stable anchors and nearest-neighbor
scaling; distinct pose/position frequencies; close/no-new-thread lifecycle;
config rejection and appearance preservation; animation toggle; graceful
cosmetic exceptions; and the actual device writer with a fake transport/clock,
checking changed-key writes, exact agent replacement pixels, and shutdown.

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m unittest discover -s tests -p test_jelly.py -v
node --test tests/facts.test.mjs tests/harnesses.test.mjs tests/next.test.mjs
python -m ruff check ocdeck tests
python -m ruff format --check ocdeck tests
python -m pyright
python -m build
```

The project uses `unittest`; installing pytest is unnecessary for the prototype.
No existing tests were deleted or weakened.

## 24 vs 30 FPS observations

Measured using `python scripts/preview_jelly.py --benchmark` on this host.
Each row is an **unpaced simulation of 30 seconds**, with real Pillow composition
and StreamDeckMini native conversion but no HID connection/writes. These are
per-simulated-tick costs, not sustained hardware FPS or machine-wide CPU usage.
Raw results: [`benchmark.json`](benchmark.json).

| Style | Requested FPS | Composition mean ms | Composition p95 ms | Native conversion mean ms | Process CPU seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Classic | 24 | 0.0163 | 0.0229 | 0.0410 | 0.0422 |
| Classic | 30 | 0.0143 | 0.0199 | 0.0373 | 0.0475 |
| Fluid | 24 | 0.0153 | 0.0216 | 0.0453 | 0.0445 |
| Fluid | 30 | 0.0143 | 0.0200 | 0.0373 | 0.0476 |

Both are well below the CPU frame budgets (41.67ms at 24; 33.33ms at 30).
Process CPU here is about 0.14–0.16% of a single core when amortized across the
30 simulated seconds. This excludes agent rendering, broker work, scheduling
and real HID writes; it must not be read as total application CPU utilization.
Small differences between variants/rates are not statistically meaningful.

`python -m ocdeck devices` returned `[]`. Effective delivered LCD FPS, USB write
time, hardware late/dropped frames and physical stability are **not measured**.
24 FPS remains the conservative default; 30 should be selected after testing a
physical Mini. The implementation does not introduce any 60 FPS requirement.

## Reproduction and hardware acceptance

```bash
python scripts/preview_jelly.py
python scripts/preview_jelly.py --fps 30 --output docs/jelly-30
python scripts/preview_jelly.py --debug --output docs/jelly-debug
python scripts/preview_jelly.py --benchmark
```

The command creates: `jelly_static.png`, `jelly_sprite_sheet.png`,
`jelly_sprite_sheet.json`, `jelly_idle.gif`, `jelly_hop_right.gif`,
`jelly_hop_left.gif`, `jelly_hop_up.gif`, `jelly_hop_down.gif`,
`jelly_full_deck_demo.gif`, `jelly_personality.gif`,
`jelly_hop_comparison.gif`, and `jelly_hop_contact_sheet.png`.
`--benchmark` additionally writes `benchmark.json` and requires the project's
StreamDeck dependency. Normal preview generation requires only Pillow.

Enable configuration as documented in the README, close Elgato's app, and stop
the existing broker before starting this branch:

```bash
python -m ocdeck broker
```

From another terminal:

```bash
python -m ocdeck status --json
python -m ocdeck stop
```

For acceptance, run 24 FPS and 30 FPS for several minutes each, with both hop
styles; save status timing and observe actual key motion. Start an agent on a
key while Jelly is idling and mid-hop; confirm immediate replacement. Fill every
key, close sessions, disconnect/reconnect, and stop the broker. Verify no stale
Jelly pixels and clean blank/close behavior. Compare gaps 4, 8 and 12 to tune the
illusion against the real Mini bezel. No physical validation is claimed here.

## Files and remaining scope

Added source: `ocdeck/jelly.py`, `ocdeck/jelly_art.py`,
`scripts/preview_jelly.py`, `tests/test_jelly.py`.

Modified: `ocdeck/device.py`, `ocdeck/settings.py`, `README.md`.

Added documentation/artifacts: this report and all generated assets listed above
under `docs/jelly/`. Artwork source ships in the normal Python package; the
sprite sheet is a human inspection artifact, not a runtime network dependency.

Known limitations: no physical device tested; virtual gap is uncalibrated;
72px keys use smaller 1× artwork; 15/32-key geometry is tested without hardware;
no diagonal travel or pathfinding across occupied keys; no press reaction;
no virtual-pet progression or external event behavior; static main application
appearance preview does not show Jelly; configuration changes require restart.
The geometry/controller leave room for future events but this branch adds none.

Recommended next iteration: use a real Mini to tune arc, compression holds,
vertical emergence and gap, compare 24/30 with live agent churn, then decide
whether the fluid variant offers an improvement. That physical review is the
remaining acceptance gate for the central “jumped between the buttons” illusion.
