import logging
import os
import tempfile
from typing import Any

from chatgpt_tool_hub.common.log import LOG
from chatgpt_tool_hub.tools import BrowserTool, SummaryTool
from chatgpt_tool_hub.tools.base_tool import BaseTool
from chatgpt_tool_hub.tools.news import news_tool_register
from chatgpt_tool_hub.tools.web_requests import RequestsWrapper

default_tool_name = "finance-news"


class FinanceNewsTool(BaseTool):
    
    name: str = default_tool_name
    description: str = (
        "Useful when you want to stay up-to-date on global real-time financial news."
        "The tool aggregates various types of data and information from the financial investment industry."
        "input is needless for this tool."
    )

    jin10_url: str = "https://www.jin10.com/example/jin10.com.html"

    def __init__(self, **tool_kwargs: Any):
        super().__init__()

    def _run(self, tool_input: str) -> str:
        # browser
        requests_wrapper = RequestsWrapper()
        _response = BrowserTool(requests_wrapper=requests_wrapper).run(self.jin10_url)

        # create temp file
        temp_file = tempfile.mkstemp()
        file_path = temp_file[1]
        # LOG.debug(f"temp_file_path: {file_path}")

        with open(file_path, "w") as f:
            f.write(_response + "\n")
        # summary
        _summary = SummaryTool().run(str(file_path) + ", 0")

        os.remove(file_path)
        return _summary

    async def _arun(self, tool_input: str) -> str:
        pass


news_tool_register.register_tool(default_tool_name, lambda kwargs: FinanceNewsTool(**kwargs), [])


if __name__ == "__main__":
    LOG.setLevel(logging.DEBUG)

    tool = FinanceNewsTool()
    content = tool.run("")
    print(content)
