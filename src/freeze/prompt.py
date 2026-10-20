"""Turn captured context into the instruction sent to a backend."""

from __future__ import annotations

from .capture import Context

INSTRUCTIONS = """\
You are helping a developer freeze their working state so they can step away \
and resume later. Using only the context below, write a concise markdown \
summary with exactly these sections:

## What I was doing
## What's failing
## Next step
## Files touched

Be specific and base everything on the context. If something is unknown, say \
so briefly rather than guessing. Keep it tight."""


def build_prompt(ctx: Context) -> str:
    """Assemble the full prompt from captured context."""
    return "\n\n".join(
        [
            INSTRUCTIONS,
            "--- CONTEXT ---",
            f"Repository: {ctx.repo}",
            "## git status\n" + ctx.branch_status,
            "## recent commits\n" + ctx.log,
            "## diff\n" + ctx.diff,
            "## terminal\n" + ctx.terminal,
        ]
    )
