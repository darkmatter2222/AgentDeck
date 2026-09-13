\
param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
& $Python -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11 or newer required"'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ is required.' }
& $Python -m pip install --disable-pip-version-check --upgrade agentstreamdeck
if ($LASTEXITCODE -ne 0) { throw 'AgentStreamDeck package installation failed.' }
& $Python -m ocdeck install
if ($LASTEXITCODE -ne 0) { throw 'AgentStreamDeck broker startup installation failed.' }
Write-Host ''
Write-Host 'AgentStreamDeck is installed. The broker starts automatically at sign-in.'
Write-Host 'Install the native hook/plugin in each project you want to monitor; no launcher is required.'
Write-Host 'Run: ocdeck status'
