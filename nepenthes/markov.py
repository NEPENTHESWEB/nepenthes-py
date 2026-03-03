"""In-memory Markov chain text generator trained from a corpus file."""

import random
import logging
from collections import defaultdict
from typing import Optional

logger = logging.getLogger("nepenthes")

_CHAIN_ORDER = 2


class MarkovEngine:
    """Builds an n-gram chain from a corpus and generates babble text."""

    def __init__(self):
        self._chain: dict[tuple[str, ...], list[str]] = defaultdict(list)
        self._starters: list[tuple[str, ...]] = []
        self._trained = False

    @property
    def trained(self) -> bool:
        return self._trained

    def train(self, corpus_path: str) -> None:
        logger.info("Training Markov chain from %s ...", corpus_path)
        with open(corpus_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        words = text.split()
        if len(words) < _CHAIN_ORDER + 1:
            logger.warning("Corpus too small (%d words), Markov output will be poor", len(words))

        for i in range(len(words) - _CHAIN_ORDER):
            key = tuple(words[i : i + _CHAIN_ORDER])
            next_word = words[i + _CHAIN_ORDER]
            self._chain[key].append(next_word)

            if i == 0 or words[i - 1].endswith((".", "!", "?")):
                self._starters.append(key)

        if not self._starters and self._chain:
            self._starters = list(self._chain.keys())

        self._trained = True
        logger.info(
            "Markov training complete: %d keys, %d starters",
            len(self._chain), len(self._starters),
        )

    def generate(self, min_tokens: int = 30, max_tokens: int = 120,
                 rng: Optional[random.Random] = None) -> str:
        if not self._trained or not self._starters:
            return "The quick brown fox jumps over the lazy dog. " * 5

        r = rng or random.Random()
        count = r.randint(min_tokens, max_tokens)
        key = r.choice(self._starters)
        result = list(key)

        for _ in range(count - _CHAIN_ORDER):
            candidates = self._chain.get(key)
            if not candidates:
                key = r.choice(self._starters)
                result.append(key[0])
                continue
            next_word = r.choice(candidates)
            result.append(next_word)
            key = tuple(result[-_CHAIN_ORDER:])

        return " ".join(result)

    def generate_paragraphs(self, min_count: int = 2, max_count: int = 5,
                            min_tokens: int = 30, max_tokens: int = 120,
                            rng: Optional[random.Random] = None) -> list[str]:
        r = rng or random.Random()
        n = r.randint(min_count, max_count)
        return [self.generate(min_tokens, max_tokens, rng=r) for _ in range(n)]


_corpus_cache: dict[str, MarkovEngine] = {}


def get_or_train(corpus_path: str) -> MarkovEngine:
    """Return a shared MarkovEngine for the given corpus, training only once."""
    if corpus_path not in _corpus_cache:
        engine = MarkovEngine()
        engine.train(corpus_path)
        _corpus_cache[corpus_path] = engine
    return _corpus_cache[corpus_path]
