"""Tool for the Bing search API."""
from rich.console import Console

from ...common.log import LOG
from ...chains.llm import LLMChain
from ...models import build_model_params
from ...models.model_factory import ModelFactory
from ...common.utils import get_from_dict_or_env

from ..tool_register import main_tool_register
from .. import BaseTool
from .wrapper import BingSearchAPIWrapper
from .prompt import QUERY_PROMPT

default_tool_name = "bing-search"


class BingSearchTool(BaseTool):
    """Tool that adds the capability to query the Bing search API.

    In order to set this up, follow instructions at:
    https://levelup.gitconnected.com/api-tutorial-how-to-use-bing-web-search-api-in-python-4165d5592a7e
    """

    name: str = default_tool_name
    description: str = (
        "A wrapper around Bing Search. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query."
    )
    api_wrapper: BingSearchAPIWrapper = None
    debug: bool = False

    def __init__(self, console: Console = Console(), **tool_kwargs):
        super().__init__(console=console)
        self.api_wrapper = BingSearchAPIWrapper(**tool_kwargs)

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        self.bot = LLMChain(llm=llm, prompt=QUERY_PROMPT)

        self.debug = get_from_dict_or_env(tool_kwargs, "bing_search_debug", "BING_SEARCH_DEBUG", False)

    def _run(self, query: str) -> str:
        """Use the tool."""
        query = self.bot(query)
        LOG.debug(f"[{default_tool_name}]: search_query: {query}")
        if self.debug:
            return query

        return self.api_wrapper.run(query["text"])

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("BingSearchTool does not support async")

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: BingSearchTool(console, **kwargs),
                                 tool_input_keys=["bing_subscription_key"])

if __name__ == "__main__":
    tool = BingSearchTool()
    result = tool.run("帮我查询北京有哪些区。")
    print(result)
