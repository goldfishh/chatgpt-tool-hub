import importlib

from chatgpt_tool_hub.common.log import LOG

# dev tool: arxiv_search   debug   visual_dl  searxng_search
all_tool_package_list = ["bing_search", "google_search", "meteo", "news", "morning_news",
                         "python", "terminal", "web_requests", "wikipedia", "wolfram_alpha"]

for package_name in all_tool_package_list:
    try:
        importlib.import_module("chatgpt_tool_hub.tools." + package_name)
    except Exception as e:
        LOG.info(f"[{package_name}] init failed, error_info: " + repr(e))
