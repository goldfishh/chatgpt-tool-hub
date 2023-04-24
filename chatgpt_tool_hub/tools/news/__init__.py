import importlib
import os

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.tools import get_packages
from chatgpt_tool_hub.tools.tool_register import ToolRegister

news_tool_register = ToolRegister()
try:
    all_tool_package_list = get_packages(f"{os.path.dirname(os.path.abspath(__file__))}")
except Exception as e:
    LOG.debug(f"get_packages error: {repr(e)}")
    all_tool_package_list = ["finance_news", "morning_news", "news_api"]
    LOG.debug(f"Detected main tool package: {repr(all_tool_package_list)}")

for package_name in all_tool_package_list:
    try:
        importlib.import_module(f"chatgpt_tool_hub.tools.news.{package_name}")
    except Exception as e:
        LOG.info(f"[news.{package_name}] init failed, error_info: {repr(e)}")


from chatgpt_tool_hub.tools.news.tool import NewsTool

__all__ = [
    "NewsTool",
    "news_tool_register"
]
