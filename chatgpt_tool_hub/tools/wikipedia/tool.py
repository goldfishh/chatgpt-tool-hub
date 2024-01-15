"""Tool for the Wikipedia API."""
from typing import Any

from rich.console import Console

from ...common.log import LOG
from ...chains.llm import LLMChain
from ...models import build_model_params
from ...models.model_factory import ModelFactory
from ...common.utils import get_from_dict_or_env
from .. import BaseTool
from ..tool_register import main_tool_register
from .wrapper import WikipediaAPIWrapper
from .prompt import QUERY_PROMPT

default_tool_name = "wikipedia"


class WikipediaTool(BaseTool):
    """Tool that adds the capability to search using the Wikipedia API."""

    name: str = default_tool_name
    description: str = (
        "Useful for when you need to answer general questions about "
        "people, places, companies, historical events, or other subjects. "
        "Input should be a search query."
    )
    api_wrapper: WikipediaAPIWrapper = None
    debug: bool = False

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        # 这个工具直接返回内容
        super().__init__(console=console, return_direct=False)
        self.api_wrapper = WikipediaAPIWrapper(**tool_kwargs)

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        self.bot = LLMChain(llm=llm, prompt=QUERY_PROMPT)

        self.debug = get_from_dict_or_env(tool_kwargs, "wikipedia_debug", "WIKIPEDIA_DEBUG", False)

    def _run(self, query: str) -> str:
        """Use the Wikipedia tool."""
        query = self.bot(query)
        LOG.debug(f"[{default_tool_name}]: search_query: {query}")
        if self.debug:
            return query
        
        return self.api_wrapper.run(query["text"])

    async def _arun(self, query: str) -> str:
        """Use the Wikipedia tool asynchronously."""
        raise NotImplementedError("WikipediaQueryTool does not support async")

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: WikipediaTool(console, **kwargs), [])
