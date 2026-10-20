import subprocess

from freeze.capture import capture, truncate


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def make_repo(path):
    path.mkdir()
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "t@example.com")
    _git(path, "config", "user.name", "Test")
    (path / "a.txt").write_text("hello\n")
    _git(path, "add", "a.txt")
    _git(path, "commit", "-q", "-m", "initial")
    return path


def test_capture_on_temp_repo(tmp_path):
    repo = make_repo(tmp_path / "r")
    (repo / "a.txt").write_text("hello world\n")

    ctx = capture(repo)

    assert ctx.repo == str(repo.resolve())
    assert "## " in ctx.branch_status or "main" in ctx.branch_status or ctx.branch_status
    assert "initial" in ctx.log
    assert "hello world" in ctx.diff


def test_capture_clean_repo_reports_no_changes(tmp_path):
    repo = make_repo(tmp_path / "r")
    ctx = capture(repo)
    assert ctx.diff == "(no changes)"


def test_truncate_marks_dropped_chars():
    text = "x" * 100
    out = truncate(text, limit=10)
    assert out.startswith("x" * 10)
    assert "truncated 90 chars" in out


def test_truncate_leaves_short_text():
    assert truncate("short", limit=100) == "short"
