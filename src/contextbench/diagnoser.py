"""Claude API-based context file diagnosis."""

import json
import logging
import os
import time

import anthropic

from contextbench.models import ContextFile, DiagnosisReport, Issue, IssueType, Severity
from contextbench.tokenizer import count_tokens, find_local_issues

logger = logging.getLogger(__name__)

MAX_RETRIES = 2

DIAGNOSIS_PROMPT = """## Context Files to Analyze

{files_content}

## Analysis Instructions

Analyze these AI agent context files (CLAUDE.md, SOUL.md, rules/) for issues that waste tokens, confuse the agent, or reduce instruction effectiveness.

Find the following:

### 1. Duplicate/Overlapping Instructions
Instructions that say the same thing in different words or locations.
Cite both locations (file:line), explain the overlap, suggest which to keep.

### 2. Contradictory Directives
Instructions that conflict with each other.
Cite both locations, explain the contradiction, suggest resolution.

### 3. Ambiguous Instructions
Directives an AI agent could interpret multiple ways.
Cite location, explain ambiguity, suggest clearer phrasing.

### 4. Verbose / Low-Value Content
Sections that use many tokens to convey little actionable information.
Cite location, current token count, suggest concise replacement.

### 5. Dead Rules
Instructions referencing tools, frameworks, or patterns not mentioned elsewhere, suggesting they may be outdated.

## Output (strict JSON)
{{
  "issues": [
    {{
      "issue_type": "duplicate|overlap|contradiction|ambiguity|verbosity|dead_rule",
      "severity": "critical|high|medium|low",
      "title": "short description in Korean",
      "description": "detailed explanation in Korean",
      "locations": ["file.md:L12-L15", "rules/coding.md:L3-L8"],
      "suggestion": "actionable fix in Korean",
      "estimated_waste_tokens": 150
    }}
  ],
  "summary": "One paragraph overall assessment in Korean",
  "total_estimated_waste_percentage": 35
}}"""


def diagnose(files: list[ContextFile], model: str = "claude-haiku-4-5-20251001", use_llm: bool = True) -> DiagnosisReport:
    """Run diagnosis: local checks + optional LLM analysis."""
    if not files:
        return DiagnosisReport(summary="분석할 파일이 없습니다.")

    local_issues = find_local_issues(files)

    llm_issues: list[Issue] = []
    summary = ""
    llm_waste_pct = 0.0

    if use_llm:
        llm_issues, summary, llm_waste_pct = _run_llm_diagnosis(files, model)

    all_issues = tuple(local_issues + llm_issues)
    total_tokens = sum(f.token_count for f in files)
    waste_tokens = sum(i.estimated_waste_tokens for i in all_issues)
    waste_pct = (waste_tokens / total_tokens * 100) if total_tokens > 0 else 0.0

    if not summary:
        summary = f"{'로컬 + LLM' if use_llm else '로컬'} 검사 완료: {len(all_issues)}건 발견"
        if not use_llm:
            summary += " (LLM 분석 미실행)"

    return DiagnosisReport(
        files=tuple(files),
        issues=all_issues,
        total_tokens=total_tokens,
        estimated_waste_tokens=waste_tokens,
        waste_percentage=max(waste_pct, llm_waste_pct),
        summary=summary,
        model_used=model if use_llm else "local-only",
    )


def _format_files_for_prompt(files: list[ContextFile]) -> str:
    """Format files with line numbers for the diagnosis prompt."""
    parts = []
    for f in files:
        numbered_lines = "\n".join(
            f"{i + 1}: {line}" for i, line in enumerate(f.content.split("\n"))
        )
        parts.append(f"=== {f.path} ({f.token_count} tokens) ===\n{numbered_lines}")
    return "\n\n".join(parts)


def _run_llm_diagnosis(
    files: list[ContextFile], model: str
) -> tuple[list[Issue], str, float]:
    """Run Claude API diagnosis with retry."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set")
        return [], "API 키가 설정되지 않았습니다.", 0.0

    files_content = _format_files_for_prompt(files)
    prompt = DIAGNOSIS_PROMPT.format(files_content=files_content)

    client = anthropic.Anthropic(api_key=api_key)

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=8000,
                temperature=0.2,
                system="You are a JSON-only API. Return ONLY valid JSON. No markdown, no commentary, no code fences.",
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            data = json.loads(content)
            return _parse_issues(data), data.get("summary", ""), data.get("total_estimated_waste_percentage", 0.0)

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2)
        except Exception as e:
            logger.warning(f"Claude API error (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2)

    return [], "LLM 분석 실패 (재시도 초과)", 0.0


SEVERITY_MAP = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
}

ISSUE_TYPE_MAP = {
    "duplicate": IssueType.DUPLICATE,
    "overlap": IssueType.OVERLAP,
    "contradiction": IssueType.CONTRADICTION,
    "ambiguity": IssueType.AMBIGUITY,
    "verbosity": IssueType.VERBOSITY,
    "dead_rule": IssueType.DEAD_RULE,
}


def _parse_issues(data: dict) -> list[Issue]:
    """Parse LLM JSON response into Issue objects."""
    issues = []
    for item in data.get("issues", []):
        issue_type = ISSUE_TYPE_MAP.get(item.get("issue_type", ""), IssueType.AMBIGUITY)
        severity = SEVERITY_MAP.get(item.get("severity", ""), Severity.MEDIUM)
        issues.append(
            Issue(
                issue_type=issue_type,
                severity=severity,
                title=item.get("title", ""),
                description=item.get("description", ""),
                locations=tuple(item.get("locations", [])),
                suggestion=item.get("suggestion", ""),
                estimated_waste_tokens=item.get("estimated_waste_tokens", 0),
            )
        )
    return issues
