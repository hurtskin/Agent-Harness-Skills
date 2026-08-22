# Example-kind pilot: no PBT library — plain script assertion.
$ErrorActionPreference = 'Stop'
$root = if ($args[0]) { $args[0] } else { (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path }
$readme = Join-Path $root 'README.md'
if (-not (Test-Path $readme)) {
    Write-Error "README.md missing"
    exit 1
}
$text = Get-Content $readme -Raw
if ($text.Length -lt 200) {
    Write-Error "README.md too short"
    exit 1
}
Write-Host '[example] README.md OK'
exit 0
