import json
from typing import Any
from datetime import datetime, timedelta, timezone
from rich.console import Console

from ....chains.llm import LLMChain
from ....common.utils import get_from_dict_or_env
from ....common.log import LOG
from ....models import build_model_params
from ....models.model_factory import ModelFactory
from ....tools.web_requests import RequestsWrapper
from ... import BaseTool
from .. import news_tool_register
from .prompt import QUERY_PROMPT

default_tool_name = "news-api"


class NewsApiTool(BaseTool):
    name: str = default_tool_name
    description: str = (
        "Use this when you want to get information about the top headlines of current news stories. "
        "The input should be a question in natural language that this API can answer."
    )
    api_key: str = None
    debug: bool = False    

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        super().__init__(console=console)

        self.api_key = get_from_dict_or_env(tool_kwargs, "news_api_key", "NEWS_API_KEY")
        self.debug = get_from_dict_or_env(tool_kwargs, "news_api_debug", "NEWS_API_DEBUG", False)
        
        llm = ModelFactory().create_llm_model(**build_model_params(tool_kwargs))
        self.bot = LLMChain(llm=llm, prompt=QUERY_PROMPT)

    def _run(self, query: str) -> str:
        """Use the tool."""
        if not query:
            return "the input of tool is empty"
        
        query = self.bot(query)
        LOG.debug(f"[{default_tool_name}]: search_query: {query}")
        if self.debug:
            return query
        query_url = query["text"].strip()
        try:
            requests_wrapper = RequestsWrapper(headers={"X-Api-Key": self.api_key})
            api_response = requests_wrapper.get(query_url)
            response_json = json.loads(api_response)
            if response_json["status"] != "ok":
                LOG.error(f"[{default_tool_name}] code: {response_json.get('code', '')}, message: {response_json.get('message', '')}")
                return f"{response_json['message']}" if response_json.get('message') else 'call news-api error'
        except Exception as e:
            LOG.error(f"[{default_tool_name}] parsing api_response error: {repr(e)}")
            return f"parsing api_response error"
        if not response_json.get("articles", []):
            return f"not news searched"
        
        _news_list = []
        for article in response_json["articles"]:
            if not article.get('title', '') or not article.get('url', ''):
                continue

            _title = article.get('title', '')
            _author = article.get('author', '')
            if article.get('publishedAt'):
                _date_str = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00')) \
                                    .astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
            
            _source = article.get('source', {}).get('name', '')

            _description = article.get('description', '')
            _content = article.get('content', '')
            _url = article.get('url', '')
            _news_str = f"《{_title}》 {_source} {_author}"
            if _date_str:
                _news_str += f"\n日期：{_date_str}"
            if _description:
                _news_str += f"\n\n{_description}"
            if _content:
                _news_str += f"\n\n{_content}"
            if _url:
                _news_str += f"\n链接：{_url}"
            _news_list.append(_news_str)
        _news_content = "\n\n---\n\n".join(_news_list)

        return _news_content
    

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("NewsTool does not support async")


news_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: NewsApiTool(console, **kwargs), ["news_api_key"])
