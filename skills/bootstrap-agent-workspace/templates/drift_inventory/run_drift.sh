#!/usr/bin/env bash
# Inventory drift runner. Interpreter: --python or PYTHON env.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${REPO_ROOT:-$(cd "$HERE/../.." && pwd)}"
INVENTORY="${INVENTORY:-specs/drift/pilot/inventory.yaml}"
FORMAT="${FORMAT:-text}"
PYTHON="${PYTHON_ARG:-${PYTHON:-python}}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python) PYTHON="$2"; shift 2 ;;
    --repo-root) REPO_ROOT="$(cd "$2" && pwd)"; shift 2 ;;
    --inventory) INVENTORY="$2"; shift 2 ;;
    --format) FORMAT="$2"; shift 2 ;;
    *) echo "unknown: $1" >&2; exit 2 ;;
  esac
done

exec "$PYTHON" "$HERE/drift_inventory.py" \
  --repo-root "$REPO_ROOT" \
  --inventory "$REPO_ROOT/$INVENTORY" \
  --format "$FORMAT"
