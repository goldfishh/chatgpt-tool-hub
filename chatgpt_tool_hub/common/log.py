import os
import sys
import logging
from .constants import LOGGING_LEVEL, LOGGING_FMT, LOGGING_DATEFMT


def _get_logger(level: int = LOGGING_LEVEL):
    logger = logging.getLogger("tool")

    for h in logger.handlers:
        h.close()
        logger.removeHandler(h)
        del h
    logger.handlers.clear()
    logger.propagate = False

    logger.setLevel(level)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter(LOGGING_FMT, datefmt=LOGGING_DATEFMT))

    # fh = logging.FileHandler(f'{os.getcwd()}/tool.log', encoding='utf-8')
    # fh.setFormatter(logging.Formatter(LOGGING_FMT, datefmt=LOGGING_DATEFMT))

    logger.addHandler(ch)
    # logger.addHandler(fh)
    return logger


def refresh(level: int = LOGGING_LEVEL):
    global LOG
    LOG = _get_logger(level)


# 日志句柄
LOG = _get_logger()
