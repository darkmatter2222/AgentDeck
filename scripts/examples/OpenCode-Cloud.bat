@echo off
setlocal
REM Uses providers in your normal OpenCode config; pass --model provider/model.
set "OPENCODE_CONFIG="
set "OPENCODE_CONFIG_CONTENT="
set "OPENCODE_CONFIG_DIR="
call "%~dp0..\Launch-Agent.bat" --profile opencode -- %*
exit /b %ERRORLEVEL%
