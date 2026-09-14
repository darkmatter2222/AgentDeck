# Windows, Linux, WSL, SSH, containers and remote model boundaries

[Project overview](../README.md) · [Documentation index](README.md)

The broker validates native local process IDs and creation timestamps. A process inside another operating system, container or remote host is not automatically a valid Windows desktop identity. A shared directory or forwarded localhost port does not translate that identity.

| Environment | Current behavior |
|---|---|
| Native Windows OpenCode | Global server plugin; normal launch; window capture/fallback |
| Native Windows hook harness | Project hook; normal launch; no managed launcher required |
| Windows Terminal tabs/panes | Shared top-level window can be ambiguous; exact tab selection absent |
| VS Code Copilot | Preview workspace hooks; window focus, no exact chat selector |
| Native Linux | User systemd startup and broker/rendering; no desktop focus |
| WSL, Docker or SSH guest runtime | Cross-environment identity/transport relay not implemented |
| macOS | No supported automatic startup/focus workflow documented |
| Local CLI calling a remote model API | Observed local CLI remains local; model host does not change process identity |
| Multiple clients on one OpenCode server | Not independently mapped by default process-wide adapter |

## Remote model versus remote agent process

A Windows Claude/OpenCode process calling a model served on another machine remains a local agent process and can use the normal integration. Running that same CLI over SSH moves its PID and hook execution to the remote machine, which the current Windows broker cannot register as a local process.

## What a future remote relay would require

A host-side process would need to own the Windows window and lifetime, translate a bounded authenticated guest snapshot into a local registration, and use a separate scoped credential. Guest PIDs must remain metadata. Disconnect, reconnect, broker restart, guest exit and identical PIDs across guests need explicit tests. This is a design boundary, not an available installation option.

Do not bind the current broker to 0.0.0.0 or copy its unrestricted local token into remote environments to work around the missing relay. The existing per-launch Node relay is only a local compatibility mechanism.

## Related guides

[Normal installation](FIRST-RUN.md) · [Local launchers](LAUNCHERS.md) · [Focus](features/FOCUS.md) · [Privacy](features/PRIVACY.md) · [Architecture](ARCHITECTURE.md)
