"""File discovery and loading."""

import logging
import os
from pathlib import Path

from contextbench.models import ContextFile
from contextbench.tokenizer import count_tokens

logger = logging.getLogger(__name__)

CONTEXT_FILE_PATTERNS = [
    "CLAUDE.md",
    "SOUL.md",
    "AGENTS.md",
    "MEMORY.md",
    "IDENTITY.md",
]

CONTEXT_DIR_PATTERNS = [
    "rules",
    ".claude/rules",
    ".claude/skills",
]


def load_context_files(paths: list[str]) -> list[ContextFile]:
    """Load context files from given paths (files or directories)."""
    discovered: list[str] = []

    for p in paths:
        path = Path(p)
        if path.is_file() and path.suffix == ".md":
            discovered.append(str(path))
        elif path.is_dir():
            discovered.extend(_discover_in_directory(str(path)))
        else:
            logger.warning(f"Skipping: {p} (not a .md file or directory)")

    files = []
    for filepath in sorted(set(discovered)):
        ctx_file = _load_single_file(filepath)
        if ctx_file:
            files.append(ctx_file)

    logger.info(f"Loaded {len(files)} context files")
    return files


def _discover_in_directory(directory: str) -> list[str]:
    """Find context files in a directory."""
    found: list[str] = []
    base = Path(directory)

    for name in CONTEXT_FILE_PATTERNS:
        candidate = base / name
        if candidate.exists():
            found.append(str(candidate))

    for dir_pattern in CONTEXT_DIR_PATTERNS:
        rules_dir = base / dir_pattern
        if rules_dir.is_dir():
            for md_file in sorted(rules_dir.glob("**/*.md")):
                found.append(str(md_file))

    # If directory itself contains .md files (e.g., passing rules/ directly)
    if not found:
        for md_file in sorted(base.glob("*.md")):
            found.append(str(md_file))

    return found


MAX_FILE_SIZE = 1_000_000  # 1MB


def _load_single_file(filepath: str) -> ContextFile | None:
    """Read a file and create a ContextFile."""
    try:
        file_size = os.path.getsize(filepath)
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"Skipping {filepath}: {file_size:,} bytes exceeds 1MB limit")
            return None

        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        return ContextFile(
            path=filepath,
            content=content,
            token_count=count_tokens(content),
            line_count=len(content.split("\n")),
        )
    except Exception as e:
        logger.error(f"Failed to load {filepath}: {e}")
        return None
