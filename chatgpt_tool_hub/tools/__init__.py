import importlib

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.tools.summary import SummaryTool
from chatgpt_tool_hub.tools.web_requests.browser import BrowserTool
from chatgpt_tool_hub.tools.python import PythonREPLTool
from chatgpt_tool_hub.tools.terminal import TerminalTool


def dynamic_tool_loader():
    # dev tool: arxiv_search   debug   visual_dl  searxng_search
    all_tool_package_list = ["bing_search", "google_search", "meteo", "news",
                             "web_requests", "wikipedia", "wolfram_alpha"]

    for package_name in all_tool_package_list:
        try:
            importlib.import_module("chatgpt_tool_hub.tools." + package_name)
        except Exception as e:
            LOG.info(f"[{package_name}] init failed, error_info: " + repr(e))


__all__ = [
    "SummaryTool",
    "BrowserTool",
    "PythonREPLTool",
    "TerminalTool",
    "dynamic_tool_loader"
]
