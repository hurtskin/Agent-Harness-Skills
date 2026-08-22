# Light PBT verification runner (local sandbox — not shipped in Skills yet).
# Interpreter: Agent/hook passes -Python or sets $env:PYTHON; no venv/PATH search in script.
# Usage:
#   powershell -File specs/verification/run_verify.ps1 -Python python
#   $env:PYTHON='uv run python'; powershell -File specs/verification/run_verify.ps1
#   powershell -File specs/verification/run_verify.ps1 -PreCommit
#   powershell -File specs/verification/run_verify.ps1 -DryRun

[CmdletBinding()]
param(
    [switch]$PreCommit,
    [switch]$DryRun,
    [string[]]$Paths = @(),
    [string]$Python = '',
    [string]$RepoRoot = ''
)

$ErrorActionPreference = 'Stop'
$Here = $PSScriptRoot
if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $Here '..\..')).Path
} else {
    $RepoRoot = (Resolve-Path $RepoRoot).Path
}

$python = if ($Python) { $Python } elseif ($env:PYTHON) { $env:PYTHON } else { 'python' }

function Normalize-PathSlash([string]$p) {
    return ($p -replace '\\', '/').TrimStart('./')
}

function Test-WatchHit([string]$file, [string[]]$patterns) {
    $norm = Normalize-PathSlash $file
    foreach ($pat in $patterns) {
        $p = Normalize-PathSlash $pat
        if ($p.EndsWith('/**')) {
            $prefix = $p.Substring(0, $p.Length - 3)
            if ($norm -eq $prefix -or $norm.StartsWith("$prefix/")) { return $true }
        } elseif ($norm -like ($p -replace '/', '\')) {
            return $true
        } elseif ($norm -eq $p) {
            return $true
        }
    }
    return $false
}

function Get-StagedFiles([string]$root) {
    Push-Location $root
    try {
        $out = git diff --cached --name-only --diff-filter=ACMR 2>$null
        if (-not $out) { return @() }
        return @($out | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    } finally {
        Pop-Location
    }
}

function Read-MatrixModules([string]$matrixPath) {
    if (-not (Test-Path $matrixPath)) {
        throw "matrix not found: $matrixPath"
    }
    $text = Get-Content $matrixPath -Raw
    $modules = @()
    $current = $null
    $inWatch = $false
    $inTest = $false
    foreach ($line in ($text -split "`n")) {
        $t = $line.TrimEnd()
        if ($t -match '^\s*-\s+id:\s*(.+)$') {
            if ($current) { $modules += $current }
            $current = [ordered]@{
                id = $Matches[1].Trim()
                kind = ''
                pbt = $false
                watch = @()
                test = @{}
            }
            $inWatch = $false
            $inTest = $false
            continue
        }
        if (-not $current) { continue }
        if ($t -match '^\s+kind:\s*(\S+)') {
            $current.kind = $Matches[1].Trim()
        } elseif ($t -match '^\s+pbt:\s*(true|false)') {
            $current.pbt = ($Matches[1] -eq 'true')
        } elseif ($t -match '^\s+watch:\s*$') {
            $inWatch = $true
            $inTest = $false
        } elseif ($t -match '^\s+test:\s*$') {
            $inWatch = $false
            $inTest = $true
        } elseif ($inWatch -and $t -match '^\s+-\s+(.+)$') {
            $current.watch += $Matches[1].Trim()
        } elseif ($inTest -and $t -match '^\s+(\w+):\s*(.+)$') {
            $current.test[$Matches[1]] = $Matches[2].Trim().Trim('"')
        }
    }
    if ($current) { $modules += $current }

    foreach ($mod in $modules) {
        if (-not $mod.kind) {
            $mod.kind = if ($mod.pbt) { 'pbt' } else { 'manual' }
        }
    }

    return @($modules | Where-Object {
            $_.kind -ne 'manual' -and $_.test.ContainsKey('command') -and $_.test.ContainsKey('cwd')
        })
}

$matrixPath = Join-Path $Here 'matrix.yaml'
$modules = Read-MatrixModules $matrixPath
if ($Paths.Count -gt 0) {
    $staged = $Paths
} elseif ($PreCommit) {
    $staged = Get-StagedFiles $RepoRoot
} else {
    $staged = @()
}

$ran = 0
$skipped = 0

foreach ($mod in $modules) {
    if ($PreCommit -or $Paths.Count -gt 0) {
        $hit = $false
        foreach ($f in $staged) {
            if (Test-WatchHit $f $mod.watch) { $hit = $true; break }
        }
        if (-not $hit) {
            Write-Host "[verify] SKIP module $($mod.id) (no staged watch hit)"
            $skipped++
            continue
        }
    }

    $cmdTemplate = $mod.test.command.Replace('{python}', $python).Replace('{repo_root}', $RepoRoot)
    $cwd = $mod.test.cwd.Replace('{repo_root}', $RepoRoot)
    Write-Host "[verify] RUN module $($mod.id) (kind=$($mod.kind))"
    Write-Host "  cwd: $cwd"
    Write-Host "  cmd: $cmdTemplate"

    if ($DryRun) {
        $ran++
        continue
    }

    Push-Location $cwd
    try {
        Invoke-Expression $cmdTemplate
        if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    } catch {
        Write-Error $_
        exit 1
    } finally {
        Pop-Location
    }
    $ran++
}

Write-Host "[verify] done ran=$ran skipped=$skipped python=$python"
if ($ran -eq 0 -and $PreCommit) {
    Write-Host '[verify] pre-commit: nothing to run (ok)'
}
exit 0
