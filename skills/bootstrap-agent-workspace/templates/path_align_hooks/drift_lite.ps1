# drift-lite: L0 path-pairing diagnosis (Windows).
# Standalone:
#   powershell -NoProfile -File tools/path_align_hooks/drift_lite.ps1
#   powershell -NoProfile -File tools/path_align_hooks/drift_lite.ps1 -FailOnRisk
# Twin: bash tools/path_align_hooks/drift_lite.sh
#
# stdout: JSON report. Exit 0 unless -FailOnRisk and risk present (then 1).

[CmdletBinding()]
param(
    [string]$RepoRoot = '',
    [switch]$FailOnRisk
)

$ErrorActionPreference = 'Continue'
$ScriptDir = $PSScriptRoot

function Resolve-RepoRoot([string]$hint) {
    if ($hint) { return (Resolve-Path $hint).Path }
    Push-Location $ScriptDir
    try {
        $git = git rev-parse --show-toplevel 2>$null
        if ($git) { return $git.Trim() }
    } finally { Pop-Location }
    # Default install: <repo>/tools/path_align_hooks
    return (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
}

$RepoRoot = Resolve-RepoRoot $RepoRoot
$LastDrift = Join-Path $ScriptDir 'last-drift.json'

function Test-ToolingNoise([string]$path) {
    $n = ($path -replace '\\', '/').ToLowerInvariant().TrimEnd('/')
    $prefixes = @(
        '.cursor/', '.claude/', '.trae/', '.codex/', '.pi/', '.qoder/',
        'tools/path_align_hooks/'
    )
    foreach ($p in $prefixes) {
        if ($n -eq $p.TrimEnd('/') -or $n.StartsWith($p)) { return $true }
    }
    return $false
}

function Get-ChangedFiles([string]$root) {
    $files = New-Object System.Collections.Generic.List[string]
    Push-Location $root
    try {
        $porcelain = git status --porcelain -uall 2>$null
        if ($porcelain) {
            foreach ($line in ($porcelain -split "`n")) {
                if ($line.Length -lt 4) { continue }
                $path = $line.Substring(3).Trim()
                if ($path -match ' -> ') { $path = ($path -split ' -> ', 2)[1] }
                $norm = ($path -replace '\\', '/')
                if (Test-ToolingNoise $norm) { continue }
                if (-not $files.Contains($norm)) { $files.Add($norm) | Out-Null }
            }
        }
        $diff = git diff --name-only HEAD 2>$null
        if ($diff) {
            foreach ($path in ($diff -split "`n")) {
                $p = $path.Trim() -replace '\\', '/'
                if (-not $p -or (Test-ToolingNoise $p)) { continue }
                if (-not $files.Contains($p)) { $files.Add($p) | Out-Null }
            }
        }
    } finally {
        Pop-Location
    }
    return [string[]]@($files)
}

function Test-Relevant([string]$path) {
    $lower = $path.ToLowerInvariant()
    foreach ($h in @('specs/', 'src/', 'skills/', 'openapi', '.schema.json')) {
        if ($lower.Contains($h) -or $lower.StartsWith($h)) { return $true }
    }
    return $false
}

function Test-SpecSide([string]$path) {
    $l = $path.ToLowerInvariant() -replace '\\', '/'
    if ($l.StartsWith('specs/')) { return $true }
    if ($l.Contains('openapi')) { return $true }
    if ($l.Contains('.schema.json')) { return $true }
    return $false
}

function Test-CodeSide([string]$path) {
    $l = $path.ToLowerInvariant() -replace '\\', '/'
    # Never treat specs/** as code via extension (pilot / embedded examples).
    if ($l.StartsWith('specs/')) { return $false }
    if ($l.StartsWith('skills/') -or $l.StartsWith('src/')) { return $true }
    foreach ($ext in @('.py', '.ts', '.tsx', '.js')) {
        if ($l.EndsWith($ext)) { return $true }
    }
    return $false
}

function Get-Cluster([string]$path) {
    $p = $path -replace '\\', '/'
    if ($p -match '^(skills/[^/]+)') { return $Matches[1] }
    if ($p -match '^(specs/[^/]+/[^/]+)') { return $Matches[1] }
    if ($p -match '^(specs/[^/]+)') { return $Matches[1] }
    if ($p -match '^(src/[^/]+)') { return $Matches[1] }
    return ($p -split '/')[0]
}

function New-DriftReport {
    $changed = [string[]]@(Get-ChangedFiles $RepoRoot)
    $relevant = [string[]]@($changed | Where-Object { $_ -and (Test-Relevant $_) })
    $specFiles = [string[]]@($relevant | Where-Object { Test-SpecSide $_ })
    $codeFiles = [string[]]@($relevant | Where-Object { Test-CodeSide $_ })
    $clusters = [string[]]@($relevant | ForEach-Object { Get-Cluster $_ } | Select-Object -Unique)

    $riskCode = $null
    $risk = $null
    $actions = @()

    if ($relevant.Count -eq 0) {
        return [ordered]@{
            ok           = $true
            risk_code    = $null
            risk         = $null
            summary      = 'No relevant spec/code changes in dirty tree.'
            changed      = @($changed | Select-Object -First 100)
            relevant     = @()
            spec_files   = @()
            code_files   = @()
            clusters     = @()
            actions      = @()
            repo_root    = $RepoRoot
            generated_at = (Get-Date).ToUniversalTime().ToString('o')
            engine       = 'drift_lite.ps1'
        }
    }

    $sample = ($relevant | Select-Object -First 12) -join ', '
    $clusterSample = ($clusters | Select-Object -First 8) -join ', '

    if ($codeFiles.Count -gt 0 -and $specFiles.Count -eq 0) {
        $riskCode = 'CODE_WITHOUT_SPEC'
        $risk = "drift-lite: CODE_WITHOUT_SPEC - code/skills changed without specs/openapi/schema. files=$sample"
        $actions = @(
            [ordered]@{
                id          = 'A1'
                side        = 'spec'
                op          = 'add_or_update'
                targets     = @($codeFiles | Select-Object -First 20)
                clusters    = @($clusters)
                instruction = "Add or update specs/ (and/or openapi/schema) for clusters: $clusterSample"
            },
            [ordered]@{
                id          = 'A2'
                side        = 'either'
                op          = 'justify'
                targets     = @()
                clusters    = @($clusters)
                instruction = 'Or briefly explain why this turn is intentionally code-only (no Spec update).'
            }
        )
    } elseif ($specFiles.Count -gt 0 -and $codeFiles.Count -eq 0) {
        $riskCode = 'SPEC_WITHOUT_CODE'
        $risk = "drift-lite: SPEC_WITHOUT_CODE - specs/openapi/schema changed without code/skills. files=$sample"
        $actions = @(
            [ordered]@{
                id          = 'A1'
                side        = 'code'
                op          = 'add_or_update'
                targets     = @($specFiles | Select-Object -First 20)
                clusters    = @($clusters)
                instruction = "Implement or update code/skills for clusters: $clusterSample"
            },
            [ordered]@{
                id          = 'A2'
                side        = 'either'
                op          = 'justify'
                targets     = @()
                clusters    = @($clusters)
                instruction = 'Or briefly explain why this turn is intentionally Spec-only (no code update).'
            }
        )
    }

    $ok = ($null -eq $riskCode)
    $summary = if ($ok) {
        "Paired changes OK (spec_side=$($specFiles.Count), code_side=$($codeFiles.Count)). clusters=$clusterSample"
    } else {
        $risk
    }

    return [ordered]@{
        ok           = $ok
        risk_code    = $riskCode
        risk         = $risk
        summary      = $summary
        changed      = @($changed | Select-Object -First 100)
        relevant     = @($relevant | Select-Object -First 50)
        spec_files   = @($specFiles | Select-Object -First 50)
        code_files   = @($codeFiles | Select-Object -First 50)
        clusters     = @($clusters)
        actions      = $actions
        repo_root    = $RepoRoot
        generated_at = (Get-Date).ToUniversalTime().ToString('o')
        engine       = 'drift_lite.ps1'
    }
}

$report = New-DriftReport
($report | ConvertTo-Json -Depth 8) | Set-Content -Path $LastDrift -Encoding utf8
[Console]::Out.Write(($report | ConvertTo-Json -Depth 8 -Compress))
[Console]::Error.WriteLine("[drift_lite] ok=$($report.ok) risk_code=$($report.risk_code) relevant=$($report.relevant.Count)")

if ($FailOnRisk -and -not $report.ok) { exit 1 }
exit 0
