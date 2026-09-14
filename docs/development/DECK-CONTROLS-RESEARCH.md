# Research and design: physical launch and approval controls

Reviewed September 14, 2026. This is a qualitative review of developer reports and primary product documentation, not a prevalence survey.

| Developer concern | Evidence | Design response |
|---|---|---|
| A notification is insufficient if answering still requires returning to the original UI. | [Claude actionable approval request](https://github.com/anthropics/claude-code/issues/62458), [mobile approval request](https://github.com/anthropics/claude-code/issues/60433). | Review and decide on the deck where a native request-specific transport exists. |
| Remote approval can appear successful while the native session remains blocked. | [Claude approval hang report](https://github.com/anthropics/claude-code/issues/52084). | Show queued, delivered and confirmed handoff separately; provide native-terminal fallback. |
| Parallel sessions need deliberate working directories. | [VS Code wrong-directory report](https://github.com/microsoft/vscode/issues/296854). | Store explicit absolute cwd, show folder before launch, never mutate the broker's global cwd. |
| Multiple agents editing one checkout can conflict. | [Developer discussion of parallel sessions and worktrees](https://www.reddit.com/r/GithubCopilot/comments/1st22ff/how_are_you_managing_multiple_coding_agents_in/). | Support distinct existing worktrees as named profiles; avoid silently creating branches or altering repositories. |
| Repeated permission prompts encourage habitual approval. | [Anthropic's analysis of permission fatigue](https://www.anthropic.com/engineering/claude-code-auto-mode). | Require explicit entry into a selected request; no global approval button and no persistent “allow all” policy change. |

These observations informed the design; they do not establish that every developer wants the same workflow. Controls and permission handoff are independently opt-in.

## Primary API references

- [Claude hook reference](https://code.claude.com/docs/en/hooks#permissionrequest): native `PermissionRequest` response with `decision.behavior`. The adapter returns only allow/deny for the held invocation and never sends permission-rule updates. Expiry or transport failure returns to normal native handling.
- [OpenCode SDK](https://opencode.ai/docs/sdk/) and [generated SDK source](https://github.com/anomalyco/opencode/blob/dev/packages/sdk/js/src/v2/gen/sdk.gen.ts): legacy session permission response plus current `permission.reply`. The adapter selects an available method and responds with `once` or `reject` to a live request ID.
- [Copilot hook reference](https://docs.github.com/en/copilot/reference/hooks-reference): `permissionRequest` runs before permission-service rule evaluation. Treating it as a listener for already-pending prompts would intercept a different set of actions. This implementation retains focus fallback.
- [Existing harness coverage](../HARNESSES.md) defines the other shipped integrations. Activity hooks and question events are not treated as permission transports.

## Engineering acceptance

The implementation includes CLI/INI round trips, request expiry and lease loss, slot reuse, one-time decision delivery, stale menu presses, launch argument/cwd preservation, disabled-mode fallback, and a real Node Claude-hook to HTTP broker integration test. Renderer previews use production drawing code. Linux mock tests cannot establish Windows Terminal launch, HID gesture timing or native installed-harness behavior on physical hardware; those remain manual acceptance items before release.

Manual acceptance: test every configured harness launch on Windows, verify the selected folder and live slot, test Claude/OpenCode allow and deny on harmless fixture actions, expire/cancel a prompt, unplug/reconnect the deck, fill all slots, and verify that Jelly taps and normal window focus retain their behavior. Include an installed-wheel run so bundled JS paths and hook upgrades are exercised.
