#!/usr/bin/env bash
# Light verification runner (local sandbox). See README.md.
# Interpreter: pass --python or export PYTHON; no venv/PATH search in script.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$HERE/../.." && pwd)}"
PRE_COMMIT=0
DRY_RUN=0
PYTHON_ARG=""
PATHS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pre-commit) PRE_COMMIT=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --repo-root) REPO_ROOT="$(cd "$2" && pwd)"; shift 2 ;;
    --python) PYTHON_ARG="$2"; shift 2 ;;
    --paths) PATHS+=("$2"); shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

PYTHON="${PYTHON_ARG:-${PYTHON:-python}}"
MATRIX="$HERE/matrix.yaml"

normalize_slash() { echo "$1" | sed 's#\\#/#g' | sed 's#^\./##'; }

watch_hit() {
  local file norm pat prefix
  norm="$(normalize_slash "$1")"
  shift
  for pat in "$@"; do
    pat="$(normalize_slash "$pat")"
    if [[ "$pat" == */** ]]; then
      prefix="${pat%/**}"
      if [[ "$norm" == "$prefix" || "$norm" == "$prefix"/* ]]; then return 0; fi
    elif [[ "$norm" == "$pat" ]]; then return 0; fi
  done
  return 1
}

subst_placeholders() {
  local cmd="$1"
  cmd="${cmd//\{python\}/$PYTHON}"
  cmd="${cmd//\{repo_root\}/$REPO_ROOT}"
  printf '%s' "$cmd"
}

# Minimal matrix reader: emits records "id|kind|cwd|command|watch_csv"
read_matrix_records() {
  awk -v repo="$REPO_ROOT" '
    /^  - id:/ { if (id != "") emit(); gsub(/^  - id: */, ""); id=$0; kind=""; cwd=""; cmd=""; watch_n=0; in_watch=0; in_test=0; next }
    /^    kind:/ { gsub(/^    kind: */, ""); kind=$0; next }
    /^    pbt: true/ && kind=="" { kind="pbt"; next }
    /^    watch:/ { in_watch=1; in_test=0; next }
    /^    test:/ { in_watch=0; in_test=1; next }
    in_watch && /^      - / { gsub(/^      - /, ""); watch[watch_n++]=$0; next }
    in_test && /^      cwd:/ { gsub(/^      cwd: */, ""); gsub(/"/, "", $0); cwd=$0; next }
    in_test && /^      command:/ { gsub(/^      command: */, ""); gsub(/"/, "", $0); cmd=$0; next }
    function emit() {
      if (kind == "" && id != "") kind="manual"
      if (kind == "manual" || cmd == "" || cwd == "") return
      w = watch[0]
      for (i = 1; i < watch_n; i++) w = w "," watch[i]
      gsub(/\{repo_root\}/, repo, cwd)
      print id "|" kind "|" cwd "|" cmd "|" w
    }
    END { emit() }
  ' "$MATRIX"
}

STAGED=()
if [[ ${#PATHS[@]} -gt 0 ]]; then
  STAGED=("${PATHS[@]}")
elif [[ "$PRE_COMMIT" -eq 1 ]]; then
  mapfile -t STAGED < <(git -C "$REPO_ROOT" diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)
fi

ran=0
skipped=0

while IFS='|' read -r mod_id mod_kind mod_cwd mod_cmd watch_csv; do
  [[ -z "$mod_id" ]] && continue
  IFS=',' read -r -a WATCH_PATTERNS <<< "$watch_csv"

  if [[ "$PRE_COMMIT" -eq 1 || ${#PATHS[@]} -gt 0 ]]; then
    hit=0
    for f in "${STAGED[@]}"; do
      [[ -z "$f" ]] && continue
      if watch_hit "$f" "${WATCH_PATTERNS[@]}"; then hit=1; break; fi
    done
    if [[ "$hit" -eq 0 ]]; then
      echo "[verify] SKIP module $mod_id (no staged watch hit)"
      skipped=$((skipped + 1))
      continue
    fi
  fi

  cmd="$(subst_placeholders "$mod_cmd")"
  echo "[verify] RUN module $mod_id (kind=$mod_kind)"
  echo "  cwd: $mod_cwd"
  echo "  cmd: $cmd"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    ran=$((ran + 1))
    continue
  fi

  pushd "$mod_cwd" >/dev/null
  eval "$cmd"
  popd >/dev/null
  ran=$((ran + 1))
done < <(read_matrix_records)

echo "[verify] done ran=$ran skipped=$skipped python=$PYTHON"
if [[ "$ran" -eq 0 && "$PRE_COMMIT" -eq 1 ]]; then
  echo "[verify] pre-commit: nothing to run (ok)"
fi
