"""D2 detector: spec field table <-> BaseModel annotations."""

from __future__ import annotations

import ast

from drift_check.adapters.base import CodeTarget, SpecAdapter, SpecLocation
from drift_check.detectors.common import DriftFinding, Severity


_PYTHON_RESERVED_NAMES = {"model_config"}


def _annotation_text(node: ast.expr | None) -> str:
    return ast.unparse(node) if node is not None else ""


def _extract_basemodel_fields(tree: ast.AST) -> dict[str, dict[str, str]]:
    """Return annotated fields for BaseModel or model_config-bearing classes."""
    models: dict[str, dict[str, str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        is_basemodel = any(
            (isinstance(base, ast.Name) and base.id == "BaseModel")
            or (isinstance(base, ast.Attribute) and base.attr == "BaseModel")
            for base in node.bases
        )
        has_model_config = any(
            isinstance(item, (ast.Assign, ast.AnnAssign))
            and (
                (isinstance(item, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id == "model_config"
                    for target in item.targets
                ))
                or (isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
                    and item.target.id == "model_config")
            )
            for item in node.body
        )
        if not (is_basemodel or has_model_config):
            continue
        fields = {
            item.target.id: _annotation_text(item.annotation)
            for item in node.body
            if isinstance(item, ast.AnnAssign)
            and isinstance(item.target, ast.Name)
            and item.target.id not in _PYTHON_RESERVED_NAMES
        }
        models[node.name] = fields
    return models


def _type_mismatch(expected: str, actual: str) -> bool:
    if expected.lower() in {"枚举", "enum"}:
        return "enum" not in actual.lower()
    if expected.lower() in {"值对象", "basemodel"}:
        return "basemodel" not in actual.lower()
    return False


def detect(
    spec: SpecLocation,
    code_target: CodeTarget,
    adapter: SpecAdapter,
) -> list[DriftFinding]:
    """Compare one spec's §4 fields with one code target's model fields."""
    spec_fields = [
        field
        for field in adapter.parse_field_table(spec.spec_md.read_text(encoding="utf-8"))
        if "kind=field" in field.source_section
    ]
    tree = ast.parse(code_target.py_path.read_text(encoding="utf-8"))
    models = _extract_basemodel_fields(tree)
    code_fields = {
        name: annotation
        for fields in models.values()
        for name, annotation in fields.items()
    }
    spec_by_name = {field.name: field for field in spec_fields}
    findings: list[DriftFinding] = []

    for name in sorted(spec_by_name.keys() - code_fields.keys()):
        findings.append(
            DriftFinding(
                detector="D2b",
                severity=Severity.ERROR,
                spec_path=spec.rel_spec_id,
                message=f"spec field {name!r} missing from code",
                evidence={"kind": "field_missing", "spec_field": name},
            )
        )
    for name in sorted(code_fields.keys() - spec_by_name.keys()):
        findings.append(
            DriftFinding(
                detector="D2b",
                severity=Severity.WARNING,
                spec_path=spec.rel_spec_id,
                message=f"code field {name!r} missing from spec",
                evidence={"kind": "field_extra", "code_field": name},
            )
        )
    for name in sorted(spec_by_name.keys() & code_fields.keys()):
        expected = spec_by_name[name].field_type
        actual = code_fields[name]
        if _type_mismatch(expected, actual):
            findings.append(
                DriftFinding(
                    detector="D2b",
                    severity=Severity.WARNING,
                    spec_path=spec.rel_spec_id,
                    message=f"field {name!r} type mismatch: spec={expected} code={actual}",
                    evidence={
                        "kind": "type_mismatch",
                        "spec_field": name,
                        "expected_type": expected,
                        "actual_type": actual,
                    },
                )
            )
    return findings
