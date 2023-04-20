from chatgpt_tool_hub.common.log import LOG


def dynamic_tool_loader():
    # dev tool: debug   visual_dl  searxng_search
    all_tool_package_list = ["bing_search", "google_search", "meteo", "news", "arxiv_search",
                             "web_requests", "wikipedia", "wolfram_alpha"]

    for package_name in all_tool_package_list:
        try:
            import importlib
            importlib.import_module("chatgpt_tool_hub.tools." + package_name)
        except Exception as e:
            LOG.info(f"[{package_name}] init failed, error_info: " + repr(e))


from chatgpt_tool_hub.tools.python import PythonREPLTool
from chatgpt_tool_hub.tools.summary import SummaryTool
from chatgpt_tool_hub.tools.terminal import TerminalTool
from chatgpt_tool_hub.tools.web_requests import BrowserTool


__all__ = [
    "SummaryTool",
    "PythonREPLTool",
    "TerminalTool",
    "BrowserTool",
    "dynamic_tool_loader"
]
