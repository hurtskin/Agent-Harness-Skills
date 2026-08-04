"""FastMCP server exposing 4 tools over stdio transport.

Tools (4):
    - list_recent_changelog(limit=10)  → [{version, date, title, anchor, line_range}]
    - load_relevant_changelog(keywords=[...], limit=5) → [{..., content, score}]
    - latest_changelog_version()        → {version, title, path}   (no embedding)
    - append_log_entry(title, body, date) → {version, date, title, path, bytes_before, bytes_after}

Usage:
    uv run python -m changelog_rag.server

Environment variables:
    CHANGELOG_RAG_AGENTS_MD  — absolute path to the decision changelog file (default: ../../决策日志.md)
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .core import ChangelogIndex, append_entry, delete_entry, latest_version, update_entry

mcp = FastMCP("changelog-rag")

# Default: 决策日志.md (decision changelog file; intentionally NOT auto-loaded
# by Trae IDE, which only auto-loads the project context file in the project root).
_DEFAULT_AGENTS_MD = (
    Path(__file__).resolve().parent.parent.parent.parent.parent / "决策日志.md"
)


def _resolve_path() -> Path:
    # Priority 1: explicit override via env var
    env = os.environ.get("CHANGELOG_RAG_AGENTS_MD")
    if env:
        return Path(env).expanduser().resolve()
    # Priority 2: derive from CWD (works when MCP config sets `cwd` to project root)
    cwd = Path(os.getcwd()).resolve()
    candidate = cwd / "决策日志.md"
    if candidate.is_file():
        return candidate
    # Priority 3: walk up from this file looking for 决策日志.md (max 6 levels)
    p = Path(__file__).resolve()
    for _ in range(6):
        p = p.parent
        if (p / "决策日志.md").is_file():
            return p / "决策日志.md"
    # Priority 4: hardcoded relative path from this file (legacy fallback)
    return _DEFAULT_AGENTS_MD.resolve()


_index: ChangelogIndex | None = None


def _get_index() -> ChangelogIndex:
    global _index
    if _index is None:
        _index = ChangelogIndex(_resolve_path())
    return _index


@mcp.tool()
def list_recent_changelog(limit: int = 10) -> list[dict]:
    """Return the most recent N decision-log entries (no embedding).

    Args:
        limit: Maximum number of entries to return (default 10, max 50).

    Returns:
        List of {version, date, title, anchor, line_range}, ordered newest-first.
    """
    limit = max(1, min(int(limit), 50))
    return _get_index().list_recent(limit=limit)


@mcp.tool()
def load_relevant_changelog(keywords: list[str], limit: int = 5) -> list[dict]:
    """Return top-K decision-log entries semantically matched to keywords.

    Args:
        keywords: One or more search terms (e.g. ["sub-07", "ValidationError"]).
        limit: Maximum number of entries to return (default 5, max 20).

    Returns:
        List of {version, date, title, anchor, score, line_range, content}.
    """
    keywords = [str(k).strip() for k in (keywords or []) if str(k).strip()]
    if not keywords:
        return []
    limit = max(1, min(int(limit), 20))
    return _get_index().search(keywords=keywords, limit=limit)


@mcp.tool()
def latest_changelog_version() -> dict:
    """Return the latest decision-log version number + title.

    Reads 决策日志.md and scans for `### vN` headers (no embedding needed).
    Use this BEFORE appending a new entry if you need to know the current vN.

    Returns:
        {version: int, title: str|None, path: str}.
        `version=0, title=None` means the file has no entries yet.
    """
    return latest_version(_resolve_path())


@mcp.tool()
def append_log_entry(title: str, body: str, date: str = "2026-07-11") -> dict:
    """Append a new decision entry at the end of 决策日志.md.

    Auto-increments version = max(existing vN) + 1. **Strictly append-only**:
    never rewrites, reorders, or trims any existing entry (defends lessons §19
    append-only contract).

    Args:
        title: One-line summary (e.g. "sub-09 v1.1.0 代码落地").
        body: Markdown body (bullets / sections / free-form). Pass an empty
              string for a bare entry.
        date: ISO date string (default "2026-07-11").

    Returns:
        {version, date, title, path, bytes_before, bytes_after}.

    Notes for callers:
        - 中文 / Markdown 内容建议写到临时文件再用 Read 读取后传入（避免 shell 引号截断）
        - 临时文件必须 `_temp` 开头 + 使用后立即删除（按 §6.1 临时文件红线）
        - 此工具调用后**不需要**重起 MCP server——index 在下次 read 时按 mtime 自动 rebuild
    """
    result = append_entry(_resolve_path(), title=title, body=body, date=date)
    # invalidate cached index so next list_recent / load_relevant picks up new entry
    global _index
    _index = None
    return result


@mcp.tool()
def update_log_entry(
    version: int,
    occurrence: int,
    new_body: str = "",
    new_title: str = "",
    new_date: str = "",
) -> dict:
    """Update an existing decision-log entry in place (v86).

    Byte-level overwrite of the target entry. Does NOT append a vN+1 audit
    trail (user explicitly chose direct overwrite over the vN+1-audit scheme).

    **Disambiguation of duplicate vN**: `occurrence` is REQUIRED (no default).
    Caller must first call `list_recent_changelog(limit=N)` to inspect which
    occurrences of `version` exist, then pass the specific occurrence number.

    Args:
        version    : target vN (e.g. 89).
        occurrence : 1-based index — which occurrence of `version` to update.
        new_body   : replacement body markdown. Empty string = wipe to "".
                     To keep body unchanged, pass the exact original body string.
        new_title  : replacement title. Empty string = keep original.
        new_date   : replacement date (YYYY-MM-DD). Empty string = keep original.

    Returns:
        {version, occurrence, old_title, new_title, bytes_before, bytes_after,
         body_replaced, title_replaced}.

    Notes:
        - Invalidates in-process index cache; next read auto-rebuilds.
        - **No MCP server restart required** (lessons §20).
        - **DEVIATES from lessons §19 append-only** — see lessons §32.
    """
    result = update_entry(
        _resolve_path(),
        version=version,
        occurrence=occurrence,
        new_body=new_body,
        new_title=new_title,
        new_date=new_date,
    )
    global _index
    _index = None
    return result


@mcp.tool()
def delete_log_entry(version: int, occurrence: int) -> dict:
    """Delete an existing decision-log entry in place (v86).

    Body is wiped to ""; the header line is KEPT so vN's position remains
    locatable for future updates / list queries. This deviates from lessons
    §19 strict-append-only — see lessons §32.

    **Disambiguation of duplicate vN**: `occurrence` is REQUIRED (no default).

    Args:
        version    : target vN (e.g. 89).
        occurrence : 1-based index — which occurrence of `version` to delete.

    Returns:
        {version, occurrence, old_body_bytes, bytes_before, bytes_after}.

    Notes:
        - **Does NOT** remove the `### vN` header line — only wipes body to "".
        - Invalidates in-process index cache; next read auto-rebuilds.
    """
    result = delete_entry(_resolve_path(), version=version, occurrence=occurrence)
    global _index
    _index = None
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="changelog-rag MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport (default: stdio)",
    )
    args = parser.parse_args()
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()