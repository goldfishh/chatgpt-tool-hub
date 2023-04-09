import importlib

from chatgpt_tool_hub.common.log import LOG

all_tool_package_list = ["arxiv_search", "bing_search", "debug", "google_search", "meteo", "news", "visual_dl",
                         "python", "searxng_search", "terminal", "web_requests", "wikipedia", "wolfram_alpha"]

for package_name in all_tool_package_list:
    try:
        importlib.import_module("chatgpt_tool_hub.tools." + package_name)
    except Exception as e:
        LOG.error(f"[{package_name}] init failed\nerror_info: " + repr(e))
