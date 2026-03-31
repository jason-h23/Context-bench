"""Tests for data models."""

from contextbench.models import (
    ComparisonReport,
    ContextFile,
    DiagnosisReport,
    Issue,
    IssueType,
    Severity,
)


def test_context_file_frozen():
    f = ContextFile(path="test.md", content="hello", token_count=1, line_count=1)
    try:
        f.path = "changed"
        assert False, "Should have raised"
    except AttributeError:
        pass


def test_issue_creation():
    issue = Issue(
        issue_type=IssueType.DUPLICATE,
        severity=Severity.HIGH,
        title="test",
        description="desc",
        locations=("a.md:L1", "b.md:L2"),
        suggestion="fix it",
        estimated_waste_tokens=100,
    )
    assert issue.severity == Severity.HIGH
    assert len(issue.locations) == 2
    assert issue.estimated_waste_tokens == 100


def test_diagnosis_report_defaults():
    report = DiagnosisReport()
    assert report.files == ()
    assert report.issues == ()
    assert report.total_tokens == 0
    assert report.waste_percentage == 0.0
    assert report.generated_at is not None


def test_comparison_report_defaults():
    report = ComparisonReport()
    assert report.before is None
    assert report.after is None
    assert report.token_diff == 0
    assert report.improvements == ()
    assert report.regressions == ()


def test_severity_ordering():
    assert Severity.CRITICAL.value == "critical"
    assert Severity.LOW.value == "low"


def test_issue_type_values():
    assert IssueType.DUPLICATE.value == "duplicate"
    assert IssueType.CONTRADICTION.value == "contradiction"
    assert IssueType.DEAD_RULE.value == "dead_rule"
