"""Compare two versions of context files."""

from contextbench.diagnoser import diagnose
from contextbench.loader import load_context_files
from contextbench.models import ComparisonReport


def compare_versions(
    before_path: str, after_path: str, model: str = "claude-haiku-4-5-20251001"
) -> ComparisonReport:
    """Compare two versions of context files."""
    before_files = load_context_files([before_path])
    after_files = load_context_files([after_path])

    before_report = diagnose(before_files, model)
    after_report = diagnose(after_files, model)

    before_titles = {i.title for i in before_report.issues}
    after_titles = {i.title for i in after_report.issues}

    improvements = tuple(sorted(before_titles - after_titles))
    regressions = tuple(sorted(after_titles - before_titles))

    return ComparisonReport(
        before=before_report,
        after=after_report,
        token_diff=after_report.total_tokens - before_report.total_tokens,
        improvements=improvements,
        regressions=regressions,
    )
