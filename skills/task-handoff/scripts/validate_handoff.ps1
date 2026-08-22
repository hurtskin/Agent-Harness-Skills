# validate_handoff.ps1 - task-handoff v2 deterministic validator (PowerShell)
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File validate_handoff.ps1 <file>
# Exit 0 = VALID (prints VALID + DIGEST); 1 = invalid; 2 = file not found.
# ASCII-only to avoid Windows PowerShell 5.1 GBK misdecode of UTF-8 scripts.
# Front matter is a restricted YAML subset (flat key:value + one sequence + single-line scalars);
# safety is enforced by rejecting any YAML feature outside that subset.
param([Parameter(Mandatory=$true)][string]$Path)
$ErrorActionPreference = "Stop"

$ALLOWED_TOP = @("schema_version","session_id","repository","branch","base_commit","working_tree","handoff_status","interrogation_round","last_audit_status","status_reason","status_evidence","created_at","updated_at")
$ALLOWED_EV  = @("kind","ref","claim","verification")
$WORKING_TREE = @("CLEAN","DIRTY","UNAVAILABLE")
$HANDOFF_STATUS = @("COLLECTING","NEEDS_ANSWERS","REVIEW_PENDING","READY","READY_WITH_RISKS","BLOCKED")
$KIND_ENUM = @("source","document","test","diff","commit","command","unverified")
$VERIF_ENUM = @("VERIFIED","UNVERIFIED")
$LAST_AUDIT = @("READY","READY_WITH_RISKS","NEEDS_ANSWERS","BLOCKED")
$TLDR_SECTIONS = @("Objective","Current State","Next Action","Blockers and Risks","Critical Constraints","Evidence Anchors")
$RFC3339 = '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$'
$HEX = '^[0-9a-fA-F]{7,64}$'

$errs = New-Object System.Collections.Generic.List[string]
function Fail([string]$m){ $script:errs.Add($m) }

function ParseVal([string]$v){
  if ($v -eq "null") { return $null }
  if ($v.Length -ge 2 -and $v.Chars(0) -eq '"' -and $v.Chars($v.Length-1) -eq '"') {
    $s = $v.Substring(1,$v.Length-2)
    $s = $s -replace '\\\\','\'
    $s = $s -replace '\\"','"'
    return $s
  }
  if ($v -cmatch '^-?\d+$') { return [int]$v }
  return $v
}

if (-not (Test-Path -LiteralPath $Path)) { [Console]::Error.WriteLine("file not found: $Path"); exit 2 }
$bytes = [System.IO.File]::ReadAllBytes($Path)
# UTF-8 check: decode then re-encode, byte length must match
$text = [System.Text.Encoding]::UTF8.GetString($bytes)
if ([System.Text.Encoding]::UTF8.GetByteCount($text) -ne $bytes.Length) { Fail("UTF-8 decode failed") }
# Normalize line endings for parsing (digest still computed on raw bytes via Get-FileHash)
$text = $text -replace "`r`n","`n" -replace "`r","`n"

# Split on the two "---`n" markers
$marker = "---`n"
$i1 = $text.IndexOf($marker)
if ($i1 -ne 0) { Fail("missing Front Matter start ---") }
$i2 = $text.IndexOf($marker, $i1 + $marker.Length)
if ($i2 -lt 0) { Fail("Front Matter not closed") }
$yamlText = $text.Substring($i1 + $marker.Length, $i2 - ($i1 + $marker.Length))
$body    = $text.Substring($i2 + $marker.Length)

# multi-document / document end marker
$sepCount = 0; foreach($ln in ($text -split "`n")){ if($ln -ceq "---"){$sepCount++} }
if ($sepCount -ne 2) { Fail("Front Matter --- separators must be exactly 2 (got $sepCount)") }
$dotCount = 0; foreach($ln in ($text -split "`n")){ if($ln -ceq "..."){$dotCount++} }
if ($dotCount -ne 0) { Fail("YAML document end marker ... rejected") }

$yamlLines = $yamlText -split "`n"
# safety: reject anchors/aliases/tags/merge/block-scalars/flow
foreach ($l in $yamlLines){
  if ($l -cmatch '(^|\s)&[A-Za-z]')   { Fail("YAML anchor rejected: $l") }
  if ($l -cmatch '(^|\s)\*[A-Za-z]')  { Fail("YAML alias rejected: $l") }
  if ($l -cmatch '^\s*!')              { Fail("YAML tag rejected: $l") }
  if ($l -cmatch '<<:')                { Fail("YAML merge key << rejected: $l") }
  if ($l -cmatch '^\s*[|>]')           { Fail("YAML block scalar rejected: $l") }
  if ($l -cmatch '{}')                 { Fail("YAML flow mapping rejected: $l") }
  if ($l -cmatch '\[\]')              { Fail("YAML flow sequence rejected: $l") }
}

# parse top-level + status_evidence (restricted subset)
$top = @{}
$evidence = @()
$curElem = $null
$mode = "top"
foreach ($l in $yamlLines){
  if ($l -cmatch '^\s*$') { continue }
  if ($l -cmatch '^\s*#') { continue }
  if ($l -cmatch '^(?<k>[a-z_]+): (?<v>.*)$'){
    $k=$matches.k; $v=$matches.v
    if ($top.ContainsKey($k)) { Fail("duplicate top-level key: $k") }
    if ($k -ceq "status_evidence"){ $mode="seq"; $top[$k]="__SEQ__"; continue }
    $top[$k] = ParseVal $v; $mode="top"; continue
  }
  if ($l -cmatch '^(?<k>[a-z_]+):\s*$'){
    $k=$matches.k
    if ($top.ContainsKey($k)) { Fail("duplicate top-level key: $k") }
    if ($k -ceq "status_evidence"){ $mode="seq"; $top[$k]="__SEQ__"; continue }
    $top[$k] = $null; $mode="top"; continue
  }
  if ($mode -ceq "seq"){
    if ($l -cmatch '^  - (?<k>[a-z_]+): (?<v>.*)$'){
      if ($curElem){ $evidence += ,$curElem }
      $curElem=@{}; $curElem[$matches.k]=ParseVal $matches.v; continue
    }
    if ($l -cmatch '^    (?<k>[a-z_]+): (?<v>.*)$'){
      if ($curElem -and $curElem.ContainsKey($matches.k)){ Fail("evidence dup key: $($matches.k)") }
      $curElem[$matches.k]=ParseVal $matches.v; continue
    }
  }
  Fail("unparseable line: $l")
}
if ($curElem){ $evidence += ,$curElem }

# top-level field set exact equality
$uniqTop = @{}
foreach($k in $top.Keys){ $uniqTop[$k]=$true }
$missing = $ALLOWED_TOP | Where-Object { -not $uniqTop.ContainsKey($_) }
$extra   = $uniqTop.Keys | Where-Object { $ALLOWED_TOP -cnotcontains $_ }
if ($missing) { Fail("top-level missing fields: $($missing -join ',')") }
if ($extra)   { Fail("top-level extra fields: $($extra -join ',')") }

# type / non-empty / enum checks
$sv = $top["schema_version"]
if (-not ($sv -is [int] -and $sv -eq 2)) { Fail("schema_version must be integer 2") }
$sid = $top["session_id"]
if (-not ($sid -is [string] -and $sid.Trim() -ne "")) { Fail("session_id must be non-empty string") }
$repo = $top["repository"]
if (-not ($repo -is [string] -and $repo.Trim() -ne "")) { Fail("repository must be non-empty string") }
$br = $top["branch"]
if (-not ($null -eq $br -or $br -is [string])) { Fail("branch must be string|null") }
$bc = $top["base_commit"]
if (-not ($null -eq $bc -or ($bc -is [string] -and $bc -cmatch $HEX))) { Fail("base_commit must be null or 7-64 hex") }
if ($WORKING_TREE -cnotcontains $top["working_tree"]) { Fail("working_tree enum invalid") }
if ($HANDOFF_STATUS -cnotcontains $top["handoff_status"]) { Fail("handoff_status enum invalid") }
$ir = $top["interrogation_round"]
if (-not ($ir -is [int] -and $ir -ge 0 -and $ir -le 3)) { Fail("interrogation_round must be int 0..3") }
$la = $top["last_audit_status"]
if (-not ($null -eq $la -or $LAST_AUDIT -ccontains $la)) { Fail("last_audit_status enum invalid") }
$sr = $top["status_reason"]
if (-not ($sr -is [string] -and $sr.Trim() -ne "")) { Fail("status_reason must be non-empty") }
if (-not ($evidence.Count -gt 0)) { Fail("status_evidence must be non-empty array") }
$ca = $top["created_at"]; $ua = $top["updated_at"]
if (-not ($ca -is [string] -and $ca -cmatch $RFC3339)) { Fail("created_at not RFC3339") }
if (-not ($ua -is [string] -and $ua -cmatch $RFC3339)) { Fail("updated_at not RFC3339") }
if ($ua -lt $ca) { Fail("updated_at earlier than created_at") }

# status_evidence elements
for ($i=0; $i -lt $evidence.Count; $i++){
  $ev = $evidence[$i]
  $ek = @($ev.Keys)
  $em = $ALLOWED_EV | Where-Object { $ek -cnotcontains $_ }
  $ex = $ek | Where-Object { $ALLOWED_EV -cnotcontains $_ }
  if ($em) { Fail("evidence[$i] missing fields: $($em -join ',')") }
  if ($ex) { Fail("evidence[$i] extra fields: $($ex -join ',')") }
  if ($KIND_ENUM -cnotcontains $ev["kind"]) { Fail("evidence[$i].kind enum invalid") }
  if (-not ($null -eq $ev["ref"] -or $ev["ref"] -is [string])) { Fail("evidence[$i].ref type invalid") }
  if (-not ($ev["claim"] -is [string] -and $ev["claim"].Trim() -ne "")) { Fail("evidence[$i].claim must be non-empty") }
  if ($VERIF_ENUM -cnotcontains $ev["verification"]) { Fail("evidence[$i].verification enum invalid") }
}
if ($evidence.Count -eq 1){
  $ev=$evidence[0]
  if (-not ($ev["kind"] -ceq "unverified" -and $null -eq $ev["ref"] -and $ev["verification"] -ceq "UNVERIFIED")){
    Fail("sole evidence element must be unverified/null/UNVERIFIED")
  }
}

# TL;DR structure (tldr = body up to next "\n# " or end; start at 1 to skip the TL;DR heading itself)
if (-not $body.TrimStart().StartsWith("# TL;DR")) { Fail("first heading after YAML must be # TL;DR") }
$tEnd = $body.IndexOf("`n# ", 1)
$tldr = if ($tEnd -ge 0) { $body.Substring(0, $tEnd) } else { $body }
if ($tldr.Length -gt 1500) { Fail("TL;DR exceeds 1500 Unicode chars ($($tldr.Length))") }
$st = $top["handoff_status"]
if ($tldr -cmatch 'Status:\s*(\S+)'){
  if ($matches[1] -cne $st){ Fail("TL;DR Status ($($matches[1])) != handoff_status ($st)") }
} else { Fail("TL;DR missing Status: line") }
$pos=0
foreach($sec in $TLDR_SECTIONS){
  $idx = $tldr.IndexOf("## $sec")
  if ($idx -lt 0){ Fail("TL;DR missing ## $sec"); break }
  if ($idx -lt $pos){ Fail("TL;DR ## $sec out of order"); break }
  $pos=$idx
}

if ($errs.Count -gt 0){
  [Console]::Error.WriteLine(($errs -join "`n"))
  exit 1
}
$digest = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLower()
[Console]::Out.WriteLine("VALID")
[Console]::Out.WriteLine("DIGEST $digest")
exit 0
