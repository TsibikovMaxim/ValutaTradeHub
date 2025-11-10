"""Настройка логирования для проекта."""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_file: str = "logs/actions.log", level=logging.INFO):
    """Настраивает логирование с ротацией файлов."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("valutatrade_hub")
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(levelname)s %(asctime)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
    )

    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
