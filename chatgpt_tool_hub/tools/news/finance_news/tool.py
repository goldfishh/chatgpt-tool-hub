import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from rich.console import Console

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.news import news_tool_register
from chatgpt_tool_hub.tools.web_requests.wrapper import RequestsWrapper

default_tool_name = "finance-news"


class FinanceNewsTool(BaseTool):
    
    name: str = default_tool_name
    description: str = (
        "Useful when you want to stay up-to-date on global real-time financial news."
        "The tool aggregates various types of data and information from the financial investment industry."
        "input is needless for this tool."
    )

    jin10_url: str = "https://www.topworldbullion.com/data/homemarketnews"
    news_set: set = set()

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console, return_direct=True)

    def _parse_js(self, source: str):
        _return_str = ""
        _start_pos = source.find("[")
        _end_pos = source.rfind("]")
        if _start_pos == -1 or _end_pos == -1 or _start_pos >= _end_pos:
            LOG.warning("parse error in finance tool, source_text: " + str(source))
            return _return_str
        return source[_start_pos:_end_pos+1]

    def _output_str_render(self, parse_resp: str):
        _resp_json = json.loads(parse_resp)
        _output_str = "当前财经资讯：{}\n\n".format(datetime.now().strftime("%Y-%m-%d"))
        _ctn = 0
        for news in reversed(_resp_json):
            _id = news['id']
            _datetime = datetime.fromisoformat(news['time'].replace('Z', '+00:00')).astimezone(timezone(timedelta(hours=8)))
            _date_str = _datetime.strftime("%Y-%m-%d %H:%M:%S")
            _content = news['data'].get('content', '').replace("<b>", "").replace("</b>", "").replace("<br/>", " ")
            _pic = news['data'].get('pic', '')
            if _pic:
                _pic = "附图: " + _pic
            _title = news['data'].get('title', '')
            if _title:
                _title = "【" + _title + "】"
            _ctn += 1
            _output_str += "{} {}.{} {} {}\n\n".format(_date_str, _ctn, _title, _content, _pic)
        return _output_str

    def _run(self, tool_input: str) -> str:
        requests_wrapper = RequestsWrapper()
        _output_str = ""
        try:
            resp = requests_wrapper.get(self.jin10_url)
            _parse_resp = self._parse_js(resp)
            _output_str = self._output_str_render(_parse_resp)
        except Exception as e:
            LOG.exception(e)
            _output_str = "出错，看日志"
        return _output_str

    async def _arun(self, tool_input: str) -> str:
        pass


news_tool_register.register_tool(default_tool_name, lambda console, kwargs: FinanceNewsTool(console, **kwargs), [])


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)

    tool = FinanceNewsTool()
    content = tool.run("")
    print(content)
