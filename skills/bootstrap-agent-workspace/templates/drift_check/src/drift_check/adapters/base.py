"""Base adapter protocol and dataclasses for drift-check."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class SpecLocation:
    """Location of a spec three-piece (spec.md / tasks.md / checklist.md)."""

    spec_dir: Path
    spec_md: Path
    tasks_md: Path
    checklist_md: Path
    rel_spec_id: str  # e.g., "spec-00-arch/sub-01-platform"


@dataclass(frozen=True)
class CodeTarget:
    """A code file that a spec task targets."""

    py_path: Path
    rel_path: str  # e.g., "src/asset_radar/protocol.py"
    layer: str  # e.g., "asset_radar", "api", "worker"
    class_names: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FieldSpec:
    """A field parsed from a spec markdown table."""

    name: str
    type: str
    required: bool
    default: str | None = None


@dataclass(frozen=True)
class TaskState:
    """A task parsed from tasks.md with its state."""

    task_id: str  # e.g., "T-sub01-01"
    state: str  # "done" | "pending" | "in_progress"
    code_target: CodeTarget | None = None


@dataclass(frozen=True)
class BugSpec:
    """A bug sub-spec location."""

    spec_dir: Path
    spec_md: Path
    slug: str  # e.g., "validation-error-handling"
    rel_path: str  # e.g., ".trae/specs/bug/validation-error-handling/spec.md"


class SpecAdapter(Protocol):
    """Protocol for project-specific spec adapters."""

    def project_root(self) -> Path:
        """Return the project root directory."""
        ...

    def list_specs(self) -> list[SpecLocation]:
        """List all spec three-pieces in the project."""
        ...

    def list_code_targets(self) -> list[CodeTarget]:
        """List all code files that specs may target."""
        ...

    def parse_field_table(self, md_text: str) -> list[FieldSpec]:
        """Parse a markdown field table into FieldSpec list."""
        ...

    def parse_gherkin_count(self, md_text: str) -> int:
        """Count Gherkin Scenario / Scenario Outline markers in spec."""
        ...

    def parse_task_states(self, md_text: str) -> list[TaskState]:
        """Parse tasks.md into TaskState list."""
        ...

    def parse_task_code_target(self, task_id: str, tasks_md: str) -> CodeTarget | None:
        """Resolve a task id to the code file it describes."""
        ...

    def parse_lesson_refs(self, md_text: str) -> list[str]:
        """Extract lesson §XX references from markdown."""
        ...

    def lesson_refs_file(self) -> Path:
        """Return path to lessons-learned.md."""
        ...

    def decision_log_file(self) -> Path | None:
        """Return path to decision log file, or None if not found."""
        ...

    def list_bug_specs(self) -> list[BugSpec]:
        """List all bug sub-specs."""
        ...

    def parse_parent_spec(self, bug_slug: str) -> str | None:
        """Parse parent spec id from bug slug (e.g., 'sub-03' -> 'spec-00-arch')."""
        ...

    def parse_changelog_table(self, spec_md_text: str) -> list[dict]:
        """Parse §9.5 changelog table from spec.md."""
        ...
