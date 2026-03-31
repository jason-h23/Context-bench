"""CLI integration tests using Click CliRunner."""

from click.testing import CliRunner

from contextbench.cli import cli


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "diagnose" in result.output
    assert "compare" in result.output
    assert "tokencount" in result.output


def test_cli_tokencount(sample_claude_md):
    runner = CliRunner()
    result = runner.invoke(cli, ["tokencount", str(sample_claude_md)])
    assert result.exit_code == 0
    assert "tokens" in result.output
    assert "Total" in result.output


def test_cli_tokencount_breakdown(sample_claude_md):
    runner = CliRunner()
    result = runner.invoke(cli, ["tokencount", "--breakdown", str(sample_claude_md)])
    assert result.exit_code == 0
    assert "tokens" in result.output


def test_cli_diagnose_no_llm(sample_claude_md, sample_rules_dir):
    runner = CliRunner()
    result = runner.invoke(cli, ["diagnose", "--no-llm", str(sample_claude_md), str(sample_rules_dir)])
    assert result.exit_code == 0
    assert "Context Diagnosis Report" in result.output
    assert "Files Analyzed" in result.output


def test_cli_diagnose_json_format(sample_claude_md):
    runner = CliRunner()
    result = runner.invoke(cli, ["diagnose", "--no-llm", "-f", "json", str(sample_claude_md)])
    assert result.exit_code == 0
    assert '"total_tokens"' in result.output


def test_cli_diagnose_markdown_format(sample_claude_md):
    runner = CliRunner()
    result = runner.invoke(cli, ["diagnose", "--no-llm", "-f", "markdown", str(sample_claude_md)])
    assert result.exit_code == 0
    assert "# Context Diagnosis Report" in result.output


def test_cli_diagnose_output_file(sample_claude_md, tmp_path):
    output_file = tmp_path / "report.md"
    runner = CliRunner()
    result = runner.invoke(cli, [
        "diagnose", "--no-llm", "-f", "markdown",
        "-o", str(output_file), str(sample_claude_md)
    ])
    assert result.exit_code == 0
    assert output_file.exists()
    assert "# Context Diagnosis Report" in output_file.read_text()


def test_cli_no_files_found(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["tokencount", str(tmp_path)])
    assert "No context files found" in result.output
