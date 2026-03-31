"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_claude_md(tmp_path):
    content = "# Project Guide\n## Build\n```bash\ncargo test\n```\n## Rules\nAlways use immutability.\n"
    f = tmp_path / "CLAUDE.md"
    f.write_text(content)
    return f


@pytest.fixture
def sample_rules_dir(tmp_path):
    rules = tmp_path / "rules"
    rules.mkdir()
    (rules / "security.md").write_text("# Security\nValidate all inputs.\nNever hardcode secrets.\n")
    (rules / "coding.md").write_text("# Coding\nValidate all inputs.\nUse immutable patterns.\n")
    return rules


@pytest.fixture
def duplicate_files(tmp_path):
    content = "# Rules\nAlways validate inputs.\nNever mutate state.\n"
    (tmp_path / "a.md").write_text(content)
    (tmp_path / "b.md").write_text(content)
    return tmp_path


@pytest.fixture
def sample_diagnosis_json():
    return {
        "issues": [
            {
                "issue_type": "duplicate",
                "severity": "high",
                "title": "중복 규칙 발견",
                "description": "입력 검증 규칙이 두 파일에서 반복됨",
                "locations": ["security.md:L2", "coding.md:L2"],
                "suggestion": "하나의 파일로 통합하세요",
                "estimated_waste_tokens": 50,
            },
            {
                "issue_type": "ambiguity",
                "severity": "medium",
                "title": "모호한 표현",
                "description": "'적절하게' 처리하라는 지시가 불명확",
                "locations": ["CLAUDE.md:L5"],
                "suggestion": "'에러 발생 시 throw하라'로 구체화",
                "estimated_waste_tokens": 0,
            },
        ],
        "summary": "2건의 이슈 발견",
        "total_estimated_waste_percentage": 25,
    }
