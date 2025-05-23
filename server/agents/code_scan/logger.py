import logging
import structlog

# 1. Configure standard logging (optional: customize handlers/formatters as needed)
logging.basicConfig(
    format="%(message)s",
    stream=None,  # Defaults to sys.stderr
    level=logging.INFO,
)

# 2. Configure structlog to use ConsoleRenderer with colors for console output
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
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
