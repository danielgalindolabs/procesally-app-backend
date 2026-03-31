import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings


def setup_logging():
    log_level = settings.LOG_LEVEL.upper()

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if root_logger.handlers:
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        fmt="[%(levelname)s] [%(asctime)s] %(message)s (%(filename)s:%(lineno)d)",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    def cdmx_converter(timestamp):
        return datetime.fromtimestamp(
            timestamp, tz=ZoneInfo("America/Mexico_City")
        ).timetuple()

    formatter.converter = cdmx_converter
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)
    logging.info(f"Logging initialized. Level: {log_level}")
