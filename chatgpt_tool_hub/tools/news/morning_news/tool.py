import json
from typing import Any
from enum import Enum
from rich.console import Console


from ....common.utils import get_from_dict_or_env
from ... import BaseTool
from .. import news_tool_register
from ...web_requests.get import RequestsWrapper

default_tool_name = "morning-news"

class OutputType(str, Enum):
    text = "text"
    image = "image"

class MorningNewsTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        "Use this tool when you want to get information about Daily 60 seconds Chinese morning news today. "
        "no input."
    )
    api_key: str = ""
    url_template: str = "https://v2.alapi.cn/api/zaobao?token={token}&format=json"
    simple: bool = True
    output_type: OutputType = OutputType.text

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        # 这个工具直接返回内容
        super().__init__(console=console, return_direct=True)

        self.api_key = get_from_dict_or_env(tool_kwargs, "morning_news_api_key", "MORNING_NEWS_API_KEY")
        self.simple = get_from_dict_or_env(tool_kwargs, "morning_news_simple", "MORNING_NEWS_SIMPLE", True)
        self.output_type = get_from_dict_or_env(tool_kwargs, "morning_news_output_type", "MORNING_NEWS_OUTPUT_TYPE", OutputType.text)

    def _run(self, _: str) -> str:
        """Use the tool."""
        morning_news_url = self.url_template.format(token=self.api_key)
        _response = RequestsWrapper(proxy="").get(morning_news_url)
        _response_json = json.loads(_response)
        
        if _response_json.get("code") == 200 or _response_json.get("msg") == "success":
            _return_data = _response_json.get('data', {})
            _date, _image_url = _return_data.get('date'), _return_data.get('image')
            _news_content = "\n".join(_return_data.get("news"))
            _weiyu = _return_data.get('weiyu')

            if self.output_type == OutputType.image:
                return json.dumps({"date": _date, "url": _image_url}, indent=4, ensure_ascii=False)
            if self.simple:
                return f"{_date}\n\n{_news_content}"
            return f"今日日期：{_date}\n\n今日早报：\n{_news_content}\n\n今日微语：{_weiyu}\n\nURL: {_image_url}\n"
        else:
            return f"[{default_tool_name}] api error, error_info: {_response_json.get('msg')}"

    async def _arun(self, _: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MorningNewsTool does not support async")


news_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: MorningNewsTool(console, **kwargs), ["morning_news_api_key"])


if __name__ == "__main__":
    tool = MorningNewsTool(morning_news_simple=False, morning_news_output_type="image")
    content = tool.run("给我发一下早报？")
    print(content)

