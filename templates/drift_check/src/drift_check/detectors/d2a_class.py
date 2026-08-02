"""D2a: spec §2 class-table vs BaseModel class names.

Reports:
- D2a class_extra  — Class listed in spec §2 but missing from
                     CodeTarget.class_names (likely renamed or never
                     implemented). WARNING severity — reported only,
                     does not block CI.

Notes:
- v208: severity downgraded from ERROR to WARNING. Rationale (decision
  log v209 / lessons §31):
  1. Spec §2 terminology tables often include CamelCase identifiers
     that are *not* Python/JS classes (factory functions like `DI`,
     const objects like `AdapterRegistry`, string enums like
     `WSConnState`, type aliases like `RobotsRule`, HTML files like
     `WebConsole`). Drift-check cannot distinguish "real class" vs
     "spec concept identifier" semantically — the heuristic is
     CamelCase by design.
  2. Drift-check detector expansion (v208) scans src/asset_radar/ +
     src/ai_worker/ + frontend/sdk/ + has `_` prefix whitelist for
     non-class identifiers. The remaining findings after expansion
     are all genuine semantic-layer discrepancies that detector
     cannot resolve (24 items across spec-01 / spec-02 / spec-03
     tracked as accepted warnings).
  3. D1 (version header) and D3 (Gherkin count) remain ERROR — they
     are mechanical checks with clear correct state.

- v210: added `_NON_CLASS_TYPE_LABELS` whitelist for spec §2 `类型` column
  values that unambiguously indicate "non-class concept" — drift-check
  skips these rows regardless of CamelCase identifier. Rationale:
  - Real-data scan (scripts/_tmp/d2a_inspect_20260730.py) confirmed that
    24 remaining D2a warnings cluster into 8 `类型` column values: `UI`
    / `枚举` / `值对象` / `函数` / `包` / `模式` / `标识` / `函数/包`
    (and the same column also contains `服务` / `服务接口` for REAL
    Python classes like MiniMaxClient / WanxiangClient — those are
    excluded from the whitelist to avoid hiding genuine missing-class
    drift).
  - Whitelisted labels: `UI` / `枚举` / `值对象` / `函数` / `函数/包` /
    `包` / `模式` / `标识`. Real classes written under these labels
    (none currently exist in the codebase) would be silently skipped
    by drift-check — by design: a class under `枚举`/`值对象` etc. is
    a contradiction that should be resolved via spec-side cleanup,
    not detector false-positive tolerance.
  - Decision log v210 / user-approved H-path / lessons §30 (real-data
    scan before detector change).

- v211: J+K combined upgrade — both JS scanner expansion and code_map
  column semantic-layer whitelist.
  - J path: `list_all_class_names()` in `asset_radar.py` extended to
    scan JS `const X = {...}` / `let X = {...}` / `var X = {...}`
    object literals (was: only `class X` / `export class X`). This
    matches spec-02 `AdapterRegistry` against `frontend/sdk/platforms/
    registry.js` `const AdapterRegistry = {...}` (2 findings resolved).
  - K path: added `_NON_CLASS_CODE_MAP_PATTERNS` whitelist (9 substring
    patterns) — `argparse subparsers` / `本 spec §` / `父 spec §` /
    `createRedactedConsole` / `deps.py::` / `\`class TableFormatter\`` /
    `factory` / `.html` / `.js`. These match real-data scan of remaining
    8 D2a warnings' `代码映射` column values (scripts/_tmp/
    inspect_code_map_20260730.py).
  - Schema: `FieldSpec` gains optional `code_map: str = ""` field
    (base.py); `parse_field_table()` extracts it from spec table's
    `代码映射` / `Code Map` / `code_map` / `映射` / `mapping` column
    or falls back to last column.
  - Decision log v211 / user-approved L-path / lessons §30 (real-data
    scan before detector change).

- We DO NOT emit `class_missing` (code has class X but spec §2 doesn't list
  it). Spec §2 is a *subset declaration*, not a complete enumeration — each
  sub-spec only documents the classes it owns. Reporting class_missing per
  sub-spec would falsely flag every spec for not listing every BaseModel in
  the codebase. See lessons §31 / v92 for the design rationale.
"""
from __future__ import annotations
from collections.abc import Iterable
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from drift_check.adapters.asset_radar import FieldSpec
from drift_check.detectors.common import DriftFinding, Severity


_CLASS_KIND_MARKER = "kind=class"

# Spec §2 `类型` column labels that mean "this is not a real class".
# Source: real-data scan of 24 remaining D2a warnings (scripts/_tmp/
# d2a_inspect_20260730.py). Excludes `服务` / `服务接口` because those
# ALSO label real Python classes (MiniMaxClient / WanxiangClient / etc.).
_NON_CLASS_TYPE_LABELS: frozenset[str] = frozenset({
    "UI",          # HTML files (e.g. WebConsole)
    "枚举",         # string-literal enums (e.g. WSConnState / WSMessageType)
    "值对象",       # const objects / string values (e.g. AmazonListingPage)
    "函数",         # factory functions
    "函数/包",      # factory function or package (e.g. Relay)
    "包",          # Python package
    "模式",         # FastAPI dependency-function aggregation (e.g. DI)
    "标识",         # string field-value identifier (e.g. ASIN)
})

# Spec §2 `代码映射` column content signatures that mean "this spec row
# refers to a non-class code entity". Source: real-data scan of 24 D2a
# warnings (scripts/_tmp/inspect_code_map_20260730.py). Each substring
# pattern matched against the row's code_map column; if matched, the row
# is skipped regardless of CamelCase identifier shape. Patterns:
# - argparse subparsers           — argparse concept (SubCommand)
# - 本 spec §                     — cross-spec reference (RobotsCache etc.)
# - 父 spec §                     — cross-spec reference (AmazonListingPage etc.)
# - createRedactedConsole         — factory-function invocation (LogContext)
# - deps.py::                     — FastAPI dependency-function (DI)
# - `class TableFormatter`        — spec abstract name vs concrete impl name
#   (Formatter — the row refers to abstract concept, concrete classes
#   are TableFormatter / JsonFormatter, the row's code_map already
#   disambiguates this)
# - factory                        — generic factory-pattern reference
# - HTML 文件 / .html              — HTML file pointer (WebConsole)
# - .js                            — JS source file pointer (RedactedConsole)
_NON_CLASS_CODE_MAP_PATTERNS: tuple[str, ...] = (
    "argparse subparsers",
    "本 spec §",
    "父 spec §",
    "createRedactedConsole",
    "deps.py::",
    "`class TableFormatter`",
    "factory",
    ".html",
    ".js",
)


def _is_class_table(fs: FieldSpec) -> bool:
    return _CLASS_KIND_MARKER in (fs.source_section or "")


def _is_class_name(name: str, field_type: str = "", code_map: str = "") -> bool:
    """Heuristic: spec class-table entries are CamelCase identifiers.

    Excludes snake_case field names. Defensive double-check beyond the
    `kind=class` source_section marker.

    v208: added underscore-prefix whitelist (spec convention for marking
    non-class identifiers like `_AIWorker` package / `_RouterFactory` factory
    function / `_AuthMiddleware` middleware function / `_TaskQueueKey`
    literal — all per spec-05-ai convention adopted in v0.3.0 drift-cleanup).
    Returns False for names starting with `_` so D2a skips them.

    v210: added `_NON_CLASS_TYPE_LABELS` whitelist — if the row's `类型`
    column matches a known non-class label (UI / 枚举 / 值对象 / 函数 /
    包 / 模式 / 标识), the row is skipped regardless of CamelCase shape.
    Real classes written under these labels would be silently skipped —
    by design (lessons §30 / v210).

    v211: added `_NON_CLASS_CODE_MAP_PATTERNS` whitelist — if the row's
    `代码映射` column contains any of the known non-class code-entity
    patterns (argparse subparsers / 本 spec § / 父 spec § / factory /
    .html / .js / etc.), the row is skipped. Real classes whose code_map
    accidentally contains these substrings would be silently skipped —
    by design (lessons §30 / v211).
    """
    if not name:
        return False
    if name.startswith("_"):
        return False
    if field_type and field_type in _NON_CLASS_TYPE_LABELS:
        return False
    if code_map:
        for pat in _NON_CLASS_CODE_MAP_PATTERNS:
            if pat in code_map:
                return False
    return name[0].isalpha() and name[0].upper() == name[0]


class D2aClassDetector:
    """Detects spec §2 class table -> code class drift (subset semantics)."""

    detector_id = "D2a"

    def detect(
        self,
        spec_id: str,
        spec_path: Path,
        field_specs: Iterable[FieldSpec],
        code_target_class_names: Iterable[str],
    ) -> list[DriftFinding]:
        spec_classes = sorted(
            {
                fs.name
                for fs in field_specs
                if _is_class_table(fs) and _is_class_name(fs.name, fs.field_type, fs.code_map)
            }
        )
        code_classes = sorted({n for n in code_target_class_names if n})
        code_set = set(code_classes)
        # spec_set retained for future class_missing detector (lessons §31: spec
        # §2 is subset declaration, not full enum — kept for future use).
        _spec_set = set(spec_classes)

        findings: list[DriftFinding] = []

        # class_extra: in spec but not in code — WARNING (v208; was ERROR).
        # See module docstring for rationale. Spec §2 class table is often
        # polluted by spec-concept CamelCase identifiers that aren't real
        # classes; detector expansion + _-prefix whitelist (v208) + type
        # column whitelist (v210) already covers most cases, but the
        # remaining items are semantic-layer discrepancies that must be
        # resolved manually via spec-side fixes (rename to `_*` prefix /
        # delete row / accept warning).
        for cls in spec_classes:
            if cls not in code_set:
                findings.append(
                    DriftFinding(
                        detector=self.detector_id,
                        severity=Severity.WARNING,
                        spec_path=str(spec_path),
                        message=(
                            f"class {cls!r} listed in spec §2 class table but "
                            f"not declared in code"
                        ),
                        evidence={
                            "kind": "class_extra",
                            "spec_class": cls,
                            "code_classes": code_classes,
                            "spec_id": spec_id,
                        },
                    )
                )

        return findings


__all__ = ["D2aClassDetector", "_NON_CLASS_TYPE_LABELS"]