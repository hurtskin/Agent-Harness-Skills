"""Fixture parity tests for the three validate_handoff implementations.

Asserts:
- the single good fixture is VALID and yields an identical SHA-256 DIGEST across
  every validator available on the current OS;
- the five bad fixtures are rejected (exit 1) by every available validator.

Availability is split across the CI matrix on purpose: the bash validator runs on
Linux and the PowerShell validator runs on Windows, while the Python validator
(the reference) runs on both. Digest equality with the Python reference ties the
other two implementations together without requiring bash and PowerShell on the
same host.
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

PY = SCRIPTS / "validate_handoff.py"
PS1 = SCRIPTS / "validate_handoff.ps1"
SH = SCRIPTS / "validate_handoff.sh"

GOOD = FIXTURES / "good.md"
BAD = sorted(FIXTURES.glob("bad*.md"))


def _available_validators() -> list[Path]:
    validators = [PY]
    if os.name == "nt":
        validators.append(PS1)
    else:
        validators.append(SH)
    return validators


def _run(validator: Path, fixture: Path) -> tuple[int, str, str]:
    if validator == PY:
        cmd = [sys.executable, str(PY), str(fixture)]
    elif validator == PS1:
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PS1),
            str(fixture),
        ]
    else:
        cmd = ["bash", str(SH), str(fixture)]
    proc = subprocess.run(cmd, capture_output=True, encoding="utf-8")
    return proc.returncode, proc.stdout, proc.stderr


def _digest(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith("DIGEST "):
            return line.split(" ", 1)[1]
    return None


class ValidatorParityTests(unittest.TestCase):
    def test_good_fixture_valid_with_identical_digest(self) -> None:
        digests: dict[str, str] = {}
        for validator in _available_validators():
            code, out, err = _run(validator, GOOD)
            self.assertEqual(0, code, f"{validator.name}: {err}")
            self.assertIn("VALID", out, f"{validator.name}: {out}")
            digests[validator.name] = _digest(out)
        self.assertEqual(1, len(set(digests.values())), f"digest mismatch: {digests}")

    def test_bad_fixtures_rejected_by_all_validators(self) -> None:
        self.assertEqual(5, len(BAD), f"expected 5 bad fixtures, got {len(BAD)}")
        for bad in BAD:
            for validator in _available_validators():
                code, out, err = _run(validator, bad)
                self.assertEqual(
                    1,
                    code,
                    f"{validator.name} {bad.name}: out={out!r} err={err!r}",
                )


if __name__ == "__main__":
    unittest.main()