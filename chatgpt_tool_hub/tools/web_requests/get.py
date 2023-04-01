import logging

from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.web_requests import BaseRequestsTool, filter_text, RequestsWrapper
from chatgpt_tool_hub.common.log import LOG


class RequestsGetTool(BaseRequestsTool, BaseTool):
    """Tool for making a GET request to an API endpoint."""

    name = "requests_get"
    description = "A portal to the internet. Use this when you need to get specific content from a website. Input " \
                  "should be a  url (i.e. https://www.google.com). The output will be the text response of the GET " \
                  "request."

    def _run(self, url: str) -> str:
        """Run the tool."""
        try:
            html = self.requests_wrapper.get(url)
            _content = filter_text(html)
            LOG.debug("[requests_get] output: " + str(_content))
        except Exception as e:
            LOG.error("[requests_get] " + str(e))
            _content = repr(e)
        return _content

    async def _arun(self, url: str) -> str:
        """Run the tool asynchronously."""
        try:
            html = await self.requests_wrapper.aget(url)
            _content = filter_text(html)
            LOG.debug("[requests_get] output: " + str(_content))
        except Exception as e:
            LOG.error("[requests_get] " + str(e))
            _content = repr(e)
        return _content


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)
    requests_wrapper = RequestsWrapper()
    tool = RequestsGetTool(requests_wrapper=requests_wrapper)
    content = tool.run("https://github.com/goldfishh/chatgpt-tool-hub")
    print(content)
