"""
Kaybetmek Yok Lugatımda...
                     Scream
"""
from __future__ import annotations

import logging
import sys
import time
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("vanity-guard")
    logger.setLevel(level)

    fmt = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)

    file_handler = RotatingFileHandler(
        LOG_DIR / "vanity-guard.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)

    logger.handlers.clear()
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


@contextmanager
def latency_timer(logger: logging.Logger, label: str):
    """
    Ne Mekanlar Ne Burjuva Mahalle

    Kullanım:
        with latency_timer(logger, "vanity_update_dispatch"):
            await do_something()
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("LATENCY %-30s %.3f ms", label, elapsed_ms)
