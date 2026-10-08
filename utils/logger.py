import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "bot.log")


def setup_logger() -> None:
    """
    Initialize application logger:
    - 15-minute log file rotation
    - Dual logging to both file and stdout stream
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = TimedRotatingFileHandler(
        filename=LOG_FILE,
        when="M",
        interval=15,
        backupCount=4,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Retrieve logger instance with module name."""
    return logging.getLogger(name)
