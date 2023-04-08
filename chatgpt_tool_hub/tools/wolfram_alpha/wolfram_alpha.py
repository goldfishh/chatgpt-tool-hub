"""Tool for the Wolfram Alpha API."""

from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.wolfram_alpha.wrapper import WolframAlphaAPIWrapper
from chatgpt_tool_hub.tools.all_tool_list import register_tool


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
    api_wrapper: WolframAlphaAPIWrapper

    def _run(self, query: str) -> str:
        """Use the WolframAlpha tool."""
        return self.api_wrapper.run(query)

    async def _arun(self, query: str) -> str:
        """Use the WolframAlpha tool asynchronously."""
        raise NotImplementedError("WolframAlphaTool does not support async")


register_tool(default_tool_name, lambda kwargs: WolframAlphaTool(api_wrapper=WolframAlphaAPIWrapper(**kwargs)),
              tool_input_keys=["wolfram_alpha_appid"])
