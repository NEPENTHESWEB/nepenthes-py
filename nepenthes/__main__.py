"""Entry point: python -m nepenthes config.yml"""

import sys
import asyncio
import logging

from .config import load_config
from .templates_engine import TemplateEngine
from .silos import SiloManager
from .stats import StatsCollector
from .server import TarpitServer


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python -m nepenthes <config.yml>", file=sys.stderr)
        sys.exit(1)

    config = load_config(sys.argv[1])

    level = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("nepenthes")
    logger.info("Nepenthes starting up...")

    template_engine = TemplateEngine(config.templates)
    silo_manager = SiloManager(config, template_engine)
    stats = StatsCollector(remember_time=config.stats_remember_time)

    server = TarpitServer(config, silo_manager, stats)

    logger.info("Initialization complete. Starting server.")
    asyncio.run(server.start())


if __name__ == "__main__":
    main()
