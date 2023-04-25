"""Tool for the Wolfram Alpha API."""

from typing import Any

from rich.console import Console

from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.wolfram_alpha.wrapper import WolframAlphaAPIWrapper

default_tool_name = "wolfram-alpha"


class WolframAlphaTool(BaseTool):
    """Tool that adds the capability to query using the Wolfram Alpha SDK."""

    name = default_tool_name
    description = (
        "A wrapper around Wolfram Alpha. "
        "Useful for when you need to answer questions about Math, "
        "Science, Technology, Culture, Society and Everyday Life. "
        "Input should be a search query."
    )
    api_wrapper: WolframAlphaAPIWrapper = None

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        # 这个工具直接返回内容
        super().__init__(console=console, return_direct=False)
        self.api_wrapper = WolframAlphaAPIWrapper(**tool_kwargs)

    def _run(self, query: str) -> str:
        """Use the WolframAlpha tool."""
        return self.api_wrapper.run(query)

    async def _arun(self, query: str) -> str:
        """Use the WolframAlpha tool asynchronously."""
        raise NotImplementedError("WolframAlphaTool does not support async")


main_tool_register.register_tool(default_tool_name, lambda console, kwargs: WolframAlphaTool(console, **kwargs),
                                 tool_input_keys=["wolfram_alpha_appid"])
