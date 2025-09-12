"""
Centralized logging configuration for StoryTime application

This module provides a configured logger that can be imported and used
throughout the application for consistent logging behavior.
"""

import logging
import sys


def setup_logger(name: str = "storytime", level: str = "INFO") -> logging.Logger:
    """
    Set up and configure a logger for the StoryTime application

    Args:
        name: Logger name (default: "storytime")
        level: Logging level as string (default: "INFO")

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger_with_config() -> logging.Logger:
    """
    Get logger configured with settings from config.py
    
    Returns:
        Configured logger instance using config settings
    """
    try:
        from config import settings
        return setup_logger(level=settings.log_level)
    except ImportError:
        # Fallback if config is not available
        return setup_logger(level="INFO")


# Create default logger instance using config
logger = get_logger_with_config()
