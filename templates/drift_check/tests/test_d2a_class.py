"""Tests for D2aClassDetector — spec §2 class table vs BaseModel classes.

v92: subset semantics. Only `class_extra` (spec lists class but code doesn't
implement) is reported. `class_missing` is dropped because spec §2 is a
subset declaration — sub-specs don't need to enumerate every BaseModel.

v208-v211 detector upgrades also covered here:
- v208 `_` prefix whitelist (underscore-prefixed names like `_AIWorker` skip)
- v208 JS scanner expansion (frontend/sdk/ const / class scan)
- v210 `_NON_CLASS_TYPE_LABELS` whitelist (UI / 枚举 / 值对象 / 函数 /
  函数/包 / 包 / 模式 / 标识 skip)
- v209 severity downgrade ERROR -> WARNING for class_extra
- v211 `_NON_CLASS_CODE_MAP_PATTERNS` whitelist (argparse subparsers /
  本 spec § / 父 spec § / createRedactedConsole / deps.py:: /
  `class TableFormatter` / factory / .html / .js skip)
"""
from pathlib import Path

import pytest

from drift_check.adapters.asset_radar import FieldSpec
from drift_check.detectors.d2a_class import D2aClassDetector


def _fs(
    name: str,
    source_section: str = "2. 术语表 | kind=class",
    field_type: str = "枚举",
    code_map: str = "",
) -> FieldSpec:
    return FieldSpec(
        name=name,
        field_type=field_type,
        required=True,
        default=None,
        source_section=source_section,
        code_map=code_map,
    )


def _spec_id() -> str:
    return "spec-00-arch"


def _spec_path(tmp_path: Path) -> Path:
    return tmp_path / "spec.md"


def test_d2a_class_extra_emits_warning() -> None:
    """Class listed in spec §2 but missing from code emits class_extra WARNING.

    v209: severity downgraded from ERROR to WARNING — D2a's spec §2 class
    table is often polluted by spec-concept CamelCase identifiers
    (factory functions / const objects / string enums) that detector
    cannot semantically distinguish from real classes. Reported as
    WARNING (CI pass) per lessons §31 user-approved decision.

    Note: `ImaginaryClass` uses `field_type="服务"` (NOT in v210 whitelist —
    `服务` is intentionally excluded because it ALSO labels real Python
    classes like MiniMaxClient / WanxiangClient). Without this, the test
    would hit the v210 type-column whitelist and emit no findings.
    """
    det = D2aClassDetector()
    spec_fields = [_fs("Platform"), _fs("ImaginaryClass", field_type="服务")]
    code_names = ["Platform"]
    findings = det.detect(_spec_id(), _spec_path(Path("/tmp")), spec_fields, code_names)
    extras = [f for f in findings if f.evidence["kind"] == "class_extra"]
    assert len(extras) == 1
    assert extras[0].evidence["spec_class"] == "ImaginaryClass"
    assert extras[0].severity.value == "warning"


def test_d2a_class_missing_no_finding() -> None:
    """Code has classes that spec §2 doesn't list — no finding (subset semantics)."""
    det = D2aClassDetector()
    spec_fields = [_fs("Platform"), _fs("TaskConfig")]
    code_names = ["Platform", "TaskConfig", "ImageMeta"]
    findings = det.detect(_spec_id(), _spec_path(Path("/tmp")), spec_fields, code_names)
    # No class_missing emitted (subset semantics — v92 design).
    misses = [f for f in findings if f.evidence["kind"] == "class_missing"]
    assert misses == []


def test_d2a_no_drift() -> None:
    """Identical class lists emit no findings."""
    det = D2aClassDetector()
    spec_fields = [_fs("Platform"), _fs("TaskConfig")]
    code_names = ["Platform", "TaskConfig"]
    findings = det.detect(_spec_id(), _spec_path(Path("/tmp")), spec_fields, code_names)
    assert findings == []


def test_d2a_ignores_non_class_table_rows() -> None:
    """Field-table rows (kind=field) should not contribute to D2a."""
    det = D2aClassDetector()
    spec_fields = [
        _fs("value", source_section="4. 数据模型 | kind=field"),
        _fs("Platform"),
    ]
    code_names = ["Platform"]
    findings = det.detect(_spec_id(), _spec_path(Path("/tmp")), spec_fields, code_names)
    # `value` is not in code_names but it's a field, not a class — should not emit.
    assert findings == []


def test_d2a_ignores_snake_case_in_class_table() -> None:
    """Defensive: snake_case names in class table should be filtered out."""
    det = D2aClassDetector()
    spec_fields = [_fs("Platform"), _fs("task_config_snake")]
    code_names = ["Platform"]
    findings = det.detect(_spec_id(), _spec_path(Path("/tmp")), spec_fields, code_names)
    # `task_config_snake` filtered out — no class_extra.
    assert findings == []


# ---------------------------------------------------------------------------
# v208 detector upgrades
# ---------------------------------------------------------------------------


def test_d2a_underscore_prefix_whitelist_v208() -> None:
    """v208: underscore-prefixed names like `_AIWorker` skip D2a entirely.

    spec-05-ai convention adopted in v0.3.0 drift-cleanup: spec §2 rows
    whose 英文名 starts with `_` are explicitly marked as non-class
    identifiers (packages / factory functions / middleware / literals).
    Real-data source: spec-05 `AIWorker` -> `_AIWorker` etc.
    """
    det = D2aClassDetector()
    spec_fields = [
        _fs("Platform", field_type="枚举"),
        _fs("_AIWorker", field_type="包"),
        _fs("_RouterFactory", field_type="函数"),
    ]
    code_names = ["Platform"]  # `_AIWorker` etc. are NOT in code (whitelist skips)
    findings = det.detect(_spec_id(), _spec_path(Path("/tmp")), spec_fields, code_names)
    extras = [f for f in findings if f.evidence["kind"] == "class_extra"]
    assert extras == []


# ---------------------------------------------------------------------------
# v210 detector upgrades — type column whitelist
# ---------------------------------------------------------------------------


def test_d2a_type_column_whitelist_v210() -> None:
    """v210: spec §2 rows with `类型` column matching known non-class labels
    (UI / 枚举 / 值对象 / 函数 / 函数/包 / 包 / 模式 / 标识) skip D2a.

    Real-data source: scripts/_tmp/d2a_inspect_20260730.py confirmed 24
    D2a warnings cluster into these 8 `类型` column values.
    """
    det = D2aClassDetector()
    code_names: list[str] = []  # none of these exist in code
    # Build rows covering all 8 whitelisted type labels.
    spec_fields = [
        _fs("WebConsole", field_type="UI"),
        _fs("WSConnState", field_type="枚举"),
        _fs("AmazonListingPage", field_type="值对象"),
        _fs("MyFactory", field_type="函数"),
        _fs("Relay", field_type="函数/包"),
        _fs("MyPackage", field_type="包"),
        _fs("DI", field_type="模式"),
        _fs("ASIN", field_type="标识"),
        # Real class without whitelist match → still emitted
        _fs("ImaginaryClass", field_type="服务"),
    ]
    findings = det.detect(_spec_id(), _spec_path(Path("/tmp")), spec_fields, code_names)
    extras = [f for f in findings if f.evidence["kind"] == "class_extra"]
    assert len(extras) == 1
    assert extras[0].evidence["spec_class"] == "ImaginaryClass"


def test_d2a_type_column_keeps_real_class_with_service_label_v210() -> None:
    """v210: `服务` / `服务接口` labels are NOT in the whitelist because
    they ALSO label real Python classes (MiniMaxClient / WanxiangClient
    etc.) — real classes must remain detectable even when their
    `类型` column says 服务. Regression guard for spec-05 services.
    """
    det = D2aClassDetector()
    spec_fields = [
        _fs("MiniMaxClient", field_type="服务"),  # real class missing from code
    ]
    findings = det.detect(_spec_id(), _spec_path(Path("/tmp")), spec_fields, [])
    extras = [f for f in findings if f.evidence["kind"] == "class_extra"]
    assert len(extras) == 1
    assert extras[0].evidence["spec_class"] == "MiniMaxClient"


# ---------------------------------------------------------------------------
# v211 detector upgrades — code_map column whitelist
# ---------------------------------------------------------------------------


def test_d2a_code_map_whitelist_argparse_v211() -> None:
    """v211: spec §2 rows whose `代码映射` column contains `argparse
    subparsers` skip D2a (spec-03 SubCommand concept).
    """
    det = D2aClassDetector()
    spec_fields = [
        _fs("SubCommand", field_type="服务", code_map="argparse subparsers"),
    ]
    findings = det.detect(_spec_id(), _spec_path(Path("/tmp")), spec_fields, [])
    extras = [f for f in findings if f.evidence["kind"] == "class_extra"]
    assert extras == []


def test_d2a_code_map_whitelist_cross_spec_refs_v211() -> None:
    """v211: cross-spec references (`本 spec §` / `父 spec §`) in code_map
    skip D2a — those rows are spec concepts whose details live in
    another spec section, not real class drift (RobotsCache /
    RobotsRule / WSMessageType / AmazonListingPage / ASIN etc.).
    """
    det = D2aClassDetector()
    spec_fields = [
        _fs("RobotsCache", field_type="值对象", code_map="本 spec §1.2"),
        _fs("AmazonListingPage", field_type="值对象", code_map="父 spec §5.2 L188"),
        _fs("WSConnState", field_type="枚举", code_map="父 spec §6.1 L199-221"),
    ]
    findings = det.detect(_spec_id(), _spec_path(Path("/tmp")), spec_fields, [])
    extras = [f for f in findings if f.evidence["kind"] == "class_extra"]
    assert extras == []


def test_d2a_code_map_whitelist_html_js_file_pointer_v211() -> None:
    """v211: HTML / JS file pointers in code_map skip D2a — those rows
    point to a test HTML page (WebConsole) or a JS source file
    (RedactedConsole), not to a Python class.
    """
    det = D2aClassDetector()
    spec_fields = [
        _fs("WebConsole", field_type="UI", code_map="`frontend/tests/web-console.html`"),
        _fs("RedactedConsole", field_type="服务接口", code_map="`frontend/sdk/log-redaction.js`"),
    ]
    findings = det.detect(_spec_id(), _spec_path(Path("/tmp")), spec_fields, [])
    extras = [f for f in findings if f.evidence["kind"] == "class_extra"]
    assert extras == []


def test_d2a_code_map_whitelist_factory_v211() -> None:
    """v211: factory-function pointers (deps.py:: / createRedactedConsole)
    in code_map skip D2a — those rows refer to function calls, not
    class declarations (DI / LogContext).
    """
    det = D2aClassDetector()
    spec_fields = [
        _fs("DI", field_type="模式", code_map="`deps.py::get_store()` / `get_orchestrator()`"),
        _fs("LogContext", field_type="值对象", code_map="`createRedactedConsole` 入参"),
    ]
    findings = det.detect(_spec_id(), _spec_path(Path("/tmp")), spec_fields, [])
    extras = [f for f in findings if f.evidence["kind"] == "class_extra"]
    assert extras == []


def test_d2a_code_map_keeps_real_class_with_class_prefix_v211() -> None:
    """v211: rows whose code_map starts with `class X` are NOT whitelisted
    (the only `class` prefix in the whitelist is `\`class TableFormatter\``
    which targets spec-03 Formatter abstract-name vs concrete-name
    mismatch). A row whose code_map just says `class Foo` must still
    emit class_extra if Foo isn't in code — the `class Foo` substring
    doesn't match any whitelist pattern.
    """
    det = D2aClassDetector()
    spec_fields = [
        _fs("ImaginaryClass", field_type="服务", code_map="`class ImaginaryClass`"),
    ]
    findings = det.detect(_spec_id(), _spec_path(Path("/tmp")), spec_fields, [])
    extras = [f for f in findings if f.evidence["kind"] == "class_extra"]
    assert len(extras) == 1
    assert extras[0].evidence["spec_class"] == "ImaginaryClass"


def test_d2a_combined_v211_real_class_passes_through_all_filters() -> None:
    """v211 combined: a row whose name is CamelCase (not _-prefixed),
    type label is 服务 (not in whitelist), code_map is `class Foo` (not
    in whitelist), but Foo IS in code_names — must NOT emit class_extra."""
    det = D2aClassDetector()
    spec_fields = [
        _fs("MiniMaxClient", field_type="服务", code_map="`class MiniMaxClient`"),
    ]
    findings = det.detect(_spec_id(), _spec_path(Path("/tmp")), spec_fields, ["MiniMaxClient"])
    extras = [f for f in findings if f.evidence["kind"] == "class_extra"]
    assert extras == []