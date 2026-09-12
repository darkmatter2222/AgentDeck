@echo off
setlocal
if not defined AGENTDECK_LOCAL_URL (
    echo Set AGENTDECK_LOCAL_URL to the Anthropic-compatible server base URL.
    exit /b 2
)
if not defined AGENTDECK_LOCAL_MODEL (
    echo Set AGENTDECK_LOCAL_MODEL to the model ID served by that endpoint.
    exit /b 2
)
set "ANTHROPIC_BASE_URL=%AGENTDECK_LOCAL_URL%"
set "ANTHROPIC_API_KEY="
set "ANTHROPIC_AUTH_TOKEN=%AGENTDECK_LOCAL_TOKEN%"
if not defined ANTHROPIC_AUTH_TOKEN set "ANTHROPIC_AUTH_TOKEN=local-dev"
set "ANTHROPIC_MODEL=%AGENTDECK_LOCAL_MODEL%"
set "ANTHROPIC_DEFAULT_OPUS_MODEL=%AGENTDECK_LOCAL_MODEL%"
set "ANTHROPIC_DEFAULT_SONNET_MODEL=%AGENTDECK_LOCAL_MODEL%"
set "ANTHROPIC_DEFAULT_HAIKU_MODEL=%AGENTDECK_LOCAL_MODEL%"
set "CLAUDE_CODE_SUBAGENT_MODEL=%AGENTDECK_LOCAL_MODEL%"
call "%~dp0..\Launch-Agent.bat" --profile claude -- --model "%AGENTDECK_LOCAL_MODEL%" %*
exit /b %ERRORLEVEL%
