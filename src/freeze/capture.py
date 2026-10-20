"""Collect the pieces of working state that go into a freeze.

Every step is tolerant of failure: if a command is missing or errors, the
corresponding field holds a short note instead of raising.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

# git diffs can be enormous; keep the prompt bounded.
DIFF_LIMIT = 20_000


@dataclass
class Context:
    repo: str
    branch_status: str
    diff: str
    log: str
    terminal: str


def _run(args, cwd=None):
    """Run a command and return stdout, or a short note on failure."""
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError:
        return f"(command not found: {args[0]})"
    except subprocess.TimeoutExpired:
        return f"(timed out: {' '.join(args)})"
    out = result.stdout.strip()
    if not out and result.stderr.strip():
        return f"(error: {result.stderr.strip()})"
    return out


def truncate(text, limit=DIFF_LIMIT):
    """Trim text to limit characters, marking what was dropped."""
    if len(text) <= limit:
        return text
    dropped = len(text) - limit
    return text[:limit] + f"\n... [truncated {dropped} chars]"


def capture_terminal():
    """Recent terminal state: tmux pane if inside tmux, else shell history."""
    if os.environ.get("TMUX"):
        pane = _run(["tmux", "capture-pane", "-p", "-S", "-200"])
        if pane and not pane.startswith("("):
            return pane
    for var in ("HISTFILE",):
        path = os.environ.get(var)
        if path and Path(path).is_file():
            lines = Path(path).read_text(errors="replace").splitlines()
            return "\n".join(lines[-50:])
    for name in (".bash_history", ".zsh_history"):
        path = Path.home() / name
        if path.is_file():
            lines = path.read_text(errors="replace").splitlines()
            return "\n".join(lines[-50:])
    return "(no terminal history available)"


def capture(repo="."):
    """Gather git and terminal state for the given repository."""
    repo = str(Path(repo).resolve())
    branch_status = _run(["git", "status", "--short", "--branch"], cwd=repo)

    staged = _run(["git", "diff", "--staged"], cwd=repo)
    unstaged = _run(["git", "diff"], cwd=repo)
    parts = []
    if staged and not staged.startswith("("):
        parts.append("# staged\n" + staged)
    if unstaged and not unstaged.startswith("("):
        parts.append("# unstaged\n" + unstaged)
    diff = truncate("\n\n".join(parts)) if parts else "(no changes)"

    log = _run(["git", "log", "-5", "--oneline"], cwd=repo)
    terminal = capture_terminal()

    return Context(
        repo=repo,
        branch_status=branch_status,
        diff=diff,
        log=log,
        terminal=terminal,
    )
