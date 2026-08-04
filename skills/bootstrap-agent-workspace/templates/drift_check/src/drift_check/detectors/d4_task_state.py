"""D4 detector: tasks.md state vs source file existence."""

from __future__ import annotations

import re

from drift_check.adapters.base import SpecAdapter, SpecLocation
from drift_check.detectors.common import DriftFinding, Severity


# Skip non-code tasks (docs, review, CI, lessons) — they intentionally
# have no code target. v87 Q3 spec review found 198 task_target_unknown
# findings break down to ~120 doc tasks + ~50 review/CI + ~25 real code.
_DOC_TASK_KEYWORDS = (
    "spec.md",
    "tasks.md",
    "checklist.md",
    "self-check",
    "changelog",
    "lessons",
    "决策日志",
    "AGENTS.md",
    "review",
    "审查",
    "评审",
    "自检",
    "审阅",
    "回填",
    "Lint",
    "grep",
    "CI",
    "commit",
    "decisions",
    "排期清单",
    "decision-log",
    "文档",
)


def _is_doc_task(task_id: str, tasks_md_text: str) -> bool:
    """Return True if the task line for task_id mentions a doc/review keyword."""
    for line in tasks_md_text.splitlines():
        if task_id not in line:
            continue
        if "T-" not in line and "?" not in line:
            continue
        low = line.lower()
        if any(kw.lower() in low for kw in _DOC_TASK_KEYWORDS):
            return True
        return False
    return False


def detect(
    spec: SpecLocation,
    adapter: SpecAdapter,
) -> list[DriftFinding]:
    """Detect drift between tasks.md task states and actual code presence.

    Algorithm:
    1. Parse task states from spec.tasks.md
    2. For each TaskState:
       a. If task is doc/review task -> skip
       b. Resolve code target via adapter.parse_task_code_target
       c. If code target None -> emit WARNING task_target_unknown
       d. If state done but py_path missing -> emit ERROR phantom_done
       e. If state pending but py_path exists -> emit ERROR phantom_pending
       f. If file exists but has no class/def -> emit WARNING empty_code_file
    """
    rel = spec.rel_spec_id
    text = spec.tasks_md.read_text(encoding="utf-8")
    states = adapter.parse_task_states(text)

    findings: list[DriftFinding] = []

    for ts in states:
        if _is_doc_task(ts.task_id, text):
            continue

        code = adapter.parse_task_code_target(ts.task_id, text, spec.spec_md)
        if code is None:
            findings.append(
                DriftFinding(
                    detector="D4",
                    severity=Severity.WARNING,
                    spec_path=f"{rel}/tasks.md",
                    message=f"任务 {ts.task_id} 未声明目标代码文件，无法判定状态",
                    evidence={
                        "kind": "task_target_unknown",
                        "task_id": ts.task_id,
                        "task_state": ts.state,
                    },
                )
            )
            continue

        exists = code.py_path.exists()
        if ts.state == "done" and not exists:
            findings.append(
                DriftFinding(
                    detector="D4",
                    severity=Severity.ERROR,
                    spec_path=f"{rel}/tasks.md",
                    message=(
                        f"任务 {ts.task_id} 标 done，但目标文件缺失：{code.rel_path}"
                    ),
                    evidence={
                        "kind": "phantom_done",
                        "task_id": ts.task_id,
                        "expected_file": code.rel_path,
                    },
                )
            )
            continue

        if ts.state == "pending" and exists:
            findings.append(
                DriftFinding(
                    detector="D4",
                    severity=Severity.ERROR,
                    spec_path=f"{rel}/tasks.md",
                    message=(
                        f"任务 {ts.task_id} 标 pending，但目标文件已存在：{code.rel_path}"
                    ),
                    evidence={
                        "kind": "phantom_pending",
                        "task_id": ts.task_id,
                        "unexpected_file": code.rel_path,
                    },
                )
            )
            continue

        if exists and ts.state == "done":
            if code.py_path.name == "__init__.py":
                continue
            code_text = code.py_path.read_text(encoding="utf-8")
            has_content = bool(re.search(
                r"^[ \t]*(?:"
                r"class\s+\w+"
                r"|def\s+\w+"
                r"|function\s+\w+"
                r"|async\s+function\s+\w+"
                r"|export\s+(?:default\s+)?(?:class|function)\s+\w+"
                r")",
                code_text, re.MULTILINE,
            ))
            if not has_content:
                findings.append(
                    DriftFinding(
                        detector="D4",
                        severity=Severity.WARNING,
                        spec_path=f"{rel}/tasks.md",
                        message=(
                            f"任务 {ts.task_id} 标 done，但目标文件无任何 class/def：{code.rel_path}"
                        ),
                        evidence={
                            "kind": "empty_code_file",
                            "task_id": ts.task_id,
                            "code_file": code.rel_path,
                        },
                    )
                )

    return findings
