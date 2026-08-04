"""D6 detector — bug sub-spec synchronization with parent spec changelog.

Validates that every ``.trae/specs/bug/<slug>/spec.md`` is referenced by the
parent spec's ``§9.5 changelog`` table. Detects the following kinds of drift:

- ``bug_no_parent`` (WARNING): bug spec has no parseable ``父 spec:`` header.
- ``bug_parent_missing`` (WARNING): parent spec id is declared but does not
  exist under ``.trae/specs/`` (i.e. not in ``adapter.list_specs()``).
- ``bug_unclosed`` (ERROR): parent spec exists but its changelog table does
  not mention the bug slug (or the slug's terminal segment).
"""

from __future__ import annotations

from pathlib import Path

from drift_check.adapters.asset_radar import AssetRadarAdapter
from drift_check.detectors.common import DriftFinding, Severity


def _find_parent_spec(parent_id: str, specs) -> object | None:
    """Locate the parent SpecLocation whose ``rel_spec_id`` starts with parent_id.

    Matches when ``rel_spec_id`` either equals ``parent_id``, starts with
    ``parent_id + "/"`` (sub-spec of parent), or starts with ``parent_id + "-"``
    (parent-id variant like ``spec-00-arch`` for prefix ``spec-00``).

    Picks the closest (shortest rel_spec_id) match so ``spec-02`` resolves to
    ``spec-02-runner`` rather than ``spec-02-runner/sub-99-foo``.
    """
    matches = [
        s
        for s in specs
        if s.rel_spec_id == parent_id
        or s.rel_spec_id.startswith(parent_id + "/")
        or s.rel_spec_id.startswith(parent_id + "-")
    ]
    if not matches:
        return None
    # Prefer exact match when available; otherwise shortest rel_spec_id.
    exact = [s for s in matches if s.rel_spec_id == parent_id]
    if exact:
        return exact[0]
    return min(matches, key=lambda s: len(s.rel_spec_id))


def _slug_match(bug_slug: str, summary: str) -> bool:
    """Return True if bug_slug (or its terminal `-`-joined segment) appears in summary."""
    if not summary:
        return False
    if bug_slug in summary:
        return True
    # terminal segment: drop the YYYY-MM-DD- prefix and the trailing -NN suffix
    parts = bug_slug.split("-")
    if len(parts) <= 1:
        return False
    # strip leading date "YYYY-MM-DD" if present
    if len(parts) >= 4 and parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
        tail_parts = parts[3:]
    else:
        tail_parts = parts
    # strip trailing -NN / -NNN counter
    while tail_parts and tail_parts[-1].isdigit():
        tail_parts = tail_parts[:-1]
    tail = "-".join(tail_parts)
    if tail and tail in summary:
        return True
    return False


def detect(adapter: AssetRadarAdapter) -> list[DriftFinding]:
    """Detect drift between bug sub-specs and parent spec §9.5 changelog.

    Algorithm:
        1. ``bugs = adapter.list_bug_specs()``
        2. For each bug, resolve ``parent = adapter.parse_parent_spec(bug.slug)``.
        3. If ``parent is None`` → WARNING ``bug_no_parent``.
        4. Else locate parent SpecLocation via ``adapter.list_specs()``; if
           missing → WARNING ``bug_parent_missing``.
        5. Parse parent's §9.5 changelog and check each ``row.summary`` for
           ``bug.slug`` (or its tail segment). If no row matches → ERROR
           ``bug_unclosed``.
    """
    bugs = adapter.list_bug_specs()
    specs = adapter.list_specs()
    findings: list[DriftFinding] = []

    for bug in bugs:
        parent_id = adapter.parse_parent_spec(bug.slug)
        if parent_id is None:
            findings.append(
                DriftFinding(
                    detector="D6",
                    severity=Severity.WARNING,
                    spec_path=bug.rel_path,
                    message=f"bug 子 spec 未声明父 spec: slug={bug.slug}",
                    evidence={
                        "kind": "bug_no_parent",
                        "bug_slug": bug.slug,
                    },
                )
            )
            continue

        parent_spec = _find_parent_spec(parent_id, specs)
        if parent_spec is None:
            findings.append(
                DriftFinding(
                    detector="D6",
                    severity=Severity.WARNING,
                    spec_path=bug.rel_path,
                    message=(
                        f"bug 声明的父 spec 不在 list_specs() 里: "
                        f"slug={bug.slug} parent={parent_id}"
                    ),
                    evidence={
                        "kind": "bug_parent_missing",
                        "bug_slug": bug.slug,
                        "parent_spec": parent_id,
                    },
                )
            )
            continue

        text = Path(parent_spec.spec_md).read_text(encoding="utf-8")
        changelog = adapter.parse_changelog_table(text)
        if not any(_slug_match(bug.slug, row.summary) for row in changelog):
            findings.append(
                DriftFinding(
                    detector="D6",
                    severity=Severity.ERROR,
                    spec_path=bug.rel_path,
                    message=(
                        f"bug 未在父 spec §9.5 changelog 出现: "
                        f"slug={bug.slug} parent={parent_spec.rel_spec_id}"
                    ),
                    evidence={
                        "kind": "bug_unclosed",
                        "bug_slug": bug.slug,
                        "parent_spec": parent_spec.rel_spec_id,
                        "changelog_versions": [row.version for row in changelog],
                    },
                )
            )

    return findings