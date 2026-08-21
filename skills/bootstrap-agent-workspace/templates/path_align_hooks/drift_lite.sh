#!/usr/bin/env bash
# drift-lite: L0 path-pairing diagnosis (Unix / Git Bash).
# Standalone:
#   bash tools/path_align_hooks/drift_lite.sh
#   bash tools/path_align_hooks/drift_lite.sh --fail-on-risk
# Twin: powershell -File tools/path_align_hooks/drift_lite.ps1
#
# stdout: JSON report. Exit 0 unless --fail-on-risk and risk present (then 1).
set -euo pipefail

FAIL_ON_RISK=0
REPO_ROOT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --fail-on-risk) FAIL_ON_RISK=1; shift ;;
    --root) REPO_ROOT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n "$REPO_ROOT" ]]; then
  ROOT="$(cd "$REPO_ROOT" && pwd)"
else
  ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
  if [[ -z "$ROOT" ]]; then
    ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
  fi
fi
LAST_DRIFT="$SCRIPT_DIR/last-drift.json"

esc() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }

is_tooling_noise() {
  local n
  n=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr '\\' '/')
  n="${n%/}"
  case "$n" in
    .cursor|.cursor/*|.claude|.claude/*|.trae|.trae/*|.codex|.codex/*|.pi|.pi/*|.qoder|.qoder/*|tools/path_align_hooks|tools/path_align_hooks/*)
      return 0 ;;
  esac
  return 1
}

is_relevant() {
  local lower
  lower=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr '\\' '/')
  case "$lower" in
    specs/*|*/specs/*|src/*|*/src/*|skills/*|*/skills/*|*openapi*|*.schema.json*) return 0 ;;
  esac
  return 1
}

is_spec_side() {
  local lower
  lower=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr '\\' '/')
  case "$lower" in
    specs/*|*openapi*|*.schema.json*) return 0 ;;
  esac
  return 1
}

is_code_side() {
  local lower
  lower=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr '\\' '/')
  case "$lower" in
    specs/*) return 1 ;;
    skills/*|src/*|*.py|*.ts|*.tsx|*.js) return 0 ;;
  esac
  return 1
}

cluster_of() {
  local p
  p=$(printf '%s' "$1" | tr '\\' '/')
  if [[ "$p" =~ ^(skills/[^/]+) ]]; then echo "${BASH_REMATCH[1]}"; return; fi
  if [[ "$p" =~ ^(specs/[^/]+/[^/]+) ]]; then echo "${BASH_REMATCH[1]}"; return; fi
  if [[ "$p" =~ ^(specs/[^/]+) ]]; then echo "${BASH_REMATCH[1]}"; return; fi
  if [[ "$p" =~ ^(src/[^/]+) ]]; then echo "${BASH_REMATCH[1]}"; return; fi
  echo "${p%%/*}"
}

FILES=()
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  is_tooling_noise "$line" && continue
  FILES+=("$line")
done < <(
  {
    git -C "$ROOT" status --porcelain -uall 2>/dev/null | while IFS= read -r line; do
      [[ ${#line} -lt 4 ]] && continue
      path="${line:3}"
      path="${path#"${path%%[![:space:]]*}"}"
      if [[ "$path" == *" -> "* ]]; then path="${path##* -> }"; fi
      printf '%s\n' "${path//\\//}"
    done
    git -C "$ROOT" diff --name-only HEAD 2>/dev/null | tr '\\' '/'
  } | awk 'NF && !seen[$0]++'
)

RELEVANT=()
SPEC_FILES=()
CODE_FILES=()
for f in "${FILES[@]:-}"; do
  if is_relevant "$f"; then
    RELEVANT+=("$f")
    is_spec_side "$f" && SPEC_FILES+=("$f")
    is_code_side "$f" && CODE_FILES+=("$f")
  fi
done

CLUSTERS=()
if [[ ${#RELEVANT[@]} -gt 0 ]]; then
  while IFS= read -r c; do
    [[ -n "$c" ]] && CLUSTERS+=("$c")
  done < <(printf '%s\n' "${RELEVANT[@]}" | while read -r x; do cluster_of "$x"; done | awk 'NF && !seen[$0]++')
fi

RISK_CODE=""
RISK_TEXT=""
OK=true
SUMMARY="No relevant spec/code changes in dirty tree."
ACTIONS_JSON="[]"

sample=$(printf '%s,' "${RELEVANT[@]:0:12}")
sample="${sample%,}"
cluster_sample=$(printf '%s,' "${CLUSTERS[@]:0:8}")
cluster_sample="${cluster_sample%,}"

if [[ ${#RELEVANT[@]} -gt 0 ]]; then
  if [[ ${#CODE_FILES[@]} -gt 0 && ${#SPEC_FILES[@]} -eq 0 ]]; then
    OK=false
    RISK_CODE="CODE_WITHOUT_SPEC"
    RISK_TEXT="drift-lite: CODE_WITHOUT_SPEC - code/skills changed without specs/openapi/schema. files=$sample"
    SUMMARY="$RISK_TEXT"
    if command -v jq >/dev/null 2>&1; then
      ACTIONS_JSON=$(jq -cn \
        --arg s "$cluster_sample" \
        --argjson targets "$(printf '%s\n' "${CODE_FILES[@]:0:20}" | jq -R . | jq -s .)" \
        --argjson clusters "$(printf '%s\n' "${CLUSTERS[@]}" | jq -R . | jq -s .)" \
        '[
          {id:"A1",side:"spec",op:"add_or_update",targets:$targets,clusters:$clusters,
           instruction:("Add or update specs/ (and/or openapi/schema) for clusters: "+$s)},
          {id:"A2",side:"either",op:"justify",targets:[],clusters:$clusters,
           instruction:"Or briefly explain why this turn is intentionally code-only (no Spec update)."}
        ]')
    fi
  elif [[ ${#SPEC_FILES[@]} -gt 0 && ${#CODE_FILES[@]} -eq 0 ]]; then
    OK=false
    RISK_CODE="SPEC_WITHOUT_CODE"
    RISK_TEXT="drift-lite: SPEC_WITHOUT_CODE - specs/openapi/schema changed without code/skills. files=$sample"
    SUMMARY="$RISK_TEXT"
    if command -v jq >/dev/null 2>&1; then
      ACTIONS_JSON=$(jq -cn \
        --arg s "$cluster_sample" \
        --argjson targets "$(printf '%s\n' "${SPEC_FILES[@]:0:20}" | jq -R . | jq -s .)" \
        --argjson clusters "$(printf '%s\n' "${CLUSTERS[@]}" | jq -R . | jq -s .)" \
        '[
          {id:"A1",side:"code",op:"add_or_update",targets:$targets,clusters:$clusters,
           instruction:("Implement or update code/skills for clusters: "+$s)},
          {id:"A2",side:"either",op:"justify",targets:[],clusters:$clusters,
           instruction:"Or briefly explain why this turn is intentionally Spec-only (no code update)."}
        ]')
    fi
  else
    SUMMARY="Paired changes OK (spec_side=${#SPEC_FILES[@]}, code_side=${#CODE_FILES[@]}). clusters=$cluster_sample"
  fi
fi

if command -v jq >/dev/null 2>&1; then
  ok_json=true
  [[ "$OK" == false ]] && ok_json=false
  risk_json=null
  risk_code_json=null
  [[ -n "$RISK_TEXT" ]] && risk_json=$(jq -cn --arg r "$RISK_TEXT" '$r')
  [[ -n "$RISK_CODE" ]] && risk_code_json=$(jq -cn --arg r "$RISK_CODE" '$r')
  REPORT=$(jq -n \
    --argjson ok "$ok_json" \
    --argjson risk "$risk_json" \
    --argjson risk_code "$risk_code_json" \
    --arg summary "$SUMMARY" \
    --argjson changed "$(printf '%s\n' "${FILES[@]:-}" | head -100 | jq -R . | jq -s .)" \
    --argjson relevant "$(printf '%s\n' "${RELEVANT[@]:-}" | head -50 | jq -R . | jq -s .)" \
    --argjson spec_files "$(printf '%s\n' "${SPEC_FILES[@]:-}" | head -50 | jq -R . | jq -s .)" \
    --argjson code_files "$(printf '%s\n' "${CODE_FILES[@]:-}" | head -50 | jq -R . | jq -s .)" \
    --argjson clusters "$(printf '%s\n' "${CLUSTERS[@]:-}" | jq -R . | jq -s .)" \
    --argjson actions "$ACTIONS_JSON" \
    --arg root "$ROOT" \
    --arg gen "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{
      ok:$ok, risk_code:$risk_code, risk:$risk, summary:$summary,
      changed:$changed, relevant:$relevant, spec_files:$spec_files, code_files:$code_files,
      clusters:$clusters, actions:$actions, repo_root:$root, generated_at:$gen, engine:"drift_lite.sh"
    }')
  printf '%s\n' "$REPORT" >"$LAST_DRIFT"
  printf '%s' "$REPORT"
else
  cat >"$LAST_DRIFT" <<EOF
{"ok": $OK, "risk_code": $(if [[ -n "$RISK_CODE" ]]; then printf '"%s"' "$(esc "$RISK_CODE")"; else echo null; fi), "summary": "$(esc "$SUMMARY")", "engine": "drift_lite.sh"}
EOF
  cat "$LAST_DRIFT" | tr -d '\n'
fi

echo "[drift_lite] ok=$OK risk_code=${RISK_CODE:-null} relevant=${#RELEVANT[@]}" >&2

if [[ "$FAIL_ON_RISK" -eq 1 && "$OK" == false ]]; then
  exit 1
fi
exit 0
