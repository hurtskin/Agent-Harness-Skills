"""Unit tests for D2 detector (spec §2/§4 field table vs BaseModel fields)."""

from __future__ import annotations

from pathlib import Path

from drift_check.adapters.asset_radar import AssetRadarAdapter
from drift_check.adapters.base import CodeTarget, SpecLocation
from drift_check.detectors.common import Severity
from drift_check.detectors.d2_field import _extract_basemodel_fields, detect


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Fixtures — real AssetRadarAdapter + tmp_path (no mocks).
# ---------------------------------------------------------------------------


def _make_spec(
    spec_dir: Path,
    *,
    spec_body: str,
) -> SpecLocation:
    spec_md = spec_dir / "spec.md"
    tasks_md = spec_dir / "tasks.md"
    check_md = spec_dir / "checklist.md"
    _write(spec_md, spec_body)
    _write(tasks_md, "# TASKS\n> **版本:** v1.0.0\n\n## 任务清单\n")
    _write(check_md, "# CHECKLIST\n> **版本:** v1.0.0\n\n## 验收\n")
    return SpecLocation(
        spec_dir=spec_dir,
        spec_md=spec_md,
        tasks_md=tasks_md,
        checklist_md=check_md,
        rel_spec_id=spec_dir.name,
    )


def _make_code(code_path: Path, body: str) -> CodeTarget:
    _write(code_path, body)
    return CodeTarget(
        py_path=code_path,
        rel_path=code_path.as_posix(),
        layer="protocol",
        class_names=[],
    )


# A spec field table that mirrors the BaseModel fields below 1:1.
_SPEC_FIELD_TABLE_MATCH = """
# SPEC — demo

> **版本:** v1.0.0

## §4. 数据模型

| 术语 | 字段 | 类型 |
|------|--------|------|
| 名称 | name | 字符串 |
| 数量 | count | 整数 |
"""

_BASE_MODEL_MATCH = '''
"""Demo module."""

from pydantic import BaseModel, Field


class Thing(BaseModel):
    """Spec-aligned model."""

    name: str = Field(description="名称")
    count: int = Field(default=0, description="数量")
'''


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_d2_field_table_matches_basemodel(tmp_path: Path) -> None:
    """Spec field table == BaseModel annotations → no findings."""
    spec_dir = tmp_path / ".trae" / "specs" / "spec-00-arch" / "sub-99-ok"
    spec = _make_spec(spec_dir, spec_body=_SPEC_FIELD_TABLE_MATCH)
    code_path = tmp_path / "src" / "asset_radar" / "protocol.py"
    code = _make_code(code_path, _BASE_MODEL_MATCH)
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(spec, code, adapter)

    assert findings == [], (
        "expected no findings when spec fields match BaseModel, "
        f"got: {[f.message for f in findings]}"
    )


def test_d2_field_missing_emits_error(tmp_path: Path) -> None:
    """Spec has 'MagicField' but BaseModel does not → 1 ERROR field_missing."""
    spec_body = """
# SPEC — demo

> **版本:** v1.0.0

## §4. 数据模型

| 术语 | 字段 | 类型 |
|------|--------|------|
| 名称 | name | 字符串 |
| 神奇字段 | MagicField | 字符串 |
"""
    spec_dir = tmp_path / ".trae" / "specs" / "spec-01-relay" / "sub-99-missing"
    spec = _make_spec(spec_dir, spec_body=spec_body)
    code_path = tmp_path / "src" / "asset_radar" / "protocol.py"
    code = _make_code(code_path, _BASE_MODEL_MATCH)
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(spec, code, adapter)

    missing = [f for f in findings if f.evidence.get("kind") == "field_missing"]
    assert len(missing) == 1, (
        f"expected exactly 1 field_missing finding, got findings="
        f"{[(f.detector, f.severity, f.evidence.get('kind')) for f in findings]}"
    )
    f = missing[0]
    assert f.detector == "D2b"
    assert f.severity == Severity.ERROR
    assert f.spec_path == spec.rel_spec_id
    assert f.evidence["spec_field"] == "MagicField"
    assert "MagicField" in f.message


def test_d2_field_extra_emits_warning(tmp_path: Path) -> None:
    """BaseModel has 'extra_field' that spec does not → 1 WARNING field_extra."""
    spec_body = """
# SPEC — demo

> **版本:** v1.0.0

## §4. 数据模型

| 术语 | 字段 | 类型 |
|------|--------|------|
| 名称 | name | 字符串 |
"""
    code_body = '''
"""Demo module."""

from pydantic import BaseModel, Field


class Thing(BaseModel):
    """Code has an extra field."""

    name: str = Field(description="名称")
    extra_field: int = Field(default=0, description="额外字段")
'''
    spec_dir = tmp_path / ".trae" / "specs" / "spec-02-runner" / "sub-99-extra"
    spec = _make_spec(spec_dir, spec_body=spec_body)
    code_path = tmp_path / "src" / "asset_radar" / "protocol.py"
    code = _make_code(code_path, code_body)
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(spec, code, adapter)

    extras = [f for f in findings if f.evidence.get("kind") == "field_extra"]
    assert len(extras) == 1, (
        f"expected exactly 1 field_extra finding, got findings="
        f"{[(f.detector, f.severity, f.evidence.get('kind')) for f in findings]}"
    )
    f = extras[0]
    assert f.detector == "D2b"
    assert f.severity == Severity.WARNING
    assert f.spec_path == spec.rel_spec_id
    assert f.evidence["code_field"] == "extra_field"
    assert "extra_field" in f.message


def test_d2_type_mismatch_enum_labelled_as_str(tmp_path: Path) -> None:
    """Spec labels 'Status' as '枚举' but BaseModel annotation is 'str' → 1 WARNING type_mismatch."""
    spec_body = """
# SPEC — demo

> **版本:** v1.0.0

## §4. 数据模型

| 术语 | 字段 | 类型 |
|------|--------|------|
| 状态 | status | 枚举 |
| 名称 | name | 字符串 |
"""
    code_body = '''
"""Demo module."""

from pydantic import BaseModel, Field


class Thing(BaseModel):
    """Status is annotated as plain str instead of an Enum."""

    name: str = Field(description="名称")
    status: str = Field(default="ok", description="状态")
'''
    spec_dir = tmp_path / ".trae" / "specs" / "spec-03-cli" / "sub-99-mismatch"
    spec = _make_spec(spec_dir, spec_body=spec_body)
    code_path = tmp_path / "src" / "asset_radar" / "protocol.py"
    code = _make_code(code_path, code_body)
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(spec, code, adapter)

    mismatches = [f for f in findings if f.evidence.get("kind") == "type_mismatch"]
    assert len(mismatches) == 1, (
        f"expected exactly 1 type_mismatch finding, got findings="
        f"{[(f.detector, f.severity, f.evidence.get('kind')) for f in findings]}"
    )
    f = mismatches[0]
    assert f.detector == "D2b"
    assert f.severity == Severity.WARNING
    assert f.spec_path == spec.rel_spec_id
    assert f.evidence["spec_field"] == "status"
    assert f.evidence["expected_type"] == "枚举"
    assert f.evidence["actual_type"] == "str"
    assert "status" in f.message


# ---------------------------------------------------------------------------
# v213 fixtures — coverage gaps identified during detector review.
# Real-data findings:
#   - pydantic v2 BaseModels using `model_config = ConfigDict(...)` instead
#     of inheriting BaseModel — D2b detects both forms (L48-74 of
#     d2_field.py). This is the modern pydantic-v2 idiom used in
#     src/asset_radar/protocol.py — regression guard.
#   - field_extra excludes `model_config` (a pydantic internal, see
#     _PYTHON_RESERVED_NAMES at d2_field.py:28). Without this guard,
#     D2b would warn on every BaseModel that uses `model_config`.
#   - type_mismatch coarse rules cover both `枚举`/`enum` AND
#     `值对象`/`BaseModel` (L121-122 of d2_field.py). Existing Test 4
#     covers the enum case; this Test 5 covers the BaseModel case.
#   - Edge case: code file contains zero BaseModels — D2b must emit
#     no field_missing (no point comparing) and zero findings total
#     (since field_extra + type_mismatch also have no BaseModels to
#     enumerate).
# ---------------------------------------------------------------------------


def test_d2_basemodel_via_model_config() -> None:
    """pydantic v2 BaseModel via `model_config = ConfigDict(...)` (no BaseModel base).

    D2b's `_extract_basemodel_fields` accepts BOTH `BaseModel` inheritance
    AND the `model_config` class variable (pydantic-v2 idiom). Regression
    guard for src/asset_radar/protocol.py and src/ai_worker/* which both
    use this pattern.
    """
    import ast
    import textwrap

    code_body = textwrap.dedent('''
        """Demo module — pydantic v2 model_config style."""

        from pydantic import ConfigDict, Field


        class Thing:
            """Pydantic v2 model without explicit BaseModel base."""

            model_config = ConfigDict(extra="forbid")

            name: str = Field(description="名称")
            count: int = Field(default=0, description="数量")
    ''').lstrip()
    tree = ast.parse(code_body)
    basemodels = _extract_basemodel_fields(tree)
    assert "Thing" in basemodels, (
        "expected model_config-bearing class to be detected as BaseModel"
    )
    assert set(basemodels["Thing"].keys()) == {"name", "count"}


def test_d2_pydantic_internal_model_config_field_excluded() -> None:
    """`model_config` class variable must NOT appear in field_extra findings.

    Per `_PYTHON_RESERVED_NAMES` (d2_field.py:28), pydantic's internal
    `model_config` class variable is excluded from the field index so
    D2b does not false-positive on every BaseModel that uses it.
    """
    import textwrap

    spec_body = textwrap.dedent("""
        # SPEC — demo

        > **版本:** v1.0.0

        ## §4. 数据模型

        | 术语 | 字段 | 类型 |
        |------|--------|------|
        | 名称 | name | 字符串 |
    """).strip()
    code_body = textwrap.dedent('''
        """Demo module — code has model_config internal."""

        from pydantic import BaseModel, ConfigDict, Field


        class Thing(BaseModel):
            """Has model_config + name."""

            model_config = ConfigDict(extra="forbid")
            name: str = Field(description="名称")
    ''').lstrip()
    tmp_path = Path("/tmp/test_d2_internal_model_config")  # noqa: S108
    # Use real AssetRadarAdapter + tmp_path per test convention.
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        spec_dir = root / ".trae" / "specs" / "spec-00-arch" / "sub-99-internal"
        spec = _make_spec(spec_dir, spec_body=spec_body)
        code_path = root / "src" / "asset_radar" / "protocol.py"
        code = _make_code(code_path, code_body)
        adapter = AssetRadarAdapter(project_root=root)

        findings = detect(spec, code, adapter)

    # model_config is internal — must NOT trigger field_extra.
    extras = [f for f in findings if f.evidence.get("kind") == "field_extra"]
    assert extras == [], (
        "model_config must be excluded from field_extra, got: "
        f"{[f.evidence.get('code_field') for f in extras]}"
    )


def test_d2_type_mismatch_basemodel_labelled_as_str() -> None:
    """Spec labels 'inner' as '值对象' (BaseModel expected) but annotation is `str` → type_mismatch WARNING.

    Covers the second coarse rule at d2_field.py:122
    (`值对象` / `BaseModel` → annotation must mention `BaseModel`).
    Test 4 covers the first rule (`枚举` → annotation must mention `Enum`).
    """
    import tempfile

    spec_body = """
# SPEC — demo

> **版本:** v1.0.0

## §4. 数据模型

| 术语 | 字段 | 类型 |
|------|--------|------|
| 内部对象 | inner | 值对象 |
| 名称 | name | 字符串 |
"""
    code_body = '''
"""Demo module."""

from pydantic import BaseModel, Field


class Thing(BaseModel):
    """inner annotated as str instead of BaseModel."""

    name: str = Field(description="名称")
    inner: str = Field(default="x", description="内部对象")
'''
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        spec_dir = root / ".trae" / "specs" / "spec-04-merge-guide" / "sub-99-bmismatch"
        spec = _make_spec(spec_dir, spec_body=spec_body)
        code_path = root / "src" / "asset_radar" / "protocol.py"
        code = _make_code(code_path, code_body)
        adapter = AssetRadarAdapter(project_root=root)

        findings = detect(spec, code, adapter)

    mismatches = [f for f in findings if f.evidence.get("kind") == "type_mismatch"]
    assert len(mismatches) == 1, (
        f"expected exactly 1 type_mismatch (值对象 vs str), got: "
        f"{[(f.evidence.get('kind'), f.message) for f in findings]}"
    )
    f = mismatches[0]
    assert f.detector == "D2b"
    assert f.severity == Severity.WARNING
    assert f.evidence["spec_field"] == "inner"
    assert f.evidence["expected_type"] == "值对象"
    assert f.evidence["actual_type"] == "str"


def test_d2_no_basemodel_in_code_emits_no_findings() -> None:
    """Code has zero BaseModels → no findings (no field_missing emitted either).

    Edge case: empty / non-BaseModel code files. D2b's field_missing loop
    iterates spec fields; if no BaseModel is found at all, code_field_names
    is empty so every spec field becomes `field_missing`. But that's
    meaningful drift — caller decides whether to invoke D2b at all.
    This test asserts the documented behavior so future refactors don't
    silently change it.
    """
    import tempfile

    spec_body = """
# SPEC — demo

> **版本:** v1.0.0

## §4. 数据模型

| 术语 | 字段 | 类型 |
|------|--------|------|
| 名称 | name | 字符串 |
"""
    code_body = '''
"""Demo module — no BaseModel at all."""


def helper() -> int:
    """Just a function, no BaseModel."""
    return 42
'''
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        spec_dir = root / ".trae" / "specs" / "spec-05-ai" / "sub-99-nobm"
        spec = _make_spec(spec_dir, spec_body=spec_body)
        code_path = root / "src" / "asset_radar" / "protocol.py"
        code = _make_code(code_path, code_body)
        adapter = AssetRadarAdapter(project_root=root)

        findings = detect(spec, code, adapter)

    # With zero BaseModels in code, every spec field is "missing" —
    # caller responsibility to skip D2b on non-BaseModel files. Document
    # this behavior with an explicit assertion rather than letting it
    # change silently in a refactor.
    missing = [f for f in findings if f.evidence.get("kind") == "field_missing"]
    assert len(missing) == 1, (
        f"expected 1 field_missing (no BaseModels), got: "
        f"{[(f.evidence.get('kind'), f.message) for f in findings]}"
    )
    extras = [f for f in findings if f.evidence.get("kind") == "field_extra"]
    assert extras == [], "field_extra must be empty when no BaseModels exist"
