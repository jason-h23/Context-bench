"""Output formatting for terminal, markdown, and JSON."""

import json

import click

from contextbench.models import DiagnosisReport, Severity

SEVERITY_COLORS = {
    Severity.CRITICAL: "red",
    Severity.HIGH: "yellow",
    Severity.MEDIUM: "cyan",
    Severity.LOW: "white",
}

SEVERITY_LABELS = {
    Severity.CRITICAL: "CRITICAL",
    Severity.HIGH: "HIGH",
    Severity.MEDIUM: "MEDIUM",
    Severity.LOW: "LOW",
}


def format_terminal(report: DiagnosisReport) -> str:
    """Format report for terminal output."""
    lines = [
        "",
        click.style("  Context Diagnosis Report", bold=True),
        click.style("  ========================", dim=True),
        "",
        f"  Files Analyzed: {len(report.files)}",
        f"  Total Tokens:   {report.total_tokens:,}",
        f"  Estimated Waste: ~{report.estimated_waste_tokens:,} tokens ({report.waste_percentage:.0f}%)",
        f"  Issues Found:   {len(report.issues)}",
        "",
    ]

    if report.issues:
        sorted_issues = sorted(report.issues, key=lambda i: list(Severity).index(i.severity))

        for issue in sorted_issues:
            color = SEVERITY_COLORS.get(issue.severity, "white")
            label = SEVERITY_LABELS.get(issue.severity, "?")
            lines.append(
                f"  [{click.style(label, fg=color, bold=True)}] {issue.title}"
            )
            for loc in issue.locations:
                lines.append(f"    {click.style(loc, dim=True)}")
            lines.append(f"    {issue.description}")
            lines.append(f"    {click.style('Fix:', fg='green')} {issue.suggestion}")
            if issue.estimated_waste_tokens > 0:
                lines.append(f"    {click.style(f'~{issue.estimated_waste_tokens} tokens', dim=True)}")
            lines.append("")

    if report.files:
        lines.append(click.style("  Token Breakdown:", bold=True))
        for f in sorted(report.files, key=lambda x: x.token_count, reverse=True):
            pct = (f.token_count / report.total_tokens * 100) if report.total_tokens > 0 else 0
            bar_len = int(pct / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            name = f.path.split("/")[-1]
            lines.append(f"    {name:<30} {f.token_count:>6} tokens  {bar} {pct:.0f}%")
        lines.append("")

    if report.summary:
        lines.append(f"  {click.style('Summary:', bold=True)} {report.summary}")
        lines.append("")

    return "\n".join(lines)


def format_markdown(report: DiagnosisReport) -> str:
    """Format report as markdown."""
    lines = [
        "# Context Diagnosis Report",
        "",
        f"**Files**: {len(report.files)} | **Tokens**: {report.total_tokens:,} | **Waste**: ~{report.waste_percentage:.0f}%",
        "",
    ]

    if report.issues:
        lines.append(f"## Issues ({len(report.issues)})")
        lines.append("")

        sorted_issues = sorted(report.issues, key=lambda i: list(Severity).index(i.severity))
        for issue in sorted_issues:
            label = SEVERITY_LABELS.get(issue.severity, "?")
            lines.append(f"### {label}: {issue.title}")
            lines.append(f"- **Type**: {issue.issue_type.value}")
            lines.append(f"- **Locations**: {', '.join(f'`{loc}`' for loc in issue.locations)}")
            lines.append(f"- **Description**: {issue.description}")
            lines.append(f"- **Suggestion**: {issue.suggestion}")
            if issue.estimated_waste_tokens > 0:
                lines.append(f"- **Estimated waste**: {issue.estimated_waste_tokens} tokens")
            lines.append("")

    if report.files:
        lines.append("## Token Breakdown")
        lines.append("")
        lines.append("| File | Tokens | % |")
        lines.append("|------|--------|---|")
        for f in sorted(report.files, key=lambda x: x.token_count, reverse=True):
            pct = (f.token_count / report.total_tokens * 100) if report.total_tokens > 0 else 0
            name = f.path.split("/")[-1]
            lines.append(f"| {name} | {f.token_count:,} | {pct:.0f}% |")
        lines.append("")

    if report.summary:
        lines.append(f"## Summary")
        lines.append("")
        lines.append(report.summary)
        lines.append("")

    return "\n".join(lines)


def format_json(report: DiagnosisReport) -> str:
    """Format report as JSON."""
    data = {
        "files": [
            {"path": f.path, "token_count": f.token_count, "line_count": f.line_count}
            for f in report.files
        ],
        "issues": [
            {
                "issue_type": i.issue_type.value,
                "severity": i.severity.value,
                "title": i.title,
                "description": i.description,
                "locations": list(i.locations),
                "suggestion": i.suggestion,
                "estimated_waste_tokens": i.estimated_waste_tokens,
            }
            for i in report.issues
        ],
        "total_tokens": report.total_tokens,
        "estimated_waste_tokens": report.estimated_waste_tokens,
        "waste_percentage": report.waste_percentage,
        "summary": report.summary,
        "model_used": report.model_used,
        "generated_at": report.generated_at,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
