"""Tests for diagnoser JSON parsing and prompt formatting (no API calls)."""

from contextbench.diagnoser import _format_files_for_prompt, _parse_issues
from contextbench.models import ContextFile, IssueType, Severity


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


def test_format_files_for_prompt_line_numbers():
    f = ContextFile(path="test.md", content="line one\nline two\nline three", token_count=6, line_count=3)
    result = _format_files_for_prompt([f])
    assert "1: line one" in result
    assert "2: line two" in result
    assert "3: line three" in result
    assert "=== test.md (6 tokens) ===" in result


def test_format_files_for_prompt_multiple_files():
    f1 = ContextFile(path="a.md", content="hello", token_count=1, line_count=1)
    f2 = ContextFile(path="b.md", content="world", token_count=1, line_count=1)
    result = _format_files_for_prompt([f1, f2])
    assert "=== a.md" in result
    assert "=== b.md" in result
    assert "1: hello" in result
    assert "1: world" in result


def test_format_files_empty_content():
    f = ContextFile(path="empty.md", content="", token_count=0, line_count=1)
    result = _format_files_for_prompt([f])
    assert "=== empty.md (0 tokens) ===" in result


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
