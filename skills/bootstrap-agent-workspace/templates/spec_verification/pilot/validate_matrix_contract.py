"""Contract-kind pilot: validate matrix.yaml minimal structure."""

from __future__ import annotations

import re
import sys
from pathlib import Path

MATRIX = Path(__file__).resolve().parent.parent / "matrix.yaml"
ALLOWED_KINDS = frozenset({"pbt", "example", "contract", "manual"})


def main() -> int:
    text = MATRIX.read_text(encoding="utf-8")
    if not re.search(r"^version:\s*\d+", text, re.M):
        print("[contract] missing version:", file=sys.stderr)
        return 1
    if "modules:" not in text:
        print("[contract] missing modules:", file=sys.stderr)
        return 1
    ids = re.findall(r"^\s+-\s+id:\s*(\S+)", text, re.M)
    if not ids:
        print("[contract] no module ids:", file=sys.stderr)
        return 1
    kinds = re.findall(r"^\s+kind:\s*(\S+)", text, re.M)
    for k in kinds:
        if k not in ALLOWED_KINDS:
            print(f"[contract] unknown kind: {k}", file=sys.stderr)
            return 1
    print(f"[contract] matrix OK ({len(ids)} modules, kinds={kinds})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
