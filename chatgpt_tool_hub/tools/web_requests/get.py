import logging
from typing import Any

from rich.console import Console

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.web_requests import BaseRequestsTool, filter_text, RequestsWrapper

default_tool_name = "url-get"


class RequestsGetTool(BaseRequestsTool, BaseTool):
    """Tool for making a GET request to an API endpoint."""

    name = default_tool_name
    description = (
        "A portal to the internet. Use this when you need to get specific content from a website. "
        "Input should be a url (i.e. https://www.google.com). "
        "The output will be the text response of the GET request."
    )

    def __init__(self, console: Console = Console(), **tool_kwargs: Any):
        # 这个工具直接返回内容
        super().__init__(console=console, requests_wrapper=RequestsWrapper(**tool_kwargs), return_direct=False)

    def _run(self, url: str) -> str:
        """Run the tool."""
        try:
            html = self.requests_wrapper.get(url)
            _content = filter_text(html)
            LOG.debug(f"[url-get] output: {str(_content)}")
        except Exception as e:
            LOG.error(f"[url-get] {str(e)}")
            _content = repr(e)
        return _content

    async def _arun(self, url: str) -> str:
        """Run the tool asynchronously."""
        try:
            html = await self.requests_wrapper.aget(url)
            _content = filter_text(html)
            LOG.debug(f"[url-get] output: {str(_content)}")
        except Exception as e:
            LOG.error(f"[url-get] {str(e)}")
            _content = repr(e)
        return _content


main_tool_register.register_tool(default_tool_name, lambda console, kwargs: RequestsGetTool(console, **kwargs), [])


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)
    requests_wrapper = RequestsWrapper()
    tool = RequestsGetTool(requests_wrapper=requests_wrapper)
    content = tool.run("https://github.com/goldfishh/chatgpt-tool-hub")
    print(content)
