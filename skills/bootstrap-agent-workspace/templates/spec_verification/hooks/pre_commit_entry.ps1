# Thin pre-commit entry — git hook / pre-commit framework call this, not run_verify.ps1 directly.
# Interpreter: set $env:PYTHON before commit, or pass -Python to this script.
# Usage (from repo root):
#   powershell -NoProfile -File specs/verification/hooks/pre_commit_entry.ps1
#   powershell -NoProfile -File specs/verification/hooks/pre_commit_entry.ps1 -Python python

[CmdletBinding()]
param(
    [string]$Python = '',
    [string]$RepoRoot = ''
)

$ErrorActionPreference = 'Stop'
$HooksDir = $PSScriptRoot
$VerifyDir = Split-Path $HooksDir -Parent

if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $VerifyDir '..\..')).Path
}

$runnerArgs = @{
    PreCommit = $true
    RepoRoot  = $RepoRoot
}
if ($Python) { $runnerArgs.Python = $Python }

try {
    & (Join-Path $VerifyDir 'run_verify.ps1') @runnerArgs
    exit 0
} catch {
    Write-Error $_
    exit 1
}
