import logging
import sys
from logging import StreamHandler

from src.config.settings import settings

LOG_FORMAT = "%(asyncio)s - %(name)s - %(levelname)s - %(message)s"


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format=LOG_FORMAT,
        handlers=[StreamHandler(sys.stdout)],
    )
