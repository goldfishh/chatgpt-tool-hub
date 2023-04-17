import importlib
from chatgpt_tool_hub.common.log import LOG

from chatgpt_tool_hub.tools.tool_register import ToolRegister

news_tool_register = ToolRegister()

all_tool_package_list = ["finance_news", "morning_news", "news_api"]

for package_name in all_tool_package_list:
    try:
        importlib.import_module("chatgpt_tool_hub.tools.news." + package_name)
        LOG.debug(f"[news.{package_name}] init success")
    except Exception as e:
        LOG.info(f"[news.{package_name}] init failed, error_info: " + repr(e))


from chatgpt_tool_hub.tools.news.tool import NewsTool

__all__ = [
    "NewsTool",
    "news_tool_register"
]
