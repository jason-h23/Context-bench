"""CLI entrypoint for contextbench."""

import logging
import os
from pathlib import Path

import click
from dotenv import load_dotenv

from contextbench import __version__
from contextbench.comparer import compare_versions
from contextbench.diagnoser import diagnose
from contextbench.formatter import format_json, format_markdown, format_terminal
from contextbench.loader import load_context_files
from contextbench.tokenizer import count_tokens_by_section

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def _load_env():
    """Load .env from current dir or project root."""
    for candidate in [".env", str(Path(__file__).parent.parent.parent / ".env")]:
        if os.path.exists(candidate):
            load_dotenv(candidate)
            return


@click.group()
@click.version_option(version=__version__)
def cli():
    """contextbench: Diagnose AI agent context files."""
    _load_env()


@cli.command(name="diagnose")
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--format", "-f", "fmt", type=click.Choice(["terminal", "markdown", "json"]),
              default="terminal", help="Output format")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Write report to file")
@click.option("--model", "-m", default="claude-haiku-4-5-20251001",
              help="Claude model for diagnosis")
@click.option("--no-llm", is_flag=True, default=False,
              help="Skip LLM analysis, only run local checks")
def diagnose_cmd(paths, fmt, output, model, no_llm):
    """Analyze context file(s) for issues.

    Examples:
      contextbench diagnose CLAUDE.md
      contextbench diagnose CLAUDE.md rules/
      contextbench diagnose --no-llm .
    """
    files = load_context_files(list(paths))
    if not files:
        click.echo("No context files found.")
        return

    report = diagnose(files, model, use_llm=not no_llm)

    formatters = {"terminal": format_terminal, "markdown": format_markdown, "json": format_json}
    result = formatters[fmt](report)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(result)
        click.echo(f"Report saved to: {output}")
    else:
        click.echo(result)


@cli.command()
@click.argument("before", type=click.Path(exists=True))
@click.argument("after", type=click.Path(exists=True))
@click.option("--model", "-m", default="claude-haiku-4-5-20251001")
def compare(before, after, model):
    """Compare two context file versions.

    Examples:
      contextbench compare CLAUDE.md.bak CLAUDE.md
    """
    result = compare_versions(before, after, model)

    click.echo(f"\n  Token diff: {result.token_diff:+d}")
    click.echo(f"  Before: {result.before.total_tokens:,} tokens, {len(result.before.issues)} issues")
    click.echo(f"  After:  {result.after.total_tokens:,} tokens, {len(result.after.issues)} issues")

    if result.improvements:
        click.echo(click.style(f"\n  Resolved ({len(result.improvements)}):", fg="green"))
        for imp in result.improvements:
            click.echo(f"    ✅ {imp}")

    if result.regressions:
        click.echo(click.style(f"\n  New issues ({len(result.regressions)}):", fg="red"))
        for reg in result.regressions:
            click.echo(f"    ❌ {reg}")

    click.echo("")


@cli.command()
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--breakdown", "-b", is_flag=True, default=False,
              help="Show per-section token breakdown")
def tokencount(paths, breakdown):
    """Count tokens in context file(s).

    Examples:
      contextbench tokencount CLAUDE.md
      contextbench tokencount rules/ --breakdown
    """
    files = load_context_files(list(paths))
    if not files:
        click.echo("No context files found.")
        return

    total = 0
    for f in sorted(files, key=lambda x: x.token_count, reverse=True):
        name = f.path.split("/")[-1]
        click.echo(f"  {name:<35} {f.token_count:>6} tokens  ({f.line_count} lines)")
        total += f.token_count

        if breakdown:
            sections = count_tokens_by_section(f.content)
            for section_name, tokens in sections:
                if tokens > 0:
                    click.echo(f"    {'└ ' + section_name:<33} {tokens:>6}")

    click.echo(f"\n  {'Total':<35} {total:>6} tokens")


if __name__ == "__main__":
    cli()
