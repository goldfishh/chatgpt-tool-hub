"""Load tools."""
from typing import Any, List
from typing import Optional

from chatgpt_tool_hub.common.callbacks import BaseCallbackManager
from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.tools.all_tool_list import get_all_tool_dict
from chatgpt_tool_hub.tools.base_tool import BaseTool


def load_tools(
    tool_names: List[str],
    callback_manager: Optional[BaseCallbackManager] = None,
    **kwargs: Any,
) -> List[BaseTool]:
    """Load tools based on their name.

    Args:
        tool_names: name of tools to load.
        callback_manager: Optional callback manager. If not provided, default global callback manager will be used.
    Returns:
        List of tools.
    """
    tools = []
    all_tool_dict = get_all_tool_dict()
    for name in tool_names:
        if name in all_tool_dict:
            _get_tool_func, extra_keys = all_tool_dict[name]

            # consistency validation between input and required params
            missing_keys = set(extra_keys).difference(kwargs)
            if missing_keys:
                raise ValueError(
                    f"Tool {name} requires some parameters that were not "
                    f"provided: {missing_keys}"
                )

            sub_kwargs = {k: kwargs[k] for k in extra_keys if k in kwargs}
            tool = _get_tool_func(sub_kwargs)

            if callback_manager is not None:
                tool.callback_manager = callback_manager

            tools.append(tool)
        else:
            LOG.error("All the tools currently supported are："+str(list(all_tool_dict)))
            raise ValueError(f"Got unknown tool: {name}")
    filter_tools = crop_tools(tools)
    return filter_tools


def crop_tools(tools: List[BaseTool]) -> List[BaseTool]:
    if len(tools) > 8:
        LOG.warning(f"get too many tools, tools after {tools[8].name} will be ignored...")
        return tools[:8]
    # todo: 检查description是否超出限制
    for tool in tools:
        pass
    return tools
