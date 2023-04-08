from typing import List

from chatgpt_tool_hub.common.log import LOG

REGISTER_TOOLS = dict()


def register_tool(name: str, function: callable, tool_input_keys: list):
    REGISTER_TOOLS[name] = (function, tool_input_keys)


def unregister_tool(name: str) -> bool:
    if REGISTER_TOOLS.get(name):
        REGISTER_TOOLS.pop(name)
        return True
    else:
        LOG.warning(f"unregister a unknown tool: {name}")
        return False


# used by chatgpt-on-wechat now , don't move it
def get_all_tool_names() -> List[str]:
    """Get a list of all possible tool names."""
    return (
        list(REGISTER_TOOLS)
    )


def get_all_tool_dict() -> dict:
    _result = dict()
    _result.update(REGISTER_TOOLS)
    return _result
