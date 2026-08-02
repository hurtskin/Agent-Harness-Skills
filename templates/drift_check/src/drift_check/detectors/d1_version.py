"""D1 detector: spec three-piece version sync."""

from __future__ import annotations

import re

from drift_check.adapters.base import SpecAdapter
from drift_check.detectors.common import DriftFinding, Severity


def detect_version_drift(adapter: SpecAdapter) -> list[DriftFinding]:
    """Check that spec.md / tasks.md / checklist.md have matching versions."""
    findings: list[DriftFinding] = []

    for spec in adapter.list_specs():
        spec_v = _extract_version(spec.spec_md.read_text(encoding="utf-8"))
        tasks_v = _extract_version(spec.tasks_md.read_text(encoding="utf-8"))
        checklist_v = _extract_version(spec.checklist_md.read_text(encoding="utf-8"))

        if spec_v is None:
            findings.append(
                DriftFinding(
                    detector="D1",
                    severity=Severity.ERROR,
                    spec_id=spec.rel_spec_id,
                    message="spec.md missing version marker",
                    details={"file": spec.spec_md.name},
                )
            )
            continue

        if tasks_v != spec_v:
            findings.append(
                DriftFinding(
                    detector="D1",
                    severity=Severity.ERROR,
                    spec_id=spec.rel_spec_id,
                    message="tasks.md version mismatch",
                    details={"spec": spec_v or "unknown", "tasks": tasks_v or "unknown"},
                )
            )

        if checklist_v != spec_v:
            findings.append(
                DriftFinding(
                    detector="D1",
                    severity=Severity.ERROR,
                    spec_id=spec.rel_spec_id,
                    message="checklist.md version mismatch",
                    details={"spec": spec_v or "unknown", "checklist": checklist_v or "unknown"},
                )
            )

    return findings


def _extract_version(md_text: str) -> str | None:
    """Extract version from markdown header (e.g., '**版本:** v1.0.0')."""
    m = re.search(r"\*\*版本[:：]\*\*\s*v?(\d+\.\d+\.\d+)", md_text)
    return m.group(1) if m else None
