import json
import logging

from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.web_requests import BaseRequestsTool, _parse_input, RequestsWrapper
from chatgpt_tool_hub.common.log import LOG


class RequestsPostTool(BaseRequestsTool, BaseTool):
    """Tool for making a POST request to an API endpoint."""

    name = "requests_post"
    description = """Use this when you want to POST to a website.
    Input should be a json string with two keys: "url" and "data".
    The value of "url" should be a string, and the value of "data" should be a dictionary of 
    key-value pairs you want to POST to the url.
    Be careful to always use double quotes for strings in the json string
    The output will be the text response of the POST request.
    """

    def _run(self, text: str) -> str:
        """Run the tool."""
        try:
            _data = _parse_input(text)
            _content = self.requests_wrapper.post(_data["url"], _data["data"])
            LOG.debug(f"[requests_post] output: {str(_content)}")
            return _content
        except Exception as e:
            LOG.error(f"[requests_post] {str(e)}")
            return repr(e)

    async def _arun(self, text: str) -> str:
        """Run the tool asynchronously."""
        try:
            _data = _parse_input(text)
            _content = await self.requests_wrapper.apost(_data["url"], _data["data"])
            LOG.debug(f"[requests_post] output: {str(_content)}")
            return _content
        except Exception as e:
            LOG.error(f"[requests_post] {str(e)}")
            return repr(e)


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)
    requests_wrapper = RequestsWrapper()
    url = "https://api.live.bilibili.com/xlive/web-room/v1/dM/gethistory"
    data = {
        "roomid": 10661147,
        "csrf_token": "",
        "csrf": "",
        "visit_id": "",
    }
    tool = RequestsPostTool(requests_wrapper=requests_wrapper)
    content = tool.run(json.dumps({"url": url, "data": data}))
    print(content)
