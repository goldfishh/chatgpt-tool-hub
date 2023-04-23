import os
import sys
import logging
from chatgpt_tool_hub.common.constants import LOGGING_LEVEL, LOGGING_FMT, LOGGING_DATEFMT


def _get_logger():
    logger = logging.getLogger("tool")

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(LOGGING_LEVEL)
    ch.setFormatter(logging.Formatter(LOGGING_FMT, datefmt=LOGGING_DATEFMT))

    fh = logging.FileHandler(f'{os.getcwd()}/tool.log', encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(LOGGING_FMT, datefmt=LOGGING_DATEFMT))

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


# 日志句柄
LOG = _get_logger()
