"""drift-check CLI entry point."""

import json
import sys
from pathlib import Path

import click

from drift_check.adapters.asset_radar import AssetRadarAdapter
from drift_check.detectors.common import DriftFinding, Severity
from drift_check.detectors.d1_version import detect as detect_d1
from drift_check.detectors.d2_field import detect as detect_d2
from drift_check.detectors.d3_gherkin import detect as detect_d3
from drift_check.detectors.d4_task_state import detect as detect_d4
from drift_check.detectors.d5_lesson_ref import detect as detect_d5
from drift_check.detectors.d6_bug_sync import detect as detect_d6


@click.group()
def main() -> None:
    """drift-check: spec <-> code drift detector."""


@main.command()
@click.option("--project-root", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--only", multiple=True, help="Run only specific detectors (e.g., --only D1 --only D4)")
def scan(project_root: Path, fmt: str, only: tuple[str, ...]) -> None:
    """Scan project for spec <-> code drift."""
    adapter = AssetRadarAdapter(project_root)

    selected = set(only) if only else {"D1", "D2", "D3", "D4", "D5", "D6"}
    findings: list[DriftFinding] = []
    specs = adapter.list_specs()
    if "D1" in selected:
        for spec in specs:
            findings.extend(detect_d1(spec, adapter))
    if "D2" in selected:
        code_targets = adapter.list_code_targets()
        for spec in specs:
            for target in code_targets:
                findings.extend(detect_d2(spec, target, adapter))
    if "D3" in selected:
        for spec in specs:
            findings.extend(detect_d3(spec, adapter))
    if "D4" in selected:
        for spec in specs:
            findings.extend(detect_d4(spec, adapter))
    if "D5" in selected:
        findings.extend(detect_d5(adapter))
    if "D6" in selected:
        findings.extend(detect_d6(adapter))

    if fmt == "json":
        output = [
            {
                "detector": f.detector,
                "severity": f.severity.value,
                "spec_path": f.spec_path,
                "message": f.message,
                "evidence": f.evidence,
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
            if f.evidence:
                for k, v in f.evidence.items():
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
