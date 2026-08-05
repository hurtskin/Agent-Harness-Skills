"""Tests for changelog_rag core: parser + index.

3 categories per soul.md §9 bug 6-step discipline:
    - Core: parser + index happy path
    - Regression: v1-v8 indexed-style rewrite must still parse
    - Integration: end-to-end search returns semantically relevant entry

Slow marker (index tests load the embedding model on first call, ~10s):
    - Run parser-only: `pytest`
    - Run all:          `pytest --run-slow`
"""

from __future__ import annotations

import os
from pathlib import Path

# Force HF offline mode BEFORE any transformers/sentence-transformers import,
# to prevent runtime adapter-config download when the model is already cached.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import numpy as np
import pytest

from changelog_rag.core import (
    ChangelogEntry,
    ChangelogIndex,
    append_entry,
    delete_entry,
    latest_version,
    parse_changelog,
    update_entry,
)


slow = pytest.mark.slow


# --- fixtures ---


SAMPLE_AGENTS_MD = """\
# Asset Radar — Agent Memory

## 🧭 本文件重点是「决策日志 / 时间轴」

## 📝 变更日志

### v1（2026-07-03：三件套初始化）
- **触发**：项目冷启动，bootstrap-agent-workspace skill 初始化 soul.md / AGENTS.md / lessons-learned.md 三件套
- **改动**：新建 `.trae/rules/soul.md`（11 节）/ `AGENTS.md`（事实层 + 当前任务占位）/ `.trae/rules/lessons-learned.md`（§14 起 append-only）
- **关键决策**：库名 = asset-radar；scope = src/ + tests/ + frontend/；runtime 零依赖契约写进 §3.5 / §6 / §10
- **遗留**：5 个开放问题待首次启动 spec 时回填
- **引用 lesson**：§14（v2 由该教训触发整段重写）

### v19（2026-07-07：sub-07-wsmessage 代码落地 + 测试漂移修复）
- **spec**：`.trae/specs/spec-00-arch/sub-07-wsmessage/{spec.md, tasks.md, checklist.md}` 三件套已立项
- **code**：WSMessage(BaseModel) 类（2 字段 type + payload）
- **test**：新增 TestWSMessage（17 TC）+ TestNestedPayloadInWSMessage（6 TC）；6 个 TC 漂移修复
- **main spec**：sub-07 状态 → ✅
- **验证**：155 items 全绿
- **引用 lesson**：§18（三件套内部漂移）

### v20（2026-07-07：changelog-rag 工具落地）
- **触发**：用户问 RAG 检索决策日志
- **改动**：新建 tools/changelog_rag/ MCP server
- **下一步**：跑通测试

## 🪤 易踩的坑

（无关内容）
"""


@pytest.fixture()
def sample_path(tmp_path: Path) -> Path:
    p = tmp_path / "AGENTS.md"
    p.write_text(SAMPLE_AGENTS_MD, encoding="utf-8")
    return p


# --- core tests: parser (FAST, no embedding) ---


def test_parse_changelog_returns_entries_in_version_order(sample_path: Path) -> None:
    entries = parse_changelog(sample_path)
    assert len(entries) == 3
    assert [e.version for e in entries] == [1, 19, 20]


def test_parse_changelog_extracts_metadata(sample_path: Path) -> None:
    entries = parse_changelog(sample_path)
    v1 = entries[0]
    assert v1.date == "2026-07-03"
    assert v1.title == "三件套初始化"
    assert "bootstrap-agent-workspace" in v1.content
    assert v1.line_start > 0
    assert v1.line_end > v1.line_start


def test_parse_changelog_stops_at_next_h2_section(sample_path: Path) -> None:
    """Sections after `## 📝 变更日志` (e.g. `## 🪤 易踩的坑`) must NOT leak into entries.

    Parser uses last-occurrence-wins for the section header; subsequent
    `## ...` headers are NOT followed.
    """
    entries = parse_changelog(sample_path)
    for e in entries:
        assert "无关内容" not in e.content
        assert "##" not in e.content


def test_parse_changelog_raises_on_missing_section(tmp_path: Path) -> None:
    bad = tmp_path / "AGENTS.md"
    bad.write_text("# Asset Radar\n\n## 普通段\n\n### v1（2024-01-01：foo）\n- body\n", encoding="utf-8")
    with pytest.raises(ValueError, match="📝 变更日志"):
        parse_changelog(bad)


def test_parse_changelog_raises_on_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_changelog(tmp_path / "nope.md")


def test_parse_changelog_empty_when_no_entries(tmp_path: Path) -> None:
    p = tmp_path / "AGENTS.md"
    p.write_text("# Asset Radar\n\n## 📝 变更日志\n\n(暂无)\n", encoding="utf-8")
    assert parse_changelog(p) == []


# --- core tests: index (SLOW, load embedding model) ---


@slow
def test_index_list_recent_returns_newest_first(sample_path: Path) -> None:
    idx = ChangelogIndex(sample_path)
    recent = idx.list_recent(limit=10)
    assert [r["version"] for r in recent] == [20, 19, 1]
    assert recent[0]["date"] == "2026-07-07"
    assert "anchor" in recent[0]
    assert "line_range" in recent[0]


@slow
def test_index_list_recent_respects_limit(sample_path: Path) -> None:
    idx = ChangelogIndex(sample_path)
    assert len(idx.list_recent(limit=2)) == 2


@slow
def test_index_search_returns_top_k(sample_path: Path) -> None:
    idx = ChangelogIndex(sample_path)
    results = idx.search(keywords=["wsmessage", "sub-07"], limit=3)
    assert len(results) >= 1
    top = results[0]
    assert "version" in top and "score" in top and "content" in top
    assert top["version"] == 19
    assert top["score"] > 0.0


@slow
def test_index_search_empty_keywords_returns_empty(sample_path: Path) -> None:
    idx = ChangelogIndex(sample_path)
    assert idx.search(keywords=[], limit=5) == []
    assert idx.search(keywords=["   "], limit=5) == []


@slow
def test_index_rebuilds_on_mtime_change(sample_path: Path) -> None:
    """Appending a new entry to AGENTS.md must rebuild the index on next access."""
    idx = ChangelogIndex(sample_path)
    assert len(idx.list_recent(limit=10)) == 3

    text = sample_path.read_text(encoding="utf-8")
    text += "\n### v21（2026-07-08：测试重建）\n- **触发**：mtime 变化\n"
    import time

    time.sleep(1.1)
    sample_path.write_text(text, encoding="utf-8")

    assert len(idx.list_recent(limit=10)) == 4


@slow
def test_index_handles_empty_changelog_gracefully(tmp_path: Path) -> None:
    p = tmp_path / "AGENTS.md"
    p.write_text("# Asset Radar\n\n## 📝 变更日志\n\n(暂无)\n", encoding="utf-8")
    idx = ChangelogIndex(p)
    assert idx.list_recent(limit=10) == []
    assert idx.search(keywords=["anything"], limit=5) == []


# --- regression: real 决策日志.md from this repo (FAST — parser only) ---


def _find_repo_decision_log(start: Path) -> Path | None:
    for directory in (start, *start.parents):
        candidate = directory / "决策日志.md"
        if candidate.is_file():
            return candidate
    return None


REAL_DECISION_LOG = _find_repo_decision_log(Path(__file__).resolve().parent)


@pytest.mark.skipif(REAL_DECISION_LOG is None, reason="no repository 决策日志.md")
def test_real_decision_log_parses_cleanly() -> None:
    """Regression: the repository 决策日志.md must parse with zero crashes."""
    assert REAL_DECISION_LOG is not None
    entries = parse_changelog(REAL_DECISION_LOG)
    assert len(entries) >= 1
    for e in entries:
        assert e.version > 0
        assert len(e.date) == 10
        assert e.title
        assert e.line_start > 0
    versions = [e.version for e in entries]
    assert versions == sorted(versions)


# --- regression: v22 bug fixes ---

SAMPLE_WITH_MANY_ENTRIES = """\
# Asset Radar

## 📝 变更日志

### v1（2026-01-01：first）
- body 1

### v2（2026-01-02：second）
- body 2

### v3（2026-01-03：third）
- body 3

### v10（2026-01-04：tenth）
- body 10

### v20（2026-01-05：twentieth）
- body 20

## 🪤 易踩的坑

无关内容
"""


def test_parser_does_not_treat_vN_headers_as_h2_boundary(tmp_path: Path) -> None:
    """v22 bug regression: `^##\\s+\\S` incorrectly matched `### vN` headers,
    cutting off parsing after v3. Fixed regex `^## [^#]` only matches ## sections.
    """
    p = tmp_path / "AGENTS.md"
    p.write_text(SAMPLE_WITH_MANY_ENTRIES, encoding="utf-8")
    entries = parse_changelog(p)
    # Should parse all 5 entries (v1, v2, v3, v10, v20), not stop at v3
    assert [e.version for e in entries] == [1, 2, 3, 10, 20]


@slow
def test_list_recent_returns_newest_first_real_order(tmp_path: Path) -> None:
    """v22 bug regression: list_recent should return newest-first (descending)."""
    p = tmp_path / "AGENTS.md"
    p.write_text(SAMPLE_WITH_MANY_ENTRIES, encoding="utf-8")
    idx = ChangelogIndex(p)
    recent = idx.list_recent(limit=10)
    # All 5 entries, ordered newest (v20) → oldest (v1)
    assert [r["version"] for r in recent] == [20, 10, 3, 2, 1]


# Force at least one assertion so `import numpy as np` above is not unused
def _numpy_import_check() -> None:
    arr = np.array([1.0, 2.0])
    assert arr.sum() == 3.0


# --- v75: append-only mutation API (latest_version + append_entry) ---


def _write_sample_with_entry(tmp_path: Path, version: int, title: str = "test") -> Path:
    """Helper: write a minimal 决策日志.md with one entry."""
    p = tmp_path / "决策日志.md"
    p.write_text(
        f"# 决策日志\n\n## 📝 变更日志\n\n### v{version}（2026-07-11：{title}）\n- body line\n",
        encoding="utf-8",
    )
    return p


def test_latest_version_returns_max_version(tmp_path: Path) -> None:
    """Core: latest_version() returns max(vN) and matching header line."""
    p = _write_sample_with_entry(tmp_path, 5)
    r = latest_version(p)
    assert r["version"] == 5
    assert "v5" in r["title"]
    assert r["path"] == str(p)


def test_latest_version_with_no_entries_returns_zero(tmp_path: Path) -> None:
    """Regression: empty changelog returns version=0, title=None (not a crash)."""
    p = tmp_path / "决策日志.md"
    p.write_text("# 决策日志\n\n## 📝 变更日志\n\n(暂无)\n", encoding="utf-8")
    r = latest_version(p)
    assert r["version"] == 0
    assert r["title"] is None


def test_latest_version_missing_file_raises(tmp_path: Path) -> None:
    """Core: missing file raises FileNotFoundError (matches RAG read path)."""
    p = tmp_path / "决策日志.md"  # not created
    with pytest.raises(FileNotFoundError):
        latest_version(p)


def test_append_entry_increments_version(tmp_path: Path) -> None:
    """Core: append_entry writes a new ### vN+1 header at end-of-file."""
    p = _write_sample_with_entry(tmp_path, 5)
    r = append_entry(p, title="new entry", body="- line A\n- line B", date="2026-07-11")
    assert r["version"] == 6
    assert r["title"] == "new entry"
    assert r["bytes_after"] > r["bytes_before"]
    text = p.read_text(encoding="utf-8")
    assert "### v6（2026-07-11：new entry）" in text
    assert "- line A" in text
    assert "- line B" in text
    # v5 must still be present (append-only contract)
    assert "### v5（2026-07-11：test）" in text


def test_append_entry_empty_changelog_starts_at_v1(tmp_path: Path) -> None:
    """Regression: empty changelog → first append becomes v1 (not v0)."""
    p = tmp_path / "决策日志.md"
    p.write_text("# 决策日志\n\n## 📝 变更日志\n\n(暂无)\n", encoding="utf-8")
    r = append_entry(p, title="seed entry", body="body", date="2026-07-11")
    assert r["version"] == 1
    text = p.read_text(encoding="utf-8")
    assert "### v1（2026-07-11：seed entry）" in text


def test_append_entry_rejects_empty_title(tmp_path: Path) -> None:
    """Core: empty / whitespace title raises ValueError (defends bad data)."""
    p = _write_sample_with_entry(tmp_path, 1)
    with pytest.raises(ValueError):
        append_entry(p, title="", body="x", date="2026-07-11")
    with pytest.raises(ValueError):
        append_entry(p, title="   ", body="x", date="2026-07-11")


def test_append_entry_appended_content_parseable(tmp_path: Path) -> None:
    """Integration: appended entries are parsed back by parse_changelog
    (no regression to the read path).
    """
    p = _write_sample_with_entry(tmp_path, 1)
    append_entry(p, title="second", body="- b1\n- b2", date="2026-07-11")
    append_entry(p, title="third", body="- c1", date="2026-07-11")
    entries = parse_changelog(p)
    assert [e.version for e in entries] == [1, 2, 3]
    assert entries[-1].title == "third"


# --- v86: mutate-in-place API (update_entry + delete_entry) ---


def _write_sample_with_two_v89(tmp_path: Path) -> Path:
    """Helper: write a sample 决策日志.md with v89 appearing TWICE (DUP case)."""
    p = tmp_path / "决策日志.md"
    p.write_text(
        "# 决策日志\n\n## 📝 变更日志\n\n"
        "### v89（2026-07-13：first v89）\n- body 1\n\n"
        "### v89（2026-07-13：second v89）\n- body 2\n\n"
        "### v90（2026-07-13：v90）\n- body 3\n",
        encoding="utf-8",
    )
    return p


def test_update_entry_replaces_body_in_place(tmp_path: Path) -> None:
    """Core: update_entry overwrites the body of the targeted vN occurrence."""
    p = _write_sample_with_two_v89(tmp_path)
    r = update_entry(p, version=89, occurrence=1, new_body="- UPDATED body 1\n")
    assert r["body_replaced"] is True
    assert r["title_replaced"] is False
    text = p.read_text(encoding="utf-8")
    assert "- UPDATED body 1" in text
    # v89 occurrence 2 must be UNTOUCHED
    assert "- body 2" in text
    # v90 must be untouched
    assert "- body 3" in text
    entries = parse_changelog(p)
    assert [e.version for e in entries] == [89, 89, 90]


def test_update_entry_disambiguates_duplicates_by_occurrence(tmp_path: Path) -> None:
    """Core: occurrence=2 targets the SECOND v89, leaves first untouched."""
    p = _write_sample_with_two_v89(tmp_path)
    r = update_entry(p, version=89, occurrence=2, new_body="- UPDATED body 2\n")
    assert r["body_replaced"] is True
    text = p.read_text(encoding="utf-8")
    # first v89 body untouched
    assert "- body 1" in text
    # second v89 body replaced
    assert "- UPDATED body 2" in text
    assert "- body 2" not in text


def test_update_entry_replaces_title_and_date(tmp_path: Path) -> None:
    """Core: update_entry with non-empty new_title rewrites the header line."""
    p = _write_sample_with_entry(tmp_path, 1)
    r = update_entry(
        p, version=1, occurrence=1,
        new_body="", new_title="renamed entry", new_date="2026-07-13",
    )
    assert r["title_replaced"] is True
    text = p.read_text(encoding="utf-8")
    assert "### v1（2026-07-13：renamed entry）" in text


def test_update_entry_raises_for_missing_version(tmp_path: Path) -> None:
    """Regression: non-existent vN raises ValueError (not silent no-op)."""
    p = _write_sample_with_entry(tmp_path, 1)
    with pytest.raises(ValueError, match="v99 not found"):
        update_entry(p, version=99, occurrence=1, new_body="x")


def test_update_entry_raises_for_out_of_range_occurrence(tmp_path: Path) -> None:
    """Regression: occurrence > existing count raises ValueError."""
    p = _write_sample_with_two_v89(tmp_path)
    with pytest.raises(ValueError, match="only 2 occurrence"):
        update_entry(p, version=89, occurrence=3, new_body="x")


def test_delete_entry_wipes_body_keeps_header(tmp_path: Path) -> None:
    """Core: delete_entry empties the body; the `### vN` header stays."""
    p = _write_sample_with_two_v89(tmp_path)
    r = delete_entry(p, version=89, occurrence=1)
    assert r["old_body_bytes"] > 0
    text = p.read_text(encoding="utf-8")
    # header line still present (so v89's position is locatable)
    assert "### v89（2026-07-13：first v89）" in text
    # body wiped
    assert "- body 1" not in text
    # second v89 untouched
    assert "- body 2" in text
    # both v89 headers still present (count == 2)
    assert text.count("### v89") == 2
    # parse_changelog still finds 3 entries (DUP handling intact)
    entries = parse_changelog(p)
    assert [e.version for e in entries] == [89, 89, 90]


def test_delete_entry_disambiguates_duplicates_by_occurrence(tmp_path: Path) -> None:
    """Core: occurrence=2 deletes the SECOND v89 only."""
    p = _write_sample_with_two_v89(tmp_path)
    delete_entry(p, version=89, occurrence=2)
    text = p.read_text(encoding="utf-8")
    # first v89 body still present
    assert "- body 1" in text
    # second v89 body gone
    assert "- body 2" not in text
    # both headers still present
    assert text.count("### v89") == 2


def test_delete_entry_then_update_can_repopulate_body(tmp_path: Path) -> None:
    """Integration: after delete, update_entry can write a new body in the
    same vN slot (proves the header retention design works end-to-end)."""
    p = _write_sample_with_entry(tmp_path, 1)
    delete_entry(p, version=1, occurrence=1)
    update_entry(p, version=1, occurrence=1, new_body="- REPOPULATED\n")
    text = p.read_text(encoding="utf-8")
    assert "### v1（2026-07-11：test）" in text
    assert "- REPOPULATED" in text