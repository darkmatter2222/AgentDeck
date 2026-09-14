# Documentation audit and verification scope

[Project overview](../../README.md) · [Documentation index](../README.md)

## Scope and source baseline

Documentation audit against repository main commit `63d29ca`, including Python CLI/broker/settings/renderers, JavaScript plugins and native-hook profiles, packaging and release workflows, PowerShell/BAT helpers, tests, existing docs, checked-in media and the printable mount. This is a documentation/source-contract review, not a new hardware or upstream-native acceptance claim.

## Recovered context and corrected drift

| Finding | Documentation change |
|---|---|
| Original YouTube demo reduced to easy-to-miss text links | Prominent linked thumbnail near the top and a media index entry |
| Many animations absent from the overview/navigation | Restored showcase sections and inventory linking every checked-in media asset |
| Stars, stats and support beneath the hero | Moved star request, dynamic badges and verified support link above it |
| Features spread across chronological records | Task-oriented feature, integration, reference and developer hubs |
| No complete argument reference | All CLI subcommands and arguments captured from the parser |
| UI settings lacked one complete defaults reference | Source-backed appearance and Jelly field tables plus UI interaction guide |
| Old setup required wrappers/OpenCode | Current first-run/tutorial/troubleshooting/environment guides describe normal native launches |
| Old guides named the wrong Windows task or nonexistent installer flags | Corrected current setup and explicitly labeled legacy helpers |
| OpenCode managed helpers expect metadata absent from fresh installs | Documented limitation and normal-launch path |
| Old update docs described GitHub lookup/manual-only publishing | Current PyPI discovery, watcher and automatic main-release workflow documented |
| Appearance said empty keys always black | Explained READY/Jelly defaults and exact opt-outs |
| Coffee text said only the cup opens support | Both displayed Jelly and cup actions documented |
| Rename instructions pinned an obsolete version | Migration now installs the current distribution |

## Verification

Run `python scripts/check-docs.py` for local link/heading resolution, media decoding, config example validation and CLI/appearance/Jelly reference coverage. The checker is included in PR CI. The media gallery preserves existing assets rather than regenerating them with potentially different historical renderers.

Local validation passed for 66 Markdown files, 991 local links, all 21 CLI commands, all 18 appearance fields, all 14 Jelly fields and 38 decoded PNG/GIF assets. Reference/config JSON examples passed the runtime validator. Representative hero, preset, motion, text, Jelly and coffee images were visually inspected. ffprobe verified the checked-in showcase MP4 as H.264, 1280×720, 24 seconds.

External YouTube playback and badge-service responses were not verified in this environment. The YouTube destination is recovered from repository history and existing references. The verified support destination remains Buy Me a Coffee. No alternative account URL was invented.

The docs distinguish current implementation, historical evidence and unverified physical/native behavior. No Windows desktop, Stream Deck USB device, live agent login or physical printed mount was available for this documentation audit. No application runtime behavior was changed.

## Maintenance

Keep current guides linked from the main README and documentation index. Put new release history in docs/releases rather than turning setup pages into chronological logs. Preserve old anchor destinations where useful and make historical context explicit. Update parser/default references whenever the implementation changes; the coverage check detects missing names, but reviewers must still verify semantics and default values.

## Related guides

[Developer hub](README.md) · [Source map](SOURCE-MAP.md) · [Documentation index](../README.md) · [Historical test evidence](../TEST-RESULTS.md)
