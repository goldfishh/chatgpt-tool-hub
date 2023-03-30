from typing import Any

from chatgpt_tool_hub.chains import APIChain
from chatgpt_tool_hub.tools.tool import Tool

default_name = "OpenMeteo API"
default_description = (
        "Useful for when you want to get weather information from the OpenMeteo API. "
        "The input should be a question in natural language that this API can answer."
    )


class MeteoWeatherTool(Tool):
    name: str
    description: str
    api_chain: APIChain = None

    def __init__(self, api_chain: APIChain, **kwargs: Any):
        super().__init__(default_name, api_chain.run, default_description, **kwargs)
        self.api_chain = api_chain

    def _run(self, query: str) -> str:
        """Use the tool."""
        return self.api_chain.run(query)

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MeteoWeatherTool does not support async")
