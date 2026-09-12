param([Parameter(Mandatory=$true)][string]$Data)
$ErrorActionPreference = 'Stop'
$task = Get-ScheduledTask -TaskName 'OpenCode Deck' -TaskPath '\' -ErrorAction SilentlyContinue
if ($task) {
    if ($task.Description -notlike 'OpenCode Deck*') { throw 'Unrelated scheduled task; refusing removal.' }
    Stop-ScheduledTask -TaskName 'OpenCode Deck' -TaskPath '\'
    Unregister-ScheduledTask -TaskName 'OpenCode Deck' -TaskPath '\' -Confirm:$false
}
$env:OCDECK_HOME = $Data

$metadata = Join-Path $Data 'install.json'
if (Test-Path -LiteralPath $metadata) {
    $install = Get-Content -LiteralPath $metadata -Raw | ConvertFrom-Json
    if ($install.configDir) {
        $entry = Join-Path $install.configDir 'plugins\ocdeck.js'
        if ((Test-Path -LiteralPath $entry) -and (Get-Content -LiteralPath $entry -Raw).StartsWith('// Managed by OpenCode Deck installer')) {
            Move-Item -LiteralPath $entry -Destination ($entry + '.agentdeck-backup-' + [DateTime]::UtcNow.Ticks)
        }
        $tui = Join-Path $install.configDir 'tui.json'
        if ((Test-Path -LiteralPath $tui) -and $install.source) {
            $config = Get-Content -LiteralPath $tui -Raw | ConvertFrom-Json
            $uri = ([System.Uri](Join-Path $install.source 'plugins\tui.mjs')).AbsoluteUri
            if ($config.plugin -contains $uri) {
                Copy-Item -LiteralPath $tui -Destination ($tui + '.agentdeck-backup-' + [DateTime]::UtcNow.Ticks)
                $config.plugin = @($config.plugin | Where-Object { $_ -ne $uri })
                $config | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $tui -Encoding UTF8
            }
        }
    }
}
$bin = Join-Path $Data 'bin'
$entries = @([Environment]::GetEnvironmentVariable('Path','User') -split ';' | Where-Object { $_ -and $_ -ne $bin })
[Environment]::SetEnvironmentVariable('Path', ($entries -join ';'), 'User')

Remove-Item -LiteralPath 'HKCU:\Software\Classes\AppUserModelId\AgentDeck' -ErrorAction SilentlyContinue
