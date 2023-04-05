import logging

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.web_requests import BaseRequestsTool, filter_text, RequestsWrapper


class BrowserTool(BaseRequestsTool, BaseTool):
    """Tool for making a GET request to an API endpoint."""

    name = "Web browser"
    # todo: browser prompt should update later
    description = "A portal to the internet. Use this when you need to get specific content from a website. Input " \
                  "should be a  url (i.e. https://www.google.com). The output will be the text response of the GET " \
                  "request."

    def _run(self, url: str) -> str:
        """Run the tool."""
        try:
            html = self.requests_wrapper.get(url)
            _content = filter_text(html)
            LOG.debug("[browser] output: " + str(_content))
        except Exception as e:
            LOG.error("[browser] " + str(e))
            _content = repr(e)
        return _content

    async def _arun(self, url: str) -> str:
        """Run the tool asynchronously."""
        raise NotImplementedError("not support run this tool in async")


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)
    requests_wrapper = RequestsWrapper()
    tool = BrowserTool(requests_wrapper=requests_wrapper)
