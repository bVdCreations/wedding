import logging
import sys

from src.config.settings import settings

LOG_FORMAT = "%(asyncio)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format=LOG_FORMAT,
        handlers=[sys.stdout],
    )
