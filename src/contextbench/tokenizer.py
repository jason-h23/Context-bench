"""Token counting and local duplicate detection."""

import hashlib
import logging
import re

import tiktoken

from contextbench.models import ContextFile, Issue, IssueType, Severity

logger = logging.getLogger(__name__)

_encoding = None


def _get_encoding():
    """Lazy-initialize tiktoken encoding."""
    global _encoding
    if _encoding is None:
        _encoding = tiktoken.get_encoding("cl100k_base")
    return _encoding


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken cl100k_base."""
    return len(_get_encoding().encode(text))


def count_tokens_by_section(text: str) -> list[tuple[str, int]]:
    """Split by markdown headings and count tokens per section."""
    sections: list[tuple[str, int]] = []
    current_heading = "(preamble)"
    current_lines: list[str] = []

    for line in text.split("\n"):
        if re.match(r"^#{1,3}\s+", line):
            if current_lines:
                content = "\n".join(current_lines)
                sections.append((current_heading, count_tokens(content)))
            current_heading = line.strip().lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        content = "\n".join(current_lines)
        sections.append((current_heading, count_tokens(content)))

    return sections


def find_local_issues(files: list[ContextFile]) -> list[Issue]:
    """Run all local (non-LLM) checks."""
    issues: list[Issue] = []
    issues.extend(_find_exact_duplicates(files))
    issues.extend(_find_near_duplicates(files))
    return issues


def _normalize(text: str) -> str:
    """Normalize text for comparison."""
    return re.sub(r"\s+", " ", text.strip().lower())


def _find_exact_duplicates(files: list[ContextFile]) -> list[Issue]:
    """Find files with identical content via SHA-256 hash."""
    hashes: dict[str, list[str]] = {}
    for f in files:
        h = hashlib.sha256(_normalize(f.content).encode()).hexdigest()
        hashes.setdefault(h, []).append(f.path)

    issues = []
    for paths in hashes.values():
        if len(paths) > 1:
            issues.append(
                Issue(
                    issue_type=IssueType.DUPLICATE,
                    severity=Severity.HIGH,
                    title=f"동일한 내용의 파일 {len(paths)}개 발견",
                    description=f"다음 파일들이 내용이 완전히 동일합니다.",
                    locations=tuple(paths),
                    suggestion="하나만 남기고 나머지는 삭제하거나, 공통 파일로 통합하세요.",
                    estimated_waste_tokens=sum(
                        f.token_count for f in files if f.path in paths[1:]
                    ),
                )
            )
    return issues


def _find_near_duplicates(files: list[ContextFile]) -> list[Issue]:
    """Find files with >70% line overlap."""
    issues = []
    checked: set[tuple[str, str]] = set()

    for i, f1 in enumerate(files):
        lines1 = set(_normalize(line) for line in f1.content.split("\n") if line.strip())
        if not lines1:
            continue

        for f2 in files[i + 1 :]:
            pair = (f1.path, f2.path)
            if pair in checked:
                continue
            checked.add(pair)

            lines2 = set(_normalize(line) for line in f2.content.split("\n") if line.strip())
            if not lines2:
                continue

            overlap = lines1 & lines2
            smaller = min(len(lines1), len(lines2))
            if smaller == 0:
                continue

            ratio = len(overlap) / smaller
            if ratio > 0.7:
                issues.append(
                    Issue(
                        issue_type=IssueType.OVERLAP,
                        severity=Severity.HIGH,
                        title=f"높은 유사도 ({ratio:.0%}) 발견",
                        description=f"{f1.path}와 {f2.path}의 내용이 {ratio:.0%} 겹칩니다.",
                        locations=(f1.path, f2.path),
                        suggestion="겹치는 내용을 하나의 파일로 통합하세요.",
                        estimated_waste_tokens=int(min(f1.token_count, f2.token_count) * ratio),
                    )
                )
    return issues
