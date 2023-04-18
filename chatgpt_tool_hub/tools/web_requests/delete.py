from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.web_requests import BaseRequestsTool


class RequestsDeleteTool(BaseRequestsTool, BaseTool):
    """Tool for making a DELETE request to an API endpoint."""

    name = "requests_delete"
    description = (
        "A portal to the internet. Use this when you need to make a DELETE request to a URL. Input should "
        "be a specific url, and the output will be the text response of the DELETE request."
    )

    def _run(self, url: str) -> str:
        """Run the tool."""
        return self.requests_wrapper.delete(url)

    async def _arun(self, url: str) -> str:
        """Run the tool asynchronously."""
        return await self.requests_wrapper.adelete(url)