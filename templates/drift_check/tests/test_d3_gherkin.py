"""Unit tests for D3 detector (Gherkin / TC-XX / tests/ count consistency)."""

from __future__ import annotations

from pathlib import Path

from drift_check.adapters.asset_radar import AssetRadarAdapter
from drift_check.adapters.base import SpecLocation
from drift_check.detectors.common import Severity
from drift_check.detectors.d3_gherkin import detect


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _spec_md_with_n_gherkin(n: int) -> str:
    """Build a spec.md containing N Scenario + Scenario Outline blocks."""
    blocks: list[str] = []
    for i in range(n):
        kind = "Scenario" if i % 2 == 0 else "Scenario Outline"
        blocks.append(
            f"{kind}: demo scenario #{i + 1}\n"
            "\n"
            "Given a precondition\n"
            "When an action\n"
            "Then an outcome\n"
        )
    return (
        "# SPEC — demo\n"
        "\n"
        "> **版本:** v1.0.0\n"
        "\n"
        "## 0. 元数据\n"
        "\n"
        "## 3. Gherkin 场景\n"
        "\n"
        + "\n".join(blocks)
    )


def _tasks_md_with_n_tc(n: int) -> str:
    """Build a tasks.md with N TC-XX markers (no other task ids)."""
    lines: list[str] = ["# TASKS — demo", "", "> **版本:** v1.0.0", "", "## 任务清单"]
    for i in range(n):
        lines.append(f"- [ ] TC-S{i:02d}-{i + 1:03d} — placeholder")
    return "\n".join(lines) + "\n"


_CHECK_BODY = (
    "# CHECKLIST — demo\n"
    "\n"
    "> **版本:** v1.0.0\n"
    "\n"
    "## 验收\n"
)


def _make_spec(
    spec_dir: Path,
    *,
    gherkin_n: int,
    tc_n: int,
    n_test_files: int = 0,
    create_tests_dir: bool = True,
) -> SpecLocation:
    spec_md = spec_dir / "spec.md"
    tasks_md = spec_dir / "tasks.md"
    check_md = spec_dir / "checklist.md"
    _write(spec_md, _spec_md_with_n_gherkin(gherkin_n))
    _write(tasks_md, _tasks_md_with_n_tc(tc_n))
    _write(check_md, _CHECK_BODY)

    tests_dir = spec_dir / "tests"
    if create_tests_dir:
        tests_dir.mkdir(parents=True, exist_ok=True)
        for i in range(n_test_files):
            _write(tests_dir / f"test_demo_{i + 1}.py", "def test_x():\n    assert True\n")

    return SpecLocation(
        spec_dir=spec_dir,
        spec_md=spec_md,
        tasks_md=tasks_md,
        checklist_md=check_md,
        rel_spec_id=spec_dir.name,
    )


def test_d3_triple_match_returns_empty(tmp_path: Path) -> None:
    """gherkin=2 / tc=2 / test files=2 → [] (all three agree)."""
    spec_dir = tmp_path / ".trae" / "specs" / "spec-00-arch" / "sub-01-aligned"
    spec = _make_spec(spec_dir, gherkin_n=2, tc_n=2, n_test_files=2)
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(spec, adapter)

    assert findings == [], (
        "expected no findings when all three counters agree, "
        f"got: {[f.message for f in findings]}"
    )


def test_d3_count_mismatch_emits_error(tmp_path: Path) -> None:
    """gherkin=3 / tc=2 / test files=3 → 1 ERROR (count_mismatch)."""
    spec_dir = tmp_path / ".trae" / "specs" / "spec-01-relay" / "sub-02-mismatch"
    spec = _make_spec(spec_dir, gherkin_n=3, tc_n=2, n_test_files=3)
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(spec, adapter)

    assert len(findings) == 1, f"expected exactly 1 finding, got {len(findings)}"
    f = findings[0]
    assert f.detector == "D3"
    assert f.severity == Severity.ERROR
    assert f.spec_path == spec.rel_spec_id
    assert f.evidence["kind"] == "count_mismatch"
    assert f.evidence["counts"] == {"gherkin": 3, "tc": 2, "tests": 3}
    assert f.evidence["deltas"] == {
        "spec_vs_tasks": 1,
        "tasks_vs_tests": -1,
        "spec_vs_tests": 0,
    }
    assert "spec=3" in f.message
    assert "tasks=2" in f.message
    assert "tests=3" in f.message


def test_d3_no_gherkin_skips_spec(tmp_path: Path) -> None:
    """gherkin=0 → [] regardless of tc / tests counts (D3 does not apply)."""
    spec_dir = tmp_path / ".trae" / "specs" / "spec-02-runner" / "sub-03-no-gherkin"
    # adapter.parse_gherkin_count returns 0 because spec has no Scenario block.
    spec = _make_spec(spec_dir, gherkin_n=0, tc_n=4, n_test_files=0)
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(spec, adapter)

    assert findings == [], (
        "expected D3 to skip specs with no Gherkin, "
        f"got: {[f.message for f in findings]}"
    )


def test_d3_missing_tests_dir_no_finding(tmp_path: Path) -> None:
    """gherkin=2 / tc=2 / tests dir absent → no finding (v92 design).

    When a spec has no co-located tests/ directory, D3 cannot meaningfully
    check test counts. The spec may have tests in the project-level tests/
    tree instead, which a co-located D3 rule would miss. v92 changed the
    behavior: test_n == 0 → no D3 finding.
    """
    spec_dir = tmp_path / ".trae" / "specs" / "spec-03-cli" / "sub-04-no-tests-dir"
    spec = _make_spec(
        spec_dir, gherkin_n=2, tc_n=2, n_test_files=0, create_tests_dir=False
    )
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(spec, adapter)

    assert findings == [], f"expected no findings, got {len(findings)}"
