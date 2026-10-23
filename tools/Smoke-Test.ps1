# Interactive Windows smoke-test helper. No CI and no automatic game launch.
param(
    [Parameter(Mandatory=$true)][string]$Archive,
    [Parameter(Mandatory=$true)][string]$WarbandRoot,
    [ValidateRange(0,8)][int]$Defenders = 4,
    [switch]$Replace
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$archivePath = (Resolve-Path $Archive).Path
$gameRoot = (Resolve-Path $WarbandRoot).Path
$moduleRoot = Join-Path $gameRoot 'Modules\ZOMBIEEE_Remaster'

if (!(Test-Path (Join-Path $gameRoot 'Modules'))) {
    throw 'Warband Modules folder not found. Point -WarbandRoot at an installed Warband game.'
}
if (!(Get-Command 'py' -ErrorAction SilentlyContinue)) {
    throw 'Python launcher py not found (install Python 3.10+).'
}

Push-Location $root
try {
    Write-Host 'Running local regression tests (these do not launch Warband)...'
    & py -3 -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Python regression tests failed' }

    $argsBuild = @('-3', 'tools\build.py', '--archive', $archivePath, '--out', $moduleRoot,
                   '--experimental-defenders', [string]$Defenders)
    if ($Replace) { $argsBuild += '--replace' }
    & py @argsBuild
    if ($LASTEXITCODE -ne 0) { throw 'Module build was refused; check RAR SHA-256, 7-Zip CRC and errors above' }

    & py -3 tools\doctor.py --module $moduleRoot
    if ($LASTEXITCODE -ne 0) { throw 'Core module doctor failed' }

    & py -3 tools\preflight.py --module $moduleRoot --json
    if ($LASTEXITCODE -ne 0) { throw 'Compiled mission preflight failed' }

    Write-Host ''
    Write-Host 'Static build complete. Next: open WSE2 1.1.5.4 and select ZOMBIEEE_Remaster.'
    Write-Host 'Host a PRIVATE City invasion mission. Capture rgl_log.txt and one screenshot.'
    Write-Host 'This script cannot certify gameplay or bot synchronization.'
}
finally {
    Pop-Location
}
