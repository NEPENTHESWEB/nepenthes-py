"""Deterministic page and URL generation with seeded randomness."""

import hashlib
import random
from typing import Optional


class URLGenerator:
    """Generates fake directory-style URLs from a wordlist."""

    def __init__(self, wordlist_path: str, prefixes: list[str]):
        with open(wordlist_path, "r", encoding="utf-8", errors="replace") as f:
            self._words = [line.strip() for line in f if line.strip()]
        self._prefixes = prefixes if prefixes else ["/"]

    @property
    def words(self) -> list[str]:
        return self._words

    def generate_url(self, depth_min: int = 2, depth_max: int = 5,
                     rng: Optional[random.Random] = None) -> str:
        r = rng or random.Random()
        prefix = r.choice(self._prefixes) if self._prefixes else ""
        depth = r.randint(depth_min, depth_max)
        parts = [r.choice(self._words) for _ in range(depth)]
        path = "/".join(parts)
        return f"{prefix}/{path}" if prefix != "/" else f"/{path}"

    def generate_urls(self, min_count: int = 5, max_count: int = 30,
                      depth_min: int = 2, depth_max: int = 5,
                      rng: Optional[random.Random] = None) -> list[str]:
        r = rng or random.Random()
        n = r.randint(min_count, max_count)
        return [self.generate_url(depth_min, depth_max, rng=r) for _ in range(n)]

    def validate_word(self, word: str) -> bool:
        return word in self._words


def make_page_seed(path: str, instance_seed: str) -> int:
    """Create a deterministic integer seed from URL path + instance seed."""
    combined = f"{instance_seed}:{path}"
    digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)
