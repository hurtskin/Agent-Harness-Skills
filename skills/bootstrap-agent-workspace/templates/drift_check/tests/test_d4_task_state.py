"""Unit tests for D4 task_state vs source detector."""

from __future__ import annotations

from pathlib import Path


from drift_check.adapters.asset_radar import AssetRadarAdapter
from drift_check.adapters.base import SpecLocation
from drift_check.detectors.common import Severity
from drift_check.detectors.d4_task_state import detect


def _make_spec(tmp_path: Path, tasks_body: str) -> SpecLocation:
    spec_dir = tmp_path / ".trae" / "specs" / "spec-x"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "spec.md").write_text("# SPEC\n", encoding="utf-8")
    (spec_dir / "tasks.md").write_text(tasks_body, encoding="utf-8")
    (spec_dir / "checklist.md").write_text("# CL\n", encoding="utf-8")
    return SpecLocation(
        spec_dir=spec_dir,
        spec_md=spec_dir / "spec.md",
        tasks_md=spec_dir / "tasks.md",
        checklist_md=spec_dir / "checklist.md",
        rel_spec_id="spec-x",
    )


def _write_py(path: Path, body: str = "class Foo:\n    pass\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_d4_done_state_with_existing_code_returns_empty(tmp_path: Path) -> None:
    """Test 1: ✅ T-sub 指向 src/xxx.py 存在 → []"""
    src = tmp_path / "src" / "foo.py"
    _write_py(src)
    tasks = "✅ T-sub01-01: do something in src/foo.py\n"
    spec = _make_spec(tmp_path, tasks)
    adapter = AssetRadarAdapter(tmp_path)
    findings = detect(spec, adapter)
    assert findings == [], f"expected no findings, got {findings}"


def test_d4_done_state_missing_code_emits_error(tmp_path: Path) -> None:
    """Test 2: ✅ T-sub 指向 src/xxx.py 不存在 → 1 ERROR phantom_done"""
    tasks = "✅ T-sub01-02: do something in src/ghost.py\n"
    spec = _make_spec(tmp_path, tasks)
    adapter = AssetRadarAdapter(tmp_path)
    findings = detect(spec, adapter)
    assert len(findings) == 1
    assert findings[0].severity == Severity.ERROR
    assert findings[0].evidence["kind"] == "phantom_done"
    assert findings[0].evidence["task_id"] == "T-sub01-02"


def test_d4_pending_state_with_existing_code_emits_error(tmp_path: Path) -> None:
    """Test 3: ⏳ T-sub 指向 src/xxx.py 存在 → 1 ERROR phantom_pending"""
    src = tmp_path / "src" / "bar.py"
    _write_py(src)
    tasks = "⏳ T-sub01-03: do something in src/bar.py\n"
    spec = _make_spec(tmp_path, tasks)
    adapter = AssetRadarAdapter(tmp_path)
    findings = detect(spec, adapter)
    assert len(findings) == 1
    assert findings[0].severity == Severity.ERROR
    assert findings[0].evidence["kind"] == "phantom_pending"


def test_d4_pending_state_without_code_target_emits_warning(tmp_path: Path) -> None:
    """Test 4: ⏳ T-sub 但 parse_task_code_target 返回 None → 1 WARNING"""
    tasks = "⏳ T-sub01-04: pending without file path\n"
    spec = _make_spec(tmp_path, tasks)
    adapter = AssetRadarAdapter(tmp_path)
    findings = detect(spec, adapter)
    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    assert findings[0].evidence["kind"] == "task_target_unknown"


def test_d4_done_state_with_empty_code_file_emits_warning(tmp_path: Path) -> None:
    """Test 5: ✅ T-sub 指向 src/xxx.py 存在但文件为空 → 1 WARNING empty_code_file"""
    src = tmp_path / "src" / "empty.py"
    _write_py(src, body="# only a comment\n")
    tasks = "✅ T-sub01-05: done in src/empty.py\n"
    spec = _make_spec(tmp_path, tasks)
    adapter = AssetRadarAdapter(tmp_path)
    findings = detect(spec, adapter)
    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    assert findings[0].evidence["kind"] == "empty_code_file"


def test_d4_done_state_with_empty_init_py_skips_check(tmp_path: Path) -> None:
    """Test 6: ✅ T-sub 指向 src/__init__.py（空） → 0 findings（package marker 跳过）"""
    src = tmp_path / "src" / "pkg" / "__init__.py"
    src.parent.mkdir(parents=True)
    src.write_text("", encoding="utf-8")
    tasks = "✅ T-sub01-06: done in src/pkg/__init__.py\n"
    spec = _make_spec(tmp_path, tasks)
    adapter = AssetRadarAdapter(tmp_path)
    findings = detect(spec, adapter)
    assert findings == [], (
        f"__init__.py should be skipped (package marker), got "
        f"{[f.evidence.get('kind') for f in findings]}"
    )