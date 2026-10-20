# context-freeze

A command-line tool that snapshots your working state into a markdown file so you can step away from a task and pick it up later. It gathers your git status, diffs, recent commits, and recent terminal activity, hands that to an LLM, and saves the model's summary as a timestamped `.md` file.

I built this as practice for the Meta Global AI Developer Hackathon. It's the first piece of a bigger project I'm calling the Cognitive Load Governor.

## Install

Requires Python 3.11 or newer.

```bash
pip install -e .
```

For the tests you also need the dev extra:

```bash
pip install -e ".[dev]"
```

Installing puts a `freeze` command on your PATH.

## Usage

Run `freeze` from inside a repository, or point it at one:

```bash
freeze                      # capture the current directory
freeze --repo ../other-repo # capture a different repository
freeze --dry-run            # print what would be sent, call no model
```

### Flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `--repo` | `.` | Repository to capture. |
| `--out` | `.freeze` | Directory to write the freeze into. |
| `--provider` | `claude` | Which LLM backend to use: `claude` or `openai`. |
| `--dry-run` | off | Print the captured context and the assembled prompt, then exit without calling a model. |

## What gets captured

`capture()` collects four things from the target repository:

- **git status:** `git status --short --branch`.
- **diff:** staged (`git diff --staged`) and unstaged (`git diff`) changes, labeled separately. The combined diff is truncated to 20,000 characters so a huge diff can't blow up the prompt, and when it's trimmed the output notes how many characters were dropped. A clean tree records `(no changes)`.
- **recent commits:** `git log -5 --oneline`.
- **terminal:** if you're inside tmux (`$TMUX` is set), the last 200 lines of the current pane via `tmux capture-pane`. Otherwise it falls back to shell history: the file named by `$HISTFILE`, then `~/.bash_history`, then `~/.zsh_history`, taking the last 50 lines. If none of those are available it records `(no terminal history available)`.

Every capture step tolerates failure, because a freeze is most useful when things are already broken. A missing command, a timeout, or a git error turns into a short parenthetical note in that field rather than crashing the run.

## Backends

The captured context is turned into a prompt that asks the model for a short markdown summary with four fixed sections: *What I was doing*, *What's failing*, *Next step*, and *Files touched*. The prompt tells the model to base everything on the provided context and to say when something is unknown instead of guessing.

Two backends can answer that prompt.

### `claude` (default)

Shells out to the Claude Code CLI in headless mode (`claude -p <prompt>`). It needs the `claude` binary on your PATH; if it isn't found, the tool tells you to install Claude Code or switch to the openai provider. Calls time out after 180 seconds.

### `openai`

Posts to any OpenAI-compatible chat-completions endpoint. It reads three environment variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `FREEZE_BASE_URL` | `https://api.openai.com/v1` | API base URL. |
| `FREEZE_API_KEY` | *(none)* | Bearer token. Required; the run fails if it's unset. |
| `FREEZE_MODEL` | `gpt-4o-mini` | Model name sent in the request. |

Any server that speaks the OpenAI chat API works if you set `FREEZE_BASE_URL`.

## Output

A successful run writes a file named `freeze-YYYYMMDD-HHMMSS.md` into the output directory (`.freeze` by default), creating the directory if needed. The file starts with a `# Freeze <timestamp>` heading followed by the model's summary, and the path is printed to stdout. `.freeze/` is in `.gitignore`, so freezes stay out of version control by default.

See [examples/sample-freeze.md](examples/sample-freeze.md) for a real freeze produced from this repository.

## Running the tests

```bash
pip install -e ".[dev]"
pytest -q
```

The suite covers capture, the prompt, output format, and backend selection. Tests do not call a model or the network. GitHub Actions runs `pytest -q` on pushes to `main` and on pull requests, on Python 3.11.

## Limitations

- The `claude` backend needs the Claude Code CLI installed and working.
- Only git repositories are understood. There's no support for other version-control systems, and a non-git directory will just produce error notes in the git fields.
- Terminal capture is best-effort. Outside tmux it reads shell history files, which may be stale, disabled, or written only on shell exit, so recent commands can be missing.
- The diff truncation cuts on a character count rather than at a hunk boundary, so a trimmed diff can end mid-hunk.
- There's no retry or streaming; a backend call that fails simply reports the error and exits non-zero.
