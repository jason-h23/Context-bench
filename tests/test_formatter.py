"""Tests for output formatters."""

import json

from contextbench.formatter import format_json, format_markdown, format_terminal
from contextbench.models import (
    ContextFile,
    DiagnosisReport,
    Issue,
    IssueType,
    Severity,
)


def _make_report():
    files = (
        ContextFile(path="CLAUDE.md", content="test", token_count=100, line_count=10),
    )
    issues = (
        Issue(
            issue_type=IssueType.DUPLICATE,
            severity=Severity.HIGH,
            title="중복 규칙",
            description="같은 내용 반복",
            locations=("CLAUDE.md:L1", "rules.md:L5"),
            suggestion="통합하세요",
            estimated_waste_tokens=50,
        ),
        Issue(
            issue_type=IssueType.AMBIGUITY,
            severity=Severity.MEDIUM,
            title="모호한 표현",
            description="해석이 다양함",
            locations=("CLAUDE.md:L3",),
            suggestion="구체화하세요",
        ),
    )
    return DiagnosisReport(
        files=files,
        issues=issues,
        total_tokens=100,
        estimated_waste_tokens=50,
        waste_percentage=50.0,
        summary="테스트 요약",
        model_used="test-model",
    )


def test_format_terminal_contains_severity():
    report = _make_report()
    output = format_terminal(report)
    assert "HIGH" in output
    assert "MEDIUM" in output


def test_format_terminal_contains_title():
    report = _make_report()
    output = format_terminal(report)
    assert "중복 규칙" in output
    assert "모호한 표현" in output


def test_format_terminal_contains_tokens():
    report = _make_report()
    output = format_terminal(report)
    assert "100" in output
    assert "50%" in output


def test_format_markdown_contains_headers():
    report = _make_report()
    output = format_markdown(report)
    assert "# Context Diagnosis Report" in output
    assert "## Issues" in output
    assert "## Token Breakdown" in output


def test_format_markdown_contains_table():
    report = _make_report()
    output = format_markdown(report)
    assert "| File |" in output
    assert "CLAUDE.md" in output


def test_format_json_valid():
    report = _make_report()
    output = format_json(report)
    data = json.loads(output)
    assert data["total_tokens"] == 100
    assert len(data["issues"]) == 2
    assert data["waste_percentage"] == 50.0


def test_format_empty_report():
    report = DiagnosisReport()
    assert "0" in format_terminal(report)
    assert "# Context Diagnosis Report" in format_markdown(report)
    data = json.loads(format_json(report))
    assert data["total_tokens"] == 0
