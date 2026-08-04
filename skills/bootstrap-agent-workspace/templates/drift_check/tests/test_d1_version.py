"""Unit tests for D1 detector (spec three-piece set version sync)."""

from __future__ import annotations

from pathlib import Path

import pytest

from drift_check.adapters.asset_radar import AssetRadarAdapter
from drift_check.adapters.base import SpecLocation
from drift_check.detectors.common import Severity
from drift_check.detectors.d1_version import detect


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


_SPEC_BODY = (
    "# SPEC — demo\n"
    "\n"
    "> **版本:** v1.0.0\n"
    "\n"
    "## 0. 元数据\n"
    "\n"
    "占位段。\n"
)

_TASKS_BODY = (
    "# TASKS — demo\n"
    "\n"
    "> **版本:** v1.0.0\n"
    "\n"
    "## 任务清单\n"
)

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
    spec_body: str = _SPEC_BODY,
    tasks_body: str = _TASKS_BODY,
    check_body: str = _CHECK_BODY,
) -> SpecLocation:
    spec_md = spec_dir / "spec.md"
    tasks_md = spec_dir / "tasks.md"
    check_md = spec_dir / "checklist.md"
    _write(spec_md, spec_body)
    _write(tasks_md, tasks_body)
    _write(check_md, check_body)
    return SpecLocation(
        spec_dir=spec_dir,
        spec_md=spec_md,
        tasks_md=tasks_md,
        checklist_md=check_md,
        rel_spec_id=spec_dir.name,
    )


def test_d1_three_versions_match_returns_empty(tmp_path: Path) -> None:
    """3 files with identical v1.0.0 → no findings."""
    spec_dir = tmp_path / ".trae" / "specs" / "spec-00-arch" / "sub-01-demo"
    spec = _make_spec(spec_dir)
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(spec, adapter)

    assert findings == [], (
        "expected no findings for matching versions, "
        f"got: {[f.message for f in findings]}"
    )


def test_d1_version_mismatch_emits_error(tmp_path: Path) -> None:
    """spec=v1.0.0 / tasks=v1.0.1 / checklist=v1.0.0 → 1 ERROR finding."""
    spec_dir = tmp_path / ".trae" / "specs" / "spec-01-relay" / "sub-02-mismatch"
    spec = _make_spec(
        spec_dir,
        tasks_body=(
            "# TASKS — demo\n"
            "\n"
            "> **版本:** v1.0.1\n"
            "\n"
            "## 任务清单\n"
        ),
    )
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(spec, adapter)

    assert len(findings) == 1, f"expected 1 finding, got {len(findings)}"
    f = findings[0]
    assert f.detector == "D1"
    assert f.severity == Severity.ERROR
    assert f.spec_path == spec.rel_spec_id
    assert "spec=v1.0.0" in f.message
    assert "tasks=v1.0.1" in f.message
    assert "checklist=v1.0.0" in f.message
    assert f.evidence["kind"] == "version_mismatch"
    assert f.evidence["versions"] == {
        "spec": "v1.0.0",
        "tasks": "v1.0.1",
        "checklist": "v1.0.0",
    }


def test_d1_missing_version_emits_warning(tmp_path: Path) -> None:
    """tasks.md 缺 **版本:** 字段 → 1 WARNING finding (not error)."""
    spec_dir = tmp_path / ".trae" / "specs" / "spec-02-runner" / "sub-03-no-version"
    spec = _make_spec(
        spec_dir,
        tasks_body=(
            "# TASKS — demo\n"
            "\n"
            "## 任务清单\n"
            "\n"
            "- [ ] T-sub03-01\n"
        ),
    )
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(spec, adapter)

    assert len(findings) == 1, f"expected 1 finding, got {len(findings)}"
    f = findings[0]
    assert f.detector == "D1"
    assert f.severity == Severity.WARNING
    assert f.spec_path == spec.rel_spec_id
    assert "tasks.md" in f.message
    assert "unknown" in f.message
    assert f.evidence["kind"] == "version_unknown"
    assert f.evidence["files"] == ["tasks.md"]
    assert f.evidence["versions"]["tasks"] == "unknown"


def test_d1_normalizes_v_prefix_and_case(tmp_path: Path) -> None:
    """V/case differences still match (v1.0.0 == V1.0.0 == 1.0.0)."""
    spec_dir = tmp_path / ".trae" / "specs" / "spec-03-cli" / "sub-04-case"
    spec = _make_spec(
        spec_dir,
        spec_body=(
            "# SPEC — demo\n"
            "\n"
            "> **版本:** V1.0.0\n"
        ),
        tasks_body=(
            "# TASKS — demo\n"
            "\n"
            "> **版本:** v1.0.0\n"
        ),
        check_body=(
            "# CHECKLIST — demo\n"
            "\n"
            "> **版本:** 1.0.0\n"
        ),
    )
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(spec, adapter)

    assert findings == [], (
        "expected normalization to treat all three as equal, "
        f"got: {[f.message for f in findings]}"
    )


def test_d1_missing_spec_md_raises(tmp_path: Path) -> None:
    """Hardening: a malformed SpecLocation with no spec.md file surfaces OSError."""
    spec_dir = tmp_path / "broken"
    bad = SpecLocation(
        spec_dir=spec_dir,
        spec_md=spec_dir / "spec.md",  # does not exist
        tasks_md=spec_dir / "tasks.md",
        checklist_md=spec_dir / "checklist.md",
        rel_spec_id="broken",
    )
    # Need to satisfy fixture file existence for tasks/checklist to keep the
    # call simple; otherwise adapter parser surface would change. Here we only
    # assert the detector does not silently swallow file errors.
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "tasks.md").write_text("# TASKS\n", encoding="utf-8")
    (spec_dir / "checklist.md").write_text("# CHECKLIST\n", encoding="utf-8")
    adapter = AssetRadarAdapter(project_root=tmp_path)

    with pytest.raises((FileNotFoundError, OSError)):
        detect(bad, adapter)