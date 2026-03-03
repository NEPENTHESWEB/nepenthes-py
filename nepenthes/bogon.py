"""Bogon filter - validates incoming URLs against the configured wordlist."""

import logging

logger = logging.getLogger("nepenthes")


class BogonFilter:
    """Checks that every path segment in a URL exists in the wordlist."""

    def __init__(self, words: set[str], prefixes: list[str]):
        self._words = words
        self._prefixes = prefixes

    def is_valid(self, path: str) -> bool:
        clean = path
        for prefix in self._prefixes:
            if clean.startswith(prefix):
                clean = clean[len(prefix):]
                break

        clean = clean.strip("/")
        if not clean:
            return True

        segments = clean.split("/")
        for segment in segments:
            if segment and segment not in self._words:
                return False
        return True
