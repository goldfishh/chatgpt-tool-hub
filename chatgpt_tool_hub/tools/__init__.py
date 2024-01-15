import os

from ..common.log import LOG
from .tool_register import ToolRegister

def get_packages(path):
    """获取指定路径下的所有包名"""
    packages = []
    for name in os.listdir(path):
        full_path = os.path.join(path, name)
        if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, "__init__.py")):
            packages.append(name)
    return packages


def dynamic_tool_loader(**kwargs):
    try:
        all_tool_package_list = get_packages(f"{os.path.dirname(os.path.abspath(__file__))}")
    except Exception as e:
        LOG.debug(f"get_packages error: {repr(e)}")
        all_tool_package_list = ["meteo", "python", "web_requests", "terminal"]
        LOG.info(f"reset to default-tool package: {repr(all_tool_package_list)}")

    for package_name in all_tool_package_list:
        try:
            import importlib
            importlib.import_module(f".tools.{package_name}", package="chatgpt_tool_hub")
        except Exception as e:
            LOG.debug(f"import [{package_name}] failed, error_info: {repr(e)}")
    
    from .tool_register import main_tool_register
    registered_tool = main_tool_register.get_registered_tool()
    invalid_tool_list = []
    for name, (func, _) in registered_tool.items():
        try:
            _ = func(**kwargs)
        except Exception as e:
            invalid_tool_list.append(name)
            LOG.info(f"[{name}] initialization failed, error_info: {repr(e)}")
    for tool in invalid_tool_list:
        main_tool_register.unregister_tool(tool)

from .base_tool import BaseTool
from .summary import SummaryTool

__all__ = [
    "BaseTool",
    "SummaryTool",

    "ToolRegister",
    
    "get_packages",
    "dynamic_tool_loader",
]
