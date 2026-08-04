"""Unit tests for D6 detector (bug sub-spec vs parent spec §9.5 changelog sync)."""

from __future__ import annotations

from pathlib import Path


from drift_check.adapters.asset_radar import AssetRadarAdapter
from drift_check.detectors.common import Severity
from drift_check.detectors.d6_bug_sync import detect


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


_SPEC_BODY_TEMPLATE = (
    "# SPEC — {title}\n"
    "\n"
    "> **版本:** v1.0.0\n"
    "\n"
    "## 0. 元数据\n"
    "\n"
    "占位段。\n"
    "\n"
    "## 9.5 变更日志\n"
    "\n"
    "| 版本 | 日期 | 摘要 |\n"
    "| --- | --- | --- |\n"
    "{rows}\n"
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


def _make_parent_spec(
    spec_dir: Path,
    *,
    title: str = "demo",
    rows: list[tuple[str, str, str]],
) -> None:
    """Build a parent spec three-piece set with §9.5 changelog rows."""
    rendered_rows = "\n".join(
        "| {} | {} | {} |".format(ver, date, summary) for ver, date, summary in rows
    )
    _write(spec_dir / "spec.md", _SPEC_BODY_TEMPLATE.format(title=title, rows=rendered_rows))
    _write(spec_dir / "tasks.md", _TASKS_BODY)
    _write(spec_dir / "checklist.md", _CHECK_BODY)


def _make_bug_spec(bug_dir: Path, *, body: str) -> None:
    """Build a bug sub-spec directory with spec.md only."""
    _write(bug_dir / "spec.md", body)


def test_d6_bug_slug_present_in_changelog_returns_empty(tmp_path: Path) -> None:
    """Test 1: bug slug appears in parent §9.5 → no findings."""
    parent_dir = tmp_path / ".trae" / "specs" / "spec-02-runner" / "sub-08-platform"
    _make_parent_spec(
        parent_dir,
        title="platform",
        rows=[
            ("v1.0.0", "2026-07-03", "基线：platform 子 spec 立项"),
            (
                "v1.0.1",
                "2026-07-09",
                "修订：闭合 2026-07-03-platform-docstring-grep-spec-00-01 报告的 docstring 字面量漂移",
            ),
        ],
    )
    bug_dir = tmp_path / ".trae" / "specs" / "bug" / "2026-07-03-platform-docstring-grep-spec-00-01"
    _make_bug_spec(
        bug_dir,
        body=(
            "# BUG — platform docstring grep 漂移\n"
            "\n"
            "> **版本:** v1.0.0\n"
            "\n"
            "父 spec: spec-02-runner/sub-08-platform\n"
            "\n"
            "## 现象\n"
            "\n"
            "占位。\n"
        ),
    )
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(adapter)

    assert findings == [], (
        "expected no findings when bug slug is referenced in changelog, "
        f"got: {[f.message for f in findings]}"
    )


def test_d6_bug_slug_missing_from_changelog_emits_error(tmp_path: Path) -> None:
    """Test 2: bug slug absent from parent §9.5 → 1 ERROR bug_unclosed."""
    parent_dir = tmp_path / ".trae" / "specs" / "spec-02-runner" / "sub-08-platform"
    _make_parent_spec(
        parent_dir,
        title="platform",
        rows=[
            ("v1.0.0", "2026-07-03", "基线：platform 子 spec 立项"),
            ("v1.0.1", "2026-07-09", "修订：其他无关修订"),
        ],
    )
    bug_dir = tmp_path / ".trae" / "specs" / "bug" / "2026-07-03-platform-docstring-grep-spec-00-01"
    _make_bug_spec(
        bug_dir,
        body=(
            "# BUG — platform docstring grep 漂移\n"
            "\n"
            "> **版本:** v1.0.0\n"
            "\n"
            "父 spec: spec-02-runner/sub-08-platform\n"
            "\n"
            "## 现象\n"
            "\n"
            "占位。\n"
        ),
    )
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(adapter)

    assert len(findings) == 1, f"expected 1 finding, got {len(findings)}"
    f = findings[0]
    assert f.detector == "D6"
    assert f.severity == Severity.ERROR
    assert f.spec_path == bug_dir.relative_to(tmp_path).as_posix() + "/spec.md"
    assert "2026-07-03-platform-docstring-grep-spec-00-01" in f.message
    assert "spec-02-runner/sub-08-platform" in f.message
    assert f.evidence["kind"] == "bug_unclosed"
    assert f.evidence["bug_slug"] == "2026-07-03-platform-docstring-grep-spec-00-01"
    assert f.evidence["parent_spec"] == "spec-02-runner/sub-08-platform"
    assert f.evidence["changelog_versions"] == ["v1.0.0", "v1.0.1"]


def test_d6_bug_without_parent_header_emits_warning(tmp_path: Path) -> None:
    """Test 3: bug spec.md has no `父 spec:` header → 1 WARNING bug_no_parent."""
    parent_dir = tmp_path / ".trae" / "specs" / "spec-02-runner" / "sub-08-platform"
    _make_parent_spec(
        parent_dir,
        title="platform",
        rows=[("v1.0.0", "2026-07-03", "基线：platform 子 spec 立项")],
    )
    bug_dir = tmp_path / ".trae" / "specs" / "bug" / "2026-07-09-orphan-bug"
    _make_bug_spec(
        bug_dir,
        body=(
            "# BUG — orphan\n"
            "\n"
            "> **版本:** v1.0.0\n"
            "\n"
            "## 现象\n"
            "\n"
            "未声明父 spec。\n"
        ),
    )
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(adapter)

    assert len(findings) == 1, f"expected 1 finding, got {len(findings)}"
    f = findings[0]
    assert f.detector == "D6"
    assert f.severity == Severity.WARNING
    assert f.spec_path == bug_dir.relative_to(tmp_path).as_posix() + "/spec.md"
    assert "未声明父 spec" in f.message
    assert "2026-07-09-orphan-bug" in f.message
    assert f.evidence["kind"] == "bug_no_parent"
    assert f.evidence["bug_slug"] == "2026-07-09-orphan-bug"


def test_d6_parent_spec_missing_emits_warning(tmp_path: Path) -> None:
    """Test 4: bug declares a parent id but no matching spec exists → WARNING bug_parent_missing."""
    # Deliberately do NOT create the parent spec directory.
    bug_dir = tmp_path / ".trae" / "specs" / "bug" / "2026-07-09-missing-parent"
    _make_bug_spec(
        bug_dir,
        body=(
            "# BUG — missing parent\n"
            "\n"
            "> **版本:** v1.0.0\n"
            "\n"
            "父 spec: spec-99-nonexistent\n"
            "\n"
            "## 现象\n"
            "\n"
            "父 spec 不存在。\n"
        ),
    )
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(adapter)

    assert len(findings) == 1, f"expected 1 finding, got {len(findings)}"
    f = findings[0]
    assert f.detector == "D6"
    assert f.severity == Severity.WARNING
    assert f.spec_path == bug_dir.relative_to(tmp_path).as_posix() + "/spec.md"
    assert "spec-99-nonexistent" in f.message
    assert "2026-07-09-missing-parent" in f.message
    assert f.evidence["kind"] == "bug_parent_missing"
    assert f.evidence["bug_slug"] == "2026-07-09-missing-parent"
    assert f.evidence["parent_spec"] == "spec-99-nonexistent"


# ---------------------------------------------------------------------------
# v213 fixtures — coverage gaps identified during detector review.
# Real-data findings:
#   - _find_parent_spec() supports short-id to long-id resolution
#     (e.g. `spec-02` → `spec-02-runner`). Used by D5 to anchor
#     lesson refs and by D6 when bug declares a short parent id.
#     Without this fixture, a future refactor that breaks the
#     `startswith(parent_id + "-")` branch would silently regress
#     existing bugs.
#   - _slug_match() supports terminal-segment matching: when a changelog
#     summary contains e.g. "闭合 platform-docstring-grep-spec-00-01",
#     the long bug slug `2026-07-03-platform-docstring-grep-spec-00-01`
#     is matched via its terminal `-`-joined segment
#     `platform-docstring-grep-spec-00-01`. Real-data: this is the
#     dominant pattern in spec-02-runner §9.5 changelog rows. Test 1
#     already covers the full-slug-match path; this Test 5 covers the
#     tail-match fallback.
# ---------------------------------------------------------------------------


def test_d6_short_parent_id_resolves_to_longer_rel_spec_id(tmp_path: Path) -> None:
    """Bug declares short id `spec-02` but actual spec dir is `spec-02-runner` → no findings.

    Regression guard for `_find_parent_spec()` `startswith(parent_id + "-")`
    branch (d6_bug_sync.py:36). Real-data scenario: a bug spec may
    intentionally reference a parent by short id for portability; D6 must
    resolve it to the actual spec directory via `rel_spec_id` prefix.
    """
    # Parent spec id is `spec-02-runner` (long form); bug declares `spec-02` (short).
    parent_dir = tmp_path / ".trae" / "specs" / "spec-02-runner" / "sub-08-platform"
    _make_parent_spec(
        parent_dir,
        title="platform",
        rows=[
            ("v1.0.0", "2026-07-03", "基线：platform 子 spec 立项"),
            (
                "v1.0.1",
                "2026-07-09",
                "修订：闭合 platform-docstring-grep-spec-00-01 报告的 docstring 字面量漂移",
            ),
        ],
    )
    bug_dir = tmp_path / ".trae" / "specs" / "bug" / "2026-07-03-platform-docstring-grep-spec-00-01"
    _make_bug_spec(
        bug_dir,
        body=(
            "# BUG — platform docstring grep 漂移\n"
            "\n"
            "> **版本:** v1.0.0\n"
            "\n"
            "父 spec: spec-02\n"  # short id, resolves to spec-02-runner
            "\n"
            "## 现象\n"
            "\n"
            "占位。\n"
        ),
    )
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(adapter)

    assert findings == [], (
        "expected short-id parent to resolve to spec-02-runner, "
        f"got: {[f.message for f in findings]}"
    )


def test_d6_bug_slug_matches_via_terminal_segment(tmp_path: Path) -> None:
    """Changelog summary contains only the slug's terminal segment → match (no false-positive).

    Regression guard for `_slug_match()` tail-match fallback
    (d6_bug_sync.py:54-67). Real-data: spec-02-runner §9.5 entries
    like `闭合 platform-docstring-grep-spec-00-01 报告的` match the
    long bug slug `2026-07-03-platform-docstring-grep-spec-00-01` via
    tail `platform-docstring-grep-spec-00-01` — D6 must NOT emit
    `bug_unclosed` ERROR in this case.
    """
    parent_dir = tmp_path / ".trae" / "specs" / "spec-02-runner" / "sub-08-platform"
    _make_parent_spec(
        parent_dir,
        title="platform",
        rows=[
            ("v1.0.0", "2026-07-03", "基线：platform 子 spec 立项"),
            # Tail-only summary — does NOT contain the full bug slug.
            (
                "v1.0.1",
                "2026-07-09",
                "修订：闭合 platform-docstring-grep-spec-00-01 报告的 docstring 字面量漂移",
            ),
        ],
    )
    bug_dir = tmp_path / ".trae" / "specs" / "bug" / "2026-07-03-platform-docstring-grep-spec-00-01"
    _make_bug_spec(
        bug_dir,
        body=(
            "# BUG — platform docstring grep 漂移\n"
            "\n"
            "> **版本:** v1.0.0\n"
            "\n"
            "父 spec: spec-02-runner/sub-08-platform\n"
            "\n"
            "## 现象\n"
            "\n"
            "占位。\n"
        ),
    )
    adapter = AssetRadarAdapter(project_root=tmp_path)

    findings = detect(adapter)

    assert findings == [], (
        "expected tail-segment match to satisfy D6 (no bug_unclosed ERROR), "
        f"got: {[f.message for f in findings]}"
    )