# AI coding-agent integration guides

[Project overview](../../README.md) · [Documentation index](../README.md)

Install native plugins/hooks for the coding tools you already use. AgentStreamDeck does not install the harness itself or require a different model provider.

| Guide | Topic |
|---|---|
| [Claude Code Stream Deck integration](CLAUDE.md) | Project settings.local.json hooks and paired AskUserQuestion coverage. |
| [Codex CLI Stream Deck integration](CODEX.md) | Project hooks, native trust and observed approvals with unknown counts. |
| [GitHub Copilot CLI Stream Deck integration](COPILOT-CLI.md) | Copilot terminal activity reporting and project hook removal. |
| [GitHub Copilot in VS Code Stream Deck integration](COPILOT-VSCODE.md) | Preview workspace hooks, native trust and editor-window scope. |
| [Cursor CLI Stream Deck integration](CURSOR.md) | Cursor agent CLI activity, configuration and limitations. |
| [Gemini CLI Stream Deck integration](GEMINI.md) | Turn/tool events, notifications and native hook response behavior. |
| [OpenCode Stream Deck integration and global plugin setup](OPENCODE.md) | Global server plugin, config homes, snapshots and optional TUI mode. |

[Coverage matrix](../HARNESSES.md#supported-integrations) · [First run](../FIRST-RUN.md) · [State semantics](../features/STATUS.md).

OpenCode uses a global plugin. The other six profiles install per-project native hooks. Native hook availability and trust depend on the installed harness version. Keep one monitored harness per OS window for reliable focus.

## Related guides

[First run](../FIRST-RUN.md) · [CLI](../CLI.md) · [UI](../UI.md) · [Troubleshooting](../TROUBLESHOOTING.md)
