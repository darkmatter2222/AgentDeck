# Contributor instructions

Read [the design and experience contract](docs/development/DESIGN_SYSTEM.md) before modifying UI, Jelly, scenes, buttons or input handling. Read [the development guide](docs/development/README.md) for repository workflows.

Preserve session-key ownership, generation-checked inputs, fixed browser destinations and render-thread isolation. New visual behavior must support Mini, Original/MK.2 and XL geometry; degrade gracefully with one or zero free keys; expose configuration in the CLI; and include linked user documentation. Keep the README focused on the product rather than a chronological update log.

For world changes, maintain [the configuration guide](docs/jelly/world.md) and [the scene catalog](docs/jelly/world-catalog.md). Run the required repository checks in `.github/workflows/ci.yml`; use offline previews for visual verification. Do not claim physical hardware validation from mock tests.
