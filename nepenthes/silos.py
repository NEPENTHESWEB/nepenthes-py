"""Silo management - virtual hosts with independent configurations."""

import os
import random
import logging
from typing import Optional

from .config import AppConfig, SiloConfig
from .markov import MarkovEngine, get_or_train
from .generator import URLGenerator, make_page_seed
from .templates_engine import TemplateEngine
from .bogon import BogonFilter

logger = logging.getLogger("nepenthes")


class Silo:
    """A single silo instance with its own corpus, wordlist, templates, etc."""

    def __init__(self, config: SiloConfig, markov: MarkovEngine,
                 url_gen: URLGenerator, template_engine: TemplateEngine,
                 instance_seed: str):
        self.config = config
        self.markov = markov
        self.url_gen = url_gen
        self.template_engine = template_engine
        self.instance_seed = instance_seed
        self.bogon = BogonFilter(set(url_gen.words), config.prefixes)

    def validate_path(self, path: str) -> bool:
        return self.bogon.is_valid(path)

    def generate_random_url(self) -> str:
        return self.url_gen.generate_url()

    def generate_page(self, path: str) -> str:
        seed = make_page_seed(path, self.instance_seed)
        rng = random.Random(seed)

        tmpl_config = self.template_engine.get_config(self.config.template)
        variables: dict = {}

        if tmpl_config:
            for m in tmpl_config.markov:
                variables[m["name"]] = self.markov.generate(
                    min_tokens=m.get("min", 30),
                    max_tokens=m.get("max", 120),
                    rng=rng,
                )

            for ma in tmpl_config.markov_array:
                variables[ma["name"]] = self.markov.generate_paragraphs(
                    min_count=ma.get("min_count", 2),
                    max_count=ma.get("max_count", 5),
                    min_tokens=ma.get("markov_min", 30),
                    max_tokens=ma.get("markov_max", 120),
                    rng=rng,
                )

            for lnk in tmpl_config.link:
                variables[lnk["name"]] = self.url_gen.generate_url(
                    depth_min=lnk.get("depth_min", 2),
                    depth_max=lnk.get("depth_max", 5),
                    rng=rng,
                )

            for la in tmpl_config.link_array:
                urls = self.url_gen.generate_urls(
                    min_count=la.get("min_count", 5),
                    max_count=la.get("max_count", 30),
                    depth_min=la.get("depth_min", 2),
                    depth_max=la.get("depth_max", 5),
                    rng=rng,
                )
                variables[la.get("name", "links")] = urls

            for b in tmpl_config.booleans:
                prob = b.get("probability", 0)
                variables[b["name"]] = rng.randint(1, 100) <= prob
        else:
            variables["content"] = self.markov.generate(rng=rng)
            variables["links"] = self.url_gen.generate_urls(rng=rng)

        return self.template_engine.render(self.config.template, variables)


class SiloManager:
    """Manages all configured silos."""

    def __init__(self, config: AppConfig, template_engine: TemplateEngine):
        self._silos: dict[str, Silo] = {}
        self._instance_seed = self._load_seed(config.seed_file)

        for silo_cfg in config.silos:
            markov = get_or_train(silo_cfg.corpus)
            url_gen = URLGenerator(silo_cfg.wordlist, silo_cfg.prefixes)
            silo = Silo(
                config=silo_cfg,
                markov=markov,
                url_gen=url_gen,
                template_engine=template_engine,
                instance_seed=self._instance_seed,
            )
            self._silos[silo_cfg.name] = silo
            logger.info("Silo '%s' initialized (corpus: %s, wordlist: %s)",
                        silo_cfg.name, silo_cfg.corpus, silo_cfg.wordlist)

    def get_silo(self, name: str) -> Silo:
        return self._silos[name]

    @staticmethod
    def _load_seed(seed_file: Optional[str]) -> str:
        if seed_file and os.path.exists(seed_file):
            with open(seed_file, "r") as f:
                return f.read().strip()

        import uuid
        seed = str(uuid.uuid4())

        if seed_file:
            try:
                with open(seed_file, "w") as f:
                    f.write(seed)
            except OSError:
                logger.warning("Could not persist seed to %s", seed_file)

        return seed
