"""Tool for the Google search API."""

from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.google_search.wrapper import GoogleSearchAPIWrapper
from chatgpt_tool_hub.tools.all_tool_list import register_tool


default_tool_name = "google-search"

class GoogleSearch(BaseTool):
    """Tool that adds the capability to query the Google search API."""

    name = default_tool_name
    description = (
        "A wrapper around Google Search. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query."
    )
    api_wrapper: GoogleSearchAPIWrapper

    def _run(self, query: str) -> str:
        """Use the tool."""
        return self.api_wrapper.run(query)

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GoogleSearchRun does not support async")


class GoogleSearchJson(BaseTool):
    """Tool that has capability to query the Google Search API and get back json."""

    name = default_tool_name
    description = (
        "A wrapper around Google Search. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query. Output is a JSON array of the query results"
    )
    api_wrapper: GoogleSearchAPIWrapper

    def _run(self, query: str) -> str:
        """Use the tool."""
        return str(self.api_wrapper.results(query))

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GoogleSearchRun does not support async")


register_tool(default_tool_name, lambda kwargs: GoogleSearchJson(api_wrapper=GoogleSearchAPIWrapper(**kwargs)),
              tool_input_keys=["google_api_key", "google_cse_id"])
