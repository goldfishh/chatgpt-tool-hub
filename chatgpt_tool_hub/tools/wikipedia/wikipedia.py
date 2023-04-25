"""Tool for the Wikipedia API."""
from typing import Any

from rich.console import Console

from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.wikipedia.wrapper import WikipediaAPIWrapper

default_tool_name = "wikipedia"


class WikipediaTool(BaseTool):
    """Tool that adds the capability to search using the Wikipedia API."""

    name = default_tool_name
    description = (
        "Useful for when you need to answer general questions about "
        "people, places, companies, historical events, or other subjects. "
        "Input should be a search query."
    )
    api_wrapper: WikipediaAPIWrapper = None

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        # 这个工具直接返回内容
        super().__init__(console=console, return_direct=False)
        self.api_wrapper = WikipediaAPIWrapper(**tool_kwargs)

    def _run(self, query: str) -> str:
        """Use the Wikipedia tool."""
        return self.api_wrapper.run(query)

    async def _arun(self, query: str) -> str:
        """Use the Wikipedia tool asynchronously."""
        raise NotImplementedError("WikipediaQueryRun does not support async")


main_tool_register.register_tool(default_tool_name, lambda console, kwargs: WikipediaTool(console, **kwargs), [])
