"""Fixture tests for the two validate_handoff implementations.

The validator ships as two language twins that together cover every OS:
PowerShell for Windows and bash+gawk for Unix (Linux/macOS). Python was removed
as redundant - ps1 + sh already cover all platforms and depend only on OS
built-ins.

Asserts:
- the single good fixture is VALID and its reported SHA-256 DIGEST equals the
  file's own byte digest (computed here, so the check stays line-ending safe);
- the five bad fixtures are rejected (exit 1).

Only the validator native to the current OS runs here. The CI matrix runs the
same fixtures on ubuntu-latest (bash) and windows-latest (PowerShell), so every
fixture is exercised against the validator of each platform.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

PS1 = SCRIPTS / "validate_handoff.ps1"
SH = SCRIPTS / "validate_handoff.sh"

GOOD = FIXTURES / "good.md"
BAD = sorted(FIXTURES.glob("bad*.md"))


def _validator() -> Path:
    return PS1 if os.name == "nt" else SH


def _run(validator: Path, fixture: Path) -> tuple[int, str, str]:
    if os.name == "nt":
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(validator),
            str(fixture),
        ]
    else:
        cmd = ["bash", str(validator), str(fixture)]
    proc = subprocess.run(cmd, capture_output=True, encoding="utf-8")
    return proc.returncode, proc.stdout, proc.stderr


def _digest(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith("DIGEST "):
            return line.split(" ", 1)[1]
    return None


class ValidatorFixtureTests(unittest.TestCase):
    def test_good_fixture_valid_with_byte_digest(self) -> None:
        validator = _validator()
        code, out, err = _run(validator, GOOD)
        self.assertEqual(0, code, f"{validator.name}: {err}")
        self.assertIn("VALID", out, f"{validator.name}: {out}")
        expected = hashlib.sha256(GOOD.read_bytes()).hexdigest()
        self.assertEqual(expected, _digest(out), f"{validator.name} digest mismatch")

    def test_bad_fixtures_rejected(self) -> None:
        self.assertEqual(5, len(BAD), f"expected 5 bad fixtures, got {len(BAD)}")
        validator = _validator()
        for bad in BAD:
            code, out, err = _run(validator, bad)
            self.assertEqual(
                1, code, f"{validator.name} {bad.name}: out={out!r} err={err!r}"
            )


if __name__ == "__main__":
    unittest.main()