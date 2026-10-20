from freeze.capture import Context
from freeze.prompt import build_prompt


def sample_context():
    return Context(
        repo="/tmp/r",
        branch_status="## main",
        diff="diff --git a b",
        log="abc123 initial",
        terminal="$ pytest",
    )


def test_prompt_contains_sections():
    prompt = build_prompt(sample_context())
    for heading in ("What I was doing", "What's failing", "Next step", "Files touched"):
        assert heading in prompt


def test_prompt_embeds_context():
    prompt = build_prompt(sample_context())
    assert "/tmp/r" in prompt
    assert "abc123 initial" in prompt
    assert "diff --git a b" in prompt
    assert "$ pytest" in prompt
