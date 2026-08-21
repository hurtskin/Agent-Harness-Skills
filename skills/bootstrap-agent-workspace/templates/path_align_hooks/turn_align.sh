#!/usr/bin/env bash
# turn_align: turn-end event -> drift_lite -> optional nudge JSON (Unix).
# Twin: powershell -File tools/path_align_hooks/turn_align.ps1
#
# stdout: {} or { nudge, message, actions }. Map message to host follow-up when registering.
# Disable nudge: PATH_ALIGN_NUDGE=0
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT" ]]; then
  ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi
LAST_STOP="$SCRIPT_DIR/last-turn-align.json"
LAST_STDIN="$SCRIPT_DIR/last-turn-align.stdin.bin"
DRIFT_LITE="$SCRIPT_DIR/drift_lite.sh"

esc() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }

if command -v dd >/dev/null 2>&1; then
  dd bs=1048576 count=1 of="$LAST_STDIN" status=none 2>/dev/null || cat >"$LAST_STDIN"
else
  cat >"$LAST_STDIN"
fi

stdin_len=$(wc -c <"$LAST_STDIN" | tr -d ' ')
stdin_head_hex=$(head -c 64 "$LAST_STDIN" 2>/dev/null | od -An -tx1 | tr -d ' \n' || true)

decode_stdin() {
  local head
  head=$(head -c 4 "$LAST_STDIN" 2>/dev/null | od -An -tx1 | tr -d ' \n' || true)
  if [[ "$head" == fffe* || "$head" == 7b00* ]]; then
    if command -v iconv >/dev/null 2>&1; then
      iconv -f UTF-16LE -t UTF-8 <"$LAST_STDIN" 2>/dev/null && return
    fi
  fi
  sed '1s/^\xEF\xBB\xBF//' <"$LAST_STDIN" 2>/dev/null || cat "$LAST_STDIN"
}

RAW="$(decode_stdin || true)"
RAW_PREVIEW="${RAW:0:1000}"
PARSE_OK=false
PARSE_ERROR=""
RECOVERED_BY=""
STATUS="unknown"
LOOP_COUNT=0
PAYLOAD_JSON="{}"

extract_json_object() {
  printf '%s' "$1" | tr -d '\0' | sed -n 's/.*\({.*}\).*/\1/p' | head -1
}

if [[ -n "${RAW//[[:space:]]/}" ]]; then
  if command -v jq >/dev/null 2>&1; then
    obj="$(printf '%s' "$RAW" | tr -d '\0' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    if ! printf '%s' "$obj" | jq -e . >/dev/null 2>&1; then
      obj="$(extract_json_object "$RAW")"
      RECOVERED_BY="brace_extract"
    fi
    if printf '%s' "$obj" | jq -e . >/dev/null 2>&1; then
      PAYLOAD_JSON="$(printf '%s' "$obj" | jq -c .)"
      STATUS="$(printf '%s' "$PAYLOAD_JSON" | jq -r '.status // .final_status // .stop.status // .event // "unknown"')"
      LOOP_COUNT="$(printf '%s' "$PAYLOAD_JSON" | jq -r '.loop_count // 0')"
      PARSE_OK=true
    else
      PARSE_ERROR="jq_parse_failed"
    fi
  else
    obj="$(extract_json_object "$RAW")"
    if [[ -n "$obj" ]]; then
      PAYLOAD_JSON="$obj"
      STATUS="$(printf '%s' "$obj" | sed -n 's/.*"status"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
      [[ -z "$STATUS" ]] && STATUS="unknown"
      LOOP_COUNT="$(printf '%s' "$obj" | sed -n 's/.*"loop_count"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p' | head -1)"
      [[ -z "$LOOP_COUNT" ]] && LOOP_COUNT=0
      PARSE_OK=true
      RECOVERED_BY="sed_fallback"
    else
      PARSE_ERROR="sed_parse_failed"
    fi
  fi
else
  PARSE_ERROR="empty_stdin"
fi

nudge_enabled() {
  local v="${PATH_ALIGN_NUDGE-}"
  if [[ -z "$v" ]]; then return 0; fi
  case "$(printf '%s' "$v" | tr '[:upper:]' '[:lower:]')" in
    0|false|no|off) return 1 ;;
    *) return 0 ;;
  esac
}

should_run_drift=0
case "$STATUS" in
  completed|success|ok|end|finished) should_run_drift=1 ;;
esac

DRIFT_JSON='{"ok":true,"risk_code":null,"risk":null,"summary":"skipped","actions":[],"relevant":[],"changed":[],"clusters":[]}'
if [[ "$should_run_drift" -eq 1 ]]; then
  DRIFT_JSON="$(bash "$DRIFT_LITE" --root "$ROOT" 2>/dev/null || true)"
  [[ -z "$DRIFT_JSON" ]] && DRIFT_JSON='{"ok":true,"risk_code":null,"summary":"drift_lite empty","actions":[],"relevant":[],"changed":[],"clusters":[]}'
else
  DRIFT_JSON=$(printf '{"ok":true,"risk_code":null,"risk":null,"summary":"Skipped drift-lite because status=%s","actions":[],"relevant":[],"changed":[],"clusters":[]}' "$(esc "$STATUS")")
fi

if command -v jq >/dev/null 2>&1; then
  parse_ok_json=false
  [[ "$PARSE_OK" == true ]] && parse_ok_json=true
  RECORD=$(jq -n \
    --arg fired "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg status "$STATUS" \
    --argjson loop "$LOOP_COUNT" \
    --arg cwd "$ROOT" \
    --argjson drift "$DRIFT_JSON" \
    --argjson parse_ok "$parse_ok_json" \
    --arg parse_error "${PARSE_ERROR:-}" \
    --arg raw_preview "$RAW_PREVIEW" \
    --arg head_hex "$stdin_head_hex" \
    --argjson stdin_len "$stdin_len" \
    --arg recovered "${RECOVERED_BY:-}" \
    --argjson payload "${PAYLOAD_JSON:-{}}" \
    '{
      fired_at:$fired,
      status:$status,
      loop_count:$loop,
      cwd:$cwd,
      changed_count:(($drift.changed // []) | length),
      relevant:($drift.relevant // []),
      risk:($drift.risk // null),
      risk_code:($drift.risk_code // null),
      summary:($drift.summary // null),
      actions:($drift.actions // []),
      clusters:($drift.clusters // []),
      drift:$drift,
      parse:{
        stdin_len:$stdin_len,
        stdin_head_hex:$head_hex,
        parse_ok:$parse_ok,
        parse_error:(if $parse_error=="" then null else $parse_error end),
        raw_preview:$raw_preview,
        recovered_by:(if $recovered=="" then null else $recovered end)
      },
      payload:$payload,
      runner:"bash"
    }')
  printf '%s\n' "$RECORD" >"$LAST_STOP"

  RISK_CODE="$(printf '%s' "$DRIFT_JSON" | jq -r '.risk_code // empty')"
  echo "[turn_align] status=$STATUS parse_ok=$PARSE_OK risk_code=${RISK_CODE:-null}" >&2

  OUT='{}'
  if nudge_enabled && [[ "$should_run_drift" -eq 1 ]] && [[ -n "$RISK_CODE" ]] && [[ "$LOOP_COUNT" -lt 2 ]]; then
    MSG=$(printf '%s' "$DRIFT_JSON" | jq -r '
      .summary as $s |
      ("Actionable work orders:\n" + (
        (.actions // []) | to_entries | map("  \(.key+1). [\(.value.id)] \(.value.instruction)") | join("\n")
      ) + "\nDo A1 (preferred) or A2 (justify one-sided). Then stop.") |
      ($s + "\n" + .)
    ')
    OUT=$(jq -cn --arg m "$MSG" --argjson a "$(printf '%s' "$DRIFT_JSON" | jq '.actions // []')" \
      '{nudge:true, message:$m, actions:$a}')
  fi
  printf '%s' "$OUT"
else
  cat >"$LAST_STOP" <<EOF
{"fired_at":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","status":"$(esc "$STATUS")","runner":"bash","risk_code":null,"summary":"jq required for full turn_align record"}
EOF
  echo "[turn_align] status=$STATUS (jq missing; limited mode)" >&2
  printf '%s' '{}'
fi

exit 0
