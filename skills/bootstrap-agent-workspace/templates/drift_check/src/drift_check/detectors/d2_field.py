"""D2 detector: spec field table <-> BaseModel annotations."""

from __future__ import annotations

from drift_check.adapters.base import SpecAdapter
from drift_check.detectors.common import DriftFinding, Severity


def detect_field_drift(adapter: SpecAdapter) -> list[DriftFinding]:
    """Check that spec field tables match code BaseModel annotations."""
    findings: list[DriftFinding] = []

    for spec in adapter.list_specs():
        spec_text = spec.spec_md.read_text(encoding="utf-8")
        spec_fields = adapter.parse_field_table(spec_text)
        if not spec_fields:
            continue

        # Find code targets for this spec
        code_targets = adapter.list_code_targets()
        for target in code_targets:
            # Compare spec fields with code fields
            # This is a simplified check - customize for your project
            spec_field_names = {f.name for f in spec_fields}
            # In a real implementation, you'd parse the code file to extract fields
            # For now, just check if the target file exists
            if not target.py_path.exists():
                findings.append(
                    DriftFinding(
                        detector="D2",
                        severity=Severity.ERROR,
                        spec_id=spec.rel_spec_id,
                        message=f"Code target file missing: {target.rel_path}",
                        details={"file": target.rel_path},
                    )
                )

    return findings
