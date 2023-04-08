from typing import Any

from chatgpt_tool_hub.chains.api import APIChain
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.models import build_model_params
from chatgpt_tool_hub.models.model_factory import ModelFactory
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.news.api_docs_prompts import NEWS_DOCS
from chatgpt_tool_hub.tools.all_tool_list import register_tool


default_tool_name = "news"


class NewsTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        "Use this when you want to get information about the top headlines of current news stories. "
        "The input should be a question in natural language that this API can answer."
    )
    api_chain: APIChain = None

    def __init__(self, **tool_kwargs: Any):
        super().__init__()

        news_api_key = get_from_dict_or_env(tool_kwargs, "news_api_key", "NEWS_API_KEY")

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))

        self.api_chain = APIChain.from_llm_and_api_docs(
            llm, NEWS_DOCS, headers={"X-Api-Key": news_api_key}
        )

    def _run(self, query: str) -> str:
        """Use the tool."""
        if not query:
            return "the input of tool is empty"
        if not self.api_chain:
            return "the tool was not initialized"

        return self.api_chain.run(query)

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("NewsTool does not support async")


register_tool(default_tool_name, lambda kwargs: NewsTool(**kwargs), ["news_api_key"])
