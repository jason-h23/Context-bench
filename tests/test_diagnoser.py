"""Tests for diagnoser JSON parsing (no API calls)."""

from contextbench.diagnoser import _parse_issues
from contextbench.models import IssueType, Severity


def test_parse_valid_issues(sample_diagnosis_json):
    issues = _parse_issues(sample_diagnosis_json)
    assert len(issues) == 2
    assert issues[0].issue_type == IssueType.DUPLICATE
    assert issues[0].severity == Severity.HIGH
    assert issues[0].estimated_waste_tokens == 50
    assert len(issues[0].locations) == 2


def test_parse_empty_issues():
    issues = _parse_issues({"issues": []})
    assert len(issues) == 0


def test_parse_missing_issues_key():
    issues = _parse_issues({})
    assert len(issues) == 0


def test_parse_unknown_issue_type():
    data = {
        "issues": [
            {
                "issue_type": "unknown_type",
                "severity": "low",
                "title": "test",
                "description": "test",
                "locations": [],
                "suggestion": "test",
            }
        ]
    }
    issues = _parse_issues(data)
    assert len(issues) == 1
    assert issues[0].issue_type == IssueType.AMBIGUITY  # fallback


def test_parse_unknown_severity():
    data = {
        "issues": [
            {
                "issue_type": "duplicate",
                "severity": "extreme",
                "title": "test",
                "description": "test",
                "locations": [],
                "suggestion": "test",
            }
        ]
    }
    issues = _parse_issues(data)
    assert issues[0].severity == Severity.MEDIUM  # fallback
