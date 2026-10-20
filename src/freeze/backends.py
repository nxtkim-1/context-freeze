"""LLM backends. Each one implements ``summarize(prompt) -> str``."""

from __future__ import annotations

import os
import subprocess

import requests


class BackendError(RuntimeError):
    pass


class ClaudeBackend:
    """Shell out to the Claude Code CLI (`claude -p`) in headless mode."""

    name = "claude"

    def summarize(self, prompt: str) -> str:
        try:
            result = subprocess.run(
                ["claude", "-p", prompt],
                capture_output=True,
                text=True,
                timeout=180,
            )
        except FileNotFoundError:
            raise BackendError(
                "claude CLI not found on PATH; install Claude Code or use --provider openai"
            )
        except subprocess.TimeoutExpired:
            raise BackendError("claude CLI timed out")
        if result.returncode != 0:
            raise BackendError(f"claude CLI failed: {result.stderr.strip()}")
        return result.stdout.strip()


class OpenAIBackend:
    """Any OpenAI-compatible chat endpoint, configured via environment.

    FREEZE_BASE_URL, FREEZE_API_KEY, FREEZE_MODEL.
    """

    name = "openai"

    def __init__(self):
        self.base_url = os.environ.get(
            "FREEZE_BASE_URL", "https://api.openai.com/v1"
        ).rstrip("/")
        self.api_key = os.environ.get("FREEZE_API_KEY")
        self.model = os.environ.get("FREEZE_MODEL", "gpt-4o-mini")

    def summarize(self, prompt: str) -> str:
        if not self.api_key:
            raise BackendError("FREEZE_API_KEY is not set")
        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=180,
            )
        except requests.RequestException as exc:
            raise BackendError(f"request failed: {exc}")
        if resp.status_code != 200:
            raise BackendError(f"endpoint returned {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


def get_backend(provider: str):
    if provider == "claude":
        return ClaudeBackend()
    if provider == "openai":
        return OpenAIBackend()
    raise BackendError(f"unknown provider: {provider}")
