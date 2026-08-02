"""Unit tests for D5 detector (lessons-learned.md anchor liveness).

Builds a complete project skeleton under ``tmp_path`` (specs + lessons +
soul.md) and exercises the real ``AssetRadarAdapter`` — no mocking.
"""

from __future__ import annotations

from pathlib import Path


from drift_check.adapters.asset_radar import AssetRadarAdapter
from drift_check.detectors.common import Severity
from drift_check.detectors.d5_lesson_ref import detect


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


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


def _make_spec_set(root: Path, rel_id: str) -> None:
    """Materialise a 3-piece spec set under ``root/.trae/specs/<rel_id>``."""
    spec_dir = root / ".trae" / "specs" / rel_id
    _write(spec_dir / "spec.md", _SPEC_BODY)
    _write(spec_dir / "tasks.md", _TASKS_BODY)
    _write(spec_dir / "checklist.md", _CHECK_BODY)


def _write_soul(root: Path, body: str) -> None:
    _write(root / ".trae" / "rules" / "soul.md", body)


def _write_lessons(root: Path, body: str) -> None:
    _write(root / ".trae" / "rules" / "lessons-learned.md", body)


def _write_agents(root: Path, body: str) -> None:
    _write(root / "AGENTS.md", body)


def _write_decision_log(root: Path, body: str) -> None:
    _write(root / "决策日志.md", body)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_d5_soul_ref_alive_returns_no_findings(tmp_path: Path) -> None:
    """soul.md 引用 §25，lessons-learned.md 含 `## §25` → []."""
    _write_soul(
        tmp_path,
        "# SOUL\n\n引用 §25 这一条作为示例。\n",
    )
    _write_lessons(
        tmp_path,
        "# Lessons\n\n## §25 禁止示例：soul 承载指南段。\n",
    )
    _write_agents(tmp_path, "# AGENTS\n\n占位。\n")
    _make_spec_set(tmp_path, "spec-00-arch/sub-01-demo")

    adapter = AssetRadarAdapter(project_root=tmp_path)
    findings = detect(adapter)

    assert findings == [], (
        "expected no findings for an alive §25 reference, "
        f"got: {[f.message for f in findings]}"
    )


def test_d5_agents_ref_missing_anchor_emits_one_error(tmp_path: Path) -> None:
    """AGENTS.md 引用 §999（不存在）→ 1 ERROR finding。

    soul.md §-refs are intentionally NOT scanned.
    """
    _write_soul(tmp_path, "# SOUL\n\n内部章节 §3.4 与 §6.2 无关 lessons。\n")
    _write_lessons(
        tmp_path,
        "# Lessons\n\n## §25 禁止示例：soul 承载指南段。\n",
    )
    _write_agents(tmp_path, "# AGENTS\n\n引用 lessons §999 这条尚未落地的教训。\n")
    _make_spec_set(tmp_path, "spec-00-arch/sub-01-demo")

    adapter = AssetRadarAdapter(project_root=tmp_path)
    findings = detect(adapter)

    assert len(findings) == 1, f"expected 1 finding, got {len(findings)}"
    f = findings[0]
    assert f.detector == "D5"
    assert f.severity == Severity.ERROR
    assert f.evidence["kind"] == "dangling_ref"
    assert f.evidence["ref"] == "§999"
    assert "§999" in f.message


def test_d5_two_sources_missing_anchor_merges_into_one_finding(
    tmp_path: Path,
) -> None:
    """AGENTS.md + spec.md 都引用 §14，但 lessons-learned.md 缺 §14 → 1 ERROR finding。

    Note: soul.md is intentionally NOT scanned (its §-prefixed numbers are
    internal section navigation, not lessons references).

    evidence.from_files 包含 2 个文件，**不**是 2 个 finding。
    """
    _write_agents(tmp_path, "# AGENTS\n\nsee lessons §14\n")
    _write_lessons(
        tmp_path,
        "# Lessons\n\n## §25 禁止示例：soul 承载指南段。\n",
    )
    _make_spec_set(tmp_path, "spec-00-arch/sub-01-demo")
    # Append a §14 reference to the spec.md body so it joins the grouping.
    spec_md = tmp_path / ".trae" / "specs" / "spec-00-arch" / "sub-01-demo" / "spec.md"
    spec_md.write_text(_SPEC_BODY + "\n引用 lessons §14。\n", encoding="utf-8")

    adapter = AssetRadarAdapter(project_root=tmp_path)
    findings = detect(adapter)

    assert len(findings) == 1, (
        f"expected exactly 1 merged finding, got {len(findings)}: "
        f"{[f.message for f in findings]}"
    )
    f = findings[0]
    assert f.detector == "D5"
    assert f.severity == Severity.ERROR
    assert f.evidence["kind"] == "dangling_ref"
    assert f.evidence["ref"] == "§14"
    from_files = f.evidence["from_files"]
    assert sorted(from_files) == sorted(
        [
            "AGENTS.md",
            "spec-00-arch/sub-01-demo/spec.md",
        ]
    ), f"unexpected from_files: {from_files}"


def test_d5_missing_decision_log_is_silently_skipped(tmp_path: Path) -> None:
    """决策日志.md 不存在 → skip（不 emit 也不 fail）。"""
    # 决策日志.md intentionally NOT written.
    assert not (tmp_path / "决策日志.md").exists()
    _write_soul(tmp_path, "# SOUL\n\nsee §25\n")
    _write_agents(tmp_path, "# AGENTS\n\n占位。\n")
    _write_lessons(
        tmp_path,
        "# Lessons\n\n## §25 禁止示例：soul 承载指南段。\n",
    )
    _make_spec_set(tmp_path, "spec-00-arch/sub-01-demo")

    adapter = AssetRadarAdapter(project_root=tmp_path)
    # Must not raise even though 决策日志.md is absent.
    findings = detect(adapter)

    assert findings == [], (
        "expected no findings when decision log is absent and all "
        f"other refs are alive, got: {[f.message for f in findings]}"
    )


def test_d5_decision_log_present_and_alive_no_findings(tmp_path: Path) -> None:
    """决策日志.md 存在 + 引用 §25 存活 → []。"""
    _write_soul(tmp_path, "# SOUL\n\n占位。\n")
    _write_agents(tmp_path, "# AGENTS\n\n占位。\n")
    _write_lessons(
        tmp_path,
        "# Lessons\n\n## §25 禁止示例：soul 承载指南段。\n",
    )
    _make_spec_set(tmp_path, "spec-00-arch/sub-01-demo")
    _write_decision_log(tmp_path, "# 决策日志\n\nv47 引用 §25 一行。\n")

    adapter = AssetRadarAdapter(project_root=tmp_path)
    findings = detect(adapter)

    assert findings == [], (
        "expected no findings when decision log ref §25 is alive, "
        f"got: {[f.message for f in findings]}"
    )


def test_d5_historical_anchor_silently_skipped(tmp_path: Path) -> None:
    """v8 决策钉死 §1-§13 是历史化锚点 → 引用它们 silent skip（不 emit ERROR）。

    Per lessons-learned.md 第 19 行「§1-§13 是早期项目内具体提醒，不通用」，
    adapter 暴露 historical_lesson_anchors() = {1..13}，D5 detector 匹配
    该集合时 silent skip，不发 dangling_ref ERROR。
    """
    _write_soul(tmp_path, "# SOUL\n\n占位。\n")
    _write_agents(tmp_path, "# AGENTS\n\n引用 lessons §3 是早期项目提醒。\n")
    _write_lessons(
        tmp_path,
        "# Lessons\n\n## §14 起 append-only。\n",  # 不含 §1-§13
    )
    _make_spec_set(tmp_path, "spec-00-arch/sub-01-demo")

    adapter = AssetRadarAdapter(project_root=tmp_path)
    findings = detect(adapter)

    assert findings == [], (
        f"expected historical §3 to be silently skipped, got: "
        f"{[f.message for f in findings]}"
    )


def test_d5_historical_silently_skipped_but_alive_alone(tmp_path: Path) -> None:
    """§3（historical）被 silent skip 同时 §25（alive）也被正常处理 → 0 findings。"""
    _write_soul(tmp_path, "# SOUL\n\n占位。\n")
    _write_agents(
        tmp_path,
        "# AGENTS\n\n引用 lessons §3（历史）以及 lessons §25（当前）。\n",
    )
    _write_lessons(
        tmp_path,
        "# Lessons\n\n## §25 禁止示例。\n",
    )
    _make_spec_set(tmp_path, "spec-00-arch/sub-01-demo")

    adapter = AssetRadarAdapter(project_root=tmp_path)
    findings = detect(adapter)

    assert findings == [], (
        f"expected both §3 (silent skip) and §25 (alive) → 0 findings, got: "
        f"{[f.message for f in findings]}"
    )


def test_d5_uses_asset_radar_adapter_without_mocking(tmp_path: Path) -> None:
    """Hardening: detect() goes through the real adapter — verifies list_specs.

    When the project has 2 spec sets and AGENTS.md cites §25 from each, the
    detector must observe both via list_specs().
    """
    _write_soul(tmp_path, "# SOUL\n\n占位。\n")
    _write_agents(tmp_path, "# AGENTS\n\nsee §25\n")
    _write_lessons(
        tmp_path,
        "# Lessons\n\n## §25 禁止示例：soul 承载指南段。\n",
    )
    _make_spec_set(tmp_path, "spec-00-arch/sub-01-demo")
    _make_spec_set(tmp_path, "spec-01-relay/sub-02-demo")

    # Append §25 reference to both spec.md files.
    for rel_id in ("spec-00-arch/sub-01-demo", "spec-01-relay/sub-02-demo"):
        spec_md = tmp_path / ".trae" / "specs" / rel_id / "spec.md"
        spec_md.write_text(_SPEC_BODY + "\n引用 §25。\n", encoding="utf-8")

    adapter = AssetRadarAdapter(project_root=tmp_path)
    # Adapter itself lists both specs (sanity for "no mock").
    assert len(adapter.list_specs()) == 2
    assert adapter.decision_log_file() is None  # not written here

    findings = detect(adapter)

    assert findings == [], (
        f"expected no findings, got: {[f.message for f in findings]}"
    )