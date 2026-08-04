"""D3 detector: Gherkin Scenario count <-> test count."""

from __future__ import annotations

import ast
import re

from drift_check.adapters.base import SpecAdapter, SpecLocation
from drift_check.detectors.common import DriftFinding, Severity


def _count_tests(spec: SpecLocation) -> int:
    test_dir = spec.spec_dir / "tests"
    if not test_dir.exists():
        return 0
    count = 0
    for path in test_dir.glob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        count += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in ast.walk(tree)
        )
    return count


def detect(spec: SpecLocation, adapter: SpecAdapter) -> list[DriftFinding]:
    """Check Gherkin scenarios, task TC markers, and co-located test functions."""
    spec_text = spec.spec_md.read_text(encoding="utf-8")
    gherkin = adapter.parse_gherkin_count(spec_text)
    if gherkin == 0:
        return []
    tasks_text = spec.tasks_md.read_text(encoding="utf-8")
    tc = len(re.findall(r"\bTC-[A-Za-z0-9_-]+", tasks_text))
    tests = _count_tests(spec)
    if gherkin == tc and (tests == 0 or tests == gherkin):
        return []
    counts = {"gherkin": gherkin, "tc": tc, "tests": tests}
    return [
        DriftFinding(
            detector="D3",
            severity=Severity.ERROR,
            spec_path=spec.rel_spec_id,
            message=f"count mismatch: spec={gherkin} tasks={tc} tests={tests}",
            evidence={
                "kind": "count_mismatch",
                "counts": counts,
                "deltas": {
                    "spec_vs_tasks": gherkin - tc,
                    "tasks_vs_tests": tc - tests,
                    "spec_vs_tests": gherkin - tests,
                },
            },
        )
    ]
