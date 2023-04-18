from typing import List

from chatgpt_tool_hub.tools.tool_register import ToolRegister


main_tool_register = ToolRegister()


# used by chatgpt-on-wechat now , don't move it
def get_all_tool_names() -> List[str]:
    """Get a list of all possible tool names."""
    return main_tool_register.get_registered_tool_names()
