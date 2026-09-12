@echo off
setlocal
set "PYTHONPATH=%~dp0..;%PYTHONPATH%"
set "AGENTDECK_PYTHON=%USERPROFILE%\.opencode-deck\venv\Scripts\python.exe"
if not exist "%AGENTDECK_PYTHON%" set "AGENTDECK_PYTHON=python"
"%AGENTDECK_PYTHON%" -m ocdeck harness-launch --profile codex -- %*
exit /b %ERRORLEVEL%
