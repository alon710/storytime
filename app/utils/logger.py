import logging
import sys
import structlog


def setup_logger(
    name: str = "storytime",
    level: str = "INFO",
) -> structlog.stdlib.BoundLogger:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )

    return structlog.get_logger(name)


def get_logger_with_config() -> structlog.stdlib.BoundLogger:
    try:
        from app.utils.settings import settings

        return setup_logger(level=settings.log_level)
    except ImportError:
        return setup_logger(level="INFO")


logger = get_logger_with_config()
