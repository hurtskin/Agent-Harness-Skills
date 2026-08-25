#!/usr/bin/env bash
# Thin pre-commit entry for git hook / CI. See hooks/README.md.
# RepoRoot auto-detected (decision v20): explicit $REPO_ROOT env > git rev-parse > AGENTS.md walk-up.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERIFY_DIR="$(cd "$HERE/.." && pwd)"

resolve_repo_root() {
  if [ -n "${REPO_ROOT:-}" ]; then echo "$REPO_ROOT"; return; fi
  local git_root
  git_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [ -n "$git_root" ]; then echo "$git_root"; return; fi
  local cur="$HERE"
  for _ in 1 2 3 4 5 6 7 8; do
    if [ -f "$cur/AGENTS.md" ]; then echo "$cur"; return; fi
    local parent
    parent="$(dirname "$cur")"
    [ "$parent" = "$cur" ] && break
    cur="$parent"
  done
  echo "$(cd "$HERE/../../.." && pwd)"
}

ROOT="$(resolve_repo_root)"
PYTHON="${PYTHON:-python}"

exec bash "$VERIFY_DIR/run_verify.sh" --pre-commit --repo-root "$ROOT" --python "$PYTHON"
