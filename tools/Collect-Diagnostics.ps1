# Run once after the FINAL solo/private WSE2 test. No upload, no telemetry service.
param(
    [Parameter(Mandatory=$true)][string]$WarbandRoot,
    [string]$Session = 'final-check',
    [string[]]$AdditionalLogs = @(),
    [string]$FlightRoot = '',
    [string]$OutputFolder = './evidence'
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$game = (Resolve-Path $WarbandRoot).Path
$module = Join-Path $game 'Modules\ZOMBIEEE_Remaster'
if (!(Test-Path $module)) { throw 'Remaster module not found in Warband Modules.' }
if (!(Get-Command py -ErrorAction SilentlyContinue)) { throw 'Python 3 launcher missing.' }
New-Item -ItemType Directory -Path $OutputFolder -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$out = Join-Path (Resolve-Path $OutputFolder).Path "ZOMBIEEE-evidence-$stamp.zip"
$report = Join-Path (Resolve-Path $OutputFolder).Path "ZOMBIEEE-report-$stamp.md"
Push-Location $root
try {
    $arguments = @('-3', 'tools\diagnostics.py', 'collect', '--game-root', $game,
        '--module', $module, '--output', $out, '--session', $Session)
    foreach ($log in $AdditionalLogs) { $arguments += @('--log', $log) }
    if ($FlightRoot -ne '') { $arguments += @('--flight-root', (Resolve-Path $FlightRoot).Path) }
    & py @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Evidence collection failed' }
    & py -3 tools\diagnostics.py verify $out
    if ($LASTEXITCODE -ne 0) { throw 'Evidence ZIP failed SHA-256 verification' }
    & py -3 tools\diagnostics.py analyze $out --report $report
    if ($LASTEXITCODE -ne 0) { throw 'Evidence analysis failed' }
    Write-Host "Saved LOCAL evidence: $out"
    Write-Host "Saved LOCAL report: $report"
    Write-Host 'No data was uploaded. Review redaction before sharing the ZIP.'
} finally { Pop-Location }
