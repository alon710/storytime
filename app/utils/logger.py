import logging
import sys


def setup_logger(
    name: str = "storytime",
    level: str = "INFO",
) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    logger.addHandler(console_handler)

    return logger


def get_logger_with_config() -> logging.Logger:
    try:
        from app.utils.settings import settings

        return setup_logger(level=settings.log_level)
    except ImportError:
        return setup_logger(level="INFO")


logger = get_logger_with_config()
