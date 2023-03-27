
from chatgpt_tool_hub.common.text_splitter import CharacterTextSplitter
from chatgpt_tool_hub.tools.web_requests import BaseRequestsTool
from chatgpt_tool_hub.tools.base_tool import BaseTool


class RequestsGetTool(BaseRequestsTool, BaseTool):
    """Tool for making a GET request to an API endpoint."""

    name = "requests_get"
    description = "A portal to the internet. Use this when you need to get specific content from a website. Input " \
                  "should be a  url (i.e. https://www.google.com). The output will be the text response of the GET " \
                  "request."

    def _run(self, url: str) -> str:
        """Run the tool."""
        content = self.requests_wrapper.get(url)
        return CharacterTextSplitter(chunk_size=2000).split_text(content)[0]

    async def _arun(self, url: str) -> str:
        """Run the tool asynchronously."""
        content = await self.requests_wrapper.aget(url)
        return CharacterTextSplitter(chunk_size=2000).split_text(content)[0]