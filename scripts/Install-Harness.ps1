param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('claude','copilot-cli','copilot-vscode','gemini','cursor')][string]$Profile,
    [string]$Project = (Get-Location).Path,
    [switch]$Remove,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$source = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $env:USERPROFILE '.opencode-deck\venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $runtime)) { $runtime = 'python' }
$oldPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = $source + [IO.Path]::PathSeparator + $oldPythonPath
    $arguments = @('-m','ocdeck','harness-install',$Profile,'--project',$Project)
    if ($Remove) { $arguments += '--remove' }
    if ($DryRun) { $arguments += '--dry-run' }
    & $runtime @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Harness configuration failed; inspect the message above.' }
} finally { $env:PYTHONPATH = $oldPythonPath }
