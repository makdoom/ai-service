import logging
import sys
from app.core.config import settings

def setup_logging():
    level = getattr(logging, settings.LOG_LEVEL, logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.stream.reconfigure(encoding="utf-8")

    logging.basicConfig(
        level=level,
        format=settings.LOG_FORMAT,
        handlers=[handler],
        # datefmt=settings.LOG_DATEFMT
        datefmt="%Y-%m-%d %H:%M:%S"


    )