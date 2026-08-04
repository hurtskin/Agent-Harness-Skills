"""drift-check CLI entry point."""

import json
import sys
from pathlib import Path

import click

from drift_check.adapters.base import SpecAdapter
from drift_check.detectors.common import DriftFinding, Severity
from drift_check.detectors.d1_version import detect_version_drift
from drift_check.detectors.d2_field import detect_field_drift
from drift_check.detectors.d3_gherkin import detect_gherkin_drift
from drift_check.detectors.d4_task_state import detect_task_state_drift
from drift_check.detectors.d5_lesson_ref import detect_lesson_ref_drift
from drift_check.detectors.d6_bug_sync import detect_bug_sync_drift


@click.group()
def main() -> None:
    """drift-check: spec <-> code drift detector."""


@main.command()
@click.option("--project-root", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--only", multiple=True, help="Run only specific detectors (e.g., --only D1 --only D4)")
def scan(project_root: Path, fmt: str, only: tuple[str, ...]) -> None:
    """Scan project for spec <-> code drift."""
    # Import adapter dynamically based on project
    # For now, use a generic adapter that works with .trae/specs/ layout
    from drift_check.adapters.template import TemplateAdapter

    adapter = TemplateAdapter(project_root)

    detectors = {
        "D1": detect_version_drift,
        "D2": detect_field_drift,
        "D3": detect_gherkin_drift,
        "D4": detect_task_state_drift,
        "D5": detect_lesson_ref_drift,
        "D6": detect_bug_sync_drift,
    }

    if only:
        detectors = {k: v for k, v in detectors.items() if k in only}

    findings: list[DriftFinding] = []
    for detector_fn in detectors.values():
        findings.extend(detector_fn(adapter))

    if fmt == "json":
        output = [
            {
                "detector": f.detector,
                "severity": f.severity.value,
                "spec_id": f.spec_id,
                "message": f.message,
                "details": f.details,
            }
            for f in findings
        ]
        click.echo(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        if not findings:
            click.echo("No drift detected.")
            return
        for f in findings:
            sev_icon = "ERROR" if f.severity == Severity.ERROR else "WARN"
            click.echo(f"[{sev_icon}] {f.detector}: {f.message}")
            if f.details:
                for k, v in f.details.items():
                    click.echo(f"      {k}: {v}")

    has_error = any(f.severity == Severity.ERROR for f in findings)
    sys.exit(1 if has_error else 0)


@main.command("list-detectors")
def list_detectors() -> None:
    """List available detectors."""
    detectors = [
        ("D1", "spec three-piece version sync", "error"),
        ("D2", "spec field table <-> BaseModel annotations", "error"),
        ("D3", "Gherkin Scenario count <-> test count", "error"),
        ("D4", "tasks.md state vs source file existence", "error / warning"),
        ("D5", "lesson §XX reference liveness", "error"),
        ("D6", "bug sub-spec -> parent spec changelog closure", "error / warning"),
    ]
    for det_id, desc, sev in detectors:
        click.echo(f"{det_id}: {desc} [{sev}]")


if __name__ == "__main__":
    main()
