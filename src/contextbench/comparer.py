"""Compare two versions of context files."""

from contextbench.diagnoser import diagnose
from contextbench.loader import load_context_files
from contextbench.models import ComparisonReport, Issue


def _issue_key(issue: Issue) -> tuple:
    """Create a stable comparison key for an issue."""
    return (issue.issue_type.value, issue.severity.value, tuple(sorted(issue.locations)))


def compare_versions(
    before_path: str, after_path: str, model: str = "claude-haiku-4-5-20251001"
) -> ComparisonReport:
    """Compare two versions of context files."""
    before_files = load_context_files([before_path])
    after_files = load_context_files([after_path])

    before_report = diagnose(before_files, model)
    after_report = diagnose(after_files, model)

    before_keys = {_issue_key(i): i.title for i in before_report.issues}
    after_keys = {_issue_key(i): i.title for i in after_report.issues}

    resolved_keys = set(before_keys) - set(after_keys)
    new_keys = set(after_keys) - set(before_keys)

    improvements = tuple(sorted(before_keys[k] for k in resolved_keys))
    regressions = tuple(sorted(after_keys[k] for k in new_keys))

    return ComparisonReport(
        before=before_report,
        after=after_report,
        token_diff=after_report.total_tokens - before_report.total_tokens,
        improvements=improvements,
        regressions=regressions,
    )
