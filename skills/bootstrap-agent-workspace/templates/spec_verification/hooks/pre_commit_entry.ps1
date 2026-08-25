# Thin pre-commit entry — git hook / pre-commit framework call this, not run_verify.ps1 directly.
# Interpreter: set $env:PYTHON before commit, or pass -Python to this script.
# Usage (from repo root or any subdir; RepoRoot auto-detected):
#   powershell -NoProfile -File <this-script>.ps1
#   powershell -NoProfile -File <this-script>.ps1 -Python python
#   powershell -NoProfile -File <this-script>.ps1 -RepoRoot D:\path\to\repo

[CmdletBinding()]
param(
    [string]$Python = '',
    [string]$RepoRoot = ''
)

$ErrorActionPreference = 'Stop'
$HooksDir = $PSScriptRoot
$VerifyDir = Split-Path $HooksDir -Parent

# Resolve RepoRoot with three-tier fallback (decision v20):
  # 1) explicit -RepoRoot (caller override)
  # 2) git rev-parse --show-toplevel (preferred; works from any subdir of a git repo)
  # 3) $PSScriptRoot 上溯直至找到 AGENTS.md 或仓库根标记（启发式，最多上溯 8 层）
function Resolve-RepoRoot {
    param([string]$Hint)
    if ($Hint) { return (Resolve-Path $Hint).Path }
    Push-Location $HooksDir
    try {
        $git = git rev-parse --show-toplevel 2>$null
        if ($git) { return $git.Trim() }
    } finally { Pop-Location }
    $cur = $HooksDir
    for ($i = 0; $i -lt 8; $i++) {
        if (Test-Path (Join-Path $cur 'AGENTS.md')) { return (Resolve-Path $cur).Path }
        $parent = Split-Path $cur -Parent
        if (-not $parent -or $parent -eq $cur) { break }
        $cur = $parent
    }
    return (Resolve-Path (Join-Path $HooksDir '..\..\..')).Path
}

$RepoRoot = Resolve-RepoRoot -Hint $RepoRoot

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
