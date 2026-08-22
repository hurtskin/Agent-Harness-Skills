#!/usr/bin/env bash
# validate_handoff.sh - task-handoff v2 deterministic validator (bash/gawk)
# Twin: validate_handoff.py (Python) and validate_handoff.ps1 (PowerShell).
#
# Usage: bash validate_handoff.sh <file>
# Exit 0 = VALID (prints VALID + DIGEST <sha256>); 1 = invalid; 2 = usage / not found.
#
# Front matter is a restricted YAML subset (flat key:value + one sequence +
# single-line scalars). Safety is enforced by rejecting any YAML feature outside
# that subset. Parity baseline: Python and PowerShell twins.
#
# Requires: gawk, grep, sha256sum, iconv, locale (coreutils). A UTF-8 locale is
# needed so the 1500-char TL;DR limit counts Unicode characters, not bytes.
set -euo pipefail

# --- pick a UTF-8 locale so gawk length() counts characters, not bytes ---
VH_LOCALE=""
if command -v locale >/dev/null 2>&1; then
  for _loc in C.utf8 C.UTF-8 en_US.UTF-8 en_US.utf8; do
    if locale -a 2>/dev/null | grep -iqxF "$_loc"; then VH_LOCALE="$_loc"; break; fi
  done
fi
: "${VH_LOCALE:=C}"

FILE="${1:-}"
if [[ -z "$FILE" ]]; then
  echo "usage: validate_handoff.sh <file>" >&2
  exit 2
fi
if [[ ! -f "$FILE" ]]; then
  echo "file not found: $FILE" >&2
  exit 2
fi

# --- 1. UTF-8 byte round-trip (mirror py raw.decode('utf-8') / ps1 GetByteCount) ---
if ! iconv -f UTF-8 -t UTF-8 "$FILE" >/dev/null 2>&1; then
  echo "UTF-8 decode failed" >&2
  exit 1
fi
_raw_bytes=$(wc -c < "$FILE" | tr -d ' ')
_reenc_bytes=$(iconv -f UTF-8 -t UTF-8 "$FILE" | wc -c | tr -d ' ')
if [[ "$_raw_bytes" != "$_reenc_bytes" ]]; then
  echo "UTF-8 decode failed" >&2
  exit 1
fi

# --- 2..16. structural + schema + TL;DR validation in gawk; errors to stderr ---
if ! LC_ALL="$VH_LOCALE" awk -f - "$FILE" <<'AWK'
BEGIN {
  set_split("schema_version session_id repository branch base_commit working_tree handoff_status interrogation_round last_audit_status status_reason status_evidence created_at updated_at", ALLOWED_TOP)
  set_split("kind ref claim verification", ALLOWED_EV)
  set_split("CLEAN DIRTY UNAVAILABLE", WORKING_TREE)
  set_split("COLLECTING NEEDS_ANSWERS REVIEW_PENDING READY READY_WITH_RISKS BLOCKED", HANDOFF_STATUS)
  set_split("source document test diff commit command unverified", KIND_ENUM)
  set_split("VERIFIED UNVERIFIED", VERIF_ENUM)
  set_split("READY READY_WITH_RISKS NEEDS_ANSWERS BLOCKED", LAST_AUDIT)
  TLDR_SECTIONS[1]="Objective"; TLDR_SECTIONS[2]="Current State"; TLDR_SECTIONS[3]="Next Action"
  TLDR_SECTIONS[4]="Blockers and Risks"; TLDR_SECTIONS[5]="Critical Constraints"; TLDR_SECTIONS[6]="Evidence Anchors"
  NSEC=6
  RFC3339="^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$"
  HEX="^[0-9a-fA-F]{7,64}$"
  INTRE="^-?[0-9]+$"
  n_err=0
  state="init"      # init | yaml | body
  sep_count=0; dot_count=0
  nyl=0; nbl=0
  mode="top"
  eidx=-1; necount=0
}
function set_split(s, arr,    tmp,i,n) { n=split(s, tmp, " "); for(i=1;i<=n;i++) arr[tmp[i]]=1 }
function fail(m) { ERRS[++n_err]=m }
function parseval(v,    s) {
  PV_TYP=""; PV_VAL=""
  if (v == "null") { PV_TYP="null"; PV_VAL=""; return }
  if (length(v)>=2 && substr(v,1,1)=="\"" && substr(v,length(v))=="\"") {
    s = substr(v,2,length(v)-2)
    gsub(/\\\\/, "\\", s)
    gsub(/\\"/, "\"", s)
    PV_TYP="str"; PV_VAL=s; return
  }
  if (v ~ INTRE) { PV_TYP="int"; PV_VAL=v; return }
  PV_TYP="str"; PV_VAL=v
}
function trim(s) { sub(/^[[:space:]]+/,"",s); sub(/[[:space:]]+$/,"",s); return s }
function joinarr(arr, n,    s,i) { s=""; for(i=1;i<=n;i++) s = s (i>1?",":"") arr[i]; return s }

# ---- line pass: split Front Matter / body, count separators ----
{
  line=$0
  if (line ~ /\r$/) sub(/\r$/,"",line)           # CRLF tolerance (digest still on raw bytes)
  if (line == "---") sep_count++
  if (line == "...") dot_count++

  if (state == "init") {
    if (FNR == 1) {
      if (line != "---") fail("missing Front Matter start ---")
      state="yaml"; next
    }
  }
  if (state == "yaml") {
    if (line == "---") { state="body"; next }
    ylines[++nyl]=line; next
  }
  if (state == "body") { blines[++nbl]=line; next }
}

END {
  if (state == "init")  fail("missing Front Matter start ---")
  if (state == "yaml")  fail("Front Matter not closed")
  if (sep_count != 2)  fail("Front Matter --- separators must be exactly 2 (got " sep_count ")")
  if (dot_count != 0)   fail("YAML document end marker ... rejected")

  yaml_safety()
  parse_yaml()
  check_top_set()
  check_types()
  check_evidence()
  check_tldr()

  if (n_err > 0) {
    for (i=1; i<=n_err; i++) print ERRS[i] > "/dev/stderr"
    exit 1
  }
  exit 0
}

# ---- YAML safety: reject features outside the restricted subset ----
function yaml_safety(    i,l) {
  for (i=1; i<=nyl; i++) {
    l = ylines[i]
    if (l ~ /(^|[[:space:]])&[A-Za-z]/)  fail("YAML anchor rejected: " l)
    if (l ~ /(^|[[:space:]])\*[A-Za-z]/)  fail("YAML alias rejected: " l)
    if (l ~ /^[[:space:]]*!/)            fail("YAML tag rejected: " l)
    if (l ~ /<<:/)                        fail("YAML merge key << rejected: " l)
    if (l ~ /^[[:space:]]*[|>]/)         fail("YAML block scalar rejected: " l)
    if (l ~ /{}/)                         fail("YAML flow mapping rejected: " l)
    if (l ~ /\[\]/)                       fail("YAML flow sequence rejected: " l)
  }
}

# ---- parse restricted YAML subset (top-level + status_evidence) ----
function parse_yaml(    i,l,p,k,v) {
  for (i=1; i<=nyl; i++) {
    l = ylines[i]
    if (l ~ /^[[:space:]]*$/) continue
    if (l ~ /^[[:space:]]*#/) continue
    if (l ~ /^[a-z_]+: /) {                       # key: value
      p=index(l, ": "); k=substr(l,1,p-1); v=substr(l,p+2)
      handle_top(k, v); continue
    }
    if (l ~ /^[a-z_]+:[[:space:]]*$/) {           # key: (null)
      p=index(l, ":"); k=substr(l,1,p-1)
      handle_top_null(k); continue
    }
    if (mode == "seq") {
      if (l ~ /^  - [a-z_]+: /) {                  # new evidence element
        sub(/^  - /, "", l); p=index(l, ": "); k=substr(l,1,p-1); v=substr(l,p+2)
        eidx=necount; necount++
        parseval(v); evval[eidx,k]=PV_VAL; evtyp[eidx,k]=PV_TYP; evseen[eidx,k]=1
        evkcount[eidx]=1; evkey[eidx,1]=k
        continue
      }
      if (l ~ /^    [a-z_]+: /) {                 # continuation of current element
        sub(/^    /, "", l); p=index(l, ": "); k=substr(l,1,p-1); v=substr(l,p+2)
        if ((eidx,k) in evseen) { fail("evidence dup key: " k); continue }
        parseval(v); evval[eidx,k]=PV_VAL; evtyp[eidx,k]=PV_TYP; evseen[eidx,k]=1
        evkcount[eidx]++; evkey[eidx, evkcount[eidx]]=k
        continue
      }
    }
    fail("unparseable line: " l)
  }
}
function handle_top(k, v) {
  if (k in topsen) { fail("duplicate top-level key: " k) }
  topsen[k]=1
  if (k == "status_evidence") { mode="seq"; topval[k]="__SEQ__"; toptyp[k]="seq"; return }
  parseval(v); topval[k]=PV_VAL; toptyp[k]=PV_TYP; mode="top"
}
function handle_top_null(k) {
  if (k in topsen) { fail("duplicate top-level key: " k) }
  topsen[k]=1
  if (k == "status_evidence") { mode="seq"; topval[k]="__SEQ__"; toptyp[k]="seq"; return }
  topval[k]=""; toptyp[k]="null"; mode="top"
}

# ---- top-level field set exact equality ----
function check_top_set(    k, nm, nx, miss, extr) {
  nm=0; nx=0
  for (k in ALLOWED_TOP) if (!(k in topsen)) miss[++nm]=k
  for (k in topsen)      if (!(k in ALLOWED_TOP)) extr[++nx]=k
  if (nm>0) fail("top-level missing fields: " joinarr(miss,nm))
  if (nx>0) fail("top-level extra fields: " joinarr(extr,nx))
}

# ---- type / non-empty / enum checks ----
function check_types(    k) {
  if (!(toptyp["schema_version"]=="int" && topval["schema_version"]=="2")) fail("schema_version must be integer 2")
  if (!(toptyp["session_id"]=="str" && trim(topval["session_id"])!=""))   fail("session_id must be non-empty string")
  if (!(toptyp["repository"]=="str" && trim(topval["repository"])!=""))   fail("repository must be non-empty string")
  if (!(toptyp["branch"]=="null" || toptyp["branch"]=="str"))              fail("branch must be string|null")
  if (!(toptyp["base_commit"]=="null" || (toptyp["base_commit"]=="str" && topval["base_commit"] ~ HEX))) fail("base_commit must be null or 7-64 hex")
  if (!(topval["working_tree"] in WORKING_TREE)) fail("working_tree enum invalid")
  if (!(topval["handoff_status"] in HANDOFF_STATUS)) fail("handoff_status enum invalid")
  if (!(toptyp["interrogation_round"]=="int" && topval["interrogation_round"]+0>=0 && topval["interrogation_round"]+0<=3)) fail("interrogation_round must be int 0..3")
  if (!(toptyp["last_audit_status"]=="null" || (topval["last_audit_status"] in LAST_AUDIT))) fail("last_audit_status enum invalid")
  if (!(toptyp["status_reason"]=="str" && trim(topval["status_reason"])!="")) fail("status_reason must be non-empty")
  if (!(necount > 0)) fail("status_evidence must be non-empty array")
  if (!(toptyp["created_at"]=="str" && topval["created_at"] ~ RFC3339)) fail("created_at not RFC3339")
  if (!(toptyp["updated_at"]=="str" && topval["updated_at"] ~ RFC3339)) fail("updated_at not RFC3339")
  if (topval["created_at"]!="" && topval["updated_at"]!="" && topval["updated_at"] < topval["created_at"]) fail("updated_at earlier than created_at")
}

# ---- status_evidence element checks ----
function check_evidence(    i, k, j, nm, nx, miss, extr) {
  for (i=0; i<necount; i++) {
    nm=0; nx=0
    for (k in ALLOWED_EV) if (!((i,k) in evseen)) miss[++nm]=k
    for (j=1; j<=evkcount[i]; j++) { k=evkey[i,j]; if (!(k in ALLOWED_EV)) extr[++nx]=k }
    if (nm>0) fail("evidence[" i "] missing fields: " joinarr(miss,nm))
    if (nx>0) fail("evidence[" i "] extra fields: " joinarr(extr,nx))
    if (!(evval[i,"kind"] in KIND_ENUM))                         fail("evidence[" i "].kind enum invalid")
    if (!(evtyp[i,"ref"]=="null" || evtyp[i,"ref"]=="str"))      fail("evidence[" i "].ref type invalid")
    if (!(evtyp[i,"claim"]=="str" && trim(evval[i,"claim"])!="")) fail("evidence[" i "].claim must be non-empty")
    if (!(evval[i,"verification"] in VERIF_ENUM))               fail("evidence[" i "].verification enum invalid")
  }
  if (necount == 1) {
    if (!(evval[0,"kind"]=="unverified" && evtyp[0,"ref"]=="null" && evval[0,"verification"]=="UNVERIFIED"))
      fail("sole evidence element must be unverified/null/UNVERIFIED")
  }
}

# ---- TL;DR structure (mirror ps1: tldr = body up to next H1 or end) ----
function check_tldr(    bi, first, tldr, pos, i, sec, idx, p, q, r, sw) {
  # trim leading blank lines, first non-blank must start with "# TL;DR"
  bi=1
  while (bi<=nbl && blines[bi] ~ /^[[:space:]]*$/) bi++
  if (bi>nbl) { fail("first heading after YAML must be # TL;DR"); return }
  first=blines[bi]
  if (substr(first,1,7) != "# TL;DR") fail("first heading after YAML must be # TL;DR")

  # collect tldr block: from body line 1 up to (excluding) next H1 after the TL;DR heading
  tldr=""; sw=0
  for (i=1; i<=nbl; i++) {
    if (sw && blines[i] ~ /^# /) break
    tldr = tldr blines[i] "\n"
    if (blines[i] ~ /^# TL;DR/) sw=1
  }
  if (length(tldr) > 1500) fail("TL;DR exceeds 1500 Unicode chars (" length(tldr) ")")

  # Status line must match handoff_status
  p = index(tldr, "Status:")
  if (p == 0) { fail("TL;DR missing Status: line") }
  else {
    q = p + 7
    while (q <= length(tldr) && substr(tldr,q,1) ~ /[[:space:]]/) q++
    r = q
    while (r <= length(tldr) && substr(tldr,r,1) !~ /[[:space:]]/) r++
    sw = substr(tldr, q, r-q)            # reuse sw as the captured status word
    if (sw == "") fail("TL;DR missing Status: line")
    else if (sw != topval["handoff_status"]) fail("TL;DR Status (" sw ") != handoff_status (" topval["handoff_status"] ")")
  }

  # six sections present and in order (break on first missing, mirror ps1)
  pos=0
  for (i=1; i<=NSEC; i++) {
    sec = "## " TLDR_SECTIONS[i]
    idx = index(tldr, sec)
    if (idx == 0) { fail("TL;DR missing ## " TLDR_SECTIONS[i]); break }
    if (idx < pos) { fail("TL;DR ## " TLDR_SECTIONS[i] " out of order"); break }
    pos = idx
  }
}
AWK
then
  exit 1
fi

# --- success: print VALID + SHA-256 byte digest of the raw file ---
digest=$(sha256sum "$FILE" | awk '{print $1}')
echo "VALID"
echo "DIGEST $digest"
exit 0
