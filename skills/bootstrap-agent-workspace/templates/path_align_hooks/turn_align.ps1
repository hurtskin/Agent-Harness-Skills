# turn_align: turn-end event -> drift_lite -> optional nudge JSON (Windows).
# Twin: bash tools/path_align_hooks/turn_align.sh
#
# stdin: host turn-end JSON (status / loop_count best-effort).
# stdout: {} or { nudge, message, actions } — map message to the host follow-up field when registering.
# Disable nudge: PATH_ALIGN_NUDGE=0

$ErrorActionPreference = 'Continue'
$ScriptDir = $PSScriptRoot

function Resolve-RepoRoot {
    Push-Location $ScriptDir
    try {
        $git = git rev-parse --show-toplevel 2>$null
        if ($git) { return $git.Trim() }
    } finally { Pop-Location }
    return (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
}

$Root = Resolve-RepoRoot
$LastStop = Join-Path $ScriptDir 'last-turn-align.json'
$LastStdin = Join-Path $ScriptDir 'last-turn-align.stdin.bin'
$DriftLite = Join-Path $ScriptDir 'drift_lite.ps1'

function Get-StdinText {
    $stdin = [Console]::OpenStandardInput()
    $ms = New-Object System.IO.MemoryStream
    $stdin.CopyTo($ms)
    $bytes = $ms.ToArray()
    [System.IO.File]::WriteAllBytes($LastStdin, $bytes)

    $meta = [ordered]@{
        stdin_len      = $bytes.Length
        stdin_head_hex = if ($bytes.Length -gt 0) {
            ($bytes[0..([Math]::Min(63, $bytes.Length - 1))] | ForEach-Object { $_.ToString('x2') }) -join ''
        } else { '' }
        parse_ok       = $false
        parse_error    = $null
        raw_preview    = $null
        recovered_by   = $null
    }

    if ($bytes.Length -eq 0) {
        return @{ payload = @{}; meta = $meta }
    }

    $encodings = @(
        [System.Text.UTF8Encoding]::new($false, $true),
        [System.Text.Encoding]::UTF8,
        [System.Text.Encoding]::Unicode,
        [System.Text.Encoding]::BigEndianUnicode
    )

    $payload = $null
    foreach ($enc in $encodings) {
        try { $text = $enc.GetString($bytes) } catch { continue }
        $meta.raw_preview = $text.Substring(0, [Math]::Min(1000, $text.Length))
        $stripped = $text.Trim()
        if (-not $stripped) { continue }
        try {
            $payload = $stripped | ConvertFrom-Json -ErrorAction Stop
            $meta.parse_ok = $true
            $meta.parse_error = $null
            break
        } catch {
            $meta.parse_error = $_.Exception.Message
            if ($stripped -match '\{[\s\S]*\}') {
                try {
                    $payload = $Matches[0] | ConvertFrom-Json -ErrorAction Stop
                    $meta.parse_ok = $true
                    $meta.parse_error = $null
                    $meta.recovered_by = 'brace_extract'
                    break
                } catch {
                    $meta.parse_error = $_.Exception.Message
                }
            }
        }
    }

    if (-not $payload) { $payload = @{} }
    return @{ payload = $payload; meta = $meta }
}

function Invoke-DriftLite {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'powershell'
    $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$DriftLite`" -RepoRoot `"$Root`""
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.WorkingDirectory = $Root
    $p = [Diagnostics.Process]::Start($psi)
    $stdout = $p.StandardOutput.ReadToEnd()
    $stderr = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    if ($stderr) { [Console]::Error.WriteLine($stderr.TrimEnd()) }
    try {
        return ($stdout | ConvertFrom-Json)
    } catch {
        return [pscustomobject]@{
            ok        = $true
            risk_code = $null
            risk      = $null
            summary   = "drift_lite parse failed: $($_.Exception.Message)"
            actions   = @()
            relevant  = @()
        }
    }
}

function Test-NudgeEnabled {
    $v = $env:PATH_ALIGN_NUDGE
    if ($null -eq $v -or $v.Trim() -eq '') { return $true }
    return $v.Trim().ToLowerInvariant() -notin @('0', 'false', 'no', 'off')
}

$parsed = Get-StdinText
$payload = $parsed.payload
$parseMeta = $parsed.meta

$status = $null
if ($payload.status) { $status = [string]$payload.status }
elseif ($payload.final_status) { $status = [string]$payload.final_status }
elseif ($payload.stop -and $payload.stop.status) { $status = [string]$payload.stop.status }
elseif ($payload.event) { $status = [string]$payload.event }
if (-not $status) { $status = 'unknown' }

$loopCount = 0
try { $loopCount = [int]$payload.loop_count } catch { $loopCount = 0 }

$drift = $null
$runDrift = $status -in @('completed', 'success', 'ok', 'end', 'finished')
if ($runDrift) {
    $drift = Invoke-DriftLite
} else {
    $drift = [pscustomobject]@{
        ok        = $true
        risk_code = $null
        risk      = $null
        summary   = "Skipped drift-lite because status=$status"
        actions   = @()
        relevant  = @()
        changed   = @()
    }
}

$record = [ordered]@{
    fired_at      = (Get-Date).ToUniversalTime().ToString('o')
    status        = $status
    loop_count    = $loopCount
    cwd           = $Root
    changed_count = @($drift.changed).Count
    relevant      = @($drift.relevant)
    risk          = $drift.risk
    risk_code     = $drift.risk_code
    summary       = $drift.summary
    actions       = @($drift.actions)
    clusters      = @($drift.clusters)
    drift         = $drift
    input_keys    = @($payload.PSObject.Properties.Name | Sort-Object)
    parse         = $parseMeta
    payload       = $payload
    runner        = 'powershell'
}
($record | ConvertTo-Json -Depth 10) | Set-Content -Path $LastStop -Encoding utf8

[Console]::Error.WriteLine(
    "[turn_align] status=$status parse_ok=$($parseMeta.parse_ok) " +
    "risk_code=$($drift.risk_code) actions=$(@($drift.actions).Count)"
)

$out = @{}
$hasRisk = $false
if ($drift.risk_code) { $hasRisk = $true }

if (
    (Test-NudgeEnabled) -and
    $runDrift -and
    $hasRisk -and
    $loopCount -lt 2
) {
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add([string]$drift.summary) | Out-Null
    $lines.Add('Actionable work orders:') | Out-Null
    $i = 1
    foreach ($a in @($drift.actions)) {
        $lines.Add("  $i. [$($a.id)] $($a.instruction)") | Out-Null
        $i++
    }
    $lines.Add('Do A1 (preferred) or A2 (justify one-sided). Then stop.') | Out-Null
    $out.nudge = $true
    $out.message = ($lines -join "`n")
    $out.actions = @($drift.actions)
}

[Console]::Out.Write(($out | ConvertTo-Json -Compress -Depth 5))
exit 0
