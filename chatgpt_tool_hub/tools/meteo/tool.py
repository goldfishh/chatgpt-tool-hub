from datetime import datetime

from rich.console import Console

from ...chains.api import APIChain
from ...models import build_model_params
from ...models.model_factory import ModelFactory
from ..tool_register import main_tool_register
from .. import BaseTool
from .docs_prompt import OPEN_METEO_DOCS

default_tool_name = "meteo"


class MeteoWeatherTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        "When you want to obtain weather information, use this tool. Analyze which weather information the user wants, "
        "describe the problem rigorously in natural language, and then pass it on to this tool."
        "It's best to append the weather granularity to the end of the input, such as 'by hour' or 'by day', "
        "with priority given to 'by hour' when querying the weather on a specific day."
    )
    api_chain: APIChain = None

    def __init__(self, console: Console = Console(), **tool_kwargs):
        super().__init__(console=console, return_direct=False)
        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        self.api_chain = APIChain.from_llm_and_api_docs(llm, OPEN_METEO_DOCS, console=console)

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

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: MeteoWeatherTool(console, **kwargs), [])
