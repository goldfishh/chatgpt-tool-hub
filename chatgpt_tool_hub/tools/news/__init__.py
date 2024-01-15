import importlib
import os

from ...common.log import LOG
from .. import get_packages
from .. import ToolRegister

# news_tool_register = ToolRegister()
from ..tool_register import main_tool_register as news_tool_register

try:
    all_tool_package_list = get_packages(f"{os.path.dirname(os.path.abspath(__file__))}")
except Exception as e:
    LOG.debug(f"get_packages error: {repr(e)}")
    all_tool_package_list = ["finance_news", "morning_news", "news_api"]
    LOG.debug(f"Detected main tool package: {repr(all_tool_package_list)}")

for package_name in all_tool_package_list:
    try:
        importlib.import_module(f".tools.news.{package_name}", package="chatgpt_tool_hub")
    except Exception as e:
        LOG.info(f"[news.{package_name}] init failed, error_info: {repr(e)}")


from .tool import NewsTool
from .finance_news.tool import FinanceNewsTool
from .morning_news.tool import MorningNewsTool
from .news_api.tool import NewsApiTool

__all__ = [
    "NewsTool",
    "FinanceNewsTool",
    "MorningNewsTool",
    "NewsApiTool",
    
    "news_tool_register"
]
