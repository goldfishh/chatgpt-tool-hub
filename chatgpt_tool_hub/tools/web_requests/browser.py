import logging

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.tools.all_tool_list import main_tool_register
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.web_requests import BaseRequestsTool, filter_text, RequestsWrapper

default_tool_name = "browser"


class BrowserTool(BaseRequestsTool, BaseTool):
    """Tool for making a GET request to an API endpoint."""

    name = default_tool_name
    description = (
        "A Google Chrome browser. Use this when you need to get specific content from a website. "
        "Input should be a url (i.e. https://github.com/goldfishh/chatgpt-tool-hub). The output "
        "will be the text response of the GET request. This tool has a higher priority than url-get tool."
    )

    def _run(self, url: str) -> str:
        """Run the tool."""
        try:
            html = self.requests_wrapper.get(url, use_browser=True)
            _content = filter_text(html)
            LOG.debug("[browser] output: " + str(_content))
        except Exception as e:
            LOG.error("[browser] " + str(e))
            _content = repr(e)
        return _content

    async def _arun(self, url: str) -> str:
        """Run the tool asynchronously."""
        raise NotImplementedError("not support run this tool in async")


main_tool_register.register_tool(default_tool_name, lambda _: BrowserTool(requests_wrapper=RequestsWrapper()), [])


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)
    requests_wrapper = RequestsWrapper()
    tool = BrowserTool(requests_wrapper=requests_wrapper)
    content = tool.run("https://github.com/goldfishh/chatgpt-tool-hub")
    print(content)
