import logging
import sys

from chatgpt_tool_hub.common.constants import LOGGING_LEVEL


def _get_logger():
    logger = logging.getLogger(__package__)
    logger.setLevel(LOGGING_LEVEL)
    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d] - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


# 日志句柄
LOG = _get_logger()
