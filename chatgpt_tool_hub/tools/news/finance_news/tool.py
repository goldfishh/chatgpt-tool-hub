import json
from datetime import datetime, timedelta, timezone
from typing import Any, List, Set

from rich.console import Console

from ....common.log import LOG
from ....common.utils import get_from_dict_or_env
from ... import BaseTool
from ...web_requests.wrapper import RequestsWrapper
from .. import news_tool_register

default_tool_name = "finance-news"


class FinanceNewsTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        "Useful when you want to stay up-to-date on global real-time financial news."
        "The tool aggregates various types of data and information from the financial investment industry."
        "input is needless for this tool."
    )

    jin10_url: str = "https://www.topworldbullion.com/data/homemarketnews"
    filter: bool = False  #是否过滤新闻
    filter_list: List[str] = []  # 过滤词，非空时生效
    simple: bool = True
    repeat_news: bool = False
    history_ids: Set[int] = set()

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console, return_direct=True)

        self.filter = get_from_dict_or_env(tool_kwargs, "finance_news_filter", "FINANCE_NEWS_FILTER", False)
        self.filter_list = get_from_dict_or_env(tool_kwargs, "finance_news_filter_list", "FINANCE_NEWS_FILTER_LIST", [])

        self.simple = get_from_dict_or_env(tool_kwargs, "finance_news_simple", "FINANCE_NEWS_SIMPLE", True)
        self.repeat_news = get_from_dict_or_env(tool_kwargs, "finance_news_repeat_news", "FINANCE_NEWS_REPEAT_NEWS", False)

    def _parse_js(self, source: str):
        """解析最外层中括号的文本"""
        _return_str = ""
        _start_pos, _end_pos = source.find("["), source.rfind("]")
        if _start_pos == -1 or _end_pos == -1 or _start_pos >= _end_pos:
            LOG.warning("parse error in finance tool, source_text: " + str(source))
            return _return_str
        return source[_start_pos:_end_pos+1]

    def _output_str_render(self, parse_resp: str):
        _resp_json = json.loads(parse_resp)
        _news_list = []
        for news in reversed(_resp_json):
            if not news.get('data', {}).get('content', ''):
                continue
            if self.repeat_news:
                _id = int(news['id'])
                if _id in self.history_ids: continue  # remove repeat news
                self.history_ids.add(_id)  # insert
                threshold_id = int(datetime.now().strftime("%Y%m%d%H%M%S000000"))
                self.history_ids = {x for x in self.history_ids if x < threshold_id}  # hash update

            _content = news['data']['content'].replace("<b>", "").replace("</b>", "").replace("<br/>", " ")

            _title = f"({news['data']['title']})" if news.get('data', {}).get('title', '') else ""
            _pic = f"[{news['data']['pic']}]" if news.get('data', {}).get('pic', '') else ""
            _date_str = datetime.fromisoformat(news['time'].replace('Z', '+00:00')) \
                                .astimezone(timezone(timedelta(hours=8))).strftime("%H:%M:%S")
            
            _news_str = "{} {} {} {}".format(_date_str, _title, _content, _pic)
            if self.filter and self.filter_list:
                found = False
                for filter_text in self.filter_list:
                    if filter_text in _news_str:
                        found = True
                        break
                if not found: continue
            _news_list.append(_news_str)
        _news_content = "\n".join(_news_list)

        if self.simple:
            return "{}\n\n{}".format(datetime.now().strftime("%Y-%m-%d"), _news_content)
        return "今日日期：{}\n\n当前财经资讯：\n{}".format(datetime.now().strftime("%Y-%m-%d"), _news_content)

    def _run(self, _: str) -> str:
        try:
            resp = RequestsWrapper(proxy="").get(self.jin10_url)
            _parse_resp = self._parse_js(resp)
            _output_str = self._output_str_render(_parse_resp)
        except Exception as e:
            LOG.exception(e)
            _output_str = "出错，看日志"
        return _output_str

    async def _arun(self, _: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MorningNewsTool does not support async")


news_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: FinanceNewsTool(console, **kwargs), [])


if __name__ == "__main__":
    tool = FinanceNewsTool()
    content = tool.run("")
    print(content)
