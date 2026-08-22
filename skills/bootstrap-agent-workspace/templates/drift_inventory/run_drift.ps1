# Inventory drift runner (local sandbox). Interpreter from Agent: -Python or $env:PYTHON.
[CmdletBinding()]
param(
    [string]$Python = '',
    [string]$RepoRoot = '',
    [string]$Inventory = 'specs/drift/pilot/inventory.yaml',
    [string]$Format = 'text'
)

$ErrorActionPreference = 'Stop'
$Here = $PSScriptRoot
if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $Here '..\..')).Path
} else {
    $RepoRoot = (Resolve-Path $RepoRoot).Path
}

$python = if ($Python) { $Python } elseif ($env:PYTHON) { $env:PYTHON } else { 'python' }
$script = Join-Path $Here 'drift_inventory.py'
$inv = Join-Path $RepoRoot $Inventory

& $python $script --repo-root $RepoRoot --inventory $inv --format $Format
exit $LASTEXITCODE
