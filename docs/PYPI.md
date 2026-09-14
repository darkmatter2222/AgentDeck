# GitHub releases and PyPI publishing workflow

[Project overview](../README.md) · [Documentation index](README.md)

The current workflow is [Automatic main release](https://github.com/darkmatter2222/AgentStreamDeck/actions/workflows/pypi.yml), defined in [.github/workflows/pypi.yml](../.github/workflows/pypi.yml). This page describes the checked-in workflow, not the success state of any particular remote run.

## What triggers publication

A push to main or manual workflow dispatch enters the release workflow. It is scoped to darkmatter2222/AgentStreamDeck. A commit already carrying a stable version tag is skipped. Otherwise the workflow determines the next patch after the highest stable version tag, stamps pyproject.toml and ocdeck/__init__.py in the build workspace, and runs verification. The stamp is not committed back to the source branch, so the installed package version can differ from the checked-in version.

There is no docs-only path exclusion: merging documentation to main can produce a new package and GitHub release. A feature-branch push does not meet the push-to-main trigger; it can still run PR CI.

## Verification and assets

The workflow runs Python and Node suites, Ruff checks/formatting and Pyright. It builds wheel/sdist, checks package metadata with Twine, produces a CycloneDX environment SBOM and a source ZIP, and includes the showcase MP4 and hero GIF when present. It generates release-asset SHA256SUMS and build-provenance attestations, then creates or updates the GitHub release.

The wheel/sdist artifact goes to the publish-pypi job, which uses the pypi environment and PyPI trusted publishing with attestations. Existing package files are skipped on retry rather than overwritten.

## Trusted publisher identity

| Field | Repository workflow value |
|---|---|
| Distribution | agentstreamdeck |
| Owner | darkmatter2222 |
| Repository | AgentStreamDeck |
| Workflow filename | pypi.yml |
| GitHub environment | pypi |

These must match the account-side publisher configuration. Existing environment review requirements still apply. A publisher mismatch or pending environment approval is separate from source-test success. Inspect the actual workflow run for the current publication result.

## Release verification

Check the new GitHub release and PyPI project, inspect asset checksums/attestations, then install the intended version in an isolated environment and run `python -m ocdeck --version`. Validate packaged runtime assets from outside a checkout. Normal first-time users still run `python -m ocdeck install` and install project hooks after pip.

The version-specific release-v*.yml workflows and docs/releases notes are historical release records. The automatic pypi.yml workflow is the current main-release entry point. Do not dispatch old release workflows as the ordinary update process.

## Related guides

[Developer setup](development/README.md) · [User upgrade guide](features/UPDATES.md) · [Release notes](https://github.com/darkmatter2222/AgentStreamDeck/releases)
