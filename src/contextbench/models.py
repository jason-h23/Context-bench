"""Data models for contextbench."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueType(Enum):
    DUPLICATE = "duplicate"
    OVERLAP = "overlap"
    CONTRADICTION = "contradiction"
    AMBIGUITY = "ambiguity"
    VERBOSITY = "verbosity"
    DEAD_RULE = "dead_rule"


@dataclass(frozen=True)
class ContextFile:
    """A loaded context file with metadata."""

    path: str
    content: str
    token_count: int
    line_count: int


@dataclass(frozen=True)
class Issue:
    """A single diagnosed issue."""

    issue_type: IssueType
    severity: Severity
    title: str
    description: str
    locations: tuple[str, ...]
    suggestion: str
    estimated_waste_tokens: int = 0


@dataclass(frozen=True)
class DiagnosisReport:
    """Complete diagnosis result."""

    files: tuple[ContextFile, ...] = ()
    issues: tuple[Issue, ...] = ()
    total_tokens: int = 0
    estimated_waste_tokens: int = 0
    waste_percentage: float = 0.0
    summary: str = ""
    model_used: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class ComparisonReport:
    """Result of comparing two context file versions."""

    before: DiagnosisReport | None = None
    after: DiagnosisReport | None = None
    token_diff: int = 0
    improvements: tuple[str, ...] = ()
    regressions: tuple[str, ...] = ()
