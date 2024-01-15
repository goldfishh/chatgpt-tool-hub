import logging
from typing import Any

from rich.console import Console

from ...common.log import LOG
from ...common.utils import get_from_dict_or_env
from ..tool_register import main_tool_register
from .. import BaseTool
from . import BaseRequestsTool, filter_text, RequestsWrapper

default_tool_name = "url-get"


class RequestsGetTool(BaseRequestsTool, BaseTool):
    """Tool for making a GET request to an API endpoint."""

    name: str = default_tool_name
    description: str = (
        "A portal to the internet. Use this when you need to get specific content from a website. "
        "Input should be a url (i.e. https://www.google.com). "
        "The output will be the text response of the GET request."
    )
    use_summary: bool = False

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        # 这个工具直接返回内容
        super().__init__(console=console, requests_wrapper=RequestsWrapper(**tool_kwargs), return_direct=False)

        self.use_summary = get_from_dict_or_env(
            tool_kwargs, 'url_get_use_summary', "URL_GET_USE_SUMMARY", True
        )

    def _run(self, url: str) -> str:
        """Run the tool."""
        try:
            html = self.requests_wrapper.get(url)
            _content = filter_text(html, self.use_summary, self.console)
            LOG.debug(f"[url-get] output: {str(_content)}")
        except Exception as e:
            LOG.error(f"[url-get] {str(e)}")
            _content = repr(e)
        return _content

    async def _arun(self, url: str) -> str:
        """Run the tool asynchronously."""
        try:
            html = await self.requests_wrapper.aget(url)
            _content = filter_text(html, self.use_summary, self.console)
            LOG.debug(f"[url-get] output: {str(_content)}")
        except Exception as e:
            LOG.error(f"[url-get] {str(e)}")
            _content = repr(e)
        return _content

# register the tool
main_tool_register.register_tool(default_tool_name, lambda console=None, **kwargs: RequestsGetTool(console, **kwargs), [])


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)
    requests_wrapper = RequestsWrapper()
    tool = RequestsGetTool(requests_wrapper=requests_wrapper)
    content = tool.run("https://github.com/goldfishh/chatgpt-tool-hub")
    print(content)
