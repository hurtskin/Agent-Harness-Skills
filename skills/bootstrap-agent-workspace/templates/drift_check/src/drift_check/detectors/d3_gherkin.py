"""D3 detector: Gherkin Scenario count <-> test count."""

from __future__ import annotations

from drift_check.adapters.base import SpecAdapter
from drift_check.detectors.common import DriftFinding, Severity


def detect_gherkin_drift(adapter: SpecAdapter) -> list[DriftFinding]:
    """Check that Gherkin scenario count matches test case count."""
    findings: list[DriftFinding] = []

    for spec in adapter.list_specs():
        spec_text = spec.spec_md.read_text(encoding="utf-8")
        gherkin_count = adapter.parse_gherkin_count(spec_text)
        if gherkin_count == 0:
            continue

        # Count TC-XX markers in spec
        import re
        tc_count = len(re.findall(r"TC-[A-Za-z0-9-]+", spec_text))

        # Count test files in spec directory
        test_dir = spec.spec_dir / "tests"
        test_file_count = 0
        if test_dir.exists():
            test_file_count = len(list(test_dir.glob("test_*.py")))

        if gherkin_count != tc_count:
            findings.append(
                DriftFinding(
                    detector="D3",
                    severity=Severity.ERROR,
                    spec_id=spec.rel_spec_id,
                    message="Gherkin scenario count != TC marker count",
                    details={
                        "gherkin": str(gherkin_count),
                        "tc_markers": str(tc_count),
                    },
                )
            )

        if test_file_count > 0 and gherkin_count != test_file_count:
            findings.append(
                DriftFinding(
                    detector="D3",
                    severity=Severity.WARNING,
                    spec_id=spec.rel_spec_id,
                    message="Gherkin scenario count != test file count",
                    details={
                        "gherkin": str(gherkin_count),
                        "test_files": str(test_file_count),
                    },
                )
            )

    return findings
