"""Regression tests for the public adapter contract."""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import get_type_hints

from drift_check.adapters.asset_radar import AssetRadarAdapter
from drift_check.adapters.base import ChangelogRow, FieldSpec, SpecAdapter


def test_public_adapter_contract_matches_asset_radar() -> None:
    """The concrete adapter and its public protocol expose one typed contract."""
    field = FieldSpec(
        name="Task",
        field_type="服务",
        required=True,
        source_section="§2 术语表 | kind=class",
        code_map="class Task",
    )
    assert field.field_type == "服务"
    assert get_type_hints(SpecAdapter.parse_changelog_table)["return"] == list[ChangelogRow]
    assert inspect.signature(SpecAdapter.parse_task_code_target) == inspect.signature(
        AssetRadarAdapter.parse_task_code_target
    )


def test_asset_radar_changelog_parser_returns_public_rows(tmp_path: Path) -> None:
    adapter = AssetRadarAdapter(tmp_path)
    rows = adapter.parse_changelog_table(
        "| 版本 | 日期 | 摘要 |\n"
        "| --- | --- | --- |\n"
        "| v1.2.3 | 2026-08-05 | close adapter drift |\n"
    )

    assert rows == [
        ChangelogRow(
            version="v1.2.3",
            date="2026-08-05",
            summary="close adapter drift",
        )
    ]
