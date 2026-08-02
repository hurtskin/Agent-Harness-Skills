# drift-check

> Spec ↔ code drift detector — 6 classes of automated validation.

Generic via Adapter pattern. Ships with a template adapter that you customize
for your project's spec layout (e.g., `.trae/specs/*`, `docs/specs/*`).

## What it detects

| ID | Class | Severity |
|---|---|---|
| D1 | spec three-piece (spec.md / tasks.md / checklist.md) version sync | error |
| D2 | spec field table ↔ Pydantic BaseModel annotations | error |
| D3 | Gherkin Scenario count ↔ TC markers ↔ `def test_` count | error |
| D4 | tasks.md `⏳/✅ T-XX` state vs source file existence + content | error / warning |
| D5 | `§XX` lesson reference liveness (refs without `## §XX` anchor in lessons-learned.md) | error |
| D6 | bug sub-spec → parent spec §9.5 changelog closure | error / warning |

## Install

```bash
cd tools/drift_check
uv sync --extra dev
```

## CLI

```bash
# Scan project root, default text format
uv run drift-check scan --project-root .

# JSON output (machine-readable)
uv run drift-check scan --project-root . --format json

# Run only specific detectors (repeatable)
uv run drift-check scan --project-root . --only D1 --only D4

# List available detectors
uv run drift-check list-detectors
```

Exit code: `0` = no errors, `1` = any error finding.

## Writing a custom adapter

Implement `drift_check.adapters.base.SpecAdapter` to support your own spec
layout:

```python
from dataclasses import dataclass
from drift_check.adapters.base import (
    BugSpec, CodeTarget, FieldSpec, SpecAdapter, SpecLocation,
)
from drift_check.detectors.common import DriftFinding


class MyProjectAdapter(SpecAdapter):
    def project_root(self): ...
    def list_specs(self) -> list[SpecLocation]: ...
    def list_code_targets(self) -> list[CodeTarget]: ...
    def parse_field_table(self, md_text: str) -> list[FieldSpec]: ...
    def parse_gherkin_count(self, md_text: str) -> int: ...
    def parse_task_states(self, md_text: str) -> list[TaskState]: ...
    def parse_task_code_target(self, task_id: str, tasks_md: str) -> CodeTarget | None: ...
    def parse_lesson_refs(self, md_text: str) -> list[str]: ...
    def lesson_refs_file(self) -> Path: ...
    def decision_log_file(self) -> Path | None: ...
    def list_bug_specs(self) -> list[BugSpec]: ...
    def parse_parent_spec(self, bug_slug: str) -> str | None: ...
    def parse_changelog_table(self, spec_md_text: str) -> list[dict]: ...
```

Then plug it into the CLI by passing the adapter instance directly.

## Architecture

```
src/drift_check/
├── __init__.py
├── cli.py                       # click entry point (scan / list-detectors / init)
├── adapters/
│   ├── base.py                  # SpecAdapter Protocol + dataclasses
│   └── template.py              # TemplateAdapter (customize for your project)
└── detectors/
    ├── common.py                # DriftFinding, Severity
    ├── d1_version.py            # three-piece version sync
    ├── d2_field.py              # spec field table ↔ BaseModel
    ├── d3_gherkin.py            # Gherkin / TC / tests count
    ├── d4_task_state.py         # tasks.md state ↔ source file
    ├── d5_lesson_ref.py         # §XX reference liveness
    └── d6_bug_sync.py           # bug → parent spec changelog
```

## Testing

```bash
uv run pytest -v
```

## Design notes

- **Generic via Adapter** — detectors know nothing about your project's
  directory layout or naming conventions. All project-specific knowledge
  lives in the adapter.
- **No mocks in tests** — every test uses a real adapter pointing at
  `tmp_path` with a real fixture directory. This catches adapter/detector
  contract drift.
- **Severity rules** — D1, D2, D3, D5 default to `error` (CI-failing);
  D4 and D6 have both `error` (real drift) and `warning` (boundary cases
  like missing target files, parent spec absent).

## Why this tool exists

The project's docs are produced by a spec-writing skill with a rigid 10-section
template. Over time, spec.md / tasks.md / checklist.md fields drift away from
the corresponding code (BaseModel fields, test counts, status markers, bug
closures). This tool makes those drifts visible and CI-fail-able.
