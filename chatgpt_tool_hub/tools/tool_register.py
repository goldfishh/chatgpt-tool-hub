from typing import List

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.common.singleton import Singleton


class ToolRegister(Singleton):
    REGISTER_TOOLS = {}

    def __init__(self):
        if not self.REGISTER_TOOLS:
            self.REGISTER_TOOLS = {}

    def register_tool(self, name: str, function: callable, tool_input_keys: list):
        self.REGISTER_TOOLS[name] = (function, tool_input_keys)

    def unregister_tool(self, name: str) -> bool:
        if self.REGISTER_TOOLS.get(name):
            self.REGISTER_TOOLS.pop(name)
            return True
        else:
            LOG.warning(f"unregister a unknown tool: {name}")
            return False

    def get_registered_tool_names(self) -> List[str]:
        """Get a list of all possible tool names."""
        return list(self.REGISTER_TOOLS)

    def get_registered_tool(self) -> dict:
        return self.REGISTER_TOOLS
