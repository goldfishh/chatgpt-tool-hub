import json
from typing import Any

from rich.console import Console

from chatgpt_tool_hub.chains import LLMChain
from chatgpt_tool_hub.common.utils import get_from_dict_or_env
from chatgpt_tool_hub.models import build_model_params
from chatgpt_tool_hub.models.model_factory import ModelFactory
from chatgpt_tool_hub.prompts import PromptTemplate
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.news import news_tool_register
from chatgpt_tool_hub.tools.news.morning_news.prompt import SUMMARY_DOCS
from chatgpt_tool_hub.tools.web_requests.get import RequestsWrapper

default_tool_name = "morning-news"


class MorningNewsTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        "Use this tool when you want to get information about Daily 60 seconds Chinese morning news today. "
        "no input."
    )
    bot: Any = None
    morning_news_api_key: str = ""
    morning_news_use_llm: bool = False

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        # 这个工具直接返回内容
        super().__init__(console=console, return_direct=True)

        self.morning_news_api_key = get_from_dict_or_env(tool_kwargs, "morning_news_api_key", "MORNING_NEWS_API_KEY")
        self.morning_news_use_llm = get_from_dict_or_env(tool_kwargs, "morning_news_use_llm", "MORNING_NEWS_USE_LLM", False)

        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        prompt = PromptTemplate(
            input_variables=["morning_news"],
            template=SUMMARY_DOCS,
        )
        self.bot = LLMChain(llm=llm, prompt=prompt)

    def _run(self, query: str) -> str:
        """Use the tool."""
        morning_news_url = f"https://v2.alapi.cn/api/zaobao?token={self.morning_news_api_key}&format=json"
        _response = RequestsWrapper().get(morning_news_url)
        _response_json = json.loads(_response)
        if self.morning_news_use_llm:
            return self.bot.run(_response)
        elif _response_json.get("code") == 200 or _response_json.get("msg") == "success":
            # 不使用llm，表明人类具有先天的优越性
            _return_data = _response_json.get('data', {})
            _date = _return_data.get('date')
            _news_content = "\n".join(_return_data.get("news"))
            _weiyu = _return_data.get('weiyu')
            _image_url = _return_data.get('image')
            return f"\n今日日期：{_date}\n\n今日早报：{_news_content}\n\n今日微语：{_weiyu}\n\nURL: {_image_url}"
        else:
            return f"[{default_tool_name}] api error, error_info: {_response_json.get('msg')}"

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("NewsTool does not support async")


news_tool_register.register_tool(default_tool_name, lambda console, kwargs: MorningNewsTool(console, **kwargs), ["morning_news_api_key"])


if __name__ == "__main__":
    tool = MorningNewsTool(morning_news_api_key="", morning_news_use_llm=False)
    content = tool.run("给我发一下早报？")
    print(content)

