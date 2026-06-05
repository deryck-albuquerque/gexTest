import logging
import hashlib

from pythonjsonlogger import jsonlogger


def mask_identifier(value: str | None):
    if not value:
        return None

    return hashlib.sha256(value.encode()).hexdigest()[:12]


def configure_logging():

    logger = logging.getLogger()

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(message)s "
        "%(correlation_id)s %(gateway)s %(event)s"
    )

    handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(handler)

    return logger


logger = configure_logging()