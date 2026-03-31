"""Tests for tokenizer and local checks."""

from contextbench.models import ContextFile
from contextbench.tokenizer import count_tokens, count_tokens_by_section, find_local_issues


def test_count_tokens_basic():
    tokens = count_tokens("hello world")
    assert tokens > 0
    assert tokens < 10


def test_count_tokens_empty():
    assert count_tokens("") == 0


def test_count_tokens_korean():
    tokens = count_tokens("안녕하세요 반갑습니다")
    assert tokens > 0


def test_count_tokens_by_section_single():
    text = "# Title\nSome content here.\n"
    sections = count_tokens_by_section(text)
    assert len(sections) == 1
    assert sections[0][0] == "Title"


def test_count_tokens_by_section_multiple():
    text = "# Intro\nHello.\n## Rules\nDo this.\n## Notes\nExtra."
    sections = count_tokens_by_section(text)
    assert len(sections) == 3
    headings = [s[0] for s in sections]
    assert "Intro" in headings
    assert "Rules" in headings
    assert "Notes" in headings


def test_count_tokens_by_section_preamble():
    text = "No heading here.\nJust text.\n## First Section\nContent."
    sections = count_tokens_by_section(text)
    assert sections[0][0] == "(preamble)"
    assert sections[1][0] == "First Section"


def test_find_exact_duplicates(duplicate_files):
    files = [
        ContextFile(
            path=str(duplicate_files / "a.md"),
            content=(duplicate_files / "a.md").read_text(),
            token_count=10,
            line_count=3,
        ),
        ContextFile(
            path=str(duplicate_files / "b.md"),
            content=(duplicate_files / "b.md").read_text(),
            token_count=10,
            line_count=3,
        ),
    ]
    issues = find_local_issues(files)
    assert len(issues) >= 1
    assert any(i.issue_type.value == "duplicate" for i in issues)


def test_find_near_duplicates():
    content_a = "# Rules\nValidate all inputs.\nNever hardcode secrets.\nUse immutable patterns.\nLog all errors.\nCheck permissions.\n"
    content_b = "# Rules\nValidate all inputs.\nNever hardcode secrets.\nUse immutable patterns.\nLog all errors.\nReview access.\n"
    files = [
        ContextFile(path="a.md", content=content_a, token_count=20, line_count=5),
        ContextFile(path="b.md", content=content_b, token_count=20, line_count=5),
    ]
    issues = find_local_issues(files)
    has_overlap = any(i.issue_type.value in ("overlap", "duplicate") for i in issues)
    assert has_overlap


def test_no_false_positives_on_distinct_files():
    files = [
        ContextFile(path="a.md", content="# Security\nValidate inputs.", token_count=5, line_count=2),
        ContextFile(path="b.md", content="# Performance\nOptimize queries.", token_count=5, line_count=2),
    ]
    issues = find_local_issues(files)
    duplicates = [i for i in issues if i.issue_type.value in ("duplicate", "overlap")]
    assert len(duplicates) == 0
