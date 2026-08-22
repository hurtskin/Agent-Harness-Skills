#!/usr/bin/env bash
# Thin pre-commit entry for git hook / CI. See hooks/README.md.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
PYTHON="${PYTHON:-python}"

exec bash "$HERE/../run_verify.sh" --pre-commit --repo-root "$ROOT" --python "$PYTHON"
