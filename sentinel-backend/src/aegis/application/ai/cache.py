"""In-memory cache for AI reasoning to prevent duplicate calls."""

import hashlib
from typing import Any


class ReasoningCache:
    """A simple in-memory cache using SHA-256 hashes of the prompts."""

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    def _hash(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def get(self, prompt: str) -> dict[str, Any] | None:
        return self._cache.get(self._hash(prompt))

    def set(self, prompt: str, response: dict[str, Any]) -> None:
        self._cache[self._hash(prompt)] = response
