# context-freeze

One command that snapshots your working state and writes a markdown "freeze"
so you can step away mid-task and resume later without rebuilding the mental
stack from scratch.

## What it does

`freeze` captures the state of a repository and your recent terminal activity,
sends it to a language model, and saves a short markdown summary with four
sections:

- **What I was doing**
- **What's failing**
- **Next step**
- **Files touched**

The summary lands in `.freeze/freeze-YYYYMMDD-HHMMSS.md` (gitignored) and the
path is printed.

## Install

```sh
pip install -e .
```

Requires Python 3.11+. The only runtime dependency is `requests`.

## Usage

```sh
freeze [--repo PATH] [--out DIR] [--provider claude|openai] [--dry-run]
```

```sh
# Summarize the current repo with the default backend
freeze

# Point at another repo and backend
freeze --repo ~/code/project --provider openai

# See exactly what would be sent, without calling a model
freeze --dry-run
```

### What gets captured

- `git status --short --branch`
- `git diff` for staged and unstaged changes (truncated to ~20k chars)
- `git log -5 --oneline`
- Terminal state: the current `tmux` pane (`tmux capture-pane -p -S -200`) when
  inside tmux, otherwise the last 50 lines of shell history

Each step is tolerant of failure. If a command is missing or errors, that
field carries a short note and the rest of the freeze still runs.

## Backends

Backends are pluggable behind a one-method interface,
`summarize(prompt) -> str`:

- **`claude`** (default) — shells out to the Claude Code CLI (`claude -p`) in
  headless mode. No configuration needed if the CLI is installed and signed in.
- **`openai`** — any OpenAI-compatible chat endpoint, configured through the
  environment:

  | Variable          | Purpose                          | Default                      |
  | ----------------- | -------------------------------- | ---------------------------- |
  | `FREEZE_BASE_URL` | API base URL                     | `https://api.openai.com/v1`  |
  | `FREEZE_API_KEY`  | bearer token                     | (required)                   |
  | `FREEZE_MODEL`    | model name                       | `gpt-4o-mini`                |

  Because the interface is just an HTTP chat-completions call, any
  OpenAI-compatible gateway works by pointing `FREEZE_BASE_URL` at it.

No keys live in the repo. Put them in your environment; `.env` is gitignored.

## Example output

See [`examples/sample-freeze.md`](examples/sample-freeze.md) for a freeze
produced by a real run of this tool against this repository.

## Design decisions

- **Capture is best-effort, never fatal.** A missing `tmux`, an empty history
  file, or a directory that is not a git repo should degrade gracefully. Every
  capture step returns a note instead of raising so you always get a freeze.
- **Diffs are truncated to ~20k chars.** Large diffs blow past model context
  windows and bury the signal. The cutoff is marked in the output so you know
  something was dropped.
- **One-method backend interface.** `summarize(prompt) -> str` keeps new
  backends trivial to add and keeps the capture/prompt logic independent of any
  provider.
- **`--dry-run` prints the full context and prompt.** You can see exactly what
  would leave your machine before anything does.
- **stdlib + `requests` only.** No heavy SDKs; the OpenAI backend is a plain
  HTTP call, which is why any compatible endpoint plugs in.

## Limitations

- **Terminal capture is partial.** Outside tmux it can only read shell history,
  which may be stale, disabled, or missing the most recent commands. Inside
  tmux it sees the current pane, not other windows or panes.
- **The model can be wrong.** The summary is a convenience, not ground truth.
  Treat "What's failing" and "Next step" as a starting point and verify against
  the actual diff and tests.
- **Only text is sent.** The freeze transmits exactly the captured git and
  terminal text to whichever backend you choose — nothing else. Review it with
  `--dry-run` if you are unsure, and remember that whatever is in your diff or
  history goes with it.
