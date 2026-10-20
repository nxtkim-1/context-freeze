from freeze.capture import Context
from freeze.cli import main, render_context, write_output


def test_write_output_format(tmp_path):
    path = write_output(tmp_path / "out", "## What I was doing\nstuff")
    assert path.exists()
    assert path.name.startswith("freeze-")
    assert path.suffix == ".md"
    text = path.read_text()
    assert text.startswith("# Freeze ")
    assert "## What I was doing" in text


def test_render_context_includes_prompt():
    ctx = Context(
        repo="/tmp/r",
        branch_status="## main",
        diff="(no changes)",
        log="abc initial",
        terminal="$ ls",
    )
    out = render_context(ctx, "THE PROMPT")
    assert "=== diff ===" in out
    assert "THE PROMPT" in out


def test_dry_run_calls_no_backend(tmp_path, capsys, monkeypatch):
    # A clean temp repo keeps git calls quiet; dry-run must not touch a model.
    import subprocess

    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    def explode(provider):
        raise AssertionError("backend must not be constructed in dry-run")

    monkeypatch.setattr("freeze.cli.get_backend", explode)

    rc = main(["--repo", str(repo), "--dry-run"])
    assert rc == 0
    assert "=== prompt ===" in capsys.readouterr().out
