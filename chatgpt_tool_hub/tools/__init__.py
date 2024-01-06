import os

from ..common.log import LOG


def get_packages(path):
    """获取指定路径下的所有包名"""
    packages = []
    for name in os.listdir(path):
        full_path = os.path.join(path, name)
        if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, "__init__.py")):
            packages.append(name)
    return packages


def dynamic_tool_loader():
    try:
        all_tool_package_list = get_packages(f"{os.path.dirname(os.path.abspath(__file__))}")
    except Exception as e:
        LOG.debug(f"get_packages error: {repr(e)}")
        all_tool_package_list = ["meteo", "system", "web_requests", "wikipedia"]
        LOG.info(f"Detected main tool package: {repr(all_tool_package_list)}")

    for package_name in all_tool_package_list:
        try:
            import importlib
            importlib.import_module(f"..tools.{package_name}")
        except Exception as e:
            LOG.info(f"[{package_name}] init failed, error_info: {repr(e)}")

from .base_tool import BaseTool
from .python import PythonREPLTool
from .summary import SummaryTool
from .terminal import TerminalTool
from .web_requests import BrowserTool
from .tool_register import ToolRegister

__all__ = [
    "BaseTool",
    "SummaryTool",
    "PythonREPLTool",
    "TerminalTool",
    "BrowserTool",

    "ToolRegister",
    
    "get_packages",
    "dynamic_tool_loader",
]
