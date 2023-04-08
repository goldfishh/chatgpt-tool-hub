"""Tool for the Wikipedia API."""

from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.wikipedia.wrapper import WikipediaAPIWrapper
from chatgpt_tool_hub.tools.all_tool_list import register_tool


default_tool_name = "wikipedia"

class WikipediaTool(BaseTool):
    """Tool that adds the capability to search using the Wikipedia API."""

    name = default_tool_name
    description = (
        "Useful for when you need to answer general questions about "
        "people, places, companies, historical events, or other subjects. "
        "Input should be a search query."
    )
    api_wrapper: WikipediaAPIWrapper

    def _run(self, query: str) -> str:
        """Use the Wikipedia tool."""
        return self.api_wrapper.run(query)

    async def _arun(self, query: str) -> str:
        """Use the Wikipedia tool asynchronously."""
        raise NotImplementedError("WikipediaQueryRun does not support async")


register_tool(default_tool_name, lambda kwargs: WikipediaTool(api_wrapper=WikipediaAPIWrapper(**kwargs)), [])
