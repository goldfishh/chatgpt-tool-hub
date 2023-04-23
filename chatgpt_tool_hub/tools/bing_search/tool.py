"""Tool for the Bing search API."""
from typing import Any

from rich.console import Console

from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.bing_search import BingSearchAPIWrapper

default_tool_name = "bing-search"


class BingSearch(BaseTool):
    """Tool that adds the capability to query the Bing search API.

    In order to set this up, follow instructions at:
    https://levelup.gitconnected.com/api-tutorial-how-to-use-bing-web-search-api-in-python-4165d5592a7e
    """

    name = default_tool_name
    description = (
        "A wrapper around Bing Search. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query."
    )
    api_wrapper: BingSearchAPIWrapper = None

    def __init__(self, console: Console = Console(), **tool_kwargs):
        super().__init__(console=console)
        self.api_wrapper = BingSearchAPIWrapper(**tool_kwargs)

    def _run(self, query: str) -> str:
        """Use the tool."""
        return self.api_wrapper.run(query)

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("BingSearch does not support async")


main_tool_register.register_tool(default_tool_name, lambda console, kwargs: BingSearch(console, **kwargs),
                                 tool_input_keys=["bing_subscription_key"])
