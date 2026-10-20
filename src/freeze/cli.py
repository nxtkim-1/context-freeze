"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from .backends import BackendError, get_backend
from .capture import capture
from .prompt import build_prompt


def render_context(ctx, prompt) -> str:
    """Human-readable dump used by --dry-run."""
    return (
        f"Repository: {ctx.repo}\n\n"
        f"=== git status ===\n{ctx.branch_status}\n\n"
        f"=== recent commits ===\n{ctx.log}\n\n"
        f"=== diff ===\n{ctx.diff}\n\n"
        f"=== terminal ===\n{ctx.terminal}\n\n"
        f"=== prompt ===\n{prompt}\n"
    )


def write_output(out_dir, summary) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = out_dir / f"freeze-{stamp}.md"
    header = f"# Freeze {stamp}\n\n"
    path.write_text(header + summary + "\n")
    return path


def build_parser():
    parser = argparse.ArgumentParser(
        prog="freeze",
        description="Snapshot your working state into a resumable markdown freeze.",
    )
    parser.add_argument("--repo", default=".", help="repository to capture (default: .)")
    parser.add_argument("--out", default=".freeze", help="output directory (default: .freeze)")
    parser.add_argument(
        "--provider",
        default="claude",
        choices=["claude", "openai"],
        help="LLM backend (default: claude)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print captured context and prompt without calling a model",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    ctx = capture(args.repo)
    prompt = build_prompt(ctx)

    if args.dry_run:
        print(render_context(ctx, prompt))
        return 0

    try:
        backend = get_backend(args.provider)
        summary = backend.summarize(prompt)
    except BackendError as exc:
        print(f"freeze: {exc}", file=sys.stderr)
        return 1

    path = write_output(args.out, summary)
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
