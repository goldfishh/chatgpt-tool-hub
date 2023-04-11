from typing import Any

from chatgpt_tool_hub.chains import LLMChain
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.models import build_model_params
from chatgpt_tool_hub.models.model_factory import ModelFactory
from chatgpt_tool_hub.prompts import PromptTemplate
from chatgpt_tool_hub.tools.all_tool_list import register_tool
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.morning_news.summary_prompt import SUMMARY_DOCS
from chatgpt_tool_hub.tools.web_requests.get import RequestsWrapper
from chatgpt_tool_hub.common.log import LOG

default_tool_name = "morning-news"


class MorningNewsTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        "Use this tool when you want to get information about Daily 60 seconds morning news today. "
        "The input should be a question in natural language that this API can answer."
    )
    bot: Any = None
    zaobao_api_key: str = ""

    def __init__(self, **tool_kwargs: Any):
        # 这个工具直接返回内容
        super().__init__(return_direct=True)
        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        prompt = PromptTemplate(
            input_variables=["morning_news"],
            template=SUMMARY_DOCS,
        )
        self.bot = LLMChain(llm=llm, prompt=prompt)

        self.zaobao_api_key = get_from_dict_or_env(tool_kwargs, "zaobao_api_key", "ZAOBAO_API_KEY")

    def _run(self, query: str) -> str:
        """Use the tool."""
        if not query:
            return "the input of tool is empty"

        morning_news_url = "https://v2.alapi.cn/api/zaobao?token={}&format={}".format(self.zaobao_api_key, "json")
        _response = RequestsWrapper().get(morning_news_url)
        LOG.debug("[morning-news]: api-response: " + str(_response))
        _return = self.bot.run(_response)
        return _return

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("NewsTool does not support async")


register_tool(default_tool_name, lambda kwargs: MorningNewsTool(**kwargs), ["zaobao_api_key"])


if __name__ == "__main__":
    tool = MorningNewsTool(zaobao_api_key="xx")
    content = tool.run("给我发一下早报？")
    print(content)

