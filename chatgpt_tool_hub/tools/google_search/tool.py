"""Tool for the Google search API."""
from typing import Any

from rich.console import Console

from ...chains.llm import LLMChain
from ...models import build_model_params
from ...models.model_factory import ModelFactory
from ...common.utils import get_from_dict_or_env
from ...common.log import LOG
from .. import BaseTool
from ..tool_register import main_tool_register
from .wrapper import GoogleSearchAPIWrapper
from .prompt import QUERY_PROMPT

default_tool_name = "google-search"


class GoogleSearchTool(BaseTool):
    """Tool that adds the capability to query the Google search API."""

    name: str = default_tool_name
    description: str = (
        "A wrapper around Google Search. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query."
    )
    api_wrapper: GoogleSearchAPIWrapper = None
    debug: bool = False

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)
        self.api_wrapper = GoogleSearchAPIWrapper(**tool_kwargs)

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        self.bot = LLMChain(llm=llm, prompt=QUERY_PROMPT)

        self.debug = get_from_dict_or_env(tool_kwargs, "google_debug", "GOOGLE_DEBUG", False)

    def _run(self, query: str) -> str:
        """Use the tool."""
        query = self.bot(query)
        LOG.debug(f"[{default_tool_name}]: search_query: {query}")
        if self.debug:
            return query
        
        return self.api_wrapper.run(query["text"])

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GoogleSearchRun does not support async")

# register the tool
main_tool_register.register_tool(default_tool_name,
                                 lambda console=None, **kwargs: GoogleSearchTool(console, **kwargs),
                                 tool_input_keys=["google_api_key", "google_cse_id"])
