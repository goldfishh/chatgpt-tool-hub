"""Tool for the SearxNG search API."""
from typing import Any

from pydantic import Extra
from rich.console import Console

from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.searxng_search.wrapper import SearxSearchWrapper

default_tool_name = "searxng-search"


class SearxSearchTool(BaseTool):
    """Tool that adds the capability to query a Searx instance."""

    name = default_tool_name
    description = (
        "A meta search engine."
        "Useful for when you need to answer questions about current events."
        "Input should be a search query."
    )
    api_wrapper: SearxSearchWrapper

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)

    def _run(self, query: str) -> str:
        """Use the tool."""
        return self.api_wrapper.run(query)

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        return await self.api_wrapper.arun(query)


class SearxSearchJsonTool(BaseTool):
    """(Json result): Tool that has capability to query a Searx instance and get back json."""

    name = "searxng-search"
    description = (
        "A meta search engine."
        "Useful for when you need to answer questions about current events."
        "Input should be a search query. Output is a JSON array of the query results"
    )
    api_wrapper: SearxSearchWrapper
    num_results: int = 4

    def __init__(self, console: Console = Console(), **tool_kwargs):
        super().__init__(console=console, return_direct=True)
        self.api_wrapper = SearxSearchWrapper(**tool_kwargs)

    class Config:
        """Pydantic config."""

        extra = Extra.ignore

    def _run(self, query: str) -> str:
        """Use the tool."""
        return str(self.api_wrapper.results(query, self.num_results))

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        return (await self.api_wrapper.aresults(query, self.num_results)).__str__()


main_tool_register.register_tool(default_tool_name,
                                 lambda console, kwargs: SearxSearchTool(console, **kwargs),
                                 tool_input_keys=["searx_search_host"])
