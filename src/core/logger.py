"""
Logging setup for pmanager-scrape.

Provides a pre-configured console logger with timestamps. Import ``logger``
directly in any module::

    from src.core.logger import logger
    logger.info("Starting scrape...")
    logger.error("Something failed", exc_info=True)  # include traceback

Pass ``exc_info=True`` to any error/critical call to automatically attach the
current exception traceback to the log record.
"""

import logging
import sys


def setup_logger(name: str = "PManagerScraper", level: int = logging.INFO) -> logging.Logger:
    """Create and configure a named logger with a stdout console handler.

    Args:
        name: Logger name (used to identify the source in log output).
        level: Minimum log level to emit (default: ``logging.INFO``).

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    log = logging.getLogger(name)
    log.setLevel(level)

    if not log.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        ch.setFormatter(formatter)
        log.addHandler(ch)

        # Uncomment to also write logs to a file:
        # fh = logging.FileHandler("scraper.log")
        # fh.setFormatter(formatter)
        # log.addHandler(fh)

    return log


logger = setup_logger()
