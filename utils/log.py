import logging

_LOGGER_NAME = "tilf"


def setup(level: int = logging.INFO) -> None:
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(handler)


def get_logger() -> logging.Logger:
    return logging.getLogger(_LOGGER_NAME)
