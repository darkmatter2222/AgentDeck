param([switch]$DryRun, [string[]]$Scan = @())
$ErrorActionPreference = 'Stop'
$data = if ($env:OCDECK_HOME) { $env:OCDECK_HOME } else { Join-Path $env:USERPROFILE '.opencode-deck' }
$metadata = Join-Path $data 'install.json'
if (-not (Test-Path -LiteralPath $metadata)) { throw 'No installation metadata. Run ocdeck uninstall --all from the installed Python environment.' }
$install = Get-Content -LiteralPath $metadata -Raw | ConvertFrom-Json
$argsList = @('-m','ocdeck','uninstall','--all')
if ($DryRun) { $argsList += '--dry-run' }
foreach ($directory in $Scan) { $argsList += @('--scan', $directory) }
& $install.python @argsList
exit $LASTEXITCODE
