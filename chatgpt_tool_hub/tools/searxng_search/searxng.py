"""Tool for the SearxNG search API."""
from pydantic import Extra

from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.searxng_search.wrapper import SearxSearchWrapper
from chatgpt_tool_hub.tools.all_tool_list import register_tool


default_tool_name =  "searxng-search"

class SearxSearchTool(BaseTool):
    """Tool that adds the capability to query a Searx instance."""

    name = default_tool_name
    description = (
        "A meta search engine."
        "Useful for when you need to answer questions about current events."
        "Input should be a search query."
    )
    api_wrapper: SearxSearchWrapper

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

    class Config:
        """Pydantic config."""

        extra = Extra.allow

    def _run(self, query: str) -> str:
        """Use the tool."""
        return str(self.api_wrapper.results(query, self.num_results))

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        return (await self.api_wrapper.aresults(query, self.num_results)).__str__()


register_tool(default_tool_name, lambda kwargs: SearxSearchTool(api_wrapper=SearxSearchWrapper(**kwargs)),
              tool_input_keys=["searx_host"])
