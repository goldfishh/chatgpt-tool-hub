"""Load tools."""
import os
from typing import Any, List
from typing import Optional

from ..common.callbacks import BaseCallbackManager
from ..common.log import LOG
from . import BaseTool, ToolRegister

from rich.console import Console

def load_tools(
    tool_names: List[str],
    tool_register: ToolRegister,
    console: Console = Console(),
    callback_manager: Optional[BaseCallbackManager] = None,
    **kwargs: Any,
) -> List[BaseTool]:
    """Load tools based on their name.

    Args:
        tool_names: name of tools to load.
        tool_register: the registered object of tools
        console: rich console
        callback_manager: Optional callback manager. If not provided, default global callback manager will be used.
    Returns:
        List of tools.
    """
    tools = []
    all_tool_dict = tool_register.get_registered_tool()
    for name in tool_names:
        if name in all_tool_dict:
            _get_tool_func, extra_keys = all_tool_dict[name]

            # consistency validation between input and required params
            try:
                if missing_keys := set(extra_keys).difference(kwargs):
                    # add env validation
                    for key in missing_keys:
                        env_key = key.upper()
                        if env_key not in os.environ or not os.environ[env_key]:
                            raise ValueError(
                                f"Tool {name} requires some parameters that were not "
                                f"provided: {env_key}"
                            )
            except Exception as e:
                LOG.info(f"[{name}] init failed, error_info: {repr(e)}")
                tool_register.unregister_tool(name)
                continue

            # todo double check here
            #
            try:
                # sub_kwargs = {k: kwargs[k] for k in extra_keys if k in kwargs}
                tool = _get_tool_func(console=console, **kwargs)
            except Exception as e:
                if console: console.log(f"[dim][bold red]{name}[/] init failed, error_info: {repr(e)}")
                tool_register.unregister_tool(name)
                continue

            if callback_manager is not None:
                tool.callback_manager = callback_manager

            tools.append(tool)
        else:
            LOG.error(f"Now registered tools are: {list(all_tool_dict)}")
            raise ValueError(f"Got unknown tool: {name}")
    return crop_tools(tools)


def crop_tools(tools: List[BaseTool]) -> List[BaseTool]:
    if len(tools) > 10:
        LOG.warning(f"loading too many tools, some tools after {tools[10].name} will be ignored...")
        return tools[:10]
    # todo: 检查description是否超出限制
    return tools
