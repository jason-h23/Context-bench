"""Tests for file loader."""

from contextbench.loader import load_context_files


def test_load_single_file(sample_claude_md):
    files = load_context_files([str(sample_claude_md)])
    assert len(files) == 1
    assert files[0].path == str(sample_claude_md)
    assert files[0].token_count > 0
    assert files[0].line_count > 0


def test_load_directory_with_rules(tmp_path):
    rules = tmp_path / "rules"
    rules.mkdir()
    (rules / "coding.md").write_text("# Coding\nUse types.")
    (rules / "security.md").write_text("# Security\nValidate.")
    (tmp_path / "CLAUDE.md").write_text("# Guide\nBuild.")

    files = load_context_files([str(tmp_path)])
    assert len(files) == 3
    paths = [f.path for f in files]
    assert any("CLAUDE.md" in p for p in paths)
    assert any("coding.md" in p for p in paths)


def test_load_ignores_non_md(tmp_path):
    (tmp_path / "config.yaml").write_text("key: value")
    (tmp_path / "CLAUDE.md").write_text("# Guide")

    files = load_context_files([str(tmp_path)])
    assert len(files) == 1


def test_load_empty_directory(tmp_path):
    files = load_context_files([str(tmp_path)])
    assert len(files) == 0


def test_load_multiple_paths(sample_claude_md, sample_rules_dir):
    files = load_context_files([str(sample_claude_md), str(sample_rules_dir)])
    assert len(files) == 3
