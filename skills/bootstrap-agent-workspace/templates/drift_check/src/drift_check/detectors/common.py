"""Common types for drift detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    """Severity level for drift findings."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class DriftFinding:
    """A single drift finding."""

    detector: str  # e.g., "D1", "D2"
    severity: Severity
    spec_id: str  # e.g., "spec-00-arch/sub-01-platform"
    message: str
    details: dict[str, str] = field(default_factory=dict)
