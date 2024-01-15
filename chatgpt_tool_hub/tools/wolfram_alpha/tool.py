"""Tool for the Wolfram Alpha API."""

from typing import Any

from rich.console import Console

from ...common.log import LOG
from ...chains.llm import LLMChain
from ...models import build_model_params
from ...models.model_factory import ModelFactory
from ...common.utils import get_from_dict_or_env
from ..tool_register import main_tool_register
from .. import BaseTool
from .wrapper import WolframAlphaAPIWrapper
from .prompt import QUERY_PROMPT

default_tool_name = "wolfram-alpha"


class WolframAlphaTool(BaseTool):
    """Tool that adds the capability to query using the Wolfram Alpha SDK."""

    name: str = default_tool_name
    description: str = (
        "A wrapper around Wolfram Alpha. "
        "Useful for when you need to answer questions about Math, "
        "Science, Technology, Culture, Society and Everyday Life. "
        "Input should be a search query."
    )
    api_wrapper: WolframAlphaAPIWrapper = None
    debug: bool = False

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        # 这个工具直接返回内容
        super().__init__(console=console, return_direct=False)
        self.api_wrapper = WolframAlphaAPIWrapper(**tool_kwargs)

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        self.bot = LLMChain(llm=llm, prompt=QUERY_PROMPT)

        self.debug = get_from_dict_or_env(tool_kwargs, "wolfram_alpha_debug", "WOLFRAM_ALPHA_DEBUG", False)

    def _run(self, query: str) -> str:
        """Use the WolframAlpha tool."""
        query = self.bot(query)
        LOG.debug(f"[{default_tool_name}]: search_query: {query}")
        if self.debug:
            return query
        
        return self.api_wrapper.run(query["text"])

    async def _arun(self, query: str) -> str:
        """Use the WolframAlpha tool asynchronously."""
        raise NotImplementedError("WolframAlphaTool does not support async")

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: WolframAlphaTool(console, **kwargs),
                                 tool_input_keys=["wolfram_alpha_appid"])
