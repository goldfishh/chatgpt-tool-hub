from typing import Any

from rich.console import Console

from chatgpt_tool_hub.chains.api import APIChain
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.models import build_model_params
from chatgpt_tool_hub.models.model_factory import ModelFactory
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.news import news_tool_register
from chatgpt_tool_hub.tools.news.news_api.docs_prompt import NEWS_DOCS

default_tool_name = "news-api"


class NewsApiTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        "Use this when you want to get information about the top headlines of current news stories. "
        "The input should be a question in natural language that this API can answer."
    )
    api_chain: APIChain = None

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)

        news_api_key = get_from_dict_or_env(tool_kwargs, "news_api_key", "NEWS_API_KEY")

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))

        self.api_chain = APIChain.from_llm_and_api_docs(
            llm, NEWS_DOCS, console=console, headers={"X-Api-Key": news_api_key}
        )

    def _run(self, query: str) -> str:
        """Use the tool."""
        if not query:
            return "the input of tool is empty"
        return (
            self.api_chain.run(query)
            if self.api_chain
            else "the tool was not initialized"
        )

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("NewsTool does not support async")


news_tool_register.register_tool(default_tool_name, lambda console, kwargs: NewsApiTool(console, **kwargs), ["news_api_key"])
