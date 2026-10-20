import pytest

from freeze.backends import BackendError, OpenAIBackend, get_backend


class FakeBackend:
    """Stand-in backend used to exercise the summarize interface offline."""

    name = "fake"

    def summarize(self, prompt):
        return f"summary of {len(prompt)} chars"


def test_fake_backend_interface():
    backend = FakeBackend()
    assert backend.summarize("hello") == "summary of 5 chars"


def test_get_backend_known():
    assert get_backend("claude").name == "claude"
    assert get_backend("openai").name == "openai"


def test_get_backend_unknown():
    with pytest.raises(BackendError):
        get_backend("nope")


def test_openai_requires_api_key(monkeypatch):
    monkeypatch.delenv("FREEZE_API_KEY", raising=False)
    backend = OpenAIBackend()
    with pytest.raises(BackendError, match="FREEZE_API_KEY"):
        backend.summarize("prompt")
