from datetime import datetime

from chatgpt_tool_hub.chains.api import APIChain
from chatgpt_tool_hub.models import build_model_params
from chatgpt_tool_hub.models.model_factory import ModelFactory
from chatgpt_tool_hub.tools.all_tool_list import register_tool
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.meteo.api_docs_prompts import OPEN_METEO_DOCS

default_tool_name = "meteo-weather"


class MeteoWeatherTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        "Useful for when you want to get weather information from the OpenMeteo API. "
        "The input should be a question in natural language that this API can answer."
        "Add a granularity description to input for the weather information to be returned: daily and hourly."
    )
    api_chain: APIChain = None

    def __init__(self, **tool_kwargs):
        super().__init__()
        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        self.api_chain = APIChain.from_llm_and_api_docs(llm, OPEN_METEO_DOCS)

    def _run(self, query: str) -> str:
        """Use the tool."""
        if not query:
            return "the input of tool is empty"
        if not self.api_chain:
            return "the tool was not initialized"

        query += f"\nThe current time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} in UTC+8."

        return self.api_chain.run(query)

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MeteoWeatherTool does not support async")


register_tool(default_tool_name, lambda kwargs: MeteoWeatherTool(**kwargs), [])
