# Living-world implementation status

[World controls](world.md) · [Coverage inventory](world-coverage.json) · [Development guide](../development/README.md)

This is an **unfinished, opt-in implementation**, not the completed living-world experience. The shipped director remains the default. The new director has explicit object definitions and activity render branches for all 57 props, but those branches are not equivalent to verified, complete behaviors. The coverage manifest deliberately keeps visual reviews pending.

## Try the development director

```console
ocdeck world configure --living-world
ocdeck world configure --no-living-world
```

Restart the broker after either command. `living_world` defaults to `false`. Existing `interactions`, `props`, `reduced_motion`, `interaction_seconds`, `max_keys`, captions and priority controls still apply. With the new director, disabling interactions also removes its physical objects. The legacy director retains its documented ambient behavior.

The new director uses existing Jelly persistence when `jelly.persistent` is enabled. World snapshots share `jelly-state.json`, use an independent version, and restore objects to storage before reconciling coordinates. They contain at most eight objects and 24 recent activity names. No offline neglect debt is accrued. A world-specific reset command is not yet implemented.

## Implemented foundations

- Exact-target free-cell breadth-first routes; orthogonal hops use the existing anticipate/flight/land renderer.
- Seeded weighted placement over the reachable component, with every valid candidate eligible. Tools get a separate work cell when space permits.
- Stable object IDs, tool home locations, reservation/held/use/changed/storage states, and bounded snapshots.
- Notice, approach, local position, reach, carry, use, return, put-down, admiration and rest stages.
- Rake contact progress, cup contents, plant water transfer values, a single applied-outcome guard, and gift-content identity creation.
- Pose-aware side grips and independent foreground object layers that crop across deck keys.
- Immediate cancellation on ownership loss, menus, help, touch, update and agent attention. Scene changes do not cancel an active activity.
- Snapshot copies created on the owner thread; periodic filesystem writes run on at most one worker. Disconnect saves happen before discarding world state.

## Work still required before enabling by default

These are unmet acceptance criteria, not optional polish:

1. Complete and inspect the contact, manipulation, cleanup and disposition of every prop. Current shared six-second use stages are insufficient for many multi-step activities.
2. Refine the rake grip, contact arc, leaf resting positions, put-down and occasional pile-play variation at all native sizes.
3. Implement actual ball chase/stopping, kite launch/reel-in, sled boarding/dismounting, gift-toy follow-up play and fountain-to-plant journeys. Current render branches are prototypes.
4. Replace unrelated ambient loops with consequences tied to actual atmosphere timing. `ATMOSPHERES` is an opportunity mapping, not completed environmental behavior coverage.
5. Reuse completed plants and other durable fixtures on later visits. Persistent snapshots currently preserve their records; the selector does not yet revisit every finished object correctly.
6. Add meaningful rest routines, personality preference, unfinished-project resumption, and a world reset control.
7. Finish all 57 prop and 25 atmosphere native-size animated reviews and all 75 scene compatibility reviews. Inspect edge/mirror cases, support/contact and face occlusion individually.
8. Resolve the remaining performance difference and add isolated cold-cache measurements. The checked-in comparison uses equal layouts and simulated durations, but the directors execute different activity poses.

## Reproduce initial evidence

```console
python scripts/preview_living_world.py
python -m unittest discover -s tests -p test_living_world.py
```

The preview script uses the production director and renderer at Mini 72px, Original/MK.2 80px and XL 96px. It writes full-deck GIFs, stage contact sheets and timing metadata. The green cell in the takeover reel represents an owned session key. These are offline simulations, not physical-device verification.

[Rake, Mini](living-previews/autumn_rake-72.gif) · [Rake, Original](living-previews/autumn_rake-80.gif) · [Rake, XL](living-previews/autumn_rake-96.gif)

[Cocoa, Mini](living-previews/autumn_cocoa-72.gif) · [Cocoa, Original](living-previews/autumn_cocoa-80.gif) · [Cocoa, XL](living-previews/autumn_cocoa-96.gif) · [Session takeover](living-previews/autumn_rake-72-takeover.gif)

## Architecture and ownership

`world_objects.py` holds immutable definitions and mutable object records. `world_interactions.py` advances intentions and material state. `world_object_art.py` consumes that state and never changes outcomes. `World` chooses the opt-in or legacy director, then composes background, Jelly and foreground layers. `DeckGeometry.route_to` differs from `route_beside`: a prop's own cell is the destination.

The device retains authority over session ownership and input precedence. World reservations never reserve a hardware key. Every tick revalidates the tool home, work cell and actor availability. A canceled carried object goes into logical storage; world visuals disappear and actor control is released. Future routes are recomputed one hop at a time.

Time advances only during valid visible use. Large elapsed-time jumps are capped, so missed time cannot silently award a completed offscreen interaction. Rendering uses copied cached sprites. The current renderer allocates a full-deck logical canvas for foreground and background; optimizing that cost requires the comparative measurements above.

## Validation at this checkpoint

- Python: 214 tests passed, with one real-process restart test skipped because this environment exposes host PIDs through `/proc`.
- Node: 30 tests passed, including permission tests.
- Ruff lint/format, Pyright, documentation validation and package build passed.
- An installed wheel imported the new modules and verified bundled JavaScript/PowerShell assets outside the checkout.
- Native stage contact sheets for the rake and cup were inspected. This is not a completed full-animation review of every asset.

[Offline comparison measurements](living-previews/comparison.json) are reproducible with `python scripts/benchmark_living_world.py`. Full-sequence capture measurements are in [timings.json](living-previews/timings.json). They do not measure USB writes or real hardware frame timing. The object compositor was changed to scale only intersecting key crops after the first measurement showed excessive full-deck allocation costs.
