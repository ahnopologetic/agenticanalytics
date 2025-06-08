import logging
import structlog

# Custom processor for concise exception tracebacks
# Only logs the last 2 lines (exception type and message) for better o11y


def short_exc_info(logger, method_name, event_dict):
    exc_info = event_dict.pop("exc_info", None)
    if exc_info:
        import traceback

        if not isinstance(exc_info, tuple):
            exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
        tb_lines = traceback.format_exception(*exc_info)
        # Only keep the last 2 lines (exception type and message)
        short_tb = "".join(tb_lines[-2:]).strip()
        event_dict["exception"] = short_tb
    return event_dict


# 1. Configure standard logging (optional: customize handlers/formatters as needed)
logging.basicConfig(
    format="%(message)s",
    stream=None,  # Defaults to sys.stderr
    level=logging.INFO,
)

# 2. Configure structlog to use ConsoleRenderer with colors for console output
# Replaces format_exc_info with short_exc_info for concise tracebacks
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        short_exc_info,  # concise exception tracebacks
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(colors=True),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
