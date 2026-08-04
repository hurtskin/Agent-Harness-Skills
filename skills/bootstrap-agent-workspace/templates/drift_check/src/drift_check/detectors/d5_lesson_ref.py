"""D5 detector — lessons-learned.md anchor liveness check.

Validates that every ``§XX`` reference appearing in soul.md / AGENTS.md /
spec.md / 决策日志.md points to a real anchor ``^## §XX`` defined in
lessons-learned.md.

References without a matching anchor are reported as ``Severity.ERROR``
(``kind=dangling_ref``). The evidence groups every source file that
mentioned the same dangling ref into a single ``from_files`` list, so a
ref cited from N places produces 1 finding (not N).
"""

from __future__ import annotations

import re
from pathlib import Path

from drift_check.adapters.asset_radar import AssetRadarAdapter
from drift_check.detectors.common import DriftFinding, Severity


# Anchor pattern: ``## §XX`` at the start of a line, where XX is digits
# optionally followed by a single lowercase letter (e.g. ``§14``, ``§22a``).
# Mirrors the lesson id format used by `lessons-learned.md` (§14 onwards).
_ANCHOR_RE = re.compile(r"^## §(\d+[a-z]?)\b", re.MULTILINE)

# Pattern that only matches "real" lessons references (with explicit
# `lessons` keyword nearby), filtering out soul.md's own section numbers
# like §3.4 / §6.2 / §10.1 which are internal sub-sections.
_LESSONS_REF_RE = re.compile(
    r"(?:lessons[^\n]{0,40}?)?§(\d+[a-z]?)\b",
)

# Always-scanned source files (in addition to spec.md list and the
# optional decision log): project-relative labels for human-readable
# error reporting.
_SOUL_REL = Path(".trae") / "rules" / "soul.md"
_AGENTS_REL = Path("AGENTS.md")


def _read_text(path: Path) -> str | None:
    """Return the file text, or ``None`` if the file does not exist."""
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _relative(path: Path, root: Path) -> str:
    """Return the project-relative path as a POSIX string."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _collect_references(adapter: AssetRadarAdapter) -> dict[str, list[str]]:
    """Collect every ``§XX`` reference across the project, grouped by id.

    Scans (in order):
      1. ``AGENTS.md``                  — fixed path under project root
      2. Every ``spec.md`` returned by ``adapter.list_specs()``
      3. ``决策日志.md`` if ``adapter.decision_log_file()`` returns a path

    Note: ``soul.md`` is intentionally NOT scanned — its own §-prefixed
    section numbers (e.g. ``§3.4``, ``§6.2``, ``§10.1``) are internal
    section navigation, not lessons references, and cannot be reliably
    distinguished from real lessons references via regex.

    Args:
        adapter: The AssetRadarAdapter bound to a project root.

    Returns:
        dict mapping ref id (e.g. ``"25"``, ``"22a"``) → sorted list of
        project-relative source file paths that mention it.
    """
    root = adapter.project_root()
    grouped: dict[str, set[str]] = {}

    def _add(ref: str, rel: str) -> None:
        if ref not in grouped:
            grouped[ref] = set()
        grouped[ref].add(rel)

    sources: list[tuple[Path, str]] = []
    agents_path = root / _AGENTS_REL
    if agents_path.exists():
        sources.append((agents_path, _AGENTS_REL.as_posix()))
    for spec in adapter.list_specs():
        sources.append((spec.spec_md, f"{spec.rel_spec_id}/spec.md"))
    decision_log = adapter.decision_log_file()
    if decision_log is not None:
        sources.append((decision_log, _relative(decision_log, root)))

    for path, rel in sources:
        text = _read_text(path)
        if text is None:
            continue
        for ref in adapter.parse_lesson_refs(text):
            _add(ref, rel)

    return {ref: sorted(files) for ref, files in grouped.items()}


def _collect_alive_anchors(adapter: AssetRadarAdapter) -> set[str]:
    """Read lessons-learned.md and return the set of ``§XX`` anchors defined.

    An anchor is a line of the form ``## §XX`` (XX = digits + optional
    single lowercase letter). Anything else is ignored. If lessons-learned.md
    does not exist, the alive set is empty — every reference is then
    dangling, which matches the "no anchor exists" semantics.
    """
    text = _read_text(adapter.lesson_refs_file())
    if text is None:
        return set()
    return set(_ANCHOR_RE.findall(text))


def detect(adapter: AssetRadarAdapter) -> list[DriftFinding]:
    """Detect dangling ``§XX`` references with no lessons-learned.md anchor.

    Algorithm:
      1. Collect every ``§XX`` reference in soul.md / AGENTS.md / all
         ``spec.md`` / ``决策日志.md`` (if it exists). Dedupe per ref id
         across sources, accumulating the source-file set.
      2. Collect every ``^## §XX`` anchor defined in lessons-learned.md.
      3. For each referenced ref id not in the alive anchor set, emit
         exactly one ``Severity.ERROR`` finding with ``evidence.from_files``
         aggregating every source that mentioned it.

    Args:
        adapter: An ``AssetRadarAdapter`` bound to a project root.

    Returns:
        List of ``DriftFinding``; empty when every reference resolves to
        a real anchor. The decision log is silently skipped when absent.
    """
    refs = _collect_references(adapter)
    alive = _collect_alive_anchors(adapter)
    historical = adapter.historical_lesson_anchors()

    findings: list[DriftFinding] = []
    for ref in sorted(refs):
        if ref in alive:
            continue
        # Silent skip: historical anchors (e.g. v8 decision's §1-§13) are
        # intentionally allowed to be dangling — they're deprecated lessons
        # that earlier specs may still reference.
        if ref in historical:
            continue
        from_files = refs[ref]
        findings.append(
            DriftFinding(
                detector="D5",
                severity=Severity.ERROR,
                spec_path=from_files[0],
                message=(
                    f"dangling lesson ref §{ref}: referenced by "
                    f"{len(from_files)} file(s), no `## §{ref}` anchor in "
                    "lessons-learned.md"
                ),
                evidence={
                    "kind": "dangling_ref",
                    "ref": f"§{ref}",
                    "from_files": from_files,
                },
            )
        )
    return findings