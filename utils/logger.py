import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "../bot.log")


def setup_logger() -> None:
    """
    راه‌اندازی logger اصلی پروژه.
    - هر 15 دقیقه فایل لاگ ریست می‌شود
    - لاگ‌ها هم در فایل و هم در کنسول نمایش داده می‌شوند
    - فراخوانی فقط یک‌بار از main.py
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── File Handler: هر 15 دقیقه ریست ──────────────────────────
    file_handler = TimedRotatingFileHandler(
        filename=LOG_FILE,
        when="M",          # بر اساس دقیقه
        interval=15,       # هر 15 دقیقه
        backupCount=4,     # نگه‌داشتن 4 فایل قبلی (1 ساعت گذشته)
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    # ── Console Handler ──────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    # ── Root Logger ──────────────────────────────────────────────
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # جلوگیری از اضافه شدن handler تکراری
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """
    دریافت logger با نام ماژول.

    استفاده در هر فایل:
        from utils.logger import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)