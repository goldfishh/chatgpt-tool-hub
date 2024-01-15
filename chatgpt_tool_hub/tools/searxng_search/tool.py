"""Tool for the SearxNG search API."""
from typing import Any

from rich.console import Console

from ...chains.llm import LLMChain
from ...models import build_model_params
from ...models.model_factory import ModelFactory
from ...common.utils import get_from_dict_or_env
from ...common.log import LOG
from .. import BaseTool
from ..tool_register import main_tool_register
from .wrapper import SearxSearchWrapper
from .prompt import QUERY_PROMPT

default_tool_name = "searxng-search"


class SearXNGSearchTool(BaseTool):
    """Tool that adds the capability to query a Searx instance."""

    name: str = default_tool_name
    description: str = (
        "A meta search engine."
        "Useful for when you need to answer questions about current events."
        "Input should be a search query."
    )
    api_wrapper: SearxSearchWrapper = None
    debug: bool = False

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)
        self.api_wrapper = SearxSearchWrapper(**tool_kwargs)

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        self.bot = LLMChain(llm=llm, prompt=QUERY_PROMPT)

        self.debug = get_from_dict_or_env(tool_kwargs, "searxng_search_debug", "SEARXNG_SEARCH_DEBUG", False)

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
        # return await self.api_wrapper.arun(query)

# register the tool
main_tool_register.register_tool(default_tool_name,
                                 lambda console=None, **kwargs: SearXNGSearchTool(console, **kwargs),
                                 tool_input_keys=["searx_search_host"])
