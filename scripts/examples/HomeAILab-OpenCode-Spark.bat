@echo off
setlocal
if not defined HOMEAILAB_ROOT (
    echo Set HOMEAILAB_ROOT to the HomeAILab checkout directory first.
    exit /b 2
)
call "%~dp0..\Launch-Agent.bat" --profile opencode --launcher "%HOMEAILAB_ROOT%\harness\opencode\opencode-spark.bat" -- %*
exit /b %ERRORLEVEL%
