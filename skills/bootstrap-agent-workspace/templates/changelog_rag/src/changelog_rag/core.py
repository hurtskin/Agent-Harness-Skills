"""Core: 决策日志.md changelog parsing + bge-small semantic retrieval.

Indexing strategy (v1, single-style only):
    - Read 决策日志.md (decision changelog file; intentionally NOT auto-loaded
      by Trae IDE, which only auto-loads the project context file in the project root)
    - Locate the `## 📝 变更日志` section (last occurrence wins)
    - Split into entries by `### vN（YYYY-MM-DD：...）` headers
    - Each entry becomes a ChangelogEntry dataclass
    - On every query, check 决策日志.md mtime; if changed, rebuild the embedding index

Why single-style only: lessons-learned.md §19 documents that historical v1-v8 entries
were rewritten to indexed style in 2026-07-07. Future entries follow the same style.
No legacy v1-v8 detailed format is supported (the appendix §19 records this decision).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

# Lazy-loaded model singleton (avoids 3-5s cold start on every tool call)
_model: SentenceTransformer | None = None
_DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"

# Regex: matches `### vN（YYYY-MM-DD：title）` (Chinese full-width parens) OR `### vN (YYYY-MM-DD: title)`
_ENTRY_HEADER_RE = re.compile(
    r"^###\s+v(?P<version>\d+)[（(](?P<date>\d{4}-\d{2}-\d{2})[：:]\s*(?P<title>.+?)[）)]\s*$",
    re.MULTILINE,
)
_CHANGELOG_SECTION_RE = re.compile(
    r"^##\s+📝\s*变更日志\s*$",
    re.MULTILINE,
)


@dataclass
class ChangelogEntry:
    """One indexed-style decision entry from 决策日志.md."""

    version: int
    date: str
    title: str
    content: str
    line_start: int
    line_end: int
    embedding: np.ndarray | None = field(default=None, repr=False)

    @property
    def anchor(self) -> str:
        return f"v{self.version}（{self.date}：{self.title}）"


def _resolve_agents_md(path: str | os.PathLike) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"决策日志.md not found at {p}")
    return p


def _extract_changelog_section(text: str) -> tuple[str, int]:
    """Return (section_text, start_line_index). Last occurrence wins."""
    matches = list(_CHANGELOG_SECTION_RE.finditer(text))
    if not matches:
        raise ValueError("决策日志.md has no `## 📝 变更日志` section")
    last = matches[-1]
    section_text = text[last.end():]
    start_line = text[: last.end()].count("\n")
    return section_text, start_line


def parse_changelog(agents_md_path: str | os.PathLike) -> list[ChangelogEntry]:
    """Parse 决策日志.md and return all changelog entries (ordered by version).

    The parameter name `agents_md_path` is kept for backward compatibility;
    it accepts any file path that contains the `## 📝 变更日志` section.
    """
    path = _resolve_agents_md(agents_md_path)
    text = path.read_text(encoding="utf-8")
    section, section_start_line = _extract_changelog_section(text)

    # Locate every ### vN header within the section
    headers = list(_ENTRY_HEADER_RE.finditer(section))
    if not headers:
        return []

    # Find the next ## ... section boundary (cuts off trailing non-changelog content).
    # Match `## ` (exactly 2 hashes + space), NOT `### ` (3 hashes) which would
    # incorrectly match every `### vN` changelog entry header.
    next_h2_re = re.compile(r"^## [^#]", re.MULTILINE)
    section_end = len(section)
    for h2 in next_h2_re.finditer(section):
        if h2.start() > headers[0].start():
            section_end = h2.start()
            break

    entries: list[ChangelogEntry] = []
    for i, h in enumerate(headers):
        # body = from this header to next ### vN header (or end of section, capped by ## boundary)
        body_start = h.end()
        if i + 1 < len(headers):
            body_end = headers[i + 1].start()
        else:
            body_end = section_end
        body = section[body_start:body_end].rstrip()

        # Convert body offset back to file line numbers
        offset_to_body_start = len(section[:body_start])
        body_start_line = section_start_line + section[:offset_to_body_start].count("\n") + 1
        body_end_line = section_start_line + section[:body_end].count("\n")

        entries.append(
            ChangelogEntry(
                version=int(h.group("version")),
                date=h.group("date"),
                title=h.group("title").strip(),
                content=body,
                line_start=body_start_line,
                line_end=body_end_line,
            )
        )
    entries.sort(key=lambda e: e.version)
    return entries


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_DEFAULT_MODEL)
    return _model


def _encode(texts: list[str]) -> np.ndarray:
    """Encode texts to L2-normalized vectors (for cosine similarity via dot product)."""
    model = _get_model()
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vecs, dtype=np.float32)


class ChangelogIndex:
    """Lazy-rebuild embedding index on 决策日志.md mtime change."""

    def __init__(self, agents_md_path: str | os.PathLike) -> None:
        self.path = _resolve_agents_md(agents_md_path)
        self._entries: list[ChangelogEntry] = []
        self._matrix: np.ndarray | None = None
        self._last_mtime: float = 0.0

    def _maybe_rebuild(self) -> None:
        mtime = self.path.stat().st_mtime
        if mtime == self._last_mtime and self._matrix is not None:
            return
        entries = parse_changelog(self.path)
        if not entries:
            self._entries = []
            self._matrix = np.zeros((0, 384), dtype=np.float32)
        else:
            texts = [f"{e.title}\n{e.content}" for e in entries]
            self._matrix = _encode(texts)
            for entry, vec in zip(entries, self._matrix):
                entry.embedding = vec
            self._entries = entries
        self._last_mtime = mtime

    def list_recent(self, limit: int = 10) -> list[dict]:
        """Return the most recent N entries (no embedding needed), newest-first.

        Entries are stored in ascending version order. Take the last `limit`,
        then reverse to descending (newest first).
        """
        self._maybe_rebuild()
        tail = self._entries[-limit:]  # last N by version (ascending)
        out = []
        for e in reversed(tail):  # flip to descending
            out.append(
                {
                    "version": e.version,
                    "date": e.date,
                    "title": e.title,
                    "anchor": e.anchor,
                    "line_range": [e.line_start, e.line_end],
                }
            )
        return out

    def search(self, keywords: list[str], limit: int = 5) -> list[dict]:
        """Return top-K entries ranked by cosine similarity to query."""
        self._maybe_rebuild()
        if not self._entries or self._matrix is None or self._matrix.shape[0] == 0:
            return []
        query = " ".join(keywords).strip()
        if not query:
            return []
        q_vec = _encode([query])[0]
        scores = self._matrix @ q_vec  # cosine (vectors are L2-normalized)
        top_idx = np.argsort(-scores)[:limit]
        out = []
        for idx in top_idx:
            e = self._entries[int(idx)]
            out.append(
                {
                    "version": e.version,
                    "date": e.date,
                    "title": e.title,
                    "anchor": e.anchor,
                    "score": float(scores[idx]),
                    "line_range": [e.line_start, e.line_end],
                    "content": e.content,
                }
            )
        return out


# ---------------------------------------------------------------------------
# Append-only mutation API (v75)
# ---------------------------------------------------------------------------
#
# Migrated from standalone tools/changelog_rag/scripts/log.py so that the
# append contract lives in the same MCP server that owns the read side
# (one source of truth for both reads and writes of 决策日志.md).
#
# Strict rules:
#   - Append only (end-of-file write); never rewrite, reorder, or trim
#     any existing entry (defends lessons §19 append-only contract).
#   - Auto-increment version = max(existing vN) + 1.
#   - Body is supplied verbatim (caller composes markdown);
#     script only wraps it with a `### vN（date：title）` header.
#   - Invalidates the in-process index so the next read picks up the new entry.

_VERSION_RE = re.compile(r"^###\s*v(\d+)\b", re.MULTILINE)


def latest_version(path: str | os.PathLike) -> dict:
    """Return {version, title, path} for the most recent changelog entry.

    Returns {version: 0, title: None, path: ...} when the file has no
    `### vN` entries yet.
    """
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"决策日志.md not found at {p}")
    text = p.read_text(encoding="utf-8")
    versions = [int(m.group(1)) for m in _VERSION_RE.finditer(text)]
    if not versions:
        return {"version": 0, "title": None, "path": str(p)}
    n = max(versions)
    # find the matching header line for human-readable output
    m = re.search(rf"^###\s*v{n}[^\n]*", text, re.MULTILINE)
    title = m.group(0).strip() if m else f"v{n}"
    return {"version": n, "title": title, "path": str(p)}


def append_entry(
    path: str | os.PathLike,
    title: str,
    body: str,
    date: str = "2026-07-11",
) -> dict:
    """Append a new decision entry at end of 决策日志.md.

    Returns {version, date, title, path, bytes_before, bytes_after}.
    Raises ValueError on empty title; FileNotFoundError if path missing.
    """
    if not title or not title.strip():
        raise ValueError("title must be a non-empty string")
    if body is None:
        body = ""
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"决策日志.md not found at {p}")
    text = p.read_text(encoding="utf-8")
    next_n = max([int(m.group(1)) for m in _VERSION_RE.finditer(text)] + [0]) + 1

    # ensure file ends with newline, then blank line, then header + body
    if not text.endswith("\n"):
        text += "\n"
    text += "\n"  # blank separator line before new entry
    header = f"### v{next_n}（{date}：{title.strip()}）"
    body_md = body if body.endswith("\n") else body + "\n"
    if not body_md.startswith("\n"):
        body_md = "\n" + body_md
    new_text = text + header + body_md + "\n"
    bytes_before = len(text)
    p.write_text(new_text, encoding="utf-8")
    return {
        "version": next_n,
        "date": date,
        "title": title.strip(),
        "path": str(p),
        "bytes_before": bytes_before,
        "bytes_after": len(new_text),
    }


# ---------------------------------------------------------------------------
# Mutate-in-place API (v86)
# ---------------------------------------------------------------------------
#
# User-confirmed 2026-07-13 design (deviates from lessons §19 append-only
# by explicit user override — see lessons §32):
#   - "Multiple same vN" disambiguation: REQUIRED `occurrence` (1-based,
#     NO default value). Agent must call `list_recent_changelog(limit=N)`
#     first and pick a specific occurrence. Forcing the agent to be
#     explicit prevents silent "I guessed wrong vN" mistakes.
#   - UPDATE: byte-level overwrite of the vN body. Title date unchanged.
#     New title optional (only replace if non-empty).
#   - DELETE: byte-level overwrite with empty body (the header line stays
#     so the vN position remains locatable; body is wiped to "").
#   - Both ops mutate the file in-place (no vN+1 audit trail) — user
#     explicitly chose direct overwrite over the proposed vN+1-audit scheme.
#
# Returns rich info dict on success so caller can verify what changed.

# Regex: matches the full header line for a specific vN
# (same shape as `_ENTRY_HEADER_RE` but anchored on a known version)
_UPDATE_HEADER_RE = re.compile(
    r"^###\s+v(?P<version>\d+)[（(](?P<date>\d{4}-\d{2}-\d{2})[：:]\s*(?P<title>.+?)[）)]\s*$",
    re.MULTILINE,
)
# Matches the START line of any vN header (for finding occurrence boundaries)
_ANY_V_HEADER_RE = re.compile(r"^###\s+v\d+\b", re.MULTILINE)


def _find_entry_byte_ranges(text: str) -> list[tuple[int, int, int]]:
    """Return list of (version, header_start, next_header_start_or_eof).

    Each tuple describes one vN entry's byte range [header_start, next).
    The LAST entry's next boundary is len(text) (end of file).
    Use this to locate the Nth occurrence of a given vN.
    """
    matches = list(_UPDATE_HEADER_RE.finditer(text))
    out: list[tuple[int, int, int]] = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((int(m.group("version")), m.start(), end))
    return out


def _resolve_entry_range(
    text: str, version: int, occurrence: int
) -> tuple[int, int, int, int]:
    """Resolve (version, occurrence) to (start, body_start, end, body_end).

    - `start`       : byte offset of the `### vN` header line
    - `body_start`  : byte offset of the line right AFTER the header
    - `end`         : byte offset of the NEXT entry's header (or EOF)
    - `body_end`    : byte offset of the line just BEFORE the next header
                      (i.e. last byte of trailing newlines belonging to this entry)

    Raises ValueError if vN doesn't exist or `occurrence` is out of range.
    """
    if occurrence < 1:
        raise ValueError(f"occurrence must be >= 1, got {occurrence}")
    ranges = _find_entry_byte_ranges(text)
    matches = [r for r in ranges if r[0] == version]
    if not matches:
        raise ValueError(f"version v{version} not found in 决策日志.md")
    if occurrence > len(matches):
        raise ValueError(
            f"v{version} has only {len(matches)} occurrence(s); "
            f"requested occurrence={occurrence}"
        )
    start, end = matches[occurrence - 1][1], matches[occurrence - 1][2]
    # body_start = first byte after the header line's trailing newline
    header_line_end = text.index("\n", start) + 1  # +1 to include the newline
    # body_end = last byte of the trailing newline block before the next header
    # walk backward from `end` over whitespace (newlines)
    body_end = end
    while body_end > header_line_end and text[body_end - 1] in "\n":
        body_end -= 1
    return start, header_line_end, end, body_end


def update_entry(
    path: str | os.PathLike,
    version: int,
    occurrence: int,
    new_body: str = "",
    new_title: str = "",
    new_date: str = "",
) -> dict:
    """Update an existing changelog entry in place (v86).

    Args:
        path       : 决策日志.md file path.
        version    : target vN (e.g. 89).
        occurrence : 1-based index; which occurrence of `version` to update.
                     REQUIRED (no default) — caller MUST resolve duplicates explicitly.
        new_body   : replacement body. Empty string allowed.
                     If None: keep original body unchanged.
        new_title  : replacement title. Empty string = keep original.
                     If provided AND non-empty, the header line is rewritten
                     with new_title (and optionally new_date).
        new_date   : replacement date (YYYY-MM-DD). Empty string = keep original.
                     Only used when new_title is also non-empty.

    Returns:
        {version, occurrence, old_title, new_title, bytes_before, bytes_after,
         body_replaced, title_replaced}.

    Raises:
        FileNotFoundError, ValueError (bad version/occurrence, bad date).
    """
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"决策日志.md not found at {p}")
    text = p.read_text(encoding="utf-8")

    start, body_start, end, body_end = _resolve_entry_range(text, version, occurrence)
    old_header_line = text[start:text.index("\n", start) + 1]
    old_body = text[body_start:body_end]

    new_header_line = old_header_line
    title_replaced = False
    if new_title and new_title.strip():
        # rewrite header with new title (and optionally new date)
        m = _UPDATE_HEADER_RE.match(old_header_line)
        if not m:
            raise ValueError(f"header line malformed: {old_header_line!r}")
        date = new_date.strip() if new_date.strip() else m.group("date")
        new_header_line = f"### v{version}（{date}：{new_title.strip()}）\n"
        title_replaced = True

    body_replaced = False
    if new_body is not None and new_body != old_body:
        body_replaced = True

    # Decide what the new entry body is
    if new_body is None:
        final_body = old_body
    else:
        final_body = new_body

    # Reconstruct: new_header + final_body + (whitespace between this entry's body_end and next entry's start)
    trailing_ws = text[body_end:end]
    new_text = text[:start] + new_header_line + final_body + trailing_ws + text[end:]

    if not body_replaced and not title_replaced:
        # nothing to do, but still return what would have happened (no write)
        return {
            "version": version,
            "occurrence": occurrence,
            "old_title": old_header_line.strip(),
            "new_title": new_header_line.strip(),
            "bytes_before": len(text),
            "bytes_after": len(text),
            "body_replaced": False,
            "title_replaced": False,
        }

    bytes_before = len(text)
    p.write_text(new_text, encoding="utf-8")
    return {
        "version": version,
        "occurrence": occurrence,
        "old_title": old_header_line.strip(),
        "new_title": new_header_line.strip(),
        "bytes_before": bytes_before,
        "bytes_after": len(new_text),
        "body_replaced": body_replaced,
        "title_replaced": title_replaced,
    }


def delete_entry(
    path: str | os.PathLike,
    version: int,
    occurrence: int,
) -> dict:
    """Delete an existing changelog entry in place (v86).

    Per user design (2026-07-13): the entry's BODY is overwritten with an
    empty string; the HEADER line is KEPT so vN's position remains locatable
    for future updates / list queries. This deviates from lessons §19
    strict-append-only — see lessons §32 for the deviation record.

    Args:
        path       : 决策日志.md file path.
        version    : target vN.
        occurrence : 1-based index; which occurrence of `version` to delete.
                     REQUIRED (no default).

    Returns:
        {version, occurrence, old_body_bytes, bytes_before, bytes_after}.

    Raises:
        FileNotFoundError, ValueError.
    """
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"决策日志.md not found at {p}")
    text = p.read_text(encoding="utf-8")

    start, body_start, end, body_end = _resolve_entry_range(text, version, occurrence)
    old_body = text[body_start:body_end]

    # Wipe body only; keep header + trailing whitespace intact
    trailing_ws = text[body_end:end]
    new_text = text[:body_start] + trailing_ws + text[end:]

    bytes_before = len(text)
    p.write_text(new_text, encoding="utf-8")
    return {
        "version": version,
        "occurrence": occurrence,
        "old_body_bytes": len(old_body),
        "bytes_before": bytes_before,
        "bytes_after": len(new_text),
    }