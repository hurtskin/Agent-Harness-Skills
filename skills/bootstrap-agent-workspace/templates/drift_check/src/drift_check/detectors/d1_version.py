"""D1 detector: spec three-piece version sync."""

from __future__ import annotations

from drift_check.adapters.base import SpecAdapter, SpecLocation
from drift_check.detectors.common import DriftFinding, Severity


def detect(spec: SpecLocation, adapter: SpecAdapter) -> list[DriftFinding]:
    """Check that one spec.md / tasks.md / checklist.md set has matching versions."""
    versions = {
        "spec": adapter.parse_version(spec.spec_md.read_text(encoding="utf-8")),
        "tasks": adapter.parse_version(spec.tasks_md.read_text(encoding="utf-8")),
        "checklist": adapter.parse_version(spec.checklist_md.read_text(encoding="utf-8")),
    }
    unknown_files = [f"{name}.md" for name, version in versions.items() if version == "unknown"]
    if unknown_files:
        return [
            DriftFinding(
                detector="D1",
                severity=Severity.WARNING,
                spec_path=spec.rel_spec_id,
                message=f"version unknown in: {', '.join(unknown_files)}",
                evidence={
                    "kind": "version_unknown",
                    "files": unknown_files,
                    "versions": versions,
                },
            )
        ]

    normalized = {name: version.lower().removeprefix("v") for name, version in versions.items()}
    if len(set(normalized.values())) == 1:
        return []

    return [
        DriftFinding(
            detector="D1",
            severity=Severity.ERROR,
            spec_path=spec.rel_spec_id,
            message=(
                f"version mismatch: spec={versions['spec']} tasks={versions['tasks']} "
                f"checklist={versions['checklist']}"
            ),
            evidence={"kind": "version_mismatch", "versions": versions},
        )
    ]
